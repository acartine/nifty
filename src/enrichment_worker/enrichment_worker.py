import logging
import sys
import time

from nifty_common.helpers import get_redis
from nifty_common.store import Trending, TrendingItem, get_trending
from nifty_common.types import Channel

log_level_val = getattr(logging, "DEBUG")
print(f"Log level set to {log_level_val}")
root = logging.getLogger()
root.setLevel(log_level_val)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(log_level_val)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)

