from datetime import datetime

from worker.time_expiry_heap import TimeExpiryHeap, Entry


def test_incr_and_get():
    sut = TimeExpiryHeap()
    now = int(datetime.timestamp(datetime(2023, 2, 6)) * 1000)
    sut.incr(1, now)
    sut.incr(2, now)
    sut.incr(2, now)
    sut.incr(2, now)
    sut.incr(3, now)
    sut.incr(3, now)
    actual = sut.get(now)
    assert actual == [Entry(2, 3), Entry(3, 2), Entry(1, 1)]

    actual = sut.get(now, 2)
    assert actual == [Entry(2, 3), Entry(3, 2)]
