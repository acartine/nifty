import time

from redis.client import Redis

from nifty_common.config import cfg


def get_redis() -> Redis:
    return Redis(host=cfg['redis']['host'], username=cfg['redis']['user'],
                 password=cfg['redis']['pwd'])


def timestamp_ms() -> int:
    return int(time.time() * 1000)
