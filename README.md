# EIS Report Generator

Công cụ Python chạy **local trên máy của bạn** để tự động tạo báo cáo PPTX
(boxplot theo CW + timeseries) từ 3 file Excel, không cần upload dữ liệu lên
đâu cả và không cần chờ approve — chỉnh file Excel/config rồi chạy lại là ra
báo cáo mới.

## Công cụ này làm gì

- **Task 1** (`productiondata.xlsx`): boxplot theo CW cho `Eis2`, `Eis5`, `Eis14`
  (Eis14 tự tính = `Eis4 + abs(Eis1) - abs(Eis2)` nếu file chưa có sẵn cột này).
  CW tính từ cột `MEETMOMENT`.
- **Task 2** (`Mix_result.xlsx`): boxplot theo CW cho `WtAvgEis2`, `WtAvgEis5`,
  `WtAvgEis14`. CW tính từ `MixNo` (ký tự thứ 3–4, ví dụ `C636-501` → CW36).
- **Task 3** (`Wt Avg Eis 2022-2026_all type.xlsx`): timeseries cho
  `WtAvgEis2`, `WtAvgEis5`, `WtAvgEis14` kèm đường moving average, các mốc
  milestone lấy từ cột `Group`.

Với mỗi chart:
- Có đường trending (mean cho boxplot, moving average cho timeseries).
- Có 1 đường mốc dọc màu đỏ "4M Implement" tại CW37, tô nền xanh dương cho
  vùng trước và xanh lá cho vùng sau.
- Title của mốc "4M Implement" được tô đỏ.
- Ở timeseries, nếu phần dữ liệu sau CW37 quá ít so với phần trước, chart tự
  tách thành 2 panel và giãn rộng panel "after" ra cho dễ nhìn (bật/tắt bằng
  config `stretch_after_milestone`).
- Toàn bộ chart được scale full khung nội dung của slide khi xuất PPTX.

## Cài đặt (một lần)

Yêu cầu Python 3.10+.

```bash
git clone <repo-url>
cd eis-report
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Chạy thử ngay với dữ liệu mẫu (không cần file thật)

```bash
python scripts/generate_sample_data.py   # sinh 3 file Excel mẫu trong sample_data/
python main.py --demo
```

Báo cáo sẽ nằm ở `output/EIS_Report.pptx`, ảnh chart từng cái ở
`output/charts/`.

## Chạy với dữ liệu thật của bạn

1. Copy file config mẫu:

   ```bash
   cp config/settings.example.yaml config/settings.yaml
   ```

2. Mở `config/settings.yaml`, sửa:
   - `task1_production_data.file`, `task2_mix_result.file`,
     `task3_timeseries.file`: đường dẫn tới 3 file Excel thật của bạn (đặt
     trong thư mục `data/` cho gọn, thư mục này đã được `.gitignore` nên
     không bị đẩy lên GitHub).
   - `columns.*`: tên cột thật trong file của bạn nếu khác với mặc định
     (`Eis1`, `Eis2`, `MEETMOMENT`, `MixNo`, `WtAvgEis2`, `Group`, ...).
   - `template.pptx_path`: đường dẫn tới file PPTX template chuẩn của công
     ty (đặt vào `assets/template.pptx` chẳng hạn). Để trống `""` nếu chưa
     có, công cụ sẽ tự tạo 1 template trắng 16:9.
   - `milestone`: CW mốc (mặc định 37), tên mốc, màu sắc. Với Task 3
     (dữ liệu nhiều năm 2022–2026), CW37 lặp lại mỗi năm nên **bạn nên khai
     báo rõ `milestone.year` hoặc `milestone.date`** để chỉ đúng thời điểm
     4M được triển khai — nếu không, công cụ sẽ tự tìm nhãn trùng tên
     milestone trong cột `Group`, và nếu vẫn không có, sẽ mặc định lấy CW37
     của năm gần nhất trong dữ liệu (có thể sai nếu 4M được áp dụng ở năm
     khác).

3. Chạy:

   ```bash
   python main.py --config config/settings.yaml
   ```

Mỗi lần có dữ liệu mới, chỉ cần thay file Excel (giữ nguyên tên cột hoặc cập
nhật lại `settings.yaml`) rồi chạy lại lệnh trên — không cần đợi ai duyệt gì
cả vì mọi thứ chạy hoàn toàn trên máy bạn.

## Cấu trúc project

```
eis-report/
├── main.py                      # entry point
├── eis_report/
│   ├── config.py                 # load + merge YAML config với default
│   ├── cw.py                     # tính CW từ MEETMOMENT hoặc MixNo
│   ├── data_loader.py            # đọc Excel, tính CW, tính Eis14 nếu thiếu
│   ├── charts.py                 # vẽ boxplot + timeseries (matplotlib)
│   ├── pptx_builder.py           # ghép chart vào PPTX theo template
│   ├── pipeline.py               # điều phối Task 1/2/3
│   └── cli.py                    # xử lý --config / --demo
├── config/settings.example.yaml  # config mẫu, copy thành settings.yaml
├── scripts/generate_sample_data.py
├── sample_data/                  # dữ liệu Excel mẫu (đã có sẵn trong repo)
└── output/                       # PPTX + PNG sinh ra (không commit)
```

## Tuỳ biến thêm

- Đổi màu/kích thước chart: mục `style` trong config.
- Muốn tắt hẳn 1 task (ví dụ chưa có file Mix_result): set
  `task2_mix_result.enabled: false`.
- Đổi độ rộng cửa sổ moving average: `task3_timeseries.moving_average_window`.
- Logic tính toán nằm gọn trong `eis_report/`, dễ chỉnh nếu công thức hoặc
  cách tính CW thay đổi.

## Troubleshooting

- **`KeyError: column X not found`**: tên cột trong config không khớp với
  file Excel thật — mở file, xem tên cột chính xác, sửa lại trong
  `settings.yaml`.
- **CW ra `NaN`/thiếu tuần**: kiểm tra định dạng `MEETMOMENT` (phải là ngày
  giờ hợp lệ) hoặc định dạng `MixNo` (ký tự 3–4 phải là số, ví dụ `C636-501`).
- **Timeseries chia sai before/after**: set rõ `milestone.year` hoặc
  `milestone.date` trong config thay vì để tool tự đoán.
