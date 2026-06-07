from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from alarmclock.exceptions import AlarmNotFoundError
from alarmclock.models import Alarm, Repeat
from alarmclock.store import AlarmStore


@pytest.fixture
def store(tmp_path: Path) -> AlarmStore:
    return AlarmStore(tmp_path / "alarms.json")


def test_round_trip(store: AlarmStore):
    tz = ZoneInfo("UTC")
    alarm = Alarm(
        id="abc12345",
        fire_at=datetime(2026, 6, 3, 7, 30, tzinfo=tz),
        label="Test",
        repeat=Repeat.DAILY,
    )
    store.add(alarm)
    loaded = store.load()
    assert len(loaded) == 1
    assert loaded[0].id == alarm.id
    assert loaded[0].label == "Test"
    assert loaded[0].repeat == Repeat.DAILY


def test_remove(store: AlarmStore):
    tz = ZoneInfo("UTC")
    alarm = Alarm(id="x1", fire_at=datetime(2026, 6, 3, 8, 0, tzinfo=tz))
    store.add(alarm)
    store.remove("x1")
    assert store.load() == []


def test_remove_missing(store: AlarmStore):
    with pytest.raises(AlarmNotFoundError):
        store.remove("missing")
