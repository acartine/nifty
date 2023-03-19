from typing import Any, Optional
import unittest
from unittest import mock
from unittest.mock import Mock, patch
from pydantic import BaseModel

import redis

from nifty.common import redis_helpers
from nifty.common.types import Key, RedisType


class TestRedisHelpers(unittest.TestCase):
    def assert_client_with_keys(
        self,
        mock_redis: Mock,
        mock_gint_fb: Mock,
        mock_g: Mock,
        redisType: RedisType,
        override_creds: Optional[str] = None,
    ):
        mock_gint_fb.return_value = 123
        mock_g.return_value = "foo"
        _actual_val = redis_helpers.get_redis(
            redisType,
            cfg_creds_section=override_creds,
        )
        key = redisType.cfg_key
        creds_key = redisType.cfg_key if not override_creds else override_creds
        mock_redis.assert_called_once_with(
            host="foo", username="foo", password="foo", port=123, decode_responses=True
        )
        mock_gint_fb.assert_called_once_with(key, "port", 6379)
        self.assertEqual(
            mock_g.mock_calls,
            [
                mock.call(key, "host"),
                mock.call(creds_key, "user" if not override_creds else "redis_user"),
                mock.call(creds_key, "pwd" if not override_creds else "redis_pwd"),
            ],
        )

    @patch("nifty.common.cfg.g")
    @patch("nifty.common.cfg.gint_fb")
    @patch("redis.client.Redis")
    def test_get_redis_client_std(
        self, mock_redis: Mock, mock_gint_fb: Mock, mock_g: Mock
    ):
        self.assert_client_with_keys(mock_redis, mock_gint_fb, mock_g, RedisType.STD)

    @patch("nifty.common.cfg.g")
    @patch("nifty.common.cfg.gint_fb")
    @patch("redis.client.Redis")
    def test_get_redis_client_cache(
        self, mock_redis: Mock, mock_gint_fb: Mock, mock_g: Mock
    ):
        self.assert_client_with_keys(mock_redis, mock_gint_fb, mock_g, RedisType.CACHE)

    @patch("nifty.common.cfg.g")
    @patch("nifty.common.cfg.gint_fb")
    @patch("redis.client.Redis")
    def test_get_redis_client_cache_with_creds(
        self, mock_redis: Mock, mock_gint_fb: Mock, mock_g: Mock
    ):
        self.assert_client_with_keys(
            mock_redis, mock_gint_fb, mock_g, RedisType.CACHE, "override_creds_section"
        )

    def test_rint_throws(self):
        with patch("redis.client.Redis") as mock_redis:  # type: ignore
            mock_redis.get.return_value = "123"
            self.assertEqual(redis_helpers.rint_throws(mock_redis, "foo"), 123)
            mock_redis.get.assert_called_once_with("foo")

            mock_redis.get.return_value = None
            with self.assertRaises(Exception):
                redis_helpers.rint_throws(mock_redis, "foo")

            mock_redis.get.return_value = "abc"
            with self.assertRaises(ValueError):
                redis_helpers.rint_throws(mock_redis, "foo")

    def test_rint(self):
        with patch("redis.client.Redis") as mock_redis:  # type: ignore
            mock_redis.get.return_value = "123"
            self.assertEqual(redis_helpers.rint(mock_redis, "foo"), 123)
            mock_redis.get.assert_called_once_with("foo")

            mock_redis.get.return_value = None
            self.assertIsNone(redis_helpers.rint(mock_redis, "foo"))

            mock_redis.get.return_value = "abc"
            with self.assertRaises(ValueError):
                redis_helpers.rint(mock_redis, "foo")

    def test_robj(self):
        class SomeClass(BaseModel):
            foo: str

        with patch("redis.client.Redis") as mock_redis:
            mock_redis.hgetall.return_value = {"foo": "bar"}
            actual = redis_helpers.robj(mock_redis, "foo", SomeClass)
            self.assertEqual(actual, SomeClass(foo="bar"))

            mock_redis.hgetall.return_value = None
            with self.assertRaises(Exception):
                redis_helpers.robj(mock_redis, "foo", SomeClass)

            self.assertIsNone(redis_helpers.robj(mock_redis, "foo", SomeClass, False))

    def test_trending_size(self):
        def mock_redis_side_effect(*args: Any, **_kwargs: Any):
            if args[0] == Key.trending_size:
                return 123
            raise Exception("Unexpected call")

        with patch("redis.client.Redis") as mock_redis:
            mock_redis.get.side_effect = mock_redis_side_effect
            self.assertEqual(redis_helpers.trending_size(mock_redis), 123)

            mock_redis.get.side_effect = None
            mock_redis.get.return_value = None
            with self.assertRaises(Exception):
                redis_helpers.trending_size(mock_redis)
