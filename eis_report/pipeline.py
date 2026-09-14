"""Orchestrates: load data -> draw charts -> assemble PPTX."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from . import charts, data_loader
from .pptx_builder import PptxReportBuilder

CHART_LABELS = {
    "eis1": "Eis1", "eis2": "Eis2", "eis4": "Eis4", "eis5": "Eis5", "eis14": "Eis14",
    "wtavgeis1": "WtAvgEis1", "wtavgeis2": "WtAvgEis2", "wtavgeis4": "WtAvgEis4",
    "wtavgeis5": "WtAvgEis5", "wtavgeis14": "WtAvgEis14",
}


def run(cfg: Dict[str, Any]) -> Path:
    charts_dir = Path(cfg["output"]["charts_dir"])
    charts_dir.mkdir(parents=True, exist_ok=True)

    milestone_cfg = cfg["milestone"]
    style_cfg = cfg["style"]

    builder = PptxReportBuilder(cfg["template"].get("pptx_path") or None)
    builder.add_title_slide(
        "EIS Production Report",
        f"CW{milestone_cfg.get('cw', 37)} - {milestone_cfg.get('title', '4M Implement')} split",
    )

    generated: list[Path] = []

    # ---- Task 1: production data boxplots -------------------------------
    t1cfg = cfg["task1_production_data"]
    if t1cfg.get("enabled", True):
        df1 = data_loader.load_task1(cfg)
        for key in t1cfg["charts"]:
            col = t1cfg["columns"][key]
            label = CHART_LABELS.get(key, col)
            out = charts.boxplot_by_cw(
                df1, value_col=col, cw_col="CW",
                title=f"{label} by CW (Production data)",
                milestone_cfg=milestone_cfg, style_cfg=style_cfg,
                out_path=charts_dir / f"task1_{key}_boxplot.png",
            )
            generated.append(out)
            builder.add_chart_slide(
                out, f"{label} by CW - Production data",
                milestone_title=milestone_cfg.get("title"),
                milestone_color=milestone_cfg.get("title_color", "#C00000"),
            )

    # ---- Task 2: Mix_result boxplots -------------------------------------
    t2cfg = cfg["task2_mix_result"]
    if t2cfg.get("enabled", True):
        df2 = data_loader.load_task2(cfg)
        for key in t2cfg["charts"]:
            col = t2cfg["columns"][key]
            label = CHART_LABELS.get(key, col)
            out = charts.boxplot_by_cw(
                df2, value_col=col, cw_col="CW",
                title=f"{label} by CW (Mix result)",
                milestone_cfg=milestone_cfg, style_cfg=style_cfg,
                out_path=charts_dir / f"task2_{key}_boxplot.png",
            )
            generated.append(out)
            builder.add_chart_slide(
                out, f"{label} by CW - Mix result",
                milestone_title=milestone_cfg.get("title"),
                milestone_color=milestone_cfg.get("title_color", "#C00000"),
            )

    # ---- Task 3: long-run timeseries --------------------------------------
    t3cfg = cfg["task3_timeseries"]
    if t3cfg.get("enabled", True):
        df3 = data_loader.load_task3(cfg)
        date_col = t3cfg.get("date_column")
        for key in t3cfg["charts"]:
            col = t3cfg["columns"][key]
            label = CHART_LABELS.get(key, col)
            out = charts.timeseries_with_ma(
                df3, date_col=date_col, value_col=col,
                title=f"{label} Timeseries (2022-2026)",
                milestone_cfg=milestone_cfg, style_cfg=style_cfg,
                out_path=charts_dir / f"task3_{key}_timeseries.png",
                group_col=t3cfg.get("group_column"),
                ma_window=t3cfg.get("moving_average_window", 5),
                stretch_after=t3cfg.get("stretch_after_milestone", True),
                min_after_width_ratio=t3cfg.get("min_after_width_ratio", 0.35),
            )
            generated.append(out)
            builder.add_chart_slide(
                out, f"{label} Timeseries",
                milestone_title=milestone_cfg.get("title"),
                milestone_color=milestone_cfg.get("title_color", "#C00000"),
            )

    pptx_path = builder.save(cfg["output"]["pptx_path"])
    print(f"Generated {len(generated)} chart(s).")
    print(f"PPTX report saved to: {pptx_path}")
    return pptx_path
