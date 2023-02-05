import logging
import sys
import time

from redis.client import Redis

from nifty.constants import REDIS_TOPLIST_KEY
from nifty_common.helpers import get_redis
from nifty_common.types import Action, ActionType, Channel
from worker.top_list import TopList

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
def _update_hotlinks(redis: Redis, toplist: TopList, now: int, size: int):
    mappings = {e.key: e.count for e in toplist.get(now, size)}
    pipeline = redis.pipeline(transaction=True)
    pipeline.delete(REDIS_TOPLIST_KEY)

    if len(toplist) > 0:
        logging.debug(f"uploading {mappings}")
        pipeline.zadd(REDIS_TOPLIST_KEY, mappings)

    pipeline.execute()


def main():
    # TODO configurable
    refresh_interval = 5
    size = 10
    expiry = 15

    read = get_redis()
    channels = read.pubsub(ignore_subscribe_messages=True)
    channels.subscribe(Channel.action)
    redis = get_redis()
    toplist = TopList(expiry * 60, refresh_interval * 2)
    last_push = int(time.time())
    running = True

    # TODO, catch ctrl-c
    while running:
        now = int(time.time())
        time_elapsed = now - last_push
        logging.debug(f"now={now} time_elapsed={time_elapsed} refresh_interval={refresh_interval}")
        if time_elapsed >= refresh_interval:
            _update_hotlinks(redis, toplist, now, size)
            last_push = now
            time_elapsed = 0
        wait_time = refresh_interval - time_elapsed
        logging.debug(f"wait_time={wait_time}")
        msg = channels.get_message(True, wait_time)
        logging.debug(msg)
        if msg:
            payload = msg['data'].decode('UTF-8')
            print(payload)
            action: Action = Action.parse_raw(payload)
            if action.type == ActionType.get:
                toplist.incr(action.url, action.at)


if __name__ == '__main__':
    main()
