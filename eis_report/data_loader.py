"""Load the three source Excel files and normalize them for charting."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pandas as pd

from .cw import cw_from_datetime, cw_from_mixno


def _add_cw_column(df: pd.DataFrame, task_cfg: Dict[str, Any]) -> pd.DataFrame:
    source = task_cfg.get("cw_source", "mixno")
    if source == "datetime":
        col = task_cfg["datetime_column"]
        if col not in df.columns:
            raise KeyError(
                f"Datetime column '{col}' not found for CW calculation. "
                f"Available columns: {list(df.columns)}"
            )
        df["CW"] = cw_from_datetime(df[col])
    elif source == "mixno":
        col = task_cfg["mixno_column"]
        if col not in df.columns:
            raise KeyError(
                f"MixNo column '{col}' not found for CW calculation. "
                f"Available columns: {list(df.columns)}"
            )
        df["CW"] = cw_from_mixno(df[col])
    else:
        raise ValueError(f"Unknown cw_source: {source!r} (expected 'datetime' or 'mixno')")

    df = df.dropna(subset=["CW"]).copy()
    df["CW"] = df["CW"].astype(int)
    return df


def _ensure_eis14(df: pd.DataFrame, columns: Dict[str, str], e1_key: str, e2_key: str,
                   e4_key: str, e14_key: str) -> pd.DataFrame:
    """Compute the Eis14 (or WtAvgEis14) column if it isn't already present.

    Formula supplied by the user: Eis14 = Eis4 + abs(Eis1) - abs(Eis2)
    """
    col14 = columns.get(e14_key)
    if col14 and col14 in df.columns:
        return df

    col1, col2, col4 = columns.get(e1_key), columns.get(e2_key), columns.get(e4_key)
    missing = [c for c in (col1, col2, col4) if c is None or c not in df.columns]
    if missing:
        raise KeyError(
            f"Cannot compute '{col14}': need columns {col1}, {col2}, {col4} "
            f"in the source file, but some are missing. Available columns: "
            f"{list(df.columns)}"
        )

    out_name = col14 or "Eis14"
    df[out_name] = df[col4] + df[col1].abs() - df[col2].abs()
    columns[e14_key] = out_name
    return df


def load_task1(cfg: Dict[str, Any]) -> pd.DataFrame:
    task_cfg = cfg["task1_production_data"]
    path = Path(task_cfg["file"])
    if not path.exists():
        raise FileNotFoundError(f"Task 1 input file not found: {path}")

    df = pd.read_excel(path, sheet_name=task_cfg.get("sheet", 0))
    df = _add_cw_column(df, task_cfg)
    df = _ensure_eis14(df, task_cfg["columns"], "eis1", "eis2", "eis4", "eis14")
    return df


def load_task2(cfg: Dict[str, Any]) -> pd.DataFrame:
    task_cfg = cfg["task2_mix_result"]
    path = Path(task_cfg["file"])
    if not path.exists():
        raise FileNotFoundError(f"Task 2 input file not found: {path}")

    df = pd.read_excel(path, sheet_name=task_cfg.get("sheet", 0))
    df = _add_cw_column(df, task_cfg)
    df = _ensure_eis14(df, task_cfg["columns"], "wtavgeis1", "wtavgeis2", "wtavgeis4", "wtavgeis14")
    return df


def load_task3(cfg: Dict[str, Any]) -> pd.DataFrame:
    task_cfg = cfg["task3_timeseries"]
    path = Path(task_cfg["file"])
    if not path.exists():
        raise FileNotFoundError(f"Task 3 input file not found: {path}")

    df = pd.read_excel(path, sheet_name=task_cfg.get("sheet", 0))
    df = _add_cw_column(df, task_cfg)

    date_col = task_cfg.get("date_column")
    if date_col and date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.sort_values(date_col).reset_index(drop=True)
    else:
        df = df.sort_values("CW").reset_index(drop=True)

    return df
