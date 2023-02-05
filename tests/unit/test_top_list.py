from datetime import datetime

from worker.top_list import TopList, Entry


def test_incr_and_get():
    sut = TopList(expiry_sec=60)
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


def test_expiry():
    sut = TopList(expiry_sec=60)
    now = int(datetime.timestamp(datetime(2023, 2, 6)) * 1000)
    one_second = 1000
    one_minute = 60 * one_second
    sut.incr(2, now)
    sut.incr(2, now + 30 * one_second)
    sut.incr(2, now + one_minute)

    actual = sut.get(now + one_minute)
    assert actual == [Entry(2, 2)]

    sut.incr(3, now + one_minute)
    sut.incr(3, now + one_minute + 30 * one_second)

    actual = sut.get(now + one_minute + 30 * one_second)
    assert actual == [Entry(3, 2), Entry(2, 1)]

    sut.incr(1, now + 2 * one_minute)
    actual = sut.get(now + 2 * one_minute)
    assert actual == [Entry(3, 1), Entry(1, 1)]

    actual = sut.get(now + 2 * one_minute + 30*one_second)
    assert actual == [Entry(1, 1)]
