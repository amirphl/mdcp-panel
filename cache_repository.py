import os
import redis

REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = int(os.getenv('REDIS_PORT'))

assert REDIS_HOST is not None
assert REDIS_PORT is not None

class CacheRepository:
    redis_connection = None

    @staticmethod
    def store(key, value, expire_in_seconds):
        redis_connection = CacheRepository.__get_redis_connection()
        redis_connection.set(key, value, expire_in_seconds)

    @staticmethod
    def get(key, get_as_string=True):
        redis_connection = CacheRepository.__get_redis_connection()
        value = redis_connection.get(key)
        if get_as_string and value is not None:
            value = value.decode("utf-8")
        return value
    
    @staticmethod
    def get_scan_iter(key_pattern):
        redis_connection = CacheRepository.__get_redis_connection()
        return redis_connection.scan_iter(key_pattern)

    @staticmethod
    def delete(key):
        redis_connection = CacheRepository.__get_redis_connection()
        redis_connection.delete(key)

    @staticmethod
    def __get_redis_connection():
        if CacheRepository.redis_connection is None:
            CacheRepository.redis_connection = redis.Redis(
                host=REDIS_HOST, port=REDIS_PORT, db=0)
        return CacheRepository.redis_connection
