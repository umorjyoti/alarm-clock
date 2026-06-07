# Architecture

## Layers

```
Consumers (scripts, host CLIs, alarm CLI)
        ↓
  alarmclock.api.AlarmService
        ↓
  models · store · scheduler · parser · notify
        ↓
  (optional) alarmclock.cli — Typer + Rich
```

- **Core** has zero third-party dependencies.
- **CLI** depends on Typer and Rich (`[cli]` extra) and only calls `AlarmService`.

## Persistence

Alarms are stored as JSON:

```json
{
  "alarms": [
    {
      "id": "a1b2c3d4",
      "fire_at": "2026-06-03T07:30:00+05:30",
      "label": "Wake up",
      "repeat": "daily",
      "enabled": true,
      "sound_path": null
    }
  ]
}
```

Default path: `~/.config/alarmclock/alarms.json` (or `$XDG_CONFIG_HOME`).

## Scheduler

The scheduler avoids busy-polling:

1. Load enabled alarms.
2. Compute the nearest next fire time.
3. `threading.Event.wait(timeout=seconds)`.
4. On wake, fire due alarms via `on_fire` or `Notifier`.
5. Once alarms are removed after firing; daily alarms remain.

`scheduler.wake()` interrupts the wait when alarms change (via `notify_store_changed()` on every store write).

## Daemon safety

- **Singleton:** `fcntl` exclusive lock on `daemon.lock` — a second instance exits immediately (prevents 10–1000 processes).
- **Stale PID cleanup:** dead PIDs are removed on `alarm start` / `alarm status`.
- **Long sleeps:** chunked to 1 hour max, then reloads alarms from disk.
- **Idle:** polls every 5 minutes when no alarms (negligible CPU).
- **Sound:** one `afplay` at a time (lock) so simultaneous alarms do not stack players.
- **Log rotation:** `daemon.log` rotates at 512 KB.

## Packaging

| Extra | Dependencies |
|-------|----------------|
| (none) | stdlib only |
| `cli` | typer, rich |
| `dev` | pytest, pytest-cov |

Console script: `alarm` → `alarmclock.cli.main:main`.
