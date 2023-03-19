import logging
import sys

from . import cfg


def init():
    log_level = cfg.g_fb("logging", "level", "WARN")
    log_level_val = getattr(logging, log_level.upper())
    print(f"Log level set to {log_level} {log_level_val}")
    root = logging.getLogger()
    root.setLevel(log_level_val)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level_val)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)-8s "
        "[%(filename)s:%(lineno)d] %(funcName)s() => %(message)s"
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)
