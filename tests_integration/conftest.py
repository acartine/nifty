import pytest
import nifty.service.app as nifty


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
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
