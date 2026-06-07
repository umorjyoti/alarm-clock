from datetime import time
from pathlib import Path

import pytest

from alarmclock import AlarmService, Repeat
from alarmclock.exceptions import AlarmNotFoundError, InvalidTimeError


@pytest.fixture
def service(tmp_path: Path) -> AlarmService:
    return AlarmService(store_path=tmp_path / "alarms.json")


def test_add_at_time(service: AlarmService):
    alarm = service.add(at=time(9, 15), label="Standup")
    assert alarm.label == "Standup"
    assert alarm.fire_at.hour == 9
    assert alarm.fire_at.minute == 15


def test_add_in_duration(service: AlarmService):
    alarm = service.add(in_="1m", label="Soon")
    assert alarm.label == "Soon"


def test_list_remove(service: AlarmService):
    alarm = service.add(at="10:00")
    assert len(service.list()) == 1
    service.remove(alarm.id)
    assert service.list() == []


def test_enable_disable(service: AlarmService):
    alarm = service.add(at="08:00")
    service.disable(alarm.id)
    assert not service.get(alarm.id).enabled
    service.enable(alarm.id)
    assert service.get(alarm.id).enabled


def test_snooze(service: AlarmService):
    alarm = service.add(in_="2h")
    original_fire = alarm.fire_at
    updated = service.snooze(alarm.id, "10m")
    assert updated.fire_at < original_fire
    assert updated.enabled


def test_status_empty(service: AlarmService):
    st = service.status()
    assert st.total == 0
    assert st.next_alarm is None


def test_add_requires_time(service: AlarmService):
    with pytest.raises(InvalidTimeError):
        service.add()


def test_get_missing(service: AlarmService):
    with pytest.raises(AlarmNotFoundError):
        service.get("nope")


def test_repeat_daily(service: AlarmService):
    alarm = service.add(at="06:00", repeat="daily")
    assert alarm.repeat == Repeat.DAILY
