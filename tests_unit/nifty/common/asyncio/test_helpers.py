import unittest
from unittest import IsolatedAsyncioTestCase, mock
from unittest.mock import Mock, patch
from nifty.common.asyncio import helpers


class TestHelpers(IsolatedAsyncioTestCase):
    @patch("asyncio.sleep")
    async def test_retry_fail(self, mock_sleep: Mock):
        @helpers.retry(max_tries=3, stack_id="test")
        async def test_func():
            raise Exception("test")

        with patch("logging.getLogger") as mock_logger:
            error_logger = Mock()
            mock_logger.return_value = error_logger

            with self.assertRaises(Exception):
                await test_func()

            self.assertEqual(error_logger.error.call_count, 1)

            self.assertEqual(mock_sleep.mock_calls, [mock.call(0.1), mock.call(0.2)])

    @patch("asyncio.sleep")
    async def test_retry_with_return(self, mock_sleep: Mock):
        times = 0

        @helpers.retry(max_tries=3, stack_id="test", first_delay=0.6)
        async def test_func():
            nonlocal times
            times += 1
            if times == 2:
                return 1
            raise Exception("test")

        actual = await test_func()
        self.assertEqual(actual, 1)
        mock_sleep.assert_called_once_with(0.6)

    @patch("asyncio.sleep")
    async def test_retry_with_bad_delay(self, mock_sleep: Mock):
        try:

            @helpers.retry(max_tries=3, stack_id="test", first_delay=-0.001)
            async def test_func():
                return 1

            await test_func()
        except ValueError:
            mock_sleep.assert_not_called()
            return

        self.fail("Should have failed")

    @patch("asyncio.sleep")
    async def test_retry_with_bad_max_tries(self, mock_sleep: Mock):
        try:

            @helpers.retry(max_tries=0, stack_id="test")
            async def test_func():
                return 1

            await test_func()
        except ValueError:
            mock_sleep.assert_not_called()
            return

        self.fail("Should have failed")
