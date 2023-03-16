import unittest
from unittest.mock import Mock, patch
from nifty.common import context


class TestContext(unittest.TestCase):
    @patch.dict("os.environ", {"APP_CONTEXT_CFG": "NIFTY", "PRIMARY_CFG": "LOCAL"})
    def test_get(self):
        actual = context.get()
        self.assertEqual(
            actual,
            context.AppContext(
                app_name=context.AppContextName.nifty, primary_cfg="local"
            ),
        )

    @patch.dict("os.environ", {"APP_CONTEXT_CFG": "NIFTY"})
    def test_get_no_primary(self):
        actual = context.get()
        self.assertEqual(
            actual, context.AppContext(app_name=context.AppContextName.nifty)
        )

    @patch.dict("os.environ", {"APP_CONTEXT_CFG": "FOO"})
    def test_get_bad_app(self):
        with self.assertRaises(Exception):
            context.get()

    @patch.dict("os.environ", {})
    def test_get_no_app(self):
        with self.assertRaises(Exception):
            context.get()
