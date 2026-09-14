"""Matplotlib chart builders: CW boxplots and Eis timeseries."""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.gridspec import GridSpec  # noqa: E402

from .cw import cw_label


def _apply_style(style_cfg: Dict[str, Any]) -> None:
    import logging

    logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
    # Fall back gracefully if the requested font (e.g. Calibri, common on
    # Windows) isn't installed on this machine.
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = [
        style_cfg.get("font_family", "Calibri"), "DejaVu Sans", "Arial", "Helvetica",
    ]
    plt.rcParams["axes.titlesize"] = 16
    plt.rcParams["axes.labelsize"] = 12
    plt.rcParams["figure.dpi"] = style_cfg.get("dpi", 200)


def _milestone_split_date(
    dates: pd.Series,
    milestone_cfg: Dict[str, Any],
    group_milestones: Optional[Dict[Any, pd.Timestamp]] = None,
) -> Optional[pd.Timestamp]:
    """Resolve the actual calendar date that CW37 corresponds to for a
    (possibly multi-year) timeseries.

    Priority:
      1. explicit `milestone.date` in config
      2. explicit `milestone.year` (+ CW) in config
      3. a label in `group_milestones` (from the Group column) whose text
         matches the milestone title (e.g. "4M Implement") - this is the
         most reliable source since it's tied to the actual event, not just
         a recurring week number
      4. fallback: CW37 of the most recent year present in the data (a
         guess - configure `milestone.year` or `.date` for accuracy)
    """
    explicit_date = milestone_cfg.get("date")
    if explicit_date:
        return pd.Timestamp(explicit_date)

    cw = int(milestone_cfg.get("cw", 37))
    year = milestone_cfg.get("year")

    if year is None and group_milestones:
        title = str(milestone_cfg.get("title", "")).strip().lower()
        for label, d in group_milestones.items():
            if title and title in str(label).strip().lower():
                return pd.Timestamp(d)

    valid_dates = pd.to_datetime(dates, errors="coerce").dropna()
    if valid_dates.empty:
        return None

    if year is None:
        year = int(valid_dates.dt.year.max())

    monday = _dt.date.fromisocalendar(int(year), cw, 1)
    return pd.Timestamp(monday)


def boxplot_by_cw(
    df: pd.DataFrame,
    value_col: str,
    cw_col: str,
    title: str,
    milestone_cfg: Dict[str, Any],
    style_cfg: Dict[str, Any],
    out_path: str | Path,
) -> Path:
    """Boxplot of `value_col` grouped by CW, with a mean-trend line and a
    before/after 4M-implementation split at `milestone_cfg['cw']`.
    """
    _apply_style(style_cfg)

    data = df[[cw_col, value_col]].dropna()
    cws: List[int] = sorted(data[cw_col].unique().tolist())
    groups = [data.loc[data[cw_col] == cw, value_col].values for cw in cws]
    positions = np.arange(1, len(cws) + 1)

    fig, ax = plt.subplots(
        figsize=(style_cfg.get("figure_width_in", 12.0), style_cfg.get("figure_height_in", 6.0))
    )

    milestone_cw = int(milestone_cfg.get("cw", 37))
    # Position of the split: midpoint between the last "before" CW and the
    # first "after" CW (>= milestone_cw counts as "after", matching the
    # "before CW37 / after CW37+" framing in the brief).
    before_idx = [i for i, cw in enumerate(cws) if cw < milestone_cw]
    split_x = (max(before_idx) + 1.5) if before_idx else 0.5

    ax.axvspan(0.5, split_x, color=milestone_cfg.get("before_color", "#DCE9F7"), zorder=0)
    ax.axvspan(
        split_x, len(cws) + 0.5, color=milestone_cfg.get("after_color", "#DFF3E1"), zorder=0
    )

    bp = ax.boxplot(
        groups,
        positions=positions,
        widths=0.6,
        patch_artist=True,
        showmeans=False,
        boxprops=dict(facecolor=style_cfg.get("box_color", "#4472C4"), alpha=0.75),
        medianprops=dict(color="black", linewidth=1.5),
        flierprops=dict(marker="o", markersize=3, alpha=0.5),
        zorder=3,
    )

    # Trend line across the mean of each CW group.
    means = [np.nanmean(g) if len(g) else np.nan for g in groups]
    ax.plot(
        positions,
        means,
        color=style_cfg.get("trend_color", "#ED7D31"),
        marker="o",
        markersize=4,
        linewidth=2,
        label="Trend (mean)",
        zorder=4,
    )

    # Milestone vertical line + red title.
    ax.axvline(split_x, color=milestone_cfg.get("line_color", "#C00000"), linewidth=2, linestyle="--", zorder=5)
    ax.text(
        split_x,
        ax.get_ylim()[1],
        f"  {milestone_cfg.get('title', '4M Implement')} (CW{milestone_cw})",
        color=milestone_cfg.get("title_color", "#C00000"),
        fontweight="bold",
        va="bottom",
        ha="left",
        rotation=0,
        fontsize=11,
    )

    ax.set_xticks(positions)
    ax.set_xticklabels([cw_label(cw) for cw in cws], rotation=45, ha="right")
    ax.set_xlim(0.5, len(cws) + 0.5)
    ax.set_ylabel(value_col)
    ax.set_title(title, fontweight="bold")
    ax.legend(loc="upper left")
    ax.grid(axis="y", linestyle=":", alpha=0.5, zorder=1)

    fig.tight_layout()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=style_cfg.get("dpi", 200))
    plt.close(fig)
    return out_path


def _first_occurrence_labels(dates: pd.Series, labels: pd.Series) -> Dict[Any, pd.Timestamp]:
    """First date at which each distinct (non-null) label value appears."""
    out: Dict[Any, pd.Timestamp] = {}
    for d, lab in zip(dates, labels):
        if pd.isna(lab) or pd.isna(d):
            continue
        if lab not in out:
            out[lab] = d
    return out


def timeseries_with_ma(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
    title: str,
    milestone_cfg: Dict[str, Any],
    style_cfg: Dict[str, Any],
    out_path: str | Path,
    group_col: Optional[str] = None,
    ma_window: int = 5,
    stretch_after: bool = True,
    min_after_width_ratio: float = 0.35,
) -> Path:
    """Timeseries line chart with moving average, a before/after CW37 split
    (shaded blue/green, red milestone line+label) and optional extra
    milestones taken from `group_col` values.
    """
    _apply_style(style_cfg)

    data = df[[date_col, value_col] + ([group_col] if group_col else [])].copy()
    data[date_col] = pd.to_datetime(data[date_col], errors="coerce")
    data = data.dropna(subset=[date_col, value_col]).sort_values(date_col).reset_index(drop=True)

    data["_ma"] = data[value_col].rolling(window=ma_window, min_periods=1).mean()

    extra_milestones = (
        _first_occurrence_labels(data[date_col], data[group_col]) if group_col else {}
    )

    split_date = _milestone_split_date(data[date_col], milestone_cfg, extra_milestones)
    before = data[data[date_col] < split_date] if split_date is not None else data
    after = data[data[date_col] >= split_date] if split_date is not None else data.iloc[0:0]

    # Don't double-draw the 4M-implement milestone: it already gets the red
    # split line + title, so drop it from the plain grey Group annotations.
    _milestone_title_lower = str(milestone_cfg.get("title", "")).strip().lower()
    extra_milestones = {
        lab: d for lab, d in extra_milestones.items()
        if not (_milestone_title_lower and _milestone_title_lower in str(lab).strip().lower())
    }

    fig = plt.figure(
        figsize=(style_cfg.get("figure_width_in", 12.0), style_cfg.get("figure_height_in", 6.0))
    )

    use_split_panels = stretch_after and split_date is not None and not before.empty and not after.empty

    if use_split_panels:
        n_before, n_after = len(before), len(after)
        raw_ratio_after = n_after / max(n_before + n_after, 1)
        width_after = max(raw_ratio_after, min_after_width_ratio)
        width_before = 1 - width_after
        gs = GridSpec(1, 2, width_ratios=[width_before, width_after], wspace=0.04)
        ax_before = fig.add_subplot(gs[0, 0])
        ax_after = fig.add_subplot(gs[0, 1], sharey=ax_before)

        ax_before.set_facecolor(milestone_cfg.get("before_color", "#DCE9F7"))
        ax_after.set_facecolor(milestone_cfg.get("after_color", "#DFF3E1"))

        for ax, seg in ((ax_before, before), (ax_after, after)):
            ax.plot(seg[date_col], seg[value_col], color=style_cfg.get("box_color", "#4472C4"),
                     linewidth=1.2, marker="o", markersize=2.5, alpha=0.85, label=value_col)
            ax.plot(seg[date_col], seg["_ma"], color=style_cfg.get("ma_color", "#ED7D31"),
                     linewidth=2.2, label=f"Moving avg ({ma_window})")
            ax.grid(axis="y", linestyle=":", alpha=0.5)
            ax.tick_params(axis="x", rotation=45)
            for lab, d in extra_milestones.items():
                if seg[date_col].min() <= d <= seg[date_col].max():
                    ax.axvline(d, color="#666666", linestyle=":", linewidth=1)
                    ax.text(d, ax.get_ylim()[1], f" {lab}", rotation=90, va="top", ha="right",
                            fontsize=8, color="#444444")

        ax_after.tick_params(axis="y", labelleft=False)
        ax_before.set_ylabel(value_col)
        ax_before.legend(loc="upper left", fontsize=9)

        # Milestone marker drawn at the seam between the two panels.
        ax_before.axvline(before[date_col].max(), color=milestone_cfg.get("line_color", "#C00000"),
                           linewidth=2, linestyle="--")
        ax_after.axvline(after[date_col].min(), color=milestone_cfg.get("line_color", "#C00000"),
                          linewidth=2, linestyle="--")
        fig.text(
            width_before, 0.96,
            f"{milestone_cfg.get('title', '4M Implement')} (CW{int(milestone_cfg.get('cw', 37))})",
            color=milestone_cfg.get("title_color", "#C00000"),
            fontweight="bold", fontsize=11, ha="center", va="top",
        )
        fig.suptitle(title, fontweight="bold", y=1.02)

    else:
        ax = fig.add_subplot(111)
        if split_date is not None:
            ax.axvspan(data[date_col].min(), split_date, color=milestone_cfg.get("before_color", "#DCE9F7"), zorder=0)
            ax.axvspan(split_date, data[date_col].max(), color=milestone_cfg.get("after_color", "#DFF3E1"), zorder=0)
            ax.axvline(split_date, color=milestone_cfg.get("line_color", "#C00000"), linewidth=2, linestyle="--", zorder=5)
            ax.text(split_date, ax.get_ylim()[1],
                    f"  {milestone_cfg.get('title', '4M Implement')} (CW{int(milestone_cfg.get('cw', 37))})",
                    color=milestone_cfg.get("title_color", "#C00000"), fontweight="bold",
                    va="bottom", ha="left", fontsize=11)

        ax.plot(data[date_col], data[value_col], color=style_cfg.get("box_color", "#4472C4"),
                linewidth=1.2, marker="o", markersize=2.5, alpha=0.85, label=value_col, zorder=3)
        ax.plot(data[date_col], data["_ma"], color=style_cfg.get("ma_color", "#ED7D31"),
                linewidth=2.2, label=f"Moving avg ({ma_window})", zorder=4)

        for lab, d in extra_milestones.items():
            ax.axvline(d, color="#666666", linestyle=":", linewidth=1, zorder=2)
            ax.text(d, ax.get_ylim()[1], f" {lab}", rotation=90, va="top", ha="right",
                    fontsize=8, color="#444444")

        ax.set_ylabel(value_col)
        ax.grid(axis="y", linestyle=":", alpha=0.5)
        ax.tick_params(axis="x", rotation=45)
        ax.legend(loc="upper left", fontsize=9)
        ax.set_title(title, fontweight="bold")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=style_cfg.get("dpi", 200), bbox_inches="tight")
    plt.close(fig)
    return out_path
