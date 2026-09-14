"""Command-line entry point.

Usage:
    python main.py --config config/settings.yaml
    python main.py --demo               # run against the bundled sample data
"""

from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

from .config import load_config
from .pipeline import run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="EIS boxplot/timeseries -> PPTX report generator")
    parser.add_argument(
        "--config", "-c", type=str, default="config/settings.yaml",
        help="Path to the YAML config file (default: config/settings.yaml)",
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="Ignore --config and run against the bundled sample_data/ files "
             "so you can see the report format before pointing at real data.",
    )
    args = parser.parse_args(argv)

    config_path = None if args.demo else args.config
    if not args.demo and not Path(config_path).exists():
        print(
            f"[!] Config file '{config_path}' not found.\n"
            f"    Copy config/settings.example.yaml to {config_path} and edit "
            f"the file paths, or run with --demo to try the sample data first.",
            file=sys.stderr,
        )
        return 2

    try:
        cfg = load_config(config_path)
        run(cfg)
    except Exception as exc:  # noqa: BLE001 - top-level CLI error boundary
        print(f"[!] Failed to generate report: {exc}", file=sys.stderr)
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
