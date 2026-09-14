"""Calendar-week (CW) calculation helpers.

Two conventions are supported, matching how the source Excel files encode
the production week:

1. ``cw_from_datetime`` — derives the ISO calendar week from a real
   datetime column (used for the production-data file, based on
   ``MEETMOMENT``).

2. ``cw_from_mixno`` — parses the week directly out of a Mix/heat number
   such as ``C636-501``, where the 3rd and 4th characters ("36") give the
   CW. This is the convention used for the Mix_result and Wt-Avg-Eis files.
"""

from __future__ import annotations

import re

import pandas as pd


def cw_from_datetime(series: pd.Series) -> pd.Series:
    """Return an integer ISO week number for each timestamp in `series`."""
    dt = pd.to_datetime(series, errors="coerce")
    return dt.dt.isocalendar().week.astype("Int64")


_MIXNO_RE = re.compile(r"^.{2}(\d{2})")


def cw_from_mixno(series: pd.Series, start_index: int = 2, length: int = 2) -> pd.Series:
    """Extract the CW number from a Mix/heat number string.

    By default this reads characters 3 and 4 (0-based index 2, length 2),
    e.g. ``C636-501`` -> ``36``. `start_index`/`length` are configurable in
    case a different mix-number format is supplied.
    """

    def _parse(value: object) -> int | None:
        if pd.isna(value):
            return None
        text = str(value).strip()
        chunk = text[start_index:start_index + length]
        if not chunk.isdigit():
            return None
        return int(chunk)

    return series.map(_parse).astype("Int64")


def cw_label(cw: int) -> str:
    return f"CW{int(cw)}"
