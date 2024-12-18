import aioredis
from django.conf import settings


class RedisConnector:
    _instance = None
    _redis = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    @classmethod
    def get_connection(cls):
        if cls._redis is None:
            cls._redis = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )
        return cls._redis

    @classmethod
    async def aget_connection(cls):
        if cls._redis is None:
            cls._redis = await aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )
        return cls._redis
