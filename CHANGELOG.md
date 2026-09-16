# Changelog

Định dạng dựa trên [Keep a Changelog](https://keepachangelog.com/), versioning
theo [SemVer](https://semver.org/) (MAJOR.MINOR.PATCH).

## [Unreleased]

## [0.3.0] - 2026-09-14

### Added
- Task 3: hỗ trợ file không có cột ngày thật — nếu chỉ có cột năm
  (`group_column`, dạng số hoặc `"YYYY-MM"`) cộng với CW, tool tự tổng hợp
  ngày (thứ Hai của tuần ISO đó) để vẽ timeseries và tách mốc 4M đúng theo
  từng năm.
- Task 3: tự bỏ tiền tố `Raw.` khỏi tên cột khi hiển thị trục/label chart
  (ví dụ cột thật `Raw.WtAvgEis2` → hiển thị `WtAvgEis2`) nếu không đụng tên
  cột khác.
- Mở rộng phạm vi dò dòng tiêu đề thật (tự động) từ 15 lên 40 dòng đầu file,
  vì có file thực tế header nằm tận dòng 21.
- Thêm `config/settings.task3_real_file.example.yaml`: mẫu cấu hình Task 3
  khớp đúng cấu trúc file `Wt Avg Eis 2022-2026_all type.xlsx` thật (sheet
  `Element_Mix_WtAvgEis2`, header dòng 21, không có cột ngày, cột năm là
  `Group`).

## [0.2.0] - 2026-09-14

### Added
- Hỗ trợ config `header: <0-based row index>` cho từng task, dùng khi file
  Excel có dòng title/merged-cell phía trên dòng tiêu đề thật.
- Tự động dò dòng tiêu đề thật khi không set `header` và kết quả đọc ra toàn
  cột `Unnamed: N` — in ra console dòng đã dò được.
- Thông báo lỗi `KeyError` (thiếu cột MixNo/datetime) giờ có gợi ý sửa khi
  phát hiện cột `Unnamed: N`.

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
