import logging
import sys
import time
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
    action: Action = Action.parse_raw(msg['data'])
    if action.type == ActionType.get:
        logging.debug(action)
        toplist.incr(action.short_url, min(action.at, timestamp_ms()))


def run():
    # TODO configurable
    refresh_interval = 3
    read = get_redis()
    channels = read.pubsub(ignore_subscribe_messages=True)
    channels.subscribe(Channel.action)
    before = time.time()
    remaining = refresh_interval

    running = True
    toplist = RedisTopList(1 * 30, get_redis(), ctor=str,
                           bucket_len_sec=1,
                           root_key='nifty')

    # TODO, catch ctrl-c
    while running:
        logging.debug(f"next refresh in {remaining}")
        msg = channels.get_message(True, remaining)
        if msg:
            handle(msg, toplist)
        else:
            toplist.reap(timestamp_ms())

        now = time.time()
        remaining -= now - before
        before = now
        if remaining <= 0:
            remaining = refresh_interval


if __name__ == '__main__':
    run()
