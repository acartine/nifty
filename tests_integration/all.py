from __future__ import annotations
from queue import Queue
from threading import Thread
from typing import Any, Dict, Type, TypeVar
from redis.client import Redis, PubSub
from flask.testing import FlaskClient
import time

from nifty.common.types import Action, ActionType, Meta, TrendEvent, TrendLinkEvent

long_url_fixture = (
    "https://askubuntu.com/questions/986525/syntax-error-near-unexpected-token-newline-error-while"
    "-installing-deb-package?noredirect=1&lq=1 "
)


def test_not_found(client: FlaskClient):
    res = client.get("/foo")
    assert res.status_code == 404


class Psl(Thread):
    def __init__(
        self,
        redis: Redis[str],
        q: Queue[Dict[str, Any]],
        expected_msgs: int,
        listen_period: int,
        *channels: str,
    ):
        super().__init__()
        self.redis = redis
        self.q = q
        self.expected_msgs = expected_msgs
        self.listen_period = listen_period
        self.channels = channels

    def run(self):
        # pass
        with self.redis.pubsub(ignore_subscribe_messages=True) as pubsub:
            pubsub.subscribe(*self.channels)
            now = time.time()
            ct = 0
            while ct < self.expected_msgs and time.time() - now < self.listen_period:
                msg = pubsub.get_message(timeout=self.listen_period)
                if msg:
                    ct += 1
                    self.q.put(msg)

            # see if there is another message so clients can assert queue size
            # and fail if there is more than expected
            msg = pubsub.get_message(timeout=0.5)
            if msg:
                self.q.put(msg)


_T_Event = TypeVar("_T_Event", bound=Meta)


def assert_msg(msg: Dict[str, Any], event_type: Type[_T_Event]) -> _T_Event:
    assert msg["data"]
    event = event_type.parse_raw(msg["data"])
    assert event.at
    assert event.uuid
    return event


def assert_action(msg: Dict[str, Any], action_type: ActionType):
    action = assert_msg(msg, Action)
    assert action.type == action_type


def assert_trend(msg: Dict[str, Any]):
    trend = assert_msg(msg, TrendEvent)
    assert trend.added
    assert len(trend.added) == 1
    assert not trend.removed


def assert_trend_link(msg: Dict[str, Any]):
    trend_link = assert_msg(msg, TrendLinkEvent)
    assert trend_link.link_id
    assert trend_link.added


def test_create_and_lookup(client: FlaskClient, redis: Redis[str]):
    msgs: Queue[Dict[str, Any]] = Queue()
    psl = Psl(redis, msgs, 4, 5, "nifty:action", "nifty:trend", "nifty:trend_link")
    psl.start()

    res = client.post(
        "/shorten",
        json={
            "long_url": "https://www.google.com",
        },
    )
    assert res.json
    assert res.json.get("short_url")
    short_url = res.json["short_url"]

    res = client.get(f"/{short_url}")
    assert res.status_code == 302
    assert res.headers.get("Location")
    assert res.headers["Location"] == "https://www.google.com"
    psl.join()
    assert msgs.qsize() == 4  # says not reliable, but probably is for this
    assert_action(msgs.get_nowait(), ActionType.create)
    assert_action(msgs.get_nowait(), ActionType.get)
    assert_trend(msgs.get_nowait())
    assert_trend_link(msgs.get_nowait())


def test_reject_invalid_url(client: FlaskClient):
    res = client.post(
        "/shorten",
        json={
            "long_url": "foo",
        },
    )
    assert res.status_code == 400
    assert res.json
    assert res.json.get("validation_error").get("body_params")
    assert len(res.json["validation_error"]["body_params"]) == 1
    assert (
        res.json["validation_error"]["body_params"][0].get("msg")
        == "invalid or missing URL scheme"
    )


def test_idempotent_post(client: FlaskClient, redis: Redis[str]):
    msgs: Queue[Dict[str, Any]] = Queue()
    psl = Psl(redis, msgs, 1, 5, "nifty:action")
    psl.start()

    # create new url
    res = client.post(
        "/shorten",
        json={
            "long_url": f"{long_url_fixture}",
        },
    )
    assert res.status_code == 201
    assert res.json
    assert res.json.get("short_url")
    short_url = res.json["short_url"]

    # try to create it again
    res = client.post(
        "/shorten",
        json={
            "long_url": f"{long_url_fixture}",
        },
    )
    # already exists, so 200 instead of 201
    assert res.status_code == 200
    assert res.json
    assert res.json.get("short_url")
    # same as one we created before
    assert res.json["short_url"] == short_url

    psl.join()
    assert msgs.qsize() == 1
    assert_action(msgs.get_nowait(), ActionType.create)
