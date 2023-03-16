import unittest
from unittest import mock
from unittest.mock import Mock, patch
from nifty.common import helpers
import datetime


class TestHelpers(unittest.TestCase):
    def test_timestamp_ms(self):
        self.assertEqual(
            helpers.timestamp_ms(
                datetime_ts=datetime.datetime.fromtimestamp(1678620136.95899)
            ),
            1678620136958,
        )

        with patch("time.time") as mock_time:
            mock_time.return_value = 1678620136.95899
            self.assertEqual(helpers.timestamp_ms(), 1678620136958)

    @patch("time.sleep")
    def test_retry_fail(self, mock_sleep: Mock):
        @helpers.retry(max_tries=3, stack_id="test")
        def test_func():
            raise Exception("test")

        with patch("logging.getLogger") as mock_logger:
            error_logger = Mock()
            mock_logger.return_value = error_logger

            with self.assertRaises(Exception):
                test_func()

            self.assertEqual(error_logger.error.call_count, 1)
            self.assertEqual(error_logger.debug.call_count, 2)

            self.assertEqual(mock_sleep.mock_calls, [mock.call(0.1), mock.call(0.2)])

    @patch("time.sleep")
    def test_retry_with_return(self, mock_sleep: Mock):
        times = 0
        @helpers.retry(max_tries=3, stack_id="test", first_delay=.6)
        def test_func():
            nonlocal times
            times += 1
            if times == 2:
                return 1
            raise Exception("test")

        self.assertEqual(test_func(), 1) 
        mock_sleep.assert_called_once_with(.6)

    @patch("time.sleep")
    def test_retry_with_bad_delay(self, mock_sleep: Mock):
        with self.assertRaises(ValueError):
            @helpers.retry(max_tries=3, stack_id="test", first_delay=-.001)
            def test_func():
                return 1
            test_func()
        mock_sleep.assert_not_called()

    @patch("time.sleep")
    def test_retry_with_bad_max_tries(self, mock_sleep: Mock):
        with self.assertRaises(ValueError):
            @helpers.retry(max_tries=0, stack_id="test")
            def test_func():
                return 1
            test_func()
        mock_sleep.assert_not_called()

    def test_opt_or(self):
        self.assertEqual(helpers.opt_or(None, 1), 1)
        self.assertEqual(helpers.opt_or(2, 1), 2)

    def test_opt_or_none(self):
        self.assertEqual(helpers.opt_or(None, None), None)
        self.assertEqual(helpers.opt_or(2, None), 2)

    def test_optint_or_none(self):
        self.assertEqual(helpers.optint_or_none(None), None)
        self.assertEqual(helpers.optint_or_none("1"), 1)

    def test_none_throws(self):
        with self.assertRaises(Exception):
            helpers.none_throws(None, "test")

        self.assertEqual(helpers.none_throws(1, "test"), 1)

    def test_noneint_throws(self):
        with self.assertRaises(Exception):
            helpers.noneint_throws(None, "test")

        self.assertEqual(helpers.noneint_throws("1", "test"), 1)
