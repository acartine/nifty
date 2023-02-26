from nifty_common.config import cfg
from nifty_common.types import Channel
from nifty_worker.common.worker import init_logger
from .trend import TrendWorker

TREND_CONFIG_KEY = 'trend'

init_logger()
trend = TrendWorker(
    trend_size=cfg.getint(TREND_CONFIG_KEY, 'size'),
    toplist_interval_sec=cfg.getint(TREND_CONFIG_KEY, 'toplist_interval_sec'),
    toplist_bucket_len_sec=cfg.getint(TREND_CONFIG_KEY, 'toplist_bucket_len_sec'))

trend.run(
    src_channel=Channel.action,
    listen_interval=cfg.getint(TREND_CONFIG_KEY, 'listen_interval_sec'))
