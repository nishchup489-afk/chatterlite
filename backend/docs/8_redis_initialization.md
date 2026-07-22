# Redis Initialization

This document defines the standard Redis initialization pattern for the ChatterLite FastAPI backend.

The purpose of this phase is only to establish Redis as shared application infrastructure. Business features such as presence, caching, WebSocket delivery, and Pub/Sub will reuse this client later.

---

## Scope

### Included

* Redis package installation
* Redis URL configuration
* Async Redis client creation
* Startup connection verification
* Application-wide Redis client storage
* FastAPI dependency access
* Graceful Redis shutdown
* Redis health checking

### Not included yet

* Online/offline presence
* Heartbeats
* WebSocket connection records
* Redis Pub/Sub
* Cross-server event delivery
* Application caching
* Rate limiting
* Background workers

---

# 1. Architecture

```text
FastAPI starts
    │
    ▼
Create Redis client
    │
    ▼
PING Redis
    │
    ▼
Store client in application.state.redis
    │
    ▼
Application accepts requests
    │
    ▼
Routes and services reuse the shared client
    │
    ▼
FastAPI shuts down
    │
    ▼
Close Redis client and connection pool
```

The Redis client should be created once during application startup.

Do not create a new Redis client inside every route or service method.

---

# 2. Project structure

```text
backend/
├── .env
├── .env.example
├── pyproject.toml
│
└── src/
    └── chatterlite/
        ├── main.py
        │
        └── core/
            ├── config.py
            ├── database.py
            └── redis_client.py
```

---

# 3. Install Redis

From the backend root:

```powershell
poetry add redis
```

Verify the installation:

```powershell
poetry show redis
```

The installed package exposes its asynchronous client through:

```python
from redis.asyncio import Redis
```

Do not install the deprecated standalone `aioredis` package.

---

# 4. Configure Redis

Open:

```text
src/chatterlite/core/config.py
```

Add a Redis URL field to the application settings:

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ChatterLite"
    app_version: str = "0.1.0"
    debug: bool = False

    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    api_v1_prefix: str = "/api/v1"

    cors_origin: list[str] = [
        "http://localhost:3000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

The required Redis setting is:

```python
redis_url: str = "redis://localhost:6379/0"
```

---

# 5. Environment variables

Add this to `.env`:

```env
REDIS_URL=redis://localhost:6379/0
```

Add the same non-secret example to `.env.example`:

```env
REDIS_URL=redis://localhost:6379/0
```

Redis URL format:

```text
redis://host:port/database
```

Example:

```text
redis://localhost:6379/0
```

Meaning:

```text
localhost   Redis server host
6379        Default Redis port
0           Redis logical database
```

For ChatterLite, logical database `0` is enough.

---

# 6. Create the Redis client module

Create:

```text
src/chatterlite/core/redis_client.py
```

```python
import logging
from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis
from redis.exceptions import RedisError

from chatterlite.core.config import get_settings


logger = logging.getLogger(__name__)


def init_redis() -> Redis:
    """
    Create the application-wide asynchronous Redis client.

    Redis.from_url() creates a Redis client backed by an internal
    connection pool. The actual connection is usually established
    when the first Redis command is executed.
    """

    settings = get_settings()

    return Redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )


async def verify_redis_connection(
    redis_client: Redis,
) -> None:
    """
    Verify Redis connectivity during application startup.

    The application fails to start when Redis cannot be reached.
    """

    try:
        connected = await redis_client.ping()

    except RedisError as error:
        logger.exception(
            "Failed to connect to Redis."
        )

        raise RuntimeError(
            "Redis connection failed."
        ) from error

    if not connected:
        raise RuntimeError(
            "Redis connection verification failed."
        )

    logger.info(
        "Redis connection established successfully."
    )


async def close_redis(
    redis_client: Redis,
) -> None:
    """
    Close the Redis client and its internal connection pool.
    """

    await redis_client.aclose()

    logger.info(
        "Redis connection closed."
    )


def get_redis(
    request: Request,
) -> Redis:
    """
    Return the Redis client stored during application startup.

    Routes and services can use this function as a FastAPI
    dependency.
    """

    redis_client: Redis | None = getattr(
        request.app.state,
        "redis",
        None,
    )

    if redis_client is None:
        raise RuntimeError(
            "Redis has not been initialized."
        )

    return redis_client


RedisDependency = Annotated[
    Redis,
    Depends(get_redis),
]
```

---

# 7. Function responsibilities

## `init_redis()`

Creates one asynchronous Redis client:

```python
redis_client = Redis.from_url(...)
```

The client uses an internal connection pool.

It does not create a separate connection for every route.

---

## `verify_redis_connection()`

Executes:

```python
await redis_client.ping()
```

A successful response returns:

```python
True
```

If Redis is unavailable, startup fails clearly instead of allowing the application to run in a partially broken state.

---

## `close_redis()`

Executes:

```python
await redis_client.aclose()
```

This closes the Redis client and its internally managed connection pool.

---

## `get_redis()`

Reads the initialized client from:

```python
request.app.state.redis
```

This allows routes to receive Redis through FastAPI dependency injection.

---

# 8. Integrate Redis with FastAPI lifespan

Open:

```text
src/chatterlite/main.py
```

Use the following application lifecycle:

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chatterlite.api.router import api_router
from chatterlite.core.config import get_settings
from chatterlite.core.database import close_database
from chatterlite.core.redis_client import (
    close_redis,
    init_redis,
    verify_redis_connection,
)


@asynccontextmanager
async def lifespan(
    application: FastAPI,
) -> AsyncIterator[None]:
    """
    Manage application-wide startup and shutdown resources.
    """

    redis_client = init_redis()

    try:
        # Startup
        await verify_redis_connection(
            redis_client
        )

        application.state.redis = redis_client

        yield

    finally:
        # Shutdown
        await close_redis(
            redis_client
        )

        await close_database()


def create_application() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redocs",
        openapi_url="/openapi.json",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(
        api_router,
        prefix=settings.api_v1_prefix,
    )

    return application


app = create_application()
```

---

# 9. Lifespan execution order

The lifecycle runs like this:

```text
redis_client = init_redis()
        │
        ▼
await verify_redis_connection(redis_client)
        │
        ▼
application.state.redis = redis_client
        │
        ▼
yield
        │
        ▼
FastAPI serves requests
        │
        ▼
Application shutdown begins
        │
        ▼
await close_redis(redis_client)
        │
        ▼
await close_database()
```

The `yield` must remain inside the `try` block:

```python
try:
    # Startup
    yield

finally:
    # Shutdown
```

Do not place `yield` inside `finally`.

---

# 10. Why the lifespan parameter must be used

Incorrect:

```python
async def lifespan(
    _: FastAPI,
):
    app.state.redis = redis_client
```

The underscore indicates that the parameter is intentionally ignored.

Using the global `app` is also unsafe because the global application is created later.

Correct:

```python
async def lifespan(
    application: FastAPI,
):
    application.state.redis = redis_client
```

FastAPI directly passes the running application instance to the lifespan function.

---

# 11. Access Redis inside routes

A route can receive Redis through the reusable dependency alias:

```python
from fastapi import APIRouter

from chatterlite.core.redis_client import (
    RedisDependency,
)


router = APIRouter(
    prefix="/redis",
    tags=["Redis"],
)


@router.get("/test")
async def test_redis(
    redis_client: RedisDependency,
) -> dict[str, str | None]:
    await redis_client.set(
        "chatterlite:test",
        "working",
        ex=60,
    )

    value = await redis_client.get(
        "chatterlite:test"
    )

    return {
        "value": value,
    }
```

The route does not initialize or close Redis.

It only uses the shared application client.

---

# 12. Redis health-check route

Create or update:

```text
src/chatterlite/api/routes/health.py
```

```python
from fastapi import APIRouter

from chatterlite.core.redis_client import (
    RedisDependency,
)


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("")
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
    }


@router.get("/redis")
async def redis_health_check(
    redis_client: RedisDependency,
) -> dict[str, str]:
    connected = await redis_client.ping()

    return {
        "status": "healthy",
        "redis": (
            "connected"
            if connected
            else "disconnected"
        ),
    }
```

Include the health router inside:

```text
src/chatterlite/api/router.py
```

```python
from fastapi import APIRouter

from chatterlite.api.routes.health import (
    router as health_router,
)


api_router = APIRouter()

api_router.include_router(
    health_router
)
```

---

# 13. Run Redis locally

Installing the Python `redis` package does not install the Redis server.

You still need a Redis server running at:

```text
localhost:6379
```

A Docker-based Redis server can be started with:

```powershell
docker run --name chatterlite-redis -p 6379:6379 -d redis:7-alpine
```

Verify the container:

```powershell
docker ps
```

Expected port mapping:

```text
0.0.0.0:6379->6379/tcp
```

Stop Redis:

```powershell
docker stop chatterlite-redis
```

Start it again:

```powershell
docker start chatterlite-redis
```

---

# 14. Start FastAPI

From the backend root:

```powershell
poetry run uvicorn chatterlite.main:app --reload
```

Expected behavior:

```text
Redis client created
Redis PING succeeds
Application startup completes
```

Test:

```text
http://localhost:8000/api/v1/health/redis
```

Expected response:

```json
{
  "status": "healthy",
  "redis": "connected"
}
```

---

# 15. Direct Redis test

You can verify Redis independently of FastAPI:

```powershell
poetry run python
```

Then run:

```python
import asyncio

from redis.asyncio import Redis


async def test_redis() -> None:
    redis_client = Redis.from_url(
        "redis://localhost:6379/0",
        decode_responses=True,
    )

    try:
        print(
            await redis_client.ping()
        )

        await redis_client.set(
            "chatterlite:test",
            "working",
            ex=30,
        )

        print(
            await redis_client.get(
                "chatterlite:test"
            )
        )

    finally:
        await redis_client.aclose()


asyncio.run(test_redis())
```

Expected output:

```text
True
working
```

The key expires automatically after 30 seconds.

---

# 16. Failure behavior

If Redis is not running, this line fails:

```python
await verify_redis_connection(
    redis_client
)
```

FastAPI should refuse to complete startup.

This is intentional when Redis is a required dependency.

The error should clearly indicate:

```text
Redis connection failed.
```

After starting Redis, restart FastAPI.

---

# 17. Rules

## Create Redis once

Correct:

```text
FastAPI startup
→ one Redis client
→ reused by routes and services
→ closed during shutdown
```

Incorrect:

```python
@router.get("/example")
async def example():
    redis_client = Redis.from_url(...)
```

That unnecessarily creates clients throughout the application.

---

## Store temporary data only

Redis will later store:

```text
Current online presence
Connection records
Heartbeat expiration
Temporary cache entries
Rate-limit counters
Pub/Sub events
```

Redis should not become the permanent source of truth for:

```text
Users
Conversations
Messages
Notifications
Last-seen history
```

Those belong in PostgreSQL.

---

## Do not close Redis inside routes

Incorrect:

```python
@router.get("/example")
async def example(
    redis_client: RedisDependency,
):
    value = await redis_client.get("key")
    await redis_client.aclose()
```

Closing it there would break the shared client for the rest of the application.

Only the lifespan shutdown logic should close Redis.

---

# 18. Later-phase usage

The initialized Redis client will be reused in later phases.

## Presence phase

```text
presence:connection:{connection_id}
presence:user:{user_id}:connections
presence:expirations
```

## WebSocket cross-server phase

```text
Redis Pub/Sub channel
Targeted user events
Multi-instance delivery
```

## Hardening phase

```text
Rate limiting
Temporary cache entries
Distributed locks
```

No new Redis initialization system will be required. These features will use the same shared client.

---

# 19. Completion checklist

```text
✅ redis package installed
✅ REDIS_URL added to Settings
✅ REDIS_URL added to .env
✅ REDIS_URL added to .env.example
✅ core/redis_client.py created
✅ Redis client created once
✅ Redis connectivity verified during startup
✅ Redis stored in application.state.redis
✅ get_redis dependency created
✅ RedisDependency alias created
✅ Redis closed during shutdown
✅ Database engine closed during shutdown
✅ Redis health endpoint works
✅ No presence logic added yet
✅ No Pub/Sub logic added yet
✅ No WebSocket logic added yet
```

---

# Final source-of-truth rule

```text
PostgreSQL stores permanent application data.

Redis stores temporary live state.

FastAPI lifespan owns the Redis client lifecycle.
```
