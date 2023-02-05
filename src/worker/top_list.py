from collections import OrderedDict
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Entry:
    key: int
    count: int


class TopList:
    REMOVED = -1

    def __init__(self, max_age: int, bucket_len_sec: Optional[int] = 1):
        self.ordered_entries = []
        self.entries = {}
        self.time_buckets = OrderedDict()
        self.expiry_sec = max_age
        self.bucket_len_sec = bucket_len_sec

    def __reap(self, ts: int):
        ts_sec = int(ts/1000)
        while len(self.time_buckets) > 0 and ts_sec - min(self.time_buckets) >= self.expiry_sec:
            item = self.time_buckets.popitem(0)
            for key, count in item[1].items():
                self.__decr(key, count)

    def __sort(self):
        self.ordered_entries.sort(key=lambda e: e.count, reverse=True)

    def __decr(self, key: int, count: Optional[int] = 1):
        entry = self.entries.get(key)
        entry.count -= count
        self.__sort()
        if entry.count <= 0:
            # we can do this because we know it will have the lowest count
            self.ordered_entries.pop()
            del self.entries[key]

    def incr(self, key: int, ts: int):
        self.__reap(ts)
        entry = self.entries.get(key)
        if not entry:
            entry = Entry(key, 0)
            self.entries[key] = entry
            self.ordered_entries.append(entry)
        entry.count += 1
        self.__sort()

        # put it in timebucket
        bucket_key = int(ts / 1000 - ts % self.bucket_len_sec)
        bucket = self.time_buckets.get(bucket_key)
        if not bucket:
            bucket = {}
            self.time_buckets[bucket_key] = bucket

        if key not in bucket:
            bucket[key] = 0

        bucket[key] += 1

    def get(self, ts: int, lim: Optional[int] = None) -> List[Entry]:
        self.__reap(ts)
        size = len(self.ordered_entries)
        local_lim = lim if lim and lim < size else size
        return [e for e in self.ordered_entries[:local_lim]]
