#!/usr/bin/env python3
"""Standalone CLI: lấy dữ liệu Mix Result từ SQL Server và lưu ra
`data/Mix_result.xlsx`, KHÔNG chạy report.

Dùng khi bạn chỉ muốn refresh file Excel để tự kiểm tra dữ liệu, xem trước,
hoặc dùng ở chỗ khác. Để chạy full report (query SQL + build PPTX) trong một
lệnh, dùng `python main.py --config config/settings.yaml` với
`task2_mix_result.source: "sql"` trong settings.yaml — main.py sẽ tự gọi lại
đúng logic trong `eis_report/db.py` mà script này cũng dùng.

Cách chạy (từ thư mục gốc repo, đã activate conda env "eis-report"):

    python scripts/fetch_mix_result.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Cho phép chạy trực tiếp `python scripts/fetch_mix_result.py` mà không cần
# `pip install -e .` — thêm thư mục gốc repo vào sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eis_report import db  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lấy dữ liệu Mix Result từ SQL Server và lưu ra Excel cho eis-report Task 2."
    )
    parser.add_argument("--config", default="config/db.json", help="Đường dẫn file config DB (mặc định config/db.json)")
    parser.add_argument("--query", default=None, help="Đường dẫn file .sql (mặc định lấy theo config/db.json)")
    parser.add_argument("--output", default=None, help="Đường dẫn file Excel output (mặc định lấy theo config/db.json)")
    args = parser.parse_args()

    try:
        db.fetch_and_cache_mix_result(args.config, args.query, args.output)
    except Exception as e:  # noqa: BLE001 - in lỗi rõ ràng cho người dùng cuối
        print(f"✗ Lỗi: {e}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
