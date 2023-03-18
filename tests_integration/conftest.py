from __future__ import annotations
import pytest
from redis import Redis
from nifty.common.types import RedisType
import nifty.service.app as nifty
from nifty.common import redis_helpers
from flask import Flask
from flask.testing import FlaskClient


@pytest.fixture()
def app():
    nifty.app.config.update(
        {
            "TESTING": True,
        }
    )

    # other setup can go here

    yield nifty.app

    # clean up / reset resources here


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    return app.test_client()


@pytest.fixture()
def redis() -> Redis[str]:
    return redis_helpers.get_redis(RedisType.STD, cfg_creds_section="integration-test")


@pytest.fixture()
def runner(app: Flask):
    return app.test_cli_runner()
