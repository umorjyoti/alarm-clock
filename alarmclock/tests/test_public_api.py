import alarmclock
from alarmclock import (
    Alarm,
    AlarmNotFoundError,
    AlarmScheduler,
    AlarmService,
    AlarmStatus,
    AlarmStore,
    InvalidTimeError,
    OnAlarmCallback,
    Repeat,
    default_store_path,
    parse_duration,
    parse_time,
)


def test_all_exports():
    expected = {
        "Alarm",
        "AlarmNotFoundError",
        "AlarmScheduler",
        "AlarmService",
        "AlarmStatus",
        "AlarmStore",
        "AlarmclockError",
        "InvalidTimeError",
        "OnAlarmCallback",
        "Repeat",
        "default_store_path",
        "parse_duration",
        "parse_time",
    }
    assert set(alarmclock.__all__) == expected


def test_alarm_service_methods():
    methods = {
        "add",
        "list",
        "get",
        "remove",
        "enable",
        "disable",
        "snooze",
        "status",
        "create_scheduler",
    }
    assert methods.issubset(dir(AlarmService))
