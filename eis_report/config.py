"""Load and validate the YAML configuration file."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Dict

import yaml

DEFAULT_CONFIG: Dict[str, Any] = {
    "output": {
        "pptx_path": "output/EIS_Report.pptx",
        "charts_dir": "output/charts",
    },
    "template": {
        # Path to the standard PPTX template provided by the user.
        # Leave empty ("") to let the tool generate a blank template.
        "pptx_path": "",
    },
    "milestone": {
        "cw": 37,
        "title": "4M Implement",
        "before_color": "#DCE9F7",  # light blue background before milestone
        "after_color": "#DFF3E1",   # light green background after milestone
        "line_color": "#C00000",
        "title_color": "#C00000",
    },
    "task1_production_data": {
        "enabled": True,
        "file": "sample_data/productiondata.xlsx",
        "sheet": 0,
        "cw_source": "datetime",          # "datetime" or "mixno"
        "datetime_column": "MEETMOMENT",
        "mixno_column": "MixNo",
        "columns": {
            "eis1": "Eis1",
            "eis2": "Eis2",
            "eis4": "Eis4",
            "eis5": "Eis5",
            "eis14": "Eis14",  # computed if missing: Eis4 + abs(Eis1) - abs(Eis2)
        },
        "charts": ["eis2", "eis5", "eis14"],
    },
    "task2_mix_result": {
        "enabled": True,
        "file": "sample_data/Mix_result.xlsx",
        "sheet": 0,
        "cw_source": "mixno",
        "datetime_column": "MEETMOMENT",
        "mixno_column": "MixNo",
        "columns": {
            "wtavgeis1": "WtAvgEis1",
            "wtavgeis2": "WtAvgEis2",
            "wtavgeis4": "WtAvgEis4",
            "wtavgeis5": "WtAvgEis5",
            "wtavgeis14": "WtAvgEis14",
        },
        "charts": ["wtavgeis2", "wtavgeis5", "wtavgeis14"],
    },
    "task3_timeseries": {
        "enabled": True,
        "file": "sample_data/Wt Avg Eis 2022-2026_all type.xlsx",
        "sheet": 0,
        "cw_source": "mixno",
        "date_column": "Date",
        "mixno_column": "MixNo",
        "group_column": "Group",
        "columns": {
            "wtavgeis2": "WtAvgEis2",
            "wtavgeis5": "WtAvgEis5",
            "wtavgeis14": "WtAvgEis14",
        },
        "charts": ["wtavgeis2", "wtavgeis5", "wtavgeis14"],
        "moving_average_window": 5,
        "stretch_after_milestone": True,
        "min_after_width_ratio": 0.35,
    },
    "style": {
        "figure_width_in": 12.0,
        "figure_height_in": 6.0,
        "dpi": 200,
        "box_color": "#4472C4",
        "trend_color": "#ED7D31",
        "ma_color": "#ED7D31",
        "font_family": "Calibri",
    },
}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(path: str | Path | None) -> Dict[str, Any]:
    """Load a YAML config and merge it on top of the built-in defaults.

    If `path` is None or the file does not exist, the defaults are returned
    unchanged (useful for `--demo` / sample-data runs).
    """
    if path is None:
        return copy.deepcopy(DEFAULT_CONFIG)

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as fh:
        user_config = yaml.safe_load(fh) or {}

    return _deep_merge(DEFAULT_CONFIG, user_config)
