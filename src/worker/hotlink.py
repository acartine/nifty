import logging
import sys

from nifty_common.constants import REDIS_TOPLIST_KEY
from nifty_common.helpers import get_redis, timestamp_ms
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


def run():
    # TODO configurable
    refresh_interval = 5
    ri_ms = refresh_interval*1000
    size = 10
    expiry = 10

    read = get_redis()
    channels = read.pubsub(ignore_subscribe_messages=True)
    channels.subscribe(Channel.action)
    redis = get_redis()
    toplist = TopList(expiry * 60, refresh_interval * 2)
    last_push_ms = timestamp_ms()
    running = True

    # TODO, catch ctrl-c
    while running:
        now_ms = timestamp_ms()

        # see if refresh interval has elapsed
        time_elapsed_ms = now_ms - last_push_ms
        if time_elapsed_ms >= ri_ms:
            mappings = {e.key: e.count for e in toplist.get(now_ms, size)}
            pipeline = redis.pipeline(transaction=True)
            pipeline.delete(REDIS_TOPLIST_KEY)
            if len(toplist) > 0:
                logging.debug(f"pushing to redis: {mappings}")
                pipeline.zadd(REDIS_TOPLIST_KEY, mappings)
            pipeline.execute()
            last_push_ms = now_ms
            time_elapsed_ms = 0

        # only block for the time left (roughly :-) )
        wait_time_sec = (ri_ms - time_elapsed_ms)/1000
        logging.debug(f"wait_time_sec={wait_time_sec}")
        msg = channels.get_message(True, wait_time_sec)
        if msg:
            payload = msg['data'].decode('UTF-8')
            action: Action = Action.parse_raw(payload)
            if action.type == ActionType.get:
                logging.debug(action)
                toplist.incr(action.link_id, action.at)


if __name__ == '__main__':
    run()
