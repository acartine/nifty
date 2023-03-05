import configparser
import os
from typing import Callable, Optional, TypeVar


class _EnvInterpolation(configparser.BasicInterpolation):
    """Interpolation which expands environment variables in values."""

    def before_get(self, parser, section, option, value, defaults):
        value = super().before_get(parser, section, option, value, defaults)
        return os.path.expandvars(value)


CFG_FILE_PATH = "config"
cfg = configparser.ConfigParser(interpolation=_EnvInterpolation())


def load_config(l_cfg: configparser.ConfigParser, prefix: Optional[str] = None):
    cfg_file = f"{prefix}_config.ini" if prefix else "config.ini"
    cfg_file = f"{CFG_FILE_PATH}/{cfg_file}"
    print(f"Loading from '{cfg_file}'...")
    l_cfg.read_file(open(cfg_file))


load_config(cfg)

# NIFTY, TREND etc.
app_context_cfg = os.environ.get("APP_CONTEXT_CFG")
if app_context_cfg is None:
    raise Exception("APP_CONTEXT_CONFIG must be set (nifty|trend ...) so we know what configs to load.")
load_config(cfg, app_context_cfg.lower())

# LOCAL, DEV, PROD, etc. etc.
primary_cfg = os.environ.get("PRIMARY_CFG")
if primary_cfg is not None:
    load_config(cfg, primary_cfg.lower())
else:
    print(
        "PRIMARY_CFG not set - to override configs, set PRIMARY_CFG=xxxx and then "
        "have config/xxxx_config.ini in place and it will be loaded!"
    )

for s in cfg.sections():
    sd = {}
    for k, v in cfg[s].items():
        print(f"{s} : {k} : {v if k.upper() != 'PWD' else '****'}")

T = TypeVar("T")


def g(section: str, key: str) -> str:
    """
    simple get, fail fast
    """

    return cfg[section][key]


def g_opt(section: str, key: str) -> Optional[str]:
    """
    simple get, return None if not found
    """

    return cfg[section].get(key)


def g_fb(section: str, key: str, fallback: str) -> str:
    """
    get with fallback
    """

    val = g_opt(section, key)
    return val if val else fallback


def gint(section: str, key: str) -> int:
    """
    Fail fast int getter


    """
    return int(g(section, key))


def gint_fb(section: str, key: str, fallback: int) -> int:
    val = g_opt(section, key)
    return int(val) if val else fallback
