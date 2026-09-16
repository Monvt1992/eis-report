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
  Có thể đọc từ file Excel có sẵn, hoặc tự query thẳng từ SQL Server rồi cache
  ra Excel (xem mục [Lấy dữ liệu Mix_result.xlsx từ SQL
  Server](#lấy-dữ-liệu-mix_resultxlsx-trực-tiếp-từ-sql-server-tuỳ-chọn)).
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

## Lấy dữ liệu Mix_result.xlsx trực tiếp từ SQL Server (tuỳ chọn)

Task 2 có thể tự query thẳng từ SQL Server nội bộ
(`DB_DATAMART_SQL.MSE.MSE1_MixResult_Info`) thay vì phải tự export
`Mix_result.xlsx` thủ công — chạy `python main.py` là tool tự query, cache
kết quả ra `data/Mix_result.xlsx`, rồi build report luôn trong 1 lệnh.

1. Cài thêm dependency (chỉ cần trên máy có quyền truy cập SQL Server nội bộ;
   không cần nếu chỉ đọc từ file Excel có sẵn):

   ```bash
   pip install -r requirements-db.txt
   ```

   Máy cần có sẵn **ODBC Driver 17 for SQL Server** (cài ở hệ điều hành,
   không qua pip được).

2. Copy file config mẫu và điền thông tin server thật:

   ```bash
   cp config/db.example.json config/db.json
   ```

   Sửa `server`/`database` trong `config/db.json` (file này đã có trong
   `.gitignore`, sẽ không bị đẩy lên GitHub).

3. Trong `config/settings.yaml`, đặt `task2_mix_result.source: "sql"` (mặc
   định trong file settings.yaml hiện tại đã bật sẵn):

   ```yaml
   task2_mix_result:
     file: "data/Mix_result.xlsx"   # vẫn được dùng để cache kết quả query
     source: "sql"
     sql:
       db_config: "config/db.json"
   ```

4. Chạy report như bình thường — bước query SQL diễn ra tự động trước khi vẽ
   chart:

   ```bash
   python main.py --config config/settings.yaml
   ```

Muốn chỉ lấy dữ liệu mà chưa cần build report (ví dụ để xem trước file
Excel), dùng script độc lập:

```bash
python scripts/fetch_mix_result.py
```

Câu SQL trong `sql/mixresult_query.sql` hiện đang lọc cứng
`MatNo = '0320800451'` và các `MixNo` bắt đầu bằng C2–C9 — sửa trực tiếp file
này nếu cần lấy vật liệu/mix khác. Muốn quay lại đọc từ file Excel có sẵn
(không query SQL nữa), đặt `task2_mix_result.source: "excel"`.

## Cấu trúc project

```
eis-report/
├── main.py                      # entry point
├── eis_report/
│   ├── config.py                 # load + merge YAML config với default
│   ├── cw.py                     # tính CW từ MEETMOMENT hoặc MixNo
│   ├── data_loader.py            # đọc Excel/SQL, tính CW, tính Eis14 nếu thiếu
│   ├── db.py                     # query Mix Result từ SQL Server (Task 2)
│   ├── charts.py                 # vẽ boxplot + timeseries (matplotlib)
│   ├── pptx_builder.py           # ghép chart vào PPTX theo template
│   ├── pipeline.py               # điều phối Task 1/2/3
│   └── cli.py                    # xử lý --config / --demo
├── config/settings.example.yaml  # config mẫu, copy thành settings.yaml
├── config/db.example.json        # config mẫu cho SQL Server, copy thành db.json
├── sql/mixresult_query.sql       # câu query dùng cho Task 2 (source: "sql")
├── scripts/
│   ├── generate_sample_data.py
│   └── fetch_mix_result.py       # lấy dữ liệu SQL độc lập, không build report
├── sample_data/                  # dữ liệu Excel mẫu (đã có sẵn trong repo)
└── output/                       # PPTX + PNG sinh ra (không commit)
```

## Tuỳ biến thêm

- Đổi màu/kích thước chart: mục `style` trong config.
- Muốn tắt hẳn 1 task (ví dụ chưa có file Mix_result): set
  `task2_mix_result.enabled: false`.
- Đổi độ rộng cửa sổ moving average: `task3_timeseries.moving_average_window`.
- Task 2 (`task2_mix_result.year_filter`, mặc định `"current"`): MixNo (vd
  `C636-501`) chứa cả năm (ký tự 2) lẫn CW (ký tự 3-4), nên nếu không lọc,
  boxplot theo CW sẽ gộp lẫn nhiều năm vào chung 1 box. Đặt số cụ thể (vd
  `2025`) để xem 1 năm khác, hoặc `null` để tắt lọc (giữ mọi năm).
- Task 3 (`task3_timeseries.stretch_after_milestone`, mặc định `false`): khi
  bật `true`, chart tách thành 2 panel before/after CW37 và giãn rộng panel
  "after" nếu nó có ít điểm hơn hẳn — hữu ích khi cần zoom sâu vào giai đoạn
  ngay sau mốc 4M, nhưng mặc định để `false` để có 1 timeline liên tục.
- Logic tính toán nằm gọn trong `eis_report/`, dễ chỉnh nếu công thức hoặc
  cách tính CW thay đổi.

## Troubleshooting

- **`KeyError: column X not found`**: tên cột trong config không khớp với
  file Excel thật — mở file, xem tên cột chính xác, sửa lại trong
  `settings.yaml`.
- **`KeyError ... Available columns: ['Unnamed: 0', 'Unnamed: 1', ...]`**:
  toàn bộ cột hiện ra là `Unnamed: N` nghĩa là pandas không đọc đúng dòng
  tiêu đề thật (thường do file có 1 dòng title hoặc merged cell phía trên
  dòng tiêu đề thật). Từ bản này, tool sẽ tự động dò dòng tiêu đề thật dựa
  trên tên cột khai báo trong `columns`/`mixno_column`/`datetime_column` và
  in ra dòng nó tìm được (kèm gợi ý set cứng `header: <số dòng, 0-based>`
  cho task đó trong `settings.yaml` để bỏ qua việc dò mỗi lần chạy). Nếu vẫn
  báo lỗi, mở file Excel thật, đếm xem dòng tiêu đề thật là dòng số mấy
  (dòng 1 = header 0, dòng 2 = header 1, ...) rồi khai báo `header:` đó cho
  task tương ứng.
- **CW ra `NaN`/thiếu tuần**: kiểm tra định dạng `MEETMOMENT` (phải là ngày
  giờ hợp lệ) hoặc định dạng `MixNo` (ký tự 3–4 phải là số, ví dụ `C636-501`).
- **Timeseries chia sai before/after**: set rõ `milestone.year` hoặc
  `milestone.date` trong config thay vì để tool tự đoán.
