from unittest.mock import Mock, patch
from src.nifty_worker.trend.toplist.toplist import RedisTopList


@patch("redis.client.Redis")
def test_toplist_incr(mock_redis: Mock) -> None:
    change_listener = Mock()
    """Test incr()"""
    toplist = RedisTopList("test", 300, mock_redis, int, change_listener)
    toplist.incr(1, 1678415471000)
    change_listener.assert_called_once_with({1}, ())
