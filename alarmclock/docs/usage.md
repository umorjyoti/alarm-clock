# CLI Usage

Requires `pip install "alarmclock[cli]"`.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error (e.g. no alarms to run) |
| 2 | Invalid input / not found |

## add

```bash
alarm add 07:30
alarm add --at 07:30 --label "Wake up"
alarm add --in 25m
alarm add --in 1h30m --repeat daily
alarm add --sound /path/to.wav
alarm add   # interactive wizard
```

## list

```bash
alarm list
alarm list --all
```

## remove / enable / disable

```bash
alarm remove abc12345
alarm disable abc12345
alarm enable abc12345
```

## snooze

```bash
alarm snooze abc12345 --for 5m
```

## status

```bash
alarm status
```

## start / stop (background — recommended)

```bash
alarm start
alarm status
alarm stop
```

Runs the scheduler in the background. Alarms play the bundled **rooster** sound (`afplay` on macOS) and show a system notification. Logs: `~/.config/alarmclock/daemon.log`.

Only **one** daemon can run (file lock). Adding alarms while the daemon runs wakes it immediately to reschedule.

## service (macOS — auto restart)

```bash
alarm service install    # start on login, restart on crash (throttled 30s)
alarm service status
alarm service uninstall
```

After logout the daemon stops; it starts again on next login if installed.

## run (foreground)

```bash
alarm run
alarm run --dashboard
```

Press `Ctrl+C` to stop. When an alarm fires, you may snooze interactively. Same rooster sound + notification as `alarm start`.

## Tips

- Run inside `tmux` or `screen` so closing the terminal does not stop the scheduler.
- Set `NO_COLOR=1` for plain output without ANSI colors.
