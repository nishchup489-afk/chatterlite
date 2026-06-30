from redis.asyncio import Redis
from dotenv import load_dotenv
import os

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")

redis_client: Redis | None = None


async def init_redis() -> Redis:
    global redis_client

    if not REDIS_URL:
        raise RuntimeError("REDIS_URL is not set")

    redis_client = Redis.from_url(
        REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=2,
    )

    await redis_client.ping()
    return redis_client


async def close_redis() -> None:
    global redis_client

    if redis_client is not None:
        await redis_client.aclose()
        redis_client = None


def get_redis() -> Redis:
    if redis_client is None:
        raise RuntimeError("Redis client not initialized")

    return redis_client