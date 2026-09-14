#!/usr/bin/env python3
"""Generate synthetic sample Excel files matching the expected schemas, so
`python main.py --demo` produces a full report without needing the real
production data. Run from the project root:

    python scripts/generate_sample_data.py
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
OUT_DIR = Path(__file__).resolve().parent.parent / "sample_data"


def _shift_after_cw(values: np.ndarray, cws: np.ndarray, split_cw: int, shift: float, noise_scale: float) -> np.ndarray:
    out = values.copy()
    mask = cws >= split_cw
    out[mask] = out[mask] + shift
    out = out + RNG.normal(0, noise_scale, size=out.shape)
    return out


def make_production_data(n_per_week: int = 25, weeks: range = range(25, 45)) -> pd.DataFrame:
    rows = []
    year = 2026
    for week in weeks:
        # Monday of that ISO week, plus random time-of-day across the week.
        monday = dt.date.fromisocalendar(year, week, 1)
        for _ in range(n_per_week):
            offset = dt.timedelta(days=float(RNG.uniform(0, 6.9)))
            meetmoment = dt.datetime.combine(monday, dt.time(0, 0)) + offset
            rows.append({"MEETMOMENT": meetmoment, "week": week})
    df = pd.DataFrame(rows)
    cws = df["week"].values

    eis1 = RNG.normal(0.15, 0.05, size=len(df))
    eis2 = _shift_after_cw(RNG.normal(1.2, 0.25, size=len(df)), cws, 37, -0.35, 0.05)
    eis4 = RNG.normal(0.9, 0.2, size=len(df))
    eis5 = _shift_after_cw(RNG.normal(2.0, 0.4, size=len(df)), cws, 37, -0.5, 0.08)

    df["Eis1"] = eis1
    df["Eis2"] = eis2
    df["Eis4"] = eis4
    df["Eis5"] = eis5
    # Eis14 left OUT on purpose so the tool demonstrates computing it:
    # Eis14 = Eis4 + abs(Eis1) - abs(Eis2)
    df = df.drop(columns=["week"])
    return df


def make_mix_result(n_per_week: int = 8, weeks: range = range(25, 45)) -> pd.DataFrame:
    rows = []
    counter = 500
    for week in weeks:
        for _ in range(n_per_week):
            counter += 1
            mixno = f"C6{week:02d}-{counter}"
            rows.append({"MixNo": mixno, "week": week})
    df = pd.DataFrame(rows)
    cws = df["week"].values

    wtavgeis1 = RNG.normal(0.15, 0.04, size=len(df))
    wtavgeis2 = _shift_after_cw(RNG.normal(1.15, 0.2, size=len(df)), cws, 37, -0.3, 0.05)
    wtavgeis4 = RNG.normal(0.85, 0.18, size=len(df))
    wtavgeis5 = _shift_after_cw(RNG.normal(1.9, 0.35, size=len(df)), cws, 37, -0.45, 0.07)

    df["WtAvgEis1"] = wtavgeis1
    df["WtAvgEis2"] = wtavgeis2
    df["WtAvgEis4"] = wtavgeis4
    df["WtAvgEis5"] = wtavgeis5
    df = df.drop(columns=["week"])
    return df


def make_timeseries(start_year: int = 2022, end_year: int = 2026) -> pd.DataFrame:
    rows = []
    counter = 100
    groups = {
        (2022, 10): "Line upgrade",
        (2023, 20): "New supplier",
        (2024, 15): "Process change",
        (2025, 37): "4M Implement",
        (2026, 5): "Post-audit review",
    }
    for year in range(start_year, end_year + 1):
        max_week = 37 if year == end_year else 52
        for week in range(1, max_week + 1):
            n = RNG.integers(2, 6)
            for _ in range(n):
                counter += 1
                monday = dt.date.fromisocalendar(year, week, 1)
                date = monday + dt.timedelta(days=int(RNG.integers(0, 5)))
                mixno = f"C{str(year)[-1]}{week:02d}-{counter}"
                rows.append({"Date": date, "MixNo": mixno, "year": year, "week": week})

    df = pd.DataFrame(rows).sort_values("Date").reset_index(drop=True)
    absolute_week = (df["year"] - start_year) * 52 + df["week"]
    split_week = (2025 - start_year) * 52 + 37
    is_after = (absolute_week >= split_week).values

    base2 = RNG.normal(1.1, 0.2, size=len(df))
    base5 = RNG.normal(1.9, 0.3, size=len(df))
    base2[is_after] -= 0.3
    base5[is_after] -= 0.4
    base2 += RNG.normal(0, 0.04, size=len(df))
    base5 += RNG.normal(0, 0.06, size=len(df))

    base14 = RNG.normal(0.6, 0.15, size=len(df))
    base14[is_after] -= 0.2
    base14 += RNG.normal(0, 0.03, size=len(df))

    df["WtAvgEis2"] = base2
    df["WtAvgEis5"] = base5
    df["WtAvgEis14"] = base14

    df["Group"] = df.apply(
        lambda r: groups.get((int(r["year"]), int(r["week"])), np.nan), axis=1
    )

    df = df.drop(columns=["year", "week"])
    return df


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    prod = make_production_data()
    prod.to_excel(OUT_DIR / "productiondata.xlsx", index=False)
    print(f"Wrote {OUT_DIR / 'productiondata.xlsx'} ({len(prod)} rows)")

    mix = make_mix_result()
    mix.to_excel(OUT_DIR / "Mix_result.xlsx", index=False)
    print(f"Wrote {OUT_DIR / 'Mix_result.xlsx'} ({len(mix)} rows)")

    ts = make_timeseries()
    ts.to_excel(OUT_DIR / "Wt Avg Eis 2022-2026_all type.xlsx", index=False)
    print(f"Wrote {OUT_DIR / 'Wt Avg Eis 2022-2026_all type.xlsx'} ({len(ts)} rows)")


if __name__ == "__main__":
    main()
