import asyncio

from nifty_common import cfg, log
from nifty_common.types import Channel
from .trend import TrendWorker

TREND_CONFIG_KEY = "trend"

log.log_init()
trend = TrendWorker(
    trend_size=cfg.gint(TREND_CONFIG_KEY, "size"),
    toplist_interval_sec=cfg.gint(TREND_CONFIG_KEY, "toplist_interval_sec"),
    toplist_bucket_len_sec=cfg.gint(TREND_CONFIG_KEY, "toplist_bucket_len_sec"),
)

asyncio.run(
    trend.run(
        src_channel=Channel.action,
        listen_interval=cfg.gint(TREND_CONFIG_KEY, "listen_interval_sec"),
    )
)
