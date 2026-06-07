# alarmclock

Python alarm clock **library** with an optional terminal CLI. Schedule reminders programmatically or use the `alarm` command.

## Install

**CLI (end users):**

```bash
pip install "alarmclock[cli]"
```

**Library only (embed in your app, no Typer/Rich):**

```bash
pip install alarmclock
```

**Development:**

```bash
cd alarmclock
pip install -e ".[all]"
```

## Quick Start — CLI

```bash
alarm add --at 07:30 --label "Wake up"
alarm start          # run in background (recommended)
alarm status
```

Foreground mode (terminal must stay open):

```bash
alarm run
```

Stop background daemon: `alarm stop`

**Auto-start on login + restart on crash (macOS):**

```bash
alarm service install
alarm service status
```

Uninstall: `alarm service uninstall`

Relative alarm:

```bash
alarm add --in 25m --label "Break"
```

## Quick Start — Library

```python
from datetime import time
from alarmclock import AlarmService

svc = AlarmService(store_path="/tmp/myapp-alarms.json")
svc.add(at=time(14, 30), label="Standup")
svc.create_scheduler(on_fire=lambda a: print(f"Fired: {a.label}")).run()
```

## Embed in your CLI (Typer)

```python
import typer
from alarmclock.cli import app as alarm_app

app = typer.Typer()
app.add_typer(alarm_app, name="alarm")  # → mytool alarm add ...
```

See [examples/embed_typer.py](examples/embed_typer.py) and [docs/library.md](docs/library.md).

## Commands

| Command | Description |
|---------|-------------|
| `alarm add` | Add alarm (`--at HH:MM` or `--in 25m`) |
| `alarm list` | List alarms (`--all` includes disabled) |
| `alarm remove <id>` | Delete alarm |
| `alarm enable/disable <id>` | Toggle without deleting |
| `alarm snooze <id> --for 5m` | Postpone |
| `alarm status` | Next alarm and countdown |
| `alarm start` | Run scheduler in background (rooster sound + OS notification) |
| `alarm stop` | Stop background daemon |
| `alarm run` | Foreground scheduler (`--dashboard` for live view) |

Full reference: [docs/usage.md](docs/usage.md).

## Configuration

| Location | Purpose |
|----------|---------|
| `~/.config/alarmclock/alarms.json` | Default alarm store |
| `$XDG_CONFIG_HOME/alarmclock/alarms.json` | XDG override |
| `NO_COLOR=1` | Disable Rich colors |

## Documentation

- [Library API](docs/library.md)
- [CLI usage](docs/usage.md)
- [Architecture](docs/architecture.md)

## License

MIT
