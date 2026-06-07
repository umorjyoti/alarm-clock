from datetime import time, timedelta

import pytest

from alarmclock.exceptions import InvalidTimeError
from alarmclock.parser import parse_duration, parse_time


def test_parse_time_valid():
    assert parse_time("07:30") == time(7, 30)
    assert parse_time("9:05") == time(9, 5)


def test_parse_time_invalid():
    with pytest.raises(InvalidTimeError):
        parse_time("25:00")
    with pytest.raises(InvalidTimeError):
        parse_time("noon")


def test_parse_duration_minutes():
    assert parse_duration("25m") == timedelta(minutes=25)
    assert parse_duration("+30m") == timedelta(minutes=30)


def test_parse_duration_compound():
    assert parse_duration("1h30m") == timedelta(hours=1, minutes=30)


def test_parse_duration_seconds():
    assert parse_duration("90s") == timedelta(seconds=90)


def test_parse_duration_days():
    assert parse_duration("3d") == timedelta(days=3)
    assert parse_duration("1h30m") == timedelta(hours=1, minutes=30)
