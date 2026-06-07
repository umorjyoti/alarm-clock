# Library API

Install the core package without CLI dependencies:

```bash
pip install alarmclock
```

## Public exports

```python
from alarmclock import (
    Alarm,
    AlarmService,
    AlarmStore,
    Repeat,
    parse_time,
    parse_duration,
    AlarmNotFoundError,
    InvalidTimeError,
)
from alarmclock.scheduler import AlarmScheduler, OnAlarmCallback
```

## AlarmService

```python
from datetime import time
from pathlib import Path
from alarmclock import AlarmService

service = AlarmService(
    store_path=Path("/tmp/myapp/alarms.json"),  # optional
)
```

| Method | Description |
|--------|-------------|
| `add(at=..., in_=..., label=..., repeat=...)` | Create alarm |
| `list(enabled_only=False)` | List alarms |
| `get(id)` | Get one alarm |
| `remove(id)` | Delete |
| `enable(id)` / `disable(id)` | Toggle |
| `snooze(id, duration)` | Postpone (`"5m"` or `timedelta`) |
| `status()` | `AlarmStatus` with next fire / countdown |
| `create_scheduler(on_fire=..., notifier=...)` | Build scheduler |

### Programmatic scheduling

```python
def on_fire(alarm):
    print(f"Alarm: {alarm.label} at {alarm.fire_at}")

scheduler = service.create_scheduler(on_fire=on_fire)
scheduler.run()          # blocking
# scheduler.start()      # background thread
# scheduler.stop()       # stop loop
```

### Custom notifier

```python
from alarmclock.notify import Notifier

class MyNotifier:
    def notify(self, alarm):
        send_slack(alarm.label)

service.create_scheduler(notifier=MyNotifier()).run()
```

## Typer embedding

```python
import typer
from alarmclock.cli import app as alarm_app

host = typer.Typer()
host.add_typer(alarm_app, name="alarm")
```

Requires `pip install "alarmclock[cli]"`.

## Primitives only

```python
from alarmclock import AlarmStore, parse_duration, Alarm

store = AlarmStore(path="alarms.json")
alarms = store.load()
```

## Versioning

SemVer from `0.1.0`. Breaking API changes are documented in `CHANGELOG.md`.
