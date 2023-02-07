import logging
import sys
from typing import Dict, List, NamedTuple

from redis.client import Redis

from hotlink_worker.top_list import Entry
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


class TopLinkWorker:
    def __init__(self):
        self.running = False
        self.redis: Redis | None = None

    def diff_lists(self, prev: List[Entry], curr: List[Entry]):
        pass

    def handle(self, msg: Dict[str, any]):
        payload = msg['data'].decode('UTF-8')
        action: Action = Action.parse_raw(payload)
        if action.type == ActionType.get:
            logging.debug(action)

    def run(self):
        # TODO configurable
        refresh_interval = 5
        ri_ms = refresh_interval * 1000
        size = 10
        expiry = 10

        read = get_redis()
        channels = read.pubsub(ignore_subscribe_messages=True)
        channels.subscribe(Channel.action)
        self.redis = get_redis()
        last_push_ms = timestamp_ms()
        running = True

        # TODO, catch ctrl-c
        while running:
            now_ms = timestamp_ms()

            # see if refresh interval has elapsed
            time_elapsed_ms = now_ms - last_push_ms

            # only block for the time left (roughly :-) )
            wait_time_sec = (ri_ms - time_elapsed_ms) / 1000
            logging.debug(f"wait_time_sec={wait_time_sec}")
            msg = channels.get_message(True, wait_time_sec)
            if msg:
                self.handle(msg)


if __name__ == '__main__':
    TopLinkWorker().run()
