import redis.asyncio as redis

from app.core.settings import settings


redis_pool = redis.ConnectionPool.from_url(
    settings.REDIS_URL, 
    decode_responses=True
)

def get_redis() -> redis.Redis:
    return redis.Redis(connection_pool=redis_pool)