import logging
import sys
import time

from nifty_common.helpers import get_redis
from nifty_common.store import Trending, TrendingItem, get_trending

log_level_val = getattr(logging, "DEBUG")
print(f"Log level set to {log_level_val}")
root = logging.getLogger()
root.setLevel(log_level_val)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(log_level_val)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)


def handle(item: TrendingItem):
    pass


def run():
    refresh_interval = 3
    running = True
    redis = get_redis()

    # TODO, catch ctrl-c
    while running:
        trending: Trending = get_trending()
        for item in trending.list:
            handle(item)

        time.sleep(refresh_interval)


if __name__ == '__main__':
    run()
