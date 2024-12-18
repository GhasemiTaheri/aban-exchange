from django.conf import REDIS_URL
from redis import Redis


class RedisConnector:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "ـredis"):
            self._redis = Redis.from_url(REDIS_URL, decode_response=True)

    def get_connection(self):
        return self._redis
