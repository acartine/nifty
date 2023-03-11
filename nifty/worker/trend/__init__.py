<<<<<<< HEAD
from nifty.common import cfg
from nifty.common.types import Channel
from .trend import TrendWorker
from nifty.worker.common.asyncio import worker

TREND_CONFIG_KEY = "trend"

worker.start(
    lambda: TrendWorker(
        trend_size=cfg.gint(TREND_CONFIG_KEY, "size"),
        toplist_interval_sec=cfg.gint(TREND_CONFIG_KEY, "toplist_interval_sec"),
        toplist_bucket_len_sec=cfg.gint(TREND_CONFIG_KEY, "toplist_bucket_len_sec"),
    ),
    src_channel=Channel.trend,
=======
import asyncio

from nifty.common import cfg, log
from nifty.common.types import Channel
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
>>>>>>> ad9d80f (refactoring for better support for unit tests.)
)
