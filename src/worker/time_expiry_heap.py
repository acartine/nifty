from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Entry:
    key: int
    count: int


class TimeExpiryHeap:
    REMOVED = -1

    def __init__(self):
        self.ordered_entries = []
        self.entries = {}

    # def reap(self, ts: int):
    #     pass

    @staticmethod
    def __sort(e1: Entry, e2: Entry) -> Entry:
        if e1.count > e2.count:
            return e1
        if e1.count == e2.count:
            return e1 if e1.key < e2.key else e2
        return e2

    def incr(self, key: int, _ts: int):
        entry = self.entries.get(key)
        if not entry:
            entry = Entry(key, 0)
            self.entries[key] = entry
            self.ordered_entries.append(entry)
        entry.count += 1
        self.ordered_entries.sort(key=lambda e: e.count, reverse=True)

    def get(self, _ts: int, lim: Optional[int] = None) -> List[Entry]:
        local_lim = lim if lim else len(self.ordered_entries)
        return [e for e in self.ordered_entries[:local_lim]]
