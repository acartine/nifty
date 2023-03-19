import os
from typing import Optional

from pydantic import BaseModel
from nifty.common.helpers import none_throws
from nifty.common.types import AppContextName

APP_NAME_CFG_KEY = "APP_CONTEXT_CFG"
PRIMARY_CFG_KEY = "PRIMARY_CFG"


class AppContext(BaseModel):
    app_name: AppContextName
    primary_cfg: Optional[str] = None


def get() -> AppContext:
    """
    Get the current context, used for configuration

    :return: the current context name, and primary context (environment-ish e.g. 'local')
    """
    app_name: Optional[AppContextName] = None
    try:
        app_context_cfg = none_throws(
            os.environ.get(APP_NAME_CFG_KEY), f"missing APP_CONTEXT_CFG"
        )
        app_name = AppContextName[app_context_cfg.lower()]
    except:
        raise Exception(
            "APP_CONTEXT_CONFIG must be set to one of"
            f" {[e.name for e in AppContextName]} so we know what configs to load.  "
            "Environment supplied '{os.environ.get(APP_NAME_CFG_KEY)}'"
        )

    # LOCAL, DEV, PROD, etc. etc.
    primary_cfg = os.environ.get(PRIMARY_CFG_KEY)
    if primary_cfg is None:
        print(
            "PRIMARY_CFG not set - to override configs, set PRIMARY_CFG=xxxx and then "
            "have config/xxxx_config.ini in place and it will be loaded!"
        )
    return AppContext(
        app_name=app_name, primary_cfg=primary_cfg.lower() if primary_cfg else None
    )
