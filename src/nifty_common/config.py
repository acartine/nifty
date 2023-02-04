import configparser
import os


class _EnvInterpolation(configparser.BasicInterpolation):
    """Interpolation which expands environment variables in values."""

    def before_get(self, parser, section, option, value, defaults):
        value = super().before_get(parser, section, option, value, defaults)
        return os.path.expandvars(value)


cfg = configparser.ConfigParser(interpolation=_EnvInterpolation())
print("Configuration from 'config.ini':")
cfg.read_file(open('config.ini'))
for s in cfg.sections():
    sd = {}
    for k, v in cfg[s].items():
        print(f"{s} : {k} : {v if k.upper() != 'PWD' else '****'}")
