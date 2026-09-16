"""SQL Server data source for Task 2 (Mix Result).

Lấy dữ liệu Mix Result trực tiếp từ SQL Server thay vì phải tự export ra
Excel thủ công. Được gọi từ `data_loader.load_task2()` khi
`task2_mix_result.source: "sql"` trong config, và cũng có thể dùng độc lập
qua `scripts/fetch_mix_result.py` nếu chỉ muốn lấy dữ liệu mà chưa cần chạy
report.

Config DB (mặc định `config/db.json`, xem `config/db.example.json`):

    {
      "database": {
        "server": "...",
        "database": "...",
        "driver": "ODBC Driver 17 for SQL Server"
      },
      "query_file": "sql/mixresult_query.sql",
      "output_file": "data/Mix_result.xlsx"
    }

`query_file`/`output_file` trong db.json chỉ là giá trị mặc định khi dùng
`scripts/fetch_mix_result.py` độc lập — khi chạy qua pipeline chính,
`output_file` luôn bị override bằng `task2_mix_result.file` trong
settings.yaml, để settings.yaml là nguồn duy nhất quyết định file nằm ở đâu.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

# Các cột mà eis_report/data_loader.py cần để chạy Task 2 (xem
# task2_mix_result.columns trong settings.yaml). WtAvgEis14 có sẵn trong kết
# quả query (đã tính đúng công thức Eis4 + abs(Eis1) - abs(Eis2) ngay trong
# SQL) nên _ensure_eis14() ở data_loader.py sẽ tự bỏ qua bước tính lại.
REQUIRED_MIX_RESULT_COLUMNS = [
    "MixNo",
    "WtAvgEis1",
    "WtAvgEis2",
    "WtAvgEis4",
    "WtAvgEis5",
    "WtAvgEis14",
]


def load_db_config(config_path: Path) -> Dict[str, Any]:
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file config DB: {config_path}\n"
            f"-> Copy config/db.example.json thành config/db.json rồi điền "
            f"server/database thật."
        )
    with config_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_query(query_path: Path) -> str:
    query_path = Path(query_path)
    if not query_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file query: {query_path}")
    return query_path.read_text(encoding="utf-8")


def build_engine(db_cfg: Dict[str, Any]):
    # Import lazily: sqlalchemy/pyodbc chỉ cần khi thực sự dùng nguồn "sql"
    # (requirements-db.txt), không bắt cả tool phải cài khi chỉ đọc Excel.
    try:
        from sqlalchemy import create_engine, text
    except ImportError as exc:
        raise ImportError(
            "Cần cài sqlalchemy + pyodbc để dùng nguồn dữ liệu SQL "
            "(task2_mix_result.source: 'sql'): pip install -r requirements-db.txt"
        ) from exc

    server = db_cfg["server"]
    database = db_cfg["database"]
    driver = db_cfg.get("driver", "ODBC Driver 17 for SQL Server").replace(" ", "+")

    db_url = (
        f"mssql+pyodbc://@{server}/{database}"
        f"?driver={driver}&trusted_connection=yes"
    )
    engine = create_engine(db_url)

    # test connection sớm để báo lỗi rõ ràng thay vì lỗi khó hiểu lúc read_sql
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    return engine


def fetch_mix_result_df(
    config_path: Path | str = "config/db.json",
    query_path: Optional[Path | str] = None,
) -> pd.DataFrame:
    """Chạy query SQL Server và trả về DataFrame thô (chưa ghi file)."""
    config = load_db_config(Path(config_path))

    resolved_query_path = Path(query_path) if query_path else Path(
        config.get("query_file", "sql/mixresult_query.sql")
    )
    query = load_query(resolved_query_path)

    engine = build_engine(config["database"])
    df = pd.read_sql(query, engine)

    missing = [c for c in REQUIRED_MIX_RESULT_COLUMNS if c not in df.columns]
    if missing:
        raise KeyError(
            f"Kết quả query thiếu cột cần cho Task 2: {missing}. "
            f"Cột hiện có: {list(df.columns)}"
        )
    return df


def fetch_and_cache_mix_result(
    config_path: Path | str = "config/db.json",
    query_path: Optional[Path | str] = None,
    output_path: Optional[Path | str] = None,
) -> pd.DataFrame:
    """Chạy query, ghi ra `output_path` (Excel) nếu có, rồi trả về DataFrame."""
    df = fetch_mix_result_df(config_path, query_path)

    config = load_db_config(Path(config_path))
    resolved_output_path = Path(output_path) if output_path else Path(
        config.get("output_file", "data/Mix_result.xlsx")
    )
    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(resolved_output_path, index=False)
    print(f"[Task 2] Đã lấy {len(df)} dòng từ SQL Server, lưu vào: {resolved_output_path}")
    return df
