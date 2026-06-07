#!/usr/bin/env python3
"""Example: embed alarmclock CLI as a Typer sub-application."""

import typer

from alarmclock.cli import app as alarm_app

host = typer.Typer(help="My tool — includes alarmclock as a subcommand.")
host.add_typer(alarm_app, name="alarm")


@host.command()
def greet(name: str = "World"):
    """Host app's own command."""
    typer.echo(f"Hello, {name}!")


if __name__ == "__main__":
    host()
