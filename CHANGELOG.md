# Changelog

Định dạng dựa trên [Keep a Changelog](https://keepachangelog.com/), versioning
theo [SemVer](https://semver.org/) (MAJOR.MINOR.PATCH).

## [Unreleased]

## [0.1.0] - 2026-09-14

### Added
- Task 1: boxplot theo CW cho Eis2/Eis5/Eis14 từ `productiondata.xlsx`, CW tính
  từ `MEETMOMENT`. Eis14 tự tính = `Eis4 + abs(Eis1) - abs(Eis2)` nếu thiếu.
- Task 2: boxplot theo CW cho WtAvgEis2/5/14 từ `Mix_result.xlsx`, CW tính từ
  `MixNo` (ký tự thứ 3–4).
- Task 3: timeseries + moving average cho WtAvgEis2/5/14 từ
  `Wt Avg Eis 2022-2026_all type.xlsx`, milestone lấy từ cột `Group`.
- Mốc "4M Implement" tại CW37 trên mọi chart: nền xanh dương (trước) / xanh lá
  (sau), line + title màu đỏ.
- Timeseries tự tách 2 panel và giãn rộng phần "after" khi dữ liệu sau mốc quá
  thưa so với phần trước.
- Xuất PPTX theo template chuẩn, chart full khung nội dung slide.
- Config YAML (`config/settings.example.yaml`) để map tên file/cột mà không
  cần sửa code.
- Script sinh dữ liệu mẫu (`scripts/generate_sample_data.py`) + chế độ
  `--demo` để chạy thử không cần file thật.
- Unit test cho tính CW và công thức Eis14.
