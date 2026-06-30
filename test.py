# app/websockets/manager.py

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

from fastapi import WebSocket
from redis.asyncio import Redis


logger = logging.getLogger(__name__)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class ClientConnection:
    """
    Represents one active WebSocket connection.

    One user can have multiple connections:
    - laptop tab
    - phone
    - second browser tab
    """

    connection_id: str
    user_id: str
    websocket: WebSocket
    device_id: str | None = None
    connected_at: str = field(default_factory=utc_now_iso)


class WebSocketManager:
    """
    ChatterLite WebSocket Manager.

    Responsibilities:
    - Track active WebSocket connections
    - Support multiple tabs/devices per user
    - Send messages to one user
    - Send messages to rooms
    - Track room membership
    - Track online/offline presence using Redis
    - Fan out events across multiple backend servers using Redis Pub/Sub

    Not responsible for:
    - Creating Redis connection
    - Closing Redis connection
    - Saving messages to database
    - Clerk authentication
    - Room permission checking
    - Message validation/business rules

    Redis should come from app/core/redis.py.
    """

    def __init__(
        self,
        redis: Redis | None = None,
        *,
        redis_channel: str = "chatterlite:ws:events",
        presence_ttl_seconds: int = 60,
        require_redis: bool = False,
    ) -> None:
        # Redis is injected from outside.
        # Manager does not create Redis itself.
        self.redis = redis
        self.redis_channel = redis_channel
        self.presence_ttl_seconds = presence_ttl_seconds
        self.require_redis = require_redis

        # Unique ID for this backend server instance.
        # Helps prevent receiving your own Redis Pub/Sub event twice.
        self.instance_id = str(uuid.uuid4())

        # Background task that listens to Redis Pub/Sub.
        self._redis_listener_task: asyncio.Task[None] | None = None
        self._started = False

        # Protects shared dictionaries from race conditions.
        self._lock = asyncio.Lock()

        # connection_id -> ClientConnection
        self.connections: dict[str, ClientConnection] = {}

        # user_id -> set(connection_id)
        self.user_connections: dict[str, set[str]] = {}

        # room_id -> set(connection_id)
        self.room_connections: dict[str, set[str]] = {}

        # connection_id -> set(room_id)
        self.connection_rooms: dict[str, set[str]] = {}

    # -------------------------------------------------------------------------
    # Redis binding / lifecycle
    # -------------------------------------------------------------------------

    def set_redis(self, redis: Redis) -> None:
        """
        Inject Redis after manager creation.

        Useful when manager is created globally but Redis is initialized
        inside FastAPI lifespan.
        """
        if self._started:
            raise RuntimeError("Cannot set Redis after WebSocketManager has started.")

        self.redis = redis

    async def start(self) -> None:
        """
        Start the WebSocket manager.

        This does not create Redis.
        It only checks the existing Redis client and starts the Pub/Sub listener.
        """
        if self._started:
            return

        if self.redis is None:
            if self.require_redis:
                raise RuntimeError("Redis is required, but no Redis client was provided.")

            logger.warning(
                "WebSocketManager started without Redis. "
                "Only local WebSocket delivery will work."
            )
            self._started = True
            return

        try:
            await self.redis.ping()
        except Exception:
            logger.exception("WebSocketManager could not ping Redis.")

            if self.require_redis:
                raise

            self.redis = None
            self._started = True
            return

        self._redis_listener_task = asyncio.create_task(
            self._listen_to_redis(),
            name="chatterlite-websocket-redis-listener",
        )

        self._started = True

        logger.info(
            "WebSocketManager started. instance_id=%s redis_channel=%s",
            self.instance_id,
            self.redis_channel,
        )

    async def stop(self) -> None:
        """
        Stop the WebSocket manager.

        Important:
        This does not close Redis.
        Redis is owned by app/core/redis.py.
        """
        if self._redis_listener_task is not None:
            self._redis_listener_task.cancel()

            try:
                await self._redis_listener_task
            except asyncio.CancelledError:
                pass

            self._redis_listener_task = None

        self._started = False

        logger.info("WebSocketManager stopped.")

    # -------------------------------------------------------------------------
    # Connection handling
    # -------------------------------------------------------------------------

    async def connect(
        self,
        websocket: WebSocket,
        *,
        user_id: str,
        device_id: str | None = None,
    ) -> str:
        """
        Accept and register one WebSocket connection.

        Returns:
            connection_id
        """
        await websocket.accept()

        connection_id = str(uuid.uuid4())

        connection = ClientConnection(
            connection_id=connection_id,
            user_id=user_id,
            websocket=websocket,
            device_id=device_id,
        )

        async with self._lock:
            self.connections[connection_id] = connection

            self.user_connections.setdefault(user_id, set()).add(connection_id)
            self.connection_rooms[connection_id] = set()

        await self._mark_connection_online(connection_id, user_id)

        await self._publish_event(
            {
                "kind": "presence",
                "event": "user.online",
                "user_id": user_id,
            }
        )

        logger.info(
            "WebSocket connected. user_id=%s connection_id=%s device_id=%s",
            user_id,
            connection_id,
            device_id,
        )

        return connection_id

    async def disconnect(self, connection_id: str) -> None:
        """
        Remove one WebSocket connection and clean up all local + Redis presence state.
        """
        async with self._lock:
            connection = self.connections.pop(connection_id, None)

            if connection is None:
                return

            user_id = connection.user_id

            user_connection_ids = self.user_connections.get(user_id)

            if user_connection_ids is not None:
                user_connection_ids.discard(connection_id)

                if not user_connection_ids:
                    self.user_connections.pop(user_id, None)

            joined_rooms = self.connection_rooms.pop(connection_id, set())

            for room_id in joined_rooms:
                room_connection_ids = self.room_connections.get(room_id)

                if room_connection_ids is None:
                    continue

                room_connection_ids.discard(connection_id)

                if not room_connection_ids:
                    self.room_connections.pop(room_id, None)

        await self._remove_connection_presence(connection_id, user_id)

        user_is_still_online = await self.is_user_online(user_id)

        if not user_is_still_online:
            await self._publish_event(
                {
                    "kind": "presence",
                    "event": "user.offline",
                    "user_id": user_id,
                }
            )

        try:
            await connection.websocket.close()
        except Exception:
            # Usually already closed. Not a big deal.
            pass

        logger.info(
            "WebSocket disconnected. user_id=%s connection_id=%s",
            user_id,
            connection_id,
        )

    # -------------------------------------------------------------------------
    # Room handling
    # -------------------------------------------------------------------------

    async def join_room(self, connection_id: str, room_id: str) -> None:
        """
        Add one connection to one room.

        Permission check should happen before this method.
        Example:
            allowed = await room_service.can_join_room(user_id, room_id)
        """
        async with self._lock:
            if connection_id not in self.connections:
                raise ValueError("Connection does not exist.")

            self.room_connections.setdefault(room_id, set()).add(connection_id)
            self.connection_rooms.setdefault(connection_id, set()).add(room_id)

        logger.info(
            "Connection joined room. connection_id=%s room_id=%s",
            connection_id,
            room_id,
        )

    async def leave_room(self, connection_id: str, room_id: str) -> None:
        """
        Remove one connection from one room.
        """
        async with self._lock:
            room_connection_ids = self.room_connections.get(room_id)

            if room_connection_ids is not None:
                room_connection_ids.discard(connection_id)

                if not room_connection_ids:
                    self.room_connections.pop(room_id, None)

            joined_rooms = self.connection_rooms.get(connection_id)

            if joined_rooms is not None:
                joined_rooms.discard(room_id)

        logger.info(
            "Connection left room. connection_id=%s room_id=%s",
            connection_id,
            room_id,
        )

    async def leave_all_rooms(self, connection_id: str) -> None:
        """
        Remove one connection from all rooms.
        """
        async with self._lock:
            joined_rooms = self.connection_rooms.pop(connection_id, set())

            for room_id in joined_rooms:
                room_connection_ids = self.room_connections.get(room_id)

                if room_connection_ids is None:
                    continue

                room_connection_ids.discard(connection_id)

                if not room_connection_ids:
                    self.room_connections.pop(room_id, None)

        logger.info("Connection left all rooms. connection_id=%s", connection_id)

    # -------------------------------------------------------------------------
    # Sending messages
    # -------------------------------------------------------------------------

    async def send_to_connection(
        self,
        connection_id: str,
        payload: dict[str, Any],
    ) -> bool:
        """
        Send payload to one exact WebSocket connection.
        """
        async with self._lock:
            connection = self.connections.get(connection_id)

        if connection is None:
            return False

        return await self._safe_send(connection, payload)

    async def send_to_user(
        self,
        user_id: str,
        payload: dict[str, Any],
        *,
        publish: bool = True,
    ) -> int:
        """
        Send payload to every local connection of this user.

        If Redis is enabled and publish=True, other backend instances
        will also receive the event and deliver it to their local sockets.
        """
        delivered_count = await self._deliver_to_user_local(user_id, payload)

        if publish:
            await self._publish_event(
                {
                    "kind": "user.message",
                    "target_user_id": user_id,
                    "payload": payload,
                }
            )

        return delivered_count

    async def send_to_room(
        self,
        room_id: str,
        payload: dict[str, Any],
        *,
        publish: bool = True,
    ) -> int:
        """
        Send payload to every local connection inside this room.

        If Redis is enabled and publish=True, other backend instances
        will also receive the event and deliver it to their local room sockets.
        """
        delivered_count = await self._deliver_to_room_local(room_id, payload)

        if publish:
            await self._publish_event(
                {
                    "kind": "room.message",
                    "room_id": room_id,
                    "payload": payload,
                }
            )

        return delivered_count

    async def broadcast_local(self, payload: dict[str, Any]) -> int:
        """
        Send payload to every socket connected to this backend instance.

        Usually useful for admin/dev/debug events.
        """
        async with self._lock:
            connections = list(self.connections.values())

        return await self._send_to_many(connections, payload)

    # -------------------------------------------------------------------------
    # Heartbeat / presence
    # -------------------------------------------------------------------------

    async def heartbeat(
        self,
        connection_id: str,
        *,
        interval_seconds: int = 25,
    ) -> None:
        """
        Application-level heartbeat.

        Browser WebSocket clients do not expose raw ping/pong control cleanly,
        so this sends JSON ping events.

        Frontend may respond with:
            { "type": "pong" }
        """
        while True:
            await asyncio.sleep(interval_seconds)

            async with self._lock:
                connection = self.connections.get(connection_id)

            if connection is None:
                return

            ok = await self._safe_send(
                connection,
                {
                    "type": "ping",
                    "connection_id": connection_id,
                    "server_time": utc_now_iso(),
                },
            )

            if not ok:
                await self.disconnect(connection_id)
                return

            await self._refresh_connection_presence(
                connection_id,
                connection.user_id,
            )

    async def is_user_online(self, user_id: str) -> bool:
        """
        Check if user is online.

        First checks local memory.
        Then checks Redis presence if available.
        """
        async with self._lock:
            if self.user_connections.get(user_id):
                return True

        if self.redis is None:
            return False

        alive_count = await self._cleanup_user_presence(user_id)
        return alive_count > 0

    async def get_online_connection_count(self, user_id: str) -> int:
        """
        Return how many active connections a user has.

        Local count is exact for this server.
        Redis count may include connections from other servers.
        """
        local_count = 0

        async with self._lock:
            local_count = len(self.user_connections.get(user_id, set()))

        if self.redis is None:
            return local_count

        return await self._cleanup_user_presence(user_id)

    # -------------------------------------------------------------------------
    # Local delivery internals
    # -------------------------------------------------------------------------

    async def _deliver_to_user_local(
        self,
        user_id: str,
        payload: dict[str, Any],
    ) -> int:
        async with self._lock:
            connection_ids = list(self.user_connections.get(user_id, set()))

            connections = [
                self.connections[connection_id]
                for connection_id in connection_ids
                if connection_id in self.connections
            ]

        return await self._send_to_many(connections, payload)

    async def _deliver_to_room_local(
        self,
        room_id: str,
        payload: dict[str, Any],
    ) -> int:
        async with self._lock:
            connection_ids = list(self.room_connections.get(room_id, set()))

            connections = [
                self.connections[connection_id]
                for connection_id in connection_ids
                if connection_id in self.connections
            ]

        return await self._send_to_many(connections, payload)

    async def _send_to_many(
        self,
        connections: Iterable[ClientConnection],
        payload: dict[str, Any],
    ) -> int:
        results = await asyncio.gather(
            *(self._safe_send(connection, payload) for connection in connections),
            return_exceptions=True,
        )

        delivered_count = 0

        for result in results:
            if result is True:
                delivered_count += 1

        return delivered_count

    async def _safe_send(
        self,
        connection: ClientConnection,
        payload: dict[str, Any],
    ) -> bool:
        try:
            await connection.websocket.send_json(payload)
            return True

        except Exception:
            logger.exception(
                "Failed to send WebSocket payload. user_id=%s connection_id=%s",
                connection.user_id,
                connection.connection_id,
            )

            await self.disconnect(connection.connection_id)
            return False

    # -------------------------------------------------------------------------
    # Redis Pub/Sub
    # -------------------------------------------------------------------------

    async def _publish_event(self, event: dict[str, Any]) -> None:
        """
        Publish an event to Redis so other backend instances can receive it.

        Redis Pub/Sub is for live fanout only.
        It does not save message history.
        """
        if self.redis is None:
            return

        event["origin_instance_id"] = self.instance_id
        event["published_at"] = utc_now_iso()

        try:
            await self.redis.publish(
                self.redis_channel,
                json.dumps(event, separators=(",", ":")),
            )

        except Exception:
            logger.exception("Failed to publish WebSocket event to Redis.")

    async def _listen_to_redis(self) -> None:
        """
        Listen for Redis Pub/Sub events from other backend instances.
        """
        if self.redis is None:
            return

        pubsub = self.redis.pubsub()

        try:
            await pubsub.subscribe(self.redis_channel)

            logger.info("Listening to Redis channel: %s", self.redis_channel)

            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )

                if message is None:
                    await asyncio.sleep(0.01)
                    continue

                raw_data = message.get("data")

                if not raw_data:
                    continue

                try:
                    event = json.loads(raw_data)
                except json.JSONDecodeError:
                    logger.warning("Invalid Redis Pub/Sub event: %s", raw_data)
                    continue

                # Ignore events published by this same backend instance.
                if event.get("origin_instance_id") == self.instance_id:
                    continue

                await self._handle_redis_event(event)

        except asyncio.CancelledError:
            raise

        except Exception:
            logger.exception("Redis Pub/Sub listener crashed.")

        finally:
            try:
                await pubsub.unsubscribe(self.redis_channel)
                await pubsub.aclose()
            except Exception:
                pass

    async def _handle_redis_event(self, event: dict[str, Any]) -> None:
        """
        Handle one Redis Pub/Sub event.
        """
        kind = event.get("kind")

        if kind == "user.message":
            target_user_id = event.get("target_user_id")
            payload = event.get("payload")

            if isinstance(target_user_id, str) and isinstance(payload, dict):
                await self._deliver_to_user_local(target_user_id, payload)

            return

        if kind == "room.message":
            room_id = event.get("room_id")
            payload = event.get("payload")

            if isinstance(room_id, str) and isinstance(payload, dict):
                await self._deliver_to_room_local(room_id, payload)

            return

        if kind == "presence":
            logger.debug("Presence event received: %s", event)
            return

        logger.warning("Unknown Redis Pub/Sub event kind: %s", kind)

    # -------------------------------------------------------------------------
    # Redis presence
    # -------------------------------------------------------------------------

    def _connection_presence_key(self, connection_id: str) -> str:
        return f"presence:connection:{connection_id}"

    def _user_connections_key(self, user_id: str) -> str:
        return f"presence:user:{user_id}:connections"

    async def _mark_connection_online(
        self,
        connection_id: str,
        user_id: str,
    ) -> None:
        """
        Mark one connection as online in Redis.
        """
        if self.redis is None:
            return

        connection_key = self._connection_presence_key(connection_id)
        user_key = self._user_connections_key(user_id)

        try:
            async with self.redis.pipeline(transaction=True) as pipe:
                pipe.setex(
                    connection_key,
                    self.presence_ttl_seconds,
                    user_id,
                )
                pipe.sadd(user_key, connection_id)
                pipe.expire(user_key, self.presence_ttl_seconds * 2)

                await pipe.execute()

        except Exception:
            logger.exception(
                "Failed to mark connection online. user_id=%s connection_id=%s",
                user_id,
                connection_id,
            )

    async def _refresh_connection_presence(
        self,
        connection_id: str,
        user_id: str,
    ) -> None:
        """
        Refresh Redis TTL for one active connection.
        """
        if self.redis is None:
            return

        connection_key = self._connection_presence_key(connection_id)
        user_key = self._user_connections_key(user_id)

        try:
            async with self.redis.pipeline(transaction=True) as pipe:
                pipe.expire(connection_key, self.presence_ttl_seconds)
                pipe.expire(user_key, self.presence_ttl_seconds * 2)

                await pipe.execute()

        except Exception:
            logger.exception(
                "Failed to refresh connection presence. user_id=%s connection_id=%s",
                user_id,
                connection_id,
            )

    async def _remove_connection_presence(
        self,
        connection_id: str,
        user_id: str,
    ) -> None:
        """
        Remove one connection from Redis presence.
        """
        if self.redis is None:
            return

        connection_key = self._connection_presence_key(connection_id)
        user_key = self._user_connections_key(user_id)

        try:
            async with self.redis.pipeline(transaction=True) as pipe:
                pipe.delete(connection_key)
                pipe.srem(user_key, connection_id)

                await pipe.execute()

            await self._cleanup_user_presence(user_id)

        except Exception:
            logger.exception(
                "Failed to remove connection presence. user_id=%s connection_id=%s",
                user_id,
                connection_id,
            )

    async def _cleanup_user_presence(self, user_id: str) -> int:
        """
        Remove stale Redis connection IDs and return alive connection count.
        """
        if self.redis is None:
            return 0

        user_key = self._user_connections_key(user_id)

        try:
            raw_connection_ids = await self.redis.smembers(user_key)
            connection_ids = list(raw_connection_ids)

            if not connection_ids:
                return 0

            async with self.redis.pipeline(transaction=False) as pipe:
                for connection_id in connection_ids:
                    pipe.exists(self._connection_presence_key(connection_id))

                exists_results = await pipe.execute()

            stale_connection_ids = [
                connection_id
                for connection_id, exists in zip(connection_ids, exists_results)
                if not exists
            ]

            if stale_connection_ids:
                await self.redis.srem(user_key, *stale_connection_ids)

            alive_count = len(connection_ids) - len(stale_connection_ids)

            if alive_count > 0:
                await self.redis.expire(
                    user_key,
                    self.presence_ttl_seconds * 2,
                )

            return alive_count

        except Exception:
            logger.exception("Failed to cleanup user presence. user_id=%s", user_id)
            return 0