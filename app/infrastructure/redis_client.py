from redis.asyncio import Redis

from app.config import settings

client: Redis | None = None


async def open_redis_client() -> None:
    global client
    client = Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_timeout=3)


async def close_redis_client() -> None:
    if client is not None:
        await client.aclose()


def get_redis_client() -> Redis:
    if client is None:
        raise RuntimeError("Redis client is not initiated. Did the app startup run?")
    return client