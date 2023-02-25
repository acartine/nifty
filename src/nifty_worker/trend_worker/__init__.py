from nifty_common.config import cfg
from nifty_common.types import Channel
from .trend_worker import TrendWorker

TrendWorker().run(
    src_channel=Channel.action,
    listen_interval=cfg.getint(Channel.trend, 'listen_interval_sec'))
