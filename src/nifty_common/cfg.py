import configparser
import os
from typing import Callable, Optional, TypeVar


class _EnvInterpolation(configparser.BasicInterpolation):
    """Interpolation which expands environment variables in values."""

    def before_get(self, parser, section, option, value, defaults):
        value = super().before_get(parser, section, option, value, defaults)
        return os.path.expandvars(value)


CFG_FILE_PATH = 'config'
cfg = configparser.ConfigParser(interpolation=_EnvInterpolation())


def load_config(l_cfg: configparser.ConfigParser, prefix: Optional[str] = None):
    cfg_file = f"{prefix}_config.ini" if prefix else 'config.ini'
    cfg_file = f"{CFG_FILE_PATH}/{cfg_file}"
    print(f"Loading from '{cfg_file}'...")
    l_cfg.read_file(open(cfg_file))


load_config(cfg)

# LOCAL, DEV, PROD, etc. etc.
primary_cfg = os.environ.get('PRIMARY_CFG')
if primary_cfg is not None:
    load_config(cfg, primary_cfg.lower())
else:
    print('PRIMARY_CFG not set - to override configs, set PRIMARY_CFG=xxxx and then '
          'have config/xxxx_config.ini in place and it will be loaded!')

for s in cfg.sections():
    sd = {}
    for k, v in cfg[s].items():
        print(f"{s} : {k} : {v if k.upper() != 'PWD' else '****'}")

T = TypeVar("T")


def get(section: str,
        key: str,
        fallback: Optional[T] = None,
        *,
        ctor: Callable[[str], T] = str) -> T:
    """
    Get optionally or return default

    :param section:
    :param key:
    :param fallback: if no value is present
    :param ctor: how to convert the value to desired type
    :return: config value in desired type, or None no value was resolved
    """
    if fallback is None:
        return ctor(cfg[section][key])

    val = cfg[section].get(key)
    if val:
        return ctor(val)

    return fallback


def getint(section: str, key: str, fallback: Optional[int]) -> int:
    """
    Fail fast int getter

    :param section:
    :param key:
    :param fallback
    :return: config value as int
    """
    return get(section, key, fallback, ctor=int)
