from collections import OrderedDict
from dataclasses import dataclass
from typing import Generic, List, Optional, TypeVar

T = TypeVar('T')


@dataclass
class Entry(Generic[T]):
    key: T
    count: int


class TopList(Generic[T]):
    REMOVED = -1

    def __init__(self, max_age: int, bucket_len_sec: Optional[int] = 1):
        self.ordered_entries = []
        self.entries = {}
        self.time_buckets = OrderedDict()
        self.expiry_sec = max_age
        self.bucket_len_sec = bucket_len_sec

    def __reap(self, ts: int):
        ts_sec = int(ts / 1000)
        while len(self.time_buckets) > 0 and ts_sec - min(self.time_buckets) >= self.expiry_sec:
            item = self.time_buckets.popitem(last=False)
            for key, count in item[1].items():
                self.__decr(key, count)

    def __len__(self) -> int:
        return len(self.ordered_entries)

    def __sort(self):
        self.ordered_entries.sort(key=lambda e: e.count, reverse=True)

    def __decr(self, key: T, count: Optional[int] = 1):
        entry = self.entries.get(key)
        entry.count -= count
        self.__sort()
        if entry.count <= 0:
            # we can do this because we know it will have the lowest count
            self.ordered_entries.pop()
            del self.entries[key]

    def incr(self, key: T, ts: int):
        self.__reap(ts)
        entry = self.entries.get(key)
        if not entry:
            entry = Entry(key, 0)
            self.entries[key] = entry
            self.ordered_entries.append(entry)
        entry.count += 1
        self.__sort()

        # put it in timebucket
        ts_secs = int(ts / 1000)
        bucket_key = ts_secs - ts_secs % self.bucket_len_sec
        bucket = self.time_buckets.get(bucket_key)
        if not bucket:
            bucket = {}
            self.time_buckets[bucket_key] = bucket

        if key not in bucket:
            bucket[key] = 0

        bucket[key] += 1

    def get(self, ts: int, lim: Optional[int] = None) -> List[Entry[T]]:
        self.__reap(ts)
        size = len(self.ordered_entries)
        local_lim = lim if lim and lim < size else size
        return [e for e in self.ordered_entries[:local_lim]]
