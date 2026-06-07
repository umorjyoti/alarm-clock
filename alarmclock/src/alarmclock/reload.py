"""Notify running schedulers when the alarm store changes."""

from __future__ import annotations

import weakref
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from alarmclock.scheduler import AlarmScheduler

_schedulers: list[weakref.ReferenceType[AlarmScheduler]] = []


def register_scheduler(scheduler: AlarmScheduler) -> None:
    _schedulers.append(weakref.ref(scheduler))


def unregister_scheduler(scheduler: AlarmScheduler) -> None:
    _schedulers[:] = [r for r in _schedulers if r() is not None and r() is not scheduler]


def notify_store_changed() -> None:
    """Wake all live schedulers so they reload and recalculate sleep."""
    for ref in list(_schedulers):
        scheduler = ref()
        if scheduler is not None:
            scheduler.wake()
