"""Rich console helpers (Terminal Swiss)."""

from __future__ import annotations

import os
from datetime import timedelta

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from alarmclock.models import Alarm, AlarmStatus

NO_COLOR = os.environ.get("NO_COLOR", "") != ""


def get_console() -> Console:
    return Console(no_color=NO_COLOR, highlight=False)


def format_countdown(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}h {minutes}m"


def print_banner(console: Console) -> None:
    console.print("[bold]alarmclock[/] — terminal alarm scheduler", style="dim")


def print_alarm_table(console: Console, alarms: list[Alarm], status: AlarmStatus | None = None) -> None:
    if not alarms:
        console.print("[dim]No alarms yet.[/]")
        console.print("  Example: [cyan]alarm add --at 07:30 --label \"Wake up\"[/]")
        return

    table = Table(
        title=f"Alarms ({status.enabled_count if status else sum(1 for a in alarms if a.enabled)} enabled)",
        show_header=True,
        header_style="bold",
        border_style="dim",
    )
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Time", no_wrap=True)
    table.add_column("Label")
    table.add_column("Repeat")
    table.add_column("Status")

    for alarm in alarms:
        fire_str = alarm.fire_at.strftime("%H:%M")
        if alarm.repeat.value == "daily":
            fire_str = alarm.fire_at.strftime("%H:%M") + " (daily)"
        state = "[green]enabled[/]" if alarm.enabled else "[dim]disabled[/]"
        if NO_COLOR:
            state = "enabled" if alarm.enabled else "disabled"
        table.add_row(
            alarm.id,
            fire_str,
            alarm.label or "—",
            alarm.repeat.value,
            state,
        )

    console.print(table)

    if status and status.next_alarm and status.seconds_until_next is not None:
        label = status.next_alarm.label or status.next_alarm.id
        countdown = format_countdown(status.seconds_until_next)
        console.print(f"Next: [bold]{label}[/] in {countdown}")


def print_status(console: Console, status: AlarmStatus) -> None:
    print_banner(console)
    console.print(f"Total alarms: {status.total}")
    console.print(f"Enabled: {status.enabled_count}")
    if status.next_alarm and status.seconds_until_next is not None:
        label = status.next_alarm.label or status.next_alarm.id
        when = status.next_fire_at.strftime("%H:%M") if status.next_fire_at else "?"
        countdown = format_countdown(status.seconds_until_next)
        console.print(f"Next: [bold]{label}[/] at {when} (in {countdown})")
    else:
        console.print("[dim]No upcoming alarms.[/]")


def print_alarm_fired(console: Console, alarm: Alarm) -> None:
    from alarmclock.notify import desktop_notification, play_sound
    from alarmclock.sounds import resolve_sound_path

    label = alarm.label or "Alarm"
    subtitle = alarm.fire_at.strftime("%H:%M — %A, %b %d, %Y")
    console.print()
    console.print(
        Panel(
            Text.assemble(
                ("ALARM: ", "bold"),
                (label, "bold"),
                "\n",
                (subtitle, "dim"),
            ),
            title="",
            border_style="bold yellow" if not NO_COLOR else None,
            padding=(1, 2),
        )
    )
    sound = resolve_sound_path(alarm)
    if sound:
        play_sound(sound)
    else:
        console.print("\a", end="")
    desktop_notification(f"Alarm: {label}", subtitle)


def print_error(console: Console, message: str, hint: str | None = None) -> None:
    console.print(f"[red]error:[/] {message}" if not NO_COLOR else f"error: {message}")
    if hint:
        console.print(f"  {hint}", style="dim")
