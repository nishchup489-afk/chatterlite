from redis.asyncio import Redis, RedisError 
from chatterlite.core.config import get_settings 
import logging


settings = get_settings()
redis_client : Redis | None = None 

logger = logging.getLogger(__name__)


async def init_redis() -> Redis:
    global redis_client 

    redis_client = Redis.from_url(
        settings.redis_url , 
        encoding = "utf-8",
        decode_responses = True ,
        socket_connect_timeout = 2 , 
        socket_timeout = 2
    )



    return redis_client



async def verify_redis_connection(
        redis : Redis
):
    try:
        is_connected = redis.ping()
    except RedisError as error:
        logger.exception(
            "could not connect to redis"
        )

        raise RuntimeError(
            "Redis connection failed"
        ) from error
    
    if not is_connected:
        raise RuntimeError("Redis not connected")
    
    logger.info("Redis connected successfully")




async def close_redis():
    global redis_client 

    if redis_client is not None :
        redis_client.aclose()
        redis_client = None


def get_redis():
    if not redis_client:
        raise RuntimeError("Redis not found")
    
    return redis_client
