import logging
import sys
from typing import Dict, NamedTuple

from hotlink_worker.top_list import AbstractTopList, RedisTopList
from nifty_common.helpers import get_redis, timestamp_ms
from nifty_common.types import Action, ActionType, Channel

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


def handle(msg: Dict[str, any], toplist: AbstractTopList[str]):
    payload = msg['data'].decode('UTF-8')
    action: Action = Action.parse_raw(payload)
    if action.type == ActionType.get:
        logging.debug(action)
        toplist.incr(action.short_url, min(action.at, timestamp_ms()))


def run():
    # TODO configurable
    refresh_interval = 3
    ri_ms = refresh_interval * 1000

    read = get_redis()
    channels = read.pubsub(ignore_subscribe_messages=True)
    channels.subscribe(Channel.action)
    before_ms = timestamp_ms()
    running = True
    toplist = RedisTopList(15 * 10, get_redis(), ctor=str,
                           bucket_len_sec=1,
                           root_key='nifty')

    # TODO, catch ctrl-c
    while running:
        now_ms = timestamp_ms()

        # see if refresh interval has elapsed
        time_elapsed_ms = now_ms - before_ms

        # swap time references
        before_ms = now_ms

        # only block for the time left (roughly :-) )
        remaining = ri_ms - time_elapsed_ms
        wait_time_sec = refresh_interval if remaining <= 0 \
            else (ri_ms - time_elapsed_ms) / 1000
        logging.debug(f"wait_time_sec={wait_time_sec}")

        msg = channels.get_message(True, wait_time_sec)
        if msg:
            handle(msg, toplist)


if __name__ == '__main__':
    run()
