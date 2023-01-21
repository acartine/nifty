import redis
import os
import logging

# for local usage, add 'localhost' to your .env
logger = logging.getLogger(__name__)
redis_host = os.environ.get('REDIS_HOST', 'redis')
logger.info(f"Using '{redis_host}'")
r = redis.Redis(host=redis_host, port=6379, decode_responses=True)


class Store:
    def __init__(self, namespace):
        self.namespace = namespace

    def __wrap(self, key):
        return key if self.namespace is None else f"{self.namespace}_{key}"

    def set(self, key, value):
        wrapped_key = self.__wrap(key)
        logger.debug(f"Storing {wrapped_key} = {value}")
        r.set(wrapped_key, value)

    def get(self, key):
        wrapped_key = self.__wrap(key)
        value = r.get(wrapped_key)
        logger.debug(f"Retrieved {wrapped_key} = {value}")
        return value
