import logging
import sys
import time
from typing import Dict, NamedTuple, Set

from redis.client import Redis

from nifty_common.claim import claim
from nifty_common.config import cfg
from nifty_common.constants import REDIS_TRENDING_KEY, REDIS_TRENDING_SIZE_KEY
from nifty_common.helpers import get_redis, retry, timestamp_ms, trending_size
from nifty_common.types import Action, ActionType, Channel
from toplist import AbstractTopList, RedisTopList

log_level_val = getattr(logging, "DEBUG")
print(f"Log level set to {log_level_val}")
root = logging.getLogger()
root.setLevel(log_level_val)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(log_level_val)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)


# redis doesn't really have great datastructures for this
# time series would have been best, but it doesn't support
# dynamic labels or aggregations limits in order

# we can run multiples of these in parallel for reliability
# they will overwrite each other but we don't need it to be exact

class TopLink(NamedTuple):
    id: int
    short_url: str
    long_url: str


def handle(msg: Dict[str, any], redis: Redis, toplist: AbstractTopList[str]):
    action: Action = Action.parse_raw(msg['data'])
    if action.type == ActionType.get:
        logging.debug(action)
        if claim(redis, f"{__name__}:{action.uuid}", 60):
            toplist.incr(action.short_url, min(action.at, timestamp_ms()))


@retry(max_tries=3, stack_id=__name__)
def set_size(redis: Redis):
    newsize = cfg.getint('trending', 'size')
    with redis.pipeline() as pipe:
        pipe.watch(REDIS_TRENDING_SIZE_KEY)
        cursize = trending_size(pipe, throws=False)
        if newsize != cursize:
            pipe.multi()
            pipe.set(REDIS_TRENDING_SIZE_KEY, newsize).execute()


def on_toplist_change(added: Set[str], removed: Set[str]):
    logging.debug(f"Added: {added}  Removed: {removed}")


def run():
    refresh_interval = cfg.getint('trending', 'refresh_sec')
    read = get_redis()
    channels = read.pubsub(ignore_subscribe_messages=True)
    channels.subscribe(Channel.action)
    before = time.time()
    remaining = refresh_interval

    running = True
    redis = get_redis()
    set_size(redis)
    toplist = RedisTopList(
        REDIS_TRENDING_KEY,
        cfg.getint('trending', 'interval_sec'),
        redis,
        listener=on_toplist_change,
        ctor=str,
        bucket_len_sec=cfg.getint('trending', 'bucket_len_sec'))

    # TODO, catch ctrl-c
    while running:
        logging.debug(f"next refresh in {remaining}")
        msg = channels.get_message(True, remaining)
        if msg:
            handle(msg, redis, toplist)
        else:
            toplist.reap(timestamp_ms())

        now = time.time()
        remaining -= now - before
        before = now
        if remaining <= 0:
            remaining = refresh_interval


if __name__ == '__main__':
    run()
