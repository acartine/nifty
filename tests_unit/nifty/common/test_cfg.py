import io
from typing import Any
import unittest
from unittest.mock import Mock, mock_open, patch
from nifty.common import cfg
from nifty.common.types import AppContextName


base_text = """
[DEFAULT]

[db]
port=123
backoff=.5

"""

app_text = """
[DEFAULT]

[db]
user=${FOO_DB_USER}
backoff=.6

"""

primary_text = """
[DEFAULT]

[db]
port=456
"""


class TestCfg(unittest.TestCase):
    def __patch(self, module: str, **kwargs: Any):
        patcher = patch(module, **kwargs)
        self.mockdict[module] = patcher.start()
        self.addCleanup(patcher.stop)

    def setUp(self) -> None:
        def open_side_effect(*args: Any, **kwargs: Any):
            if args[0] == "config/config.ini":
                return io.StringIO(base_text)
            elif args[0] == f"config/{AppContextName.nifty.value}_config.ini":
                return io.StringIO(app_text)
            elif args[0] == "config/local_config.ini":
                return io.StringIO(primary_text)
            raise Exception(f"bad file {args[0]}")

        def expandvars_side_effect(*args: Any, **kwargs: Any):
            if args[0] == "${FOO_DB_USER}":
                return "test"
            return args[0]

        self.mockdict = {}
        self.__patch("os.path.expandvars", side_effect=expandvars_side_effect)
        self.__patch("builtins.open", side_effect=open_side_effect, mock=mock_open())
        self.__patch("builtins.print")

    def tearDown(self) -> None:
        cfg.destroy()
        self.mockdict = {}

    def test_init_happy_path(
        self,
    ):
        cfg.init(app_name=AppContextName.nifty, primary_cfg="local")
        self.assertEqual(cfg.gint("db", "port"), 456)
        self.assertEqual(cfg.gfloat("db", "backoff"), 0.6)
        self.assertEqual(cfg.g("db", "user"), "test")

    def test_init_no_primary(
        self,
    ):
        cfg.init(app_name=AppContextName.nifty)
        self.assertEqual(cfg.gint("db", "port"), 123)

    def test_init_missing_app(
        self,
    ):
        with self.assertRaises(Exception):
            cfg.init(app_name=AppContextName.trend)

    def test_init_missing_primary(
        self,
    ):
        with self.assertRaises(Exception):
            cfg.init(app_name=AppContextName.nifty, primary_cfg="foo")

    def test_init_missing_config_ini(
        self,
    ):
        self.mockdict["builtins.open"].side_effect = FileNotFoundError()
        with self.assertRaises(Exception):
            cfg.init(app_name=AppContextName.nifty, primary_cfg="local")

    def test_get_operations(
        self,
    ):
        cfg.init(app_name=AppContextName.nifty, primary_cfg="local")
        self.assertEqual(cfg.gint("db", "port"), 456)
        self.assertEqual(cfg.gfloat("db", "backoff"), 0.6)
        self.assertEqual(cfg.g("db", "user"), "test")
        self.assertEqual(cfg.gint_fb("db", "port", 789), 456)
        self.assertEqual(cfg.gfloat_fb("db", "backoff", 0.7), 0.6)
        self.assertEqual(cfg.g_fb("db", "user", "foo"), "test")
        self.assertEqual(cfg.gint_fb("db", "foo", 789), 789)
        self.assertEqual(cfg.gfloat_fb("db", "foo", 0.7), 0.7)
        self.assertEqual(cfg.g_fb("db", "foo", "foo"), "foo")

        with self.assertRaises(Exception):
            cfg.gint("db", "foo")

        with self.assertRaises(Exception):
            cfg.gfloat("db", "foo")

        with self.assertRaises(Exception):
            cfg.g("db", "foo")
