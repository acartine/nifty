from redis.client import Redis

from nifty_common.helpers import get_redis
from nifty_common.types import Channel, Action, ActionType


# redis doesn't really have great datastructures for this
# time series would have been best, but it doesn't support
# dynamic labels or aggregations limits in order

# we can run multiples of these in parallel for reliability
# they will overwrite each other but we don't need it to be exact
def _update_hotlinks(_redis: Redis, _action: Action):
    pass


def main():
    read = get_redis()
    channels = read.pubsub(ignore_subscribe_messages=True)
    channels.subscribe(Channel.action)
    redis = get_redis()
    # while running
    # todo, catch ctrl-c
    # get msg w timout 1 sec
    # update stats
    # update queue
    # if update interval elapsed
    # send queue to redis

    for msg in channels.listen():
        if msg['type'] == 'message':
            payload = msg['data'].decode('UTF-8')
            print(payload)
            action = Action.parse_raw(payload)
            if action == ActionType.get:
                _update_hotlinks(redis, action)


if __name__ == '__main__':
    main()
