import abc
from abc import abstractmethod
from collections import OrderedDict
from dataclasses import dataclass
from typing import Dict, Generic, List, Optional, Tuple, TypeVar

T = TypeVar('T')


@dataclass
class Entry(Generic[T]):
    key: T
    count: int


class AbstractTimeBuckets(Generic[T], abc.ABC):
    @abstractmethod
    def __len__(self) -> int:
        pass

    @abstractmethod
    def peek(self) -> int:
        pass

    @abstractmethod
    def __getitem__(self, key: T) -> Dict[T, int]:
        pass

    @abstractmethod
    def get(self, key: T) -> Dict[T, int]:
        pass

    @abstractmethod
    def __setitem__(self, key: T, value: Dict[T, int]):
        pass

    @abstractmethod
    def pop(self) -> Tuple[int, Dict[T, int]]:
        pass


class AbstractTopList(Generic[T], abc.ABC):

    @abstractmethod
    def __timebuckets__(self) -> AbstractTimeBuckets[T]:
        pass

    @abstractmethod
    def __entry_dict__(self) -> Dict[T, Entry]:
        pass

    @abstractmethod
    def __entry_list__(self) -> List[Entry[T]]:
        pass

    def __init__(self,
                 max_age: int,
                 bucket_len_sec: Optional[int] = 1):
        self.expiry_sec = max_age
        self.bucket_len_sec = bucket_len_sec
        self.time_buckets = self.__timebuckets__()
        self.entries = self.__entry_dict__()
        self.ordered_entries = self.__entry_list__()

    def __sort(self):
        self.ordered_entries.sort(key=lambda e: e.count, reverse=True)

    def incr(self, key: T, ts_ms: int):
        self.__reap(ts_ms)
        entry = self.entries.get(key)
        if not entry:
            entry = Entry(key, 0)
            self.entries[key] = entry
            self.ordered_entries.append(entry)
        entry.count += 1
        self.__sort()

        # put it in timebucket
        ts_secs = int(ts_ms / 1000)
        bucket_key = ts_secs - ts_secs % self.bucket_len_sec
        bucket = self.time_buckets.get(bucket_key)
        if not bucket:
            bucket = {}
            self.time_buckets[bucket_key] = bucket

        if key not in bucket:
            bucket[key] = 0

        bucket[key] += 1

    def __decr(self, key: T, count: Optional[int] = 1):
        entry = self.entries.get(key)
        entry.count -= count
        self.__sort()
        if entry.count <= 0:
            # we can do this because we know it will have the lowest count
            self.ordered_entries.pop()
            del self.entries[key]

    def __reap(self, ts: int):
        ts_sec = int(ts / 1000)
        while len(self.time_buckets) > 0 and ts_sec - self.time_buckets.peek() >= self.expiry_sec:
            item = self.time_buckets.pop()
            for key, count in item[1].items():
                self.__decr(key, count)

    def get(self, ts_ms: int, lim: Optional[int] = None) -> List[Entry[T]]:
        self.__reap(ts_ms)
        size = len(self.ordered_entries)
        local_lim = lim if lim and lim < size else size
        return [e for e in self.ordered_entries[:local_lim]]


class TimeBuckets(AbstractTimeBuckets[T]):
    def __init__(self):
        self.buckets = OrderedDict()

    def peek(self) -> int:
        return min(self.buckets)

    def __getitem__(self, key: T) -> Dict[T, int]:
        return self.buckets[key]

    def get(self, key: T) -> Dict[T, int]:
        return self.buckets.get(key)

    def __setitem__(self, key: T, value: Dict[T, int]):
        self.buckets[key] = value

    def pop(self) -> Tuple[int, Dict[T, int]]:
        return self.buckets.popitem(last=False)

    def __len__(self) -> int:
        return len(self.buckets)


class TopList(AbstractTopList[T]):
    def __entry_dict__(self) -> Dict[T, Entry]:
        return {}

    def __entry_list__(self) -> List[Entry[T]]:
        return []

    def __timebuckets__(self) -> AbstractTimeBuckets[T]:
        return TimeBuckets[T]()

    def __init__(self, max_age: int, bucket_len_sec: Optional[int] = 1):
        super().__init__(max_age, bucket_len_sec)
