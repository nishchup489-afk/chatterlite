import asyncio
import uuid

from fastapi import WebSocket 
from redis.asyncio import Redis 


import logging 
from dataclasses import dataclass , field 
from datetime import datetime , timezone 


logger = logging.getLogger(__name__)

# docs available on docs/websocketmanager


# GETTING CURRENT ISO TIMES 
def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# STORING ALL CONNECTION CLASS
@dataclass(slots=True)
class ClientConnection:

    """
    Represents one active WebSocket connection.

    One user can have multiple connections:
    - laptop tab
    - phone
    - second browser tab
    """
        

    connection_id : str                          # which connection 
    user_id : str                                # which user connected
    websocket : WebSocket                        # which socket connected
    device_id : str | None = None                # which device connected
    connected_at : str = field(default_factory=utc_now_iso)


class WebsocketManager:
    """
        ChatterLite WebSocket Manager.

        Responsibilities:
        - Track active WebSocket connections
        - Support multiple tabs/devices per user
        - Send messages to one user
        - Send messages to rooms
        - Track local room subscriptions
        - Track presence using Redis
        - Fan out events across multiple backend instances using Redis Pub/Sub

        NOT responsible for:
        - SQLAlchemy database writes
        - Message validation rules
        - Clerk authentication logic
        - Business authorization logic

        Keep those in service/router layers.
    """



# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% initialize everything %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    def __init__(
            self , 
            redis : Redis | None = None ,                           # pass redis url while using the class
            *,                                                        # after redis_url if you want to pass anything that needs to be with key
            redis_channel : str = "chatterlite:ws:events",            # redis channel for pub sub 
            presence_ttl_seconds : int = 60 ,                         # time to wait while reconnecting
            require_redis : bool = True                               # what if redis connection fails
    ) -> None :
        self.redis = redis               
        self.redis_channel = redis_channel 
        self.presence_ttl_seconds = presence_ttl_seconds 
        self.require_redis = require_redis 


        self.instance_id = str(uuid.uuid4())                         # if multiple server give each server an unique id               
        self._redis_listener_task = asyncio.Task[None] | None = None # when redis starts listen to redis
        self._started = False
        self._lock = asyncio.Lock()                                  # one corutine at a time 
        


        self.connections : dict[str , ClientConnection ] = {}
        self.user_connection : dict[str , set[str]] = {}
        self.room_connections : dict[str , set[str]] = {}
        self.connection_rooms : dict[str , set[str]] = {}


# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
#                              REDIS BINDING / LIFECYCLE 
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&



# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% Redis handoff , no more redis if websocket already started %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%



    def set_redis(self , redis: Redis) -> None:
        """
        Inject Redis after manager creation.

        Useful when manager is created globally but Redis is initialized
        inside FastAPI lifespan.
        """

        if self._started:
            raise RuntimeError("Cannot set redis after websocketmanager started")
        
        self.redis = redis


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% start websocket manager

    async def start(self) -> None :

        if self._started:
            return 
        
        if self.redis is  None:
            if self.require_redis:
                raise RuntimeError("Redis is required, but no redis client was provided")
            
            logger.warning(
                "WebSocketManager started without Redis. "
                "Only local WebSocket delivery will work."
            )

            self._started = True 
            return 
        
        try:
            await self.redis.ping() 
        except Exception :
            logger.exception("WebSocketManager could not ping Redis.")

            if self.require_redis:
                raise 

            self.redis = None 
            self._started = True 
            return
        
        self._redis_listener_task = asyncio.create_task(
            self._listen_to_redis() , 
            name="chatterlite-websocket-redis-listener"
        )

        self._started = True 

        logger.info(
            "WebSocketManager started. instance_id=%s redis_channel=%s",
            self.instance_id,
            self.redis_channel,
        )
        


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% stop websocket manager

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

        logger.info("WebSocketManager stopped")


    



# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% Connect %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


        


        
        







