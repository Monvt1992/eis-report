#!/usr/bin/env python3
"""Entry point: `python main.py --config config/settings.yaml` or `--demo`."""

from eis_report.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
