from app.exceptions import RateLimitExceededException
from app.infrastructure.redis_client import get_redis_client


async def rate_limit(limit: int, window: int, name: str) -> None:
    redis = get_redis_client()
    key = f"ratelimit:{name}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, window)
    if count > limit:
        raise RateLimitExceededException()