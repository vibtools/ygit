from redis.asyncio import Redis
from backend.core.config import get_settings
_redis: Redis | None = None

def get_redis() -> Redis:
    global _redis
    if _redis is None:
        settings = get_settings()
        _redis = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis

async def redis_health() -> str:
    client = get_redis()
    pong = await client.ping()
    return "ok" if pong else "error"
