import configparser
import os
from typing import Mapping, MutableMapping, Optional, TypeAlias, TypeVar
from .helpers import none_throws

from .types import AppContextName

_Section: TypeAlias = Mapping[str, str]
_Parser: TypeAlias = MutableMapping[str, _Section]


CFG_FILE_PATH = "config"


class _EnvInterpolation(configparser.BasicInterpolation):
    """Interpolation which expands environment variables in values."""

    def before_get(
        self, parser: _Parser, section: str, option: str, value: str, defaults: _Section
    ):
        value = super().before_get(parser, section, option, value, defaults)
        return os.path.expandvars(value)


_singleton: Optional[configparser.ConfigParser] = None


def _cfg() -> configparser.ConfigParser:
    return none_throws(_singleton, "cfg not initialized")


def _load_config(l_cfg: configparser.ConfigParser, prefix: Optional[str] = None):
    cfg_file = f"{prefix}_config.ini" if prefix else "config.ini"
    cfg_file = f"{CFG_FILE_PATH}/{cfg_file}"
    print(f"Loading from '{cfg_file}'...")
    l_cfg.read_file(open(cfg_file))


def init(*, app_name: AppContextName, primary_cfg: Optional[str] = None):
    """
    Initialize the config, loading the appropriate config files
    Will first look for config.ini, then config/<app_name>_config.ini, then config/<primary_cfg>_config.ini

    The config files are loaded in that order, so the last one wins.  The first two are required, the last one is optional.

    The idea is that common configs are in config.ini, then app specific configs are in <app_name>_config.ini,
    and then finally you can override them with a <primary_cfg>_config.ini

    :param app_name: the app name, used to load the appropriate config file
    :param primary_cfg: the primary config, used to load the appropriate config file for that environment
    """
    global _singleton
    if _singleton is not None:
        raise Exception("cfg already initialized")

    cfg = configparser.ConfigParser(interpolation=_EnvInterpolation())
    _load_config(cfg)
    _load_config(cfg, app_name.value)
    if primary_cfg is not None:
        _load_config(cfg, primary_cfg.lower())

    for s in cfg.sections():
        for k, v in cfg[s].items():
            print(f"{s} : {k} : {v if k.upper() != 'PWD' else '****'}")

    _singleton = cfg


def destroy():
    """
    Destroy the config.  Useful for testing.

    Other potentional uses are if you want to reload the config, or if you want to
    prevent config access after the application has been bootstrapped.
    """
    global _singleton
    _singleton = None


T = TypeVar("T")


def g(section: str, key: str) -> str:
    """
    simple get, fail fast
    """

    return _cfg()[section][key]


def g_opt(section: str, key: str) -> Optional[str]:
    """
    simple get, return None if not found
    """

    return _cfg()[section].get(key)


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


def gfloat(section: str, key: str) -> float:
    """
    Fail fast int getter


    """
    return float(g(section, key))


def gfloat_fb(section: str, key: str, fallback: float) -> float:
    val = g_opt(section, key)
    return float(val) if val else fallback
