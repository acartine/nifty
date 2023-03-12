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
)
