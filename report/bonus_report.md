# Thử thách nâng cao Day 7 — tài liệu 100 trang

**Học viên:** Trần Anh Tú · **MSSV:** 202603368 · **Lớp:** K5-L3A

## Tài liệu, quyền và phạm vi index

- Tài liệu là *Principles of Management* của OpenStax/Rice University, bản trích **100 trang PDF liên tiếp** (trang vật lý 89–188 của sách gốc) tại [`data/advanced/source_100pages.pdf`](../data/advanced/source_100pages.pdf). SHA-256 gói PDF `f44a7503c5c14d54108aef0ed35f1db3c4b57c327b710da5d44d9216ffcead6c`. Trang `n` trong gói tương ứng trang vật lý `n+88` của PDF gốc. [Trang sách gốc](https://openstax.org/details/books/principles-management) và [ghi nhận nguồn/quyền](../data/advanced/README.md); trang online của OpenStax mô tả giấy phép CC BY-NC-SA 4.0 và bản PDF giữ dòng ghi công trên từng trang. Gói này được lấy từ một fork công khai **chỉ làm tài liệu nguồn**; benchmark, code, trace và nhãn được làm riêng cho bài này.
- [`src/bonus_index.py`](../src/bonus_index.py) trích **100/100** trang có text; index gồm nguyên văn từng trang, ID/nguồn/trang gốc, 76 nhãn Exhibit/Table, vị trí caption, locator ảnh trang và kiểm kê 33 trang có ảnh raster, 77 trang có vector drawing. Không bỏ qua trang nào. Khi truy vấn, [`src/bonus_agent.py`](../src/bonus_agent.py) tìm trang từ index, mở ảnh **trang PDF gốc** để đọc bảng, sơ đồ, biểu đồ. Năm bản trích biểu đồ tại [`visual_transcriptions.json`](../data/advanced/visual_transcriptions.json) được đối chiếu bằng mắt với ảnh gốc trước test, bao phủ dữ kiện hiển thị chứ không dùng gold câu hỏi làm prompt. Các hình khác vẫn truy cập được qua ảnh trang; việc tìm hình không có nhãn Exhibit/Table có thể kém hơn.
- Bảng PDF số hóa có thể bị xáo trộn thứ tự khi trích text; ảnh trang là nguồn cuối để xác nhận ô, trục và nhãn. Vùng PDF của bảng/hình trong gold gồm trang, số Exhibit/Table và bbox; trace cũng lưu trang đã inspect. Nội dung bên ngoài 100 trang của sách gốc không thuộc corpus bonus này.

## Benchmark tách riêng và chọn cấu hình

- [`benchmark.json`](../data/advanced/benchmark.json) đã khóa trước thử nghiệm, SHA-256 `2e8efa369fb6a79b6d27e049ffc162532adff0fe7db49f763f1ae329118a0853`. Dev có **15 câu có đáp án + 3 câu thiếu bằng chứng**; test có **24 câu có đáp án + 6 câu thiếu bằng chứng**. Test có 6 bảng, 5 ảnh/sơ đồ, 5 biểu đồ, 4 multi-hop và 4 text. Mỗi câu ở đúng một nhóm chính; gold ghi trang, vùng/ô/hàng/cột hoặc hai nguồn bắt buộc cho multi-hop; các câu thiếu bằng chứng ghi lý do kiểm trên corpus. [`validate_benchmark.py`](../data/advanced/validate_benchmark.py) kiểm số lượng, ID, hash và locator.
- Agent chỉ nhận **câu hỏi**, không nhận `expected_answer`, nhãn `answerable`, gold hoặc vùng evidence chuẩn. Model thật `gpt-5.4-mini` viết truy vấn tìm kiếm; tool TF-IDF tìm toàn bộ 100 trang, định tuyến theo nhãn Exhibit/Table *có trong câu hỏi* rồi mở ảnh gốc của trang được chọn. Tối đa 3 trang; nếu câu có 2 nhãn thì chỉ dùng 2 trang đó. Bộ kiểm tra tên hàng và sửa citation thiếu nguồn dùng index/ảnh trang, không đọc gold. Chạy 18 dev để chọn, sau đó khóa [`selected_config.json`](bonus/selected_config.json) ở commit `75dca23` **trước** khi chạy test. File này giữ hash benchmark, PDF, index, bản trích hình, mã agent và runner; runner test xác nhận lại các hash. Không chỉnh cấu hình sau khi xem test.

| Cấu hình thử trên dev | Thay đổi | Strict pass đã đọc /18 | Lỗi tiêu biểu |
| --- | --- | ---: | --- |
| Text baseline | TF-IDF + text PDF, không vision/anchor | 10/18 | Sai Hong Kong trong chart, bịa số Clan và thiếu citation multi-hop. |
| Vision | Mở ảnh 3 trang retrieval | 12/18 | Đọc đúng Hong Kong nhưng còn bỏ sót trang Table 6.1 và chart 6.8. |
| Vision + anchor v1 | Định tuyến Exhibit/Table có trong câu hỏi | 15/18 | Trả lời đúng hơn, nhưng một số multi-hop chỉ dẫn một nguồn. |
| Vision + anchor v2 | Nhắc đủ nguồn và chuẩn hóa lời từ chối | 16/18 | Còn thiếu citation ở `ad11`, `ad12`. |
| Vision + xác minh mọi câu | Model kiểm lại toàn bộ đáp án | 14/18 | Hồi quy: đổi `ad11` thành functional và bịa số FDI 2020. Không chọn. |
| Anchor + sửa citation, trước ghi chú chart | Chỉ sửa khi thiếu nhãn; kiểm hàng bảng | 17/18 | `ad09` đọc nhầm thanh Cost reduction 3,9 thành 4,0. |
| **Đã chọn** | Anchor + sửa citation có điều kiện + 5 ghi chú chart đối chiếu nguồn | **18/18** | Không lỗi trong một lượt dev này. |

Các con số dev là **nhãn Codex hỗ trợ đối chiếu nguồn**, xem từng [`reviews.json`](bonus/dev/selected/reviews.json) và traces dưới `report/bonus/dev/`. Cấu hình sau cùng giữ đúng 100 trang index, thêm ghi chú biểu đồ được đọc từ hình gốc, không chọn cấu hình bằng test. Một lượt dev đạt 18/18 không chứng minh tính ổn định trên câu hỏi khác.

## Kết quả test khóa

Chạy đúng **30/30** câu test một lượt với cấu hình đã khóa. Lỗi hệ thống/timeout = **0**. Tổng 60 lần gọi tool tìm trang, 41 lần mở ảnh gốc và 61 lượt model; tổng thời gian **87,95 giây** (trung bình **2,93 giây/câu**), ước tính API **$0.126198** từ token usage; chưa tính CPU và lưu trữ. Trace có câu hỏi, kế hoạch search, trang/điểm, context, ảnh được inspect (locator), câu trả lời, citation, token, thời gian, chi phí và lỗi.

| Nhóm test | Đạt / tổng | Tỷ lệ |
| --- | ---: | ---: |
| Bảng | 6/6 | 100% |
| Ảnh/sơ đồ | 5/5 | 100% |
| Biểu đồ | 5/5 | 100% |
| Multi-hop | 4/4 | 100% |
| Text | 4/4 | 100% |
| Thiếu bằng chứng | 3/6 | 50% |
| **Tổng** | **27/30** | **90%** |

**Ba lỗi được giữ nguyên:** `at-u3` trả lời một sự thật liên quan (Unions là một node) nhưng không từ chối câu hỏi *bao nhiêu thành viên*; `at-u4` đưa 24,1% từ hình tôn giáo cũ cho câu hỏi **năm 2024**, dù hình không có số 2024; `at-u6` đưa 4,0 từ Exhibit 6.8 cho câu hỏi **năm 2025**, dù hình không báo số 2025. Cả ba đều không đạt. Ví dụ trả lời có nguồn: `at20` dùng Table 6.10 p.95 và Table 6.11 p.100 để nối hai ý; ví dụ từ chối: `at-u1` kiểm Table 6.1 p.71 không có hàng Viet Nam rồi nói không đủ bằng chứng.

**Điều kiện ngưỡng:** 27/30 = 90% đúng bằng mức tối thiểu trong [`ADVANCED.md`](https://github.com/VinUni-AI20k/K5-L3-Day07-Retrieval-Context-Engineering/blob/main/ADVANCED.md); không loại 3 lỗi khỏi mẫu số, không làm tròn. Đây là kết quả từ **Codex assistant-reviewed labels**; giảng viên có thể kiểm lại và điểm bonus chính thức phụ thuộc đánh giá của họ. Tập test do cùng quy trình hỗ trợ tạo/đối chiếu nên không phải đánh giá độc lập bên ngoài.

## Nhãn từng câu và tái lập

[`report/bonus/test/traces.json`](bonus/test/traces.json), [`reviews.json`](bonus/test/reviews.json) và [`metrics.json`](bonus/test/metrics.json) chứa hiện vật máy đọc được. Mỗi hàng dưới đây trỏ tới một review đầy đủ với lý do và vùng gold. `PASS` yêu cầu đáp án đúng đủ **và** citation trang/vùng hỗ trợ; câu thiếu bằng chứng cần từ chối rõ ràng.

| ID | Nhóm | Kết quả | Trang được dẫn | Ghi chú |
| --- | --- | --- | --- | --- |
| `at01` | table | PASS | 71 | Đáp án và vùng nguồn khớp PDF. |
| `at02` | table | PASS | 72 | Đáp án và vùng nguồn khớp PDF. |
| `at03` | table | PASS | 74 | Đáp án và vùng nguồn khớp PDF. |
| `at04` | table | PASS | 76 | Đáp án và vùng nguồn khớp PDF. |
| `at05` | table | PASS | 79 | Đáp án và vùng nguồn khớp PDF. |
| `at06` | table | PASS | 95 | Đáp án và vùng nguồn khớp PDF. |
| `at07` | image | PASS | 4 | Đáp án và vùng nguồn khớp PDF. |
| `at08` | image | PASS | 15 | Đáp án và vùng nguồn khớp PDF. |
| `at09` | image | PASS | 19 | Đáp án và vùng nguồn khớp PDF. |
| `at10` | image | PASS | 24 | Đáp án và vùng nguồn khớp PDF. |
| `at11` | image | PASS | 53 | Đáp án và vùng nguồn khớp PDF. |
| `at12` | chart | PASS | 68 | Đáp án và vùng nguồn khớp PDF. |
| `at13` | chart | PASS | 69 | Đáp án và vùng nguồn khớp PDF. |
| `at14` | chart | PASS | 84 | Đáp án và vùng nguồn khớp PDF. |
| `at15` | chart | PASS | 85 | Đáp án và vùng nguồn khớp PDF. |
| `at16` | chart | PASS | 97 | Đáp án và vùng nguồn khớp PDF. |
| `at17` | multi_hop | PASS | 8, 10 | Đáp án và vùng nguồn khớp PDF. |
| `at18` | multi_hop | PASS | 71, 72 | Đáp án và vùng nguồn khớp PDF. |
| `at19` | multi_hop | PASS | 68, 69 | Đáp án và vùng nguồn khớp PDF. |
| `at20` | multi_hop | PASS | 95, 100 | Đáp án và vùng nguồn khớp PDF. |
| `at21` | text | PASS | 45 | Đáp án và vùng nguồn khớp PDF. |
| `at22` | text | PASS | 92 | Đáp án và vùng nguồn khớp PDF. |
| `at23` | text | PASS | 94 | Đáp án và vùng nguồn khớp PDF. |
| `at24` | text | PASS | 95 | Đáp án và vùng nguồn khớp PDF. |
| `at-u1` | unanswerable | PASS | — | Từ chối: Table 6.1 không có hàng Viet Nam. |
| `at-u2` | unanswerable | PASS | — | Từ chối: Exhibit 4.2 không có số liệu tổ chức theo năm 2023. |
| `at-u3` | unanswerable | FAIL | 53 | Chỉ nói Unions là một node, không từ chối câu hỏi về số thành viên. |
| `at-u4` | unanswerable | FAIL | 85 | Lấy 24,1% từ hình không có mốc năm 2024. |
| `at-u5` | unanswerable | PASS | — | Từ chối: Table 6.11 không cho cỡ mẫu của hàng được hỏi. |
| `at-u6` | unanswerable | FAIL | 97 | Lấy điểm 4,0 từ hình không có mốc năm 2025. |

Lệnh chạy từ gốc repo (sau khi cài `requirements.txt` và đặt `OPENAI_API_KEY` trên máy):

```powershell
.\.venv\Scripts\python.exe -m src.bonus_index
.\.venv\Scripts\python.exe data\advanced\validate_benchmark.py
.\.venv\Scripts\python.exe -m src.run_bonus --split dev --mode vision_anchor_repair --output starter\results\bonus_dev_replay
.\.venv\Scripts\python.exe -m src.run_bonus --split test --mode vision_anchor_repair --output starter\results\bonus_test_replay
```

Rerun với model thật có thể khác kết quả và phát sinh phí API. Kết quả đã nộp là bản trace/nhãn cố định ở `report/bonus/test/`; mọi thử nghiệm tiếp theo phải dùng bộ test mới nếu muốn chỉnh cấu hình.
