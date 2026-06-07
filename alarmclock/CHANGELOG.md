# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-03

### Added

- `AlarmService` public API with JSON persistence
- `AlarmScheduler` with efficient event-based waiting
- Optional CLI (`alarm` command) via `[cli]` extra
- Commands: add, list, remove, enable, disable, snooze, status, run
- Typer sub-app embedding (`alarmclock.cli.app`)
- Examples and documentation
