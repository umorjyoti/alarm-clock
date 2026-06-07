from alarmclock.api import AlarmService
from alarmclock.reload import notify_store_changed, register_scheduler


def test_store_change_wakes_registered_scheduler(tmp_path):
    service = AlarmService(store_path=tmp_path / "alarms.json")
    scheduler = service.create_scheduler(on_fire=lambda a: None)
    register_scheduler(scheduler)
    scheduler._wake.clear()

    service.add(in_="1h", label="later")
    assert scheduler._wake.is_set()

    scheduler._wake.clear()
    notify_store_changed()
    assert scheduler._wake.is_set()
