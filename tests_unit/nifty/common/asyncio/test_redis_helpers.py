from typing import Any, Optional
import unittest
from unittest import IsolatedAsyncioTestCase, mock
from unittest.mock import Mock, patch, AsyncMock
from pydantic import BaseModel

from nifty.common.asyncio import redis_helpers
from nifty.common.types import Key, RedisType


class TestRedisHelpers(IsolatedAsyncioTestCase):
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
    @patch("redis.asyncio.client.Redis")
    def test_get_redis_client_std(
        self, mock_redis: Mock, mock_gint_fb: Mock, mock_g: Mock
    ):
        self.assert_client_with_keys(mock_redis, mock_gint_fb, mock_g, RedisType.STD)

    @patch("nifty.common.cfg.g")
    @patch("nifty.common.cfg.gint_fb")
    @patch("redis.asyncio.client.Redis")
    def test_get_redis_client_cache(
        self, mock_redis: Mock, mock_gint_fb: Mock, mock_g: Mock
    ):
        self.assert_client_with_keys(mock_redis, mock_gint_fb, mock_g, RedisType.CACHE)

    @patch("nifty.common.cfg.g")
    @patch("nifty.common.cfg.gint_fb")
    @patch("redis.asyncio.client.Redis")
    def test_get_redis_client_cache_with_creds(
        self, mock_redis: Mock, mock_gint_fb: Mock, mock_g: Mock
    ):
        self.assert_client_with_keys(
            mock_redis, mock_gint_fb, mock_g, RedisType.CACHE, "override_creds_section"
        )

    async def test_rint_throws(self):
        with patch(
            "redis.asyncio.client.Redis",
        ) as mock_redis:  # type: ignore
            mock_redis.get = AsyncMock()
            mock_redis.get.return_value = "123"
            actual_value = await redis_helpers.rint(mock_redis, "foo")
            self.assertEqual(actual_value, 123)

            mock_redis.get.return_value = None
            with self.assertRaises(Exception):
                await redis_helpers.rint(mock_redis, "foo")

            mock_redis.get.return_value = "abc"
            with self.assertRaises(ValueError):
                await redis_helpers.rint(mock_redis, "foo")

    async def test_rint(self):
        with patch("redis.asyncio.client.Redis") as mock_redis:  # type: ignore
            mock_redis.get = AsyncMock()
            mock_redis.get.return_value = "123"
            actual = await redis_helpers.rint(mock_redis, "foo", throws=False)
            self.assertEqual(actual, 123)

            mock_redis.get.return_value = None
            actual = await redis_helpers.rint(mock_redis, "foo", throws=False)
            self.assertIsNone(actual)

            mock_redis.get.return_value = "abc"
            with self.assertRaises(ValueError):
                await redis_helpers.rint(mock_redis, "foo", throws=False)

    async def test_robj(self):
        class SomeClass(BaseModel):
            foo: str

        with patch("redis.asyncio.client.Redis") as mock_redis:
            mock_redis.hgetall = AsyncMock()
            mock_redis.hgetall.return_value = {"foo": "bar"}
            actual = await redis_helpers.robj(mock_redis, "foo", SomeClass)
            self.assertEqual(actual, SomeClass(foo="bar"))
            mock_redis.hgetall.return_value = None
            with self.assertRaises(Exception):
                await redis_helpers.robj(mock_redis, "foo", SomeClass)

            actual = await redis_helpers.robj(mock_redis, "foo", SomeClass, False)
            self.assertIsNone(actual)

    async def test_trending_size(self):
        def mock_redis_side_effect(*args: Any, **_kwargs: Any):
            if args[0] == Key.trending_size:
                return 123
            raise Exception("Unexpected call")

        with patch("redis.asyncio.client.Redis") as mock_redis:
            mock_redis.get = AsyncMock()
            mock_redis.get.side_effect = mock_redis_side_effect
            actual = await redis_helpers.trending_size(mock_redis)

            self.assertEqual(actual, 123)

            mock_redis.get.side_effect = None
            mock_redis.get.return_value = None
            with self.assertRaises(Exception):
                await redis_helpers.trending_size(mock_redis)
