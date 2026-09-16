"""Load the three source Excel files and normalize them for charting."""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
import re
from typing import Any, Dict, List, Optional

import pandas as pd

from .cw import cw_from_datetime, cw_from_mixno, year_from_mixno


def _expected_column_names(task_cfg: Dict[str, Any]) -> List[str]:
    """Collect every column name the config expects to find in this file.

    Used to auto-detect the real header row when the sheet has extra
    title/merged-cell rows above the actual column headers (this makes
    pandas read everything as 'Unnamed: N').
    """
    names: List[str] = []
    for key in ("mixno_column", "datetime_column", "date_column", "group_column"):
        value = task_cfg.get(key)
        if value:
            names.append(str(value))
    names.extend(str(v) for v in task_cfg.get("columns", {}).values() if v)
    return names


def _looks_unheadered(df: pd.DataFrame, min_unnamed_ratio: float = 0.5) -> bool:
    unnamed = sum(1 for c in df.columns if str(c).startswith("Unnamed:"))
    return len(df.columns) > 0 and (unnamed / len(df.columns)) >= min_unnamed_ratio


def _find_header_row(path: Path, sheet: Any, expected: List[str], scan_rows: int = 40) -> Optional[int]:
    """Scan the first `scan_rows` rows for the one that best matches the
    column names the config expects, and return its 0-based row index.
    """
    if not expected:
        return None
    raw = pd.read_excel(path, sheet_name=sheet, header=None, nrows=scan_rows)
    expected_lower = {e.strip().lower() for e in expected}
    best_row, best_score = None, 0
    for i in range(len(raw)):
        row_values = {str(v).strip().lower() for v in raw.iloc[i].tolist() if pd.notna(v)}
        score = len(expected_lower & row_values)
        if score > best_score:
            best_row, best_score = i, score
    # Require at least 2 matching expected names (or all of them, if only 1 expected)
    threshold = 1 if len(expected_lower) == 1 else 2
    if best_score >= threshold:
        return best_row
    return None


def _read_source_excel(path: Path, task_cfg: Dict[str, Any], task_label: str) -> pd.DataFrame:
    """Read an input Excel file, honoring an explicit `header` row in the
    config if given, and otherwise auto-detecting it if the default read
    comes back with mostly 'Unnamed: N' columns (extra title rows / merged
    header cells above the real header row).
    """
    sheet = task_cfg.get("sheet", 0)
    header = task_cfg.get("header", 0)
    df = pd.read_excel(path, sheet_name=sheet, header=header)

    if header == 0 and "header" not in task_cfg and _looks_unheadered(df):
        expected = _expected_column_names(task_cfg)
        scan_rows = task_cfg.get("header_scan_rows", 40)
        detected = _find_header_row(path, sheet, expected, scan_rows=scan_rows)
        if detected is not None and detected != 0:
            print(
                f"[i] {task_label}: file's real header row wasn't row 1 of the "
                f"sheet (extra title/merged rows above it) — auto-detected row "
                f"{detected + 1} as the header and re-read the file. Set "
                f"'header: {detected}' explicitly in the config to skip this "
                f"detection next time."
            )
            df = pd.read_excel(path, sheet_name=sheet, header=detected)

    return df


def _add_cw_column(df: pd.DataFrame, task_cfg: Dict[str, Any]) -> pd.DataFrame:
    source = task_cfg.get("cw_source", "mixno")
    if source == "datetime":
        col = task_cfg["datetime_column"]
        if col not in df.columns:
            hint = ""
            if any(str(c).startswith("Unnamed:") for c in df.columns):
                hint = (
                    " (columns show up as 'Unnamed: N' — the real header row "
                    "in this Excel sheet is probably not row 1; set 'header: "
                    "<0-based row index>' for this task in settings.yaml, or "
                    "check for a title/merged-cell row above the real headers)"
                )
            raise KeyError(
                f"Datetime column '{col}' not found for CW calculation. "
                f"Available columns: {list(df.columns)}{hint}"
            )
        df["CW"] = cw_from_datetime(df[col])
    elif source == "mixno":
        col = task_cfg["mixno_column"]
        if col not in df.columns:
            hint = ""
            if any(str(c).startswith("Unnamed:") for c in df.columns):
                hint = (
                    " (columns show up as 'Unnamed: N' — the real header row "
                    "in this Excel sheet is probably not row 1; set 'header: "
                    "<0-based row index>' for this task in settings.yaml, or "
                    "check for a title/merged-cell row above the real headers)"
                )
            raise KeyError(
                f"MixNo column '{col}' not found for CW calculation. "
                f"Available columns: {list(df.columns)}{hint}"
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


def _synthesize_date_from_year_cw(df: pd.DataFrame, year_col: str, cw_col: str = "CW") -> pd.Series:
    """Build a real (Monday-of-ISO-week) date from a year column + a CW
    (ISO week number) column, for files that only record 'which year' +
    'which mix/week' per row instead of an actual timestamp.

    The year column may hold a plain year (2022) or a 'YYYY-MM' style value
    for the current in-progress year (e.g. '2026-06') — only the leading
    4-digit year is used either way.
    """
    year_re = re.compile(r"(\d{4})")

    def _parse_year(value: object) -> Optional[int]:
        if pd.isna(value):
            return None
        m = year_re.match(str(value).strip())
        if m:
            return int(m.group(1))
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    def _to_date(year_val: object, cw_val: object):
        year = _parse_year(year_val)
        try:
            week = int(cw_val)
        except (TypeError, ValueError):
            return pd.NaT
        if year is None:
            return pd.NaT
        week = min(max(week, 1), 53)
        try:
            return pd.Timestamp.fromisocalendar(year, week, 1)
        except ValueError:
            return pd.NaT

    return pd.Series(
        [_to_date(y, w) for y, w in zip(df[year_col], df[cw_col])],
        index=df.index,
    )


def _prettify_raw_columns(df: pd.DataFrame, task_cfg: Dict[str, Any]) -> pd.DataFrame:
    """Some source sheets prefix the metric columns with 'Raw.' (e.g.
    'Raw.WtAvgEis2'). Drop that prefix for chart labels/legends, as long as
    it doesn't collide with an existing column name.
    """
    columns_cfg = task_cfg.get("columns", {})
    rename_map: Dict[str, str] = {}
    for key, col_name in columns_cfg.items():
        if col_name and str(col_name).startswith("Raw.") and col_name in df.columns:
            pretty = str(col_name)[len("Raw."):]
            if pretty and pretty not in df.columns and pretty not in rename_map.values():
                rename_map[col_name] = pretty
                columns_cfg[key] = pretty
    if rename_map:
        df = df.rename(columns=rename_map)
    return df


def _filter_by_mixno_year(df: pd.DataFrame, task_cfg: Dict[str, Any], task_label: str) -> pd.DataFrame:
    """Keep only rows whose MixNo year matches `year_filter` (Task 2).

    MixNo encodes the production year in its 2nd character, e.g.
    ``C636-501`` -> 2026, ``C201-505`` -> 2022 (see `cw.year_from_mixno`).
    Without this filter, CW01..CW52 boxplots would silently mix every year
    present in the data (e.g. C2xx..C6xx = 2022..2026) into the same CW
    slot. `year_filter`:
      - "current" (default): keep only the current calendar year.
      - an explicit int (e.g. 2026): keep only that year.
      - null/None: no filtering, keep every year (old behaviour).
    """
    year_filter = task_cfg.get("year_filter", "current")
    if year_filter is None:
        return df

    mixno_col = task_cfg.get("mixno_column", "MixNo")
    if mixno_col not in df.columns:
        print(
            f"[i] {task_label}: year_filter is set but column '{mixno_col}' "
            f"wasn't found — skipping the year filter."
        )
        return df

    target_year = _dt.date.today().year if year_filter == "current" else int(year_filter)
    years = year_from_mixno(df[mixno_col])
    before_n = len(df)
    df = df.loc[years == target_year].copy()
    print(
        f"[i] {task_label}: year_filter={year_filter!r} -> giữ dữ liệu năm "
        f"{target_year} từ MixNo: {len(df)}/{before_n} dòng."
    )
    return df


def load_task1(cfg: Dict[str, Any]) -> pd.DataFrame:
    task_cfg = cfg["task1_production_data"]
    path = Path(task_cfg["file"])
    if not path.exists():
        raise FileNotFoundError(f"Task 1 input file not found: {path}")

    df = _read_source_excel(path, task_cfg, "Task 1")
    df = _add_cw_column(df, task_cfg)
    df = _ensure_eis14(df, task_cfg["columns"], "eis1", "eis2", "eis4", "eis14")
    return df


def load_task2(cfg: Dict[str, Any]) -> pd.DataFrame:
    task_cfg = cfg["task2_mix_result"]
    path = Path(task_cfg["file"])

    if task_cfg.get("source", "excel") == "sql":
        # Lazy import: chỉ cần sqlalchemy/pyodbc khi thực sự dùng nguồn SQL.
        from . import db

        sql_cfg = task_cfg.get("sql", {}) or {}
        db_config_path = sql_cfg.get("db_config", "config/db.json")
        query_path = sql_cfg.get("query_file")  # None -> lấy theo db.json
        print(f"[Task 2] Đang query Mix Result từ SQL Server (config: {db_config_path}) ...")
        df = db.fetch_and_cache_mix_result(db_config_path, query_path, output_path=path)
    else:
        if not path.exists():
            raise FileNotFoundError(f"Task 2 input file not found: {path}")
        df = _read_source_excel(path, task_cfg, "Task 2")

    df = _add_cw_column(df, task_cfg)
    df = _filter_by_mixno_year(df, task_cfg, "Task 2")
    df = _ensure_eis14(df, task_cfg["columns"], "wtavgeis1", "wtavgeis2", "wtavgeis4", "wtavgeis14")
    return df


def load_task3(cfg: Dict[str, Any]) -> pd.DataFrame:
    task_cfg = cfg["task3_timeseries"]
    path = Path(task_cfg["file"])
    if not path.exists():
        raise FileNotFoundError(f"Task 3 input file not found: {path}")

    df = _read_source_excel(path, task_cfg, "Task 3")
    df = _add_cw_column(df, task_cfg)
    df = _prettify_raw_columns(df, task_cfg)

    date_col = task_cfg.get("date_column")
    if date_col and date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.sort_values(date_col).reset_index(drop=True)
    else:
        group_col = task_cfg.get("group_column")
        if group_col and group_col in df.columns and "CW" in df.columns:
            synth_col = "_synthetic_date"
            df[synth_col] = _synthesize_date_from_year_cw(df, group_col, "CW")
            dropped = int(df[synth_col].isna().sum())
            df = df.dropna(subset=[synth_col]).sort_values(synth_col).reset_index(drop=True)
            # Let the rest of the pipeline (pipeline.py / charts.py) treat this
            # like a real date column — no 'date_column' was set in the config.
            task_cfg["date_column"] = synth_col
            msg = (
                f"[i] Task 3: no 'date_column' configured — synthesized one "
                f"from '{group_col}' (year) + CW (ISO week) so the timeseries "
                f"chart and milestone split have a real timeline to plot "
                f"against. Set 'date_column' explicitly if the source file "
                f"has a real per-row date/timestamp column instead."
            )
            if dropped:
                msg += f" ({dropped} row(s) with an unparseable year/CW were dropped.)"
            print(msg)
        else:
            df = df.sort_values("CW").reset_index(drop=True)

    return df
