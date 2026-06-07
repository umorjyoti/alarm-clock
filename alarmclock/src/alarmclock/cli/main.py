"""Typer CLI entry point."""

from __future__ import annotations

import sys
from typing import Optional

import typer
from rich.prompt import Confirm, Prompt

from alarmclock.api import AlarmService
from alarmclock.exceptions import AlarmNotFoundError, AlarmclockError, InvalidTimeError
from alarmclock.models import Repeat
from alarmclock.cli.console import (
    get_console,
    print_alarm_fired,
    print_alarm_table,
    print_banner,
    print_error,
    print_status,
)

app = typer.Typer(
    name="alarm",
    help="Terminal alarm clock — set, list, and run alarms.",
    no_args_is_help=True,
    add_completion=False,
)

_service: AlarmService | None = None


def get_service() -> AlarmService:
    global _service
    if _service is None:
        _service = AlarmService()
    return _service


def _exit_invalid(message: str, hint: str | None = None) -> None:
    print_error(get_console(), message, hint)
    raise typer.Exit(code=2)


def _looks_like_clock_time(value: str) -> bool:
    """True if value looks like HH:MM rather than a duration."""
    value = value.strip().lstrip("+")
    if ":" in value:
        return True
    return value.isdigit() and len(value) <= 2


@app.command("add")
def add(
    at_pos: Optional[str] = typer.Argument(
        None,
        metavar="[AT]",
        help="Clock time HH:MM (or use --at)",
    ),
    at_time: Optional[str] = typer.Option(
        None,
        "--at",
        help="Clock time HH:MM",
    ),
    in_minutes: Optional[str] = typer.Option(
        None,
        "--in",
        help="Relative duration e.g. 25m, 1h30m, +25m",
    ),
    label: Optional[str] = typer.Option(None, "--label", "-l", help="Alarm label"),
    repeat: str = typer.Option("once", "--repeat", "-r", help="once or daily"),
    sound: Optional[str] = typer.Option(None, "--sound", help="Path to sound file"),
) -> None:
    """Add a new alarm."""
    console = get_console()
    service = get_service()

    clock_at = at_time or at_pos
    duration = in_minutes

    # Positional +25m / 25m style relative times
    if clock_at and clock_at.lstrip().startswith("+"):
        duration = clock_at.lstrip().lstrip("+").strip() or clock_at
        clock_at = None
    elif clock_at and duration is None and not _looks_like_clock_time(clock_at):
        duration = clock_at
        clock_at = None

    if clock_at is None and duration is None:
        print_banner(console)
        clock_at = Prompt.ask("Time (HH:MM) or leave empty for duration")
        if not clock_at.strip():
            duration = Prompt.ask("Duration (e.g. 25m)")
        if not label:
            label = Prompt.ask("Label (optional)", default="") or ""

    try:
        alarm = service.add(
            at=clock_at if clock_at else None,
            in_=duration,
            label=label or "",
            repeat=repeat,
            sound_path=sound,
        )
        console.print(
            f"[green]✓[/] Alarm {alarm.id} set for {alarm.fire_at.strftime('%H:%M on %b %d')}"
            if not console.no_color
            else f"Alarm {alarm.id} set for {alarm.fire_at.strftime('%H:%M on %b %d')}"
        )
    except InvalidTimeError as exc:
        _exit_invalid(str(exc), "Use HH:MM or --in 25m")
    except AlarmclockError as exc:
        _exit_invalid(str(exc))


@app.command("list")
def list_alarms(
    all_: bool = typer.Option(False, "--all", "-a", help="Include disabled alarms"),
) -> None:
    """List all alarms."""
    console = get_console()
    service = get_service()
    alarms = service.list(enabled_only=not all_)
    if all_:
        alarms = service.list()
    status = service.status()
    print_alarm_table(console, alarms, status)


@app.command("remove")
def remove(alarm_id: str = typer.Argument(..., help="Alarm ID")) -> None:
    """Remove an alarm."""
    console = get_console()
    try:
        get_service().remove(alarm_id)
        console.print(f"[green]✓[/] Removed {alarm_id}" if not console.no_color else f"Removed {alarm_id}")
    except AlarmNotFoundError:
        _exit_invalid(f"Alarm not found: {alarm_id}", "Run alarm list to see IDs")


@app.command("disable")
def disable(alarm_id: str = typer.Argument(..., help="Alarm ID")) -> None:
    """Disable an alarm without deleting it."""
    try:
        get_service().disable(alarm_id)
        get_console().print(f"Disabled {alarm_id}")
    except AlarmNotFoundError:
        _exit_invalid(f"Alarm not found: {alarm_id}")


@app.command("enable")
def enable(alarm_id: str = typer.Argument(..., help="Alarm ID")) -> None:
    """Re-enable a disabled alarm."""
    try:
        get_service().enable(alarm_id)
        get_console().print(f"Enabled {alarm_id}")
    except AlarmNotFoundError:
        _exit_invalid(f"Alarm not found: {alarm_id}")


@app.command("snooze")
def snooze(
    alarm_id: str = typer.Argument(..., help="Alarm ID"),
    for_duration: str = typer.Option("5m", "--for", "-f", help="Snooze duration"),
) -> None:
    """Snooze an alarm."""
    try:
        alarm = get_service().snooze(alarm_id, for_duration)
        get_console().print(
            f"Snoozed {alarm_id} until {alarm.fire_at.strftime('%H:%M')}"
        )
    except AlarmNotFoundError:
        _exit_invalid(f"Alarm not found: {alarm_id}")
    except InvalidTimeError as exc:
        _exit_invalid(str(exc))


@app.command("status")
def status() -> None:
    """Show next alarm, countdown, and daemon state."""
    from alarmclock.daemon import is_running, read_pid

    console = get_console()
    print_status(console, get_service().status())
    if is_running():
        console.print(f"Daemon: [green]running[/] (PID {read_pid()})" if not console.no_color else f"Daemon: running (PID {read_pid()})")
    else:
        console.print("[dim]Daemon: stopped (use `alarm start` to run in background)[/]" if not console.no_color else "Daemon: stopped (use `alarm start`)")
    if sys.platform == "darwin":
        from alarmclock.launchd import is_installed

        if is_installed():
            console.print("[dim]LaunchAgent: installed (login + crash restart)[/]" if not console.no_color else "LaunchAgent: installed")


@app.command("start")
def start_daemon_cmd() -> None:
    """Start alarms in the background (no need to keep a terminal open)."""
    from alarmclock.daemon import is_running, read_pid, start

    console = get_console()
    try:
        pid = start()
        console.print(
            f"[green]✓[/] Daemon started (PID {pid}). Alarms will fire with rooster sound + notification."
            if not console.no_color
            else f"Daemon started (PID {pid})."
        )
        console.print("  Stop with: [cyan]alarm stop[/]" if not console.no_color else "  Stop with: alarm stop")
        console.print("  Auto on login: [cyan]alarm service install[/]" if not console.no_color else "  Auto on login: alarm service install")
        console.print("  Log: ~/.config/alarmclock/daemon.log")
    except RuntimeError as exc:
        console.print(f"[yellow]{exc}[/]" if not console.no_color else str(exc))
        if is_running():
            console.print(f"  PID: {read_pid()}")
        raise typer.Exit(code=1)


@app.command("stop")
def stop_daemon_cmd() -> None:
    """Stop the background alarm daemon."""
    from alarmclock.daemon import stop

    console = get_console()
    if stop():
        console.print("[green]✓[/] Daemon stopped." if not console.no_color else "Daemon stopped.")
    else:
        console.print("[dim]Daemon was not running.[/]" if not console.no_color else "Daemon was not running.")


service_app = typer.Typer(help="Auto-start on login and restart on crash (macOS).")
app.add_typer(service_app, name="service")


@service_app.command("install")
def service_install() -> None:
    """Install macOS LaunchAgent: start on login, restart on crash."""
    import sys

    console = get_console()
    if sys.platform != "darwin":
        _exit_invalid("LaunchAgent is only supported on macOS.", "Use `alarm start` manually.")
    from alarmclock.launchd import install, is_installed

    path = install()
    console.print(f"[green]✓[/] Installed LaunchAgent: {path}" if not console.no_color else f"Installed: {path}")
    console.print("  Starts on login, restarts on crash (max every 30s).")
    console.print("  Remove with: [cyan]alarm service uninstall[/]" if not console.no_color else "  Remove: alarm service uninstall")
    if not is_installed():
        console.print("[yellow]Warning: plist file missing after install.[/]" if not console.no_color else "Warning: install may have failed.")


@service_app.command("uninstall")
def service_uninstall() -> None:
    """Remove macOS LaunchAgent."""
    import sys

    from alarmclock.daemon import stop
    from alarmclock.launchd import uninstall

    console = get_console()
    if sys.platform != "darwin":
        _exit_invalid("LaunchAgent is only supported on macOS.")
    stop()
    if uninstall():
        console.print("[green]✓[/] LaunchAgent removed." if not console.no_color else "LaunchAgent removed.")
    else:
        console.print("[dim]LaunchAgent was not installed.[/]" if not console.no_color else "Not installed.")


@service_app.command("status")
def service_status() -> None:
    """Show LaunchAgent install/load state."""
    import sys

    from alarmclock.launchd import is_installed, is_loaded, launch_agent_path

    console = get_console()
    if sys.platform != "darwin":
        console.print("LaunchAgent: N/A (macOS only)")
        return
    if is_installed():
        console.print(f"Installed: {launch_agent_path()}")
        console.print(f"Loaded: {'yes' if is_loaded() else 'no'}")
    else:
        console.print("[dim]Not installed. Run: alarm service install[/]" if not console.no_color else "Not installed.")


@app.command("run")
def run(
    dashboard: bool = typer.Option(False, "--dashboard", help="Live status refresh"),
) -> None:
    """Run the alarm scheduler until interrupted."""
    console = get_console()
    service = get_service()

    if not service.list(enabled_only=True):
        console.print("[dim]No enabled alarms. Add one with: alarm add --at 07:30[/]")
        raise typer.Exit(code=1)

    print_banner(console)
    st = service.status()
    if st.next_alarm and st.next_fire_at and st.seconds_until_next is not None:
        label = st.next_alarm.label or st.next_alarm.id
        when = st.next_fire_at.strftime("%H:%M (%Z)")
        from alarmclock.cli.console import format_countdown

        console.print(
            f"Next alarm: [bold]{label}[/] at {when} (in {format_countdown(st.seconds_until_next)})"
            if not console.no_color
            else f"Next alarm: {label} at {when} (in {format_countdown(st.seconds_until_next)})"
        )
    console.print("Scheduler running. Keep this terminal open until the alarm fires.")
    console.print("At fire time: panel + rooster sound + macOS notification.")
    console.print("Or use [cyan]alarm start[/] to run in the background. Press Ctrl+C to stop.\n")

    def on_fire(alarm):
        print_alarm_fired(console, alarm)  # includes rooster sound
        if Confirm.ask("Snooze 5m?", default=False):
            try:
                service.snooze(alarm.id, "5m")
                console.print("[dim]Snoozed 5 minutes.[/]")
            except AlarmNotFoundError:
                pass

    scheduler = service.create_scheduler(on_fire=on_fire)

    if dashboard:
        from rich.live import Live
        from rich.table import Table

        def render():
            st = service.status()
            t = Table(show_header=False, box=None)
            t.add_row("Enabled", str(st.enabled_count))
            if st.next_alarm:
                t.add_row("Next", st.next_alarm.label or st.next_alarm.id)
                from alarmclock.cli.console import format_countdown

                t.add_row("In", format_countdown(st.seconds_until_next))
            return t

        try:
            with Live(render(), refresh_per_second=1, console=console):
                scheduler.run()
        except KeyboardInterrupt:
            scheduler.stop()
    else:
        try:
            scheduler.run()
        except KeyboardInterrupt:
            scheduler.stop()
            console.print("\n[dim]Stopped.[/]")


def main() -> None:
    """Console script entry."""
    try:
        app()
    except typer.Exit:
        raise
    except AlarmclockError as exc:
        print_error(get_console(), str(exc))
        sys.exit(2)


if __name__ == "__main__":
    main()
