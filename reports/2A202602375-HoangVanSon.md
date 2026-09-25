# Individual contribution report

Mỗi thành viên copy template này thành:

```text
reports/<student-id>-<short-name>.md
```

Giới hạn khuyến nghị: 1 trang, không chép lại README hoặc mô tả lý thuyết chung. Báo cáo không phải một bài pipeline cá nhân; mục đích là ghi nhận ownership và bằng chứng đóng góp trong sản phẩm nhóm.

---

## Thông tin

- Họ và tên: Hoàng Văn Sơn
- Mã học viên:2A202602375
- Nhóm:Trung thu
- Repository/branch:2A202602375_HoangVanSon

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 1: Data collection | Viết script tự động tải các tài liệu pháp lý (PDF) từ các URL công khai và xử lý lỗi Encoding trên Windows. | `src/task1_collect_legal_docs.py` | Done |
| Task 2: Data crawling | Cấu hình logic crawl dữ liệu trang web. | `src/task2_crawl_news.py` | Done |
| Task 3: Convert Markdown | Viết hàm convert PDF sang Markdown. Tích hợp thêm module OCR bằng PyMuPDF và Tesseract để trích xuất chữ từ các file PDF bản scan. | `src/task3_convert_markdown.py` | Done |

Chỉ kê khai công việc có thể đối chiếu bằng file, commit, pull request, test hoặc kết quả evaluation.

## Quyết định kỹ thuật quan trọng

Mô tả tối đa hai quyết định mà bạn trực tiếp tham gia:

1. **Quyết định:** Tích hợp fallback OCR (`pytesseract` + `fitz`) khi convert tài liệu PDF ở Task 3.
   **Lý do/evidence:** Nhiều tài liệu pháp lý là bản scan, không có layer văn bản. Nếu chỉ dùng Markitdown thông thường sẽ trả về file rỗng. Việc thêm OCR giúp đảm bảo lấy được nội dung chữ cho pipeline RAG.
   **Trade-off:** Quá trình convert chậm hơn và tốn tài nguyên hơn (phải xử lý ảnh). Yêu cầu phải cài thêm dependencies hệ thống (Tesseract-OCR), làm môi trường cài đặt phức tạp hơn.

2. **Quyết định:** Bắt các exception an toàn và xử lý lỗi hiển thị Unicode Encode trên Windows console ở Task 1.
   **Lý do/evidence:** Terminal mặc định trên Windows dễ văng lỗi `UnicodeEncodeError` khi script in các log chứa dấu tiếng Việt, làm tiến trình bị treo.
   **Trade-off:** Log hiển thị trên console ở dạng tiếng Việt không dấu, trải nghiệm đọc kém tự nhiên hơn một chút nhưng đảm bảo tính ổn định của luồng chạy tự động.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: Chạy thực tế luồng tải 3 file PDF (luat-giao-duc, quy-che-dao-tao, nghi-dinh-81) và luồng convert PDF sang Markdown.
- Kết quả trước/sau nếu có: Task 3 ban đầu không đọc được chữ từ file PDF scan, file markdown trống. Sau khi thêm OCR, file Markdown đầu ra đã chứa đầy đủ text trích xuất được.
- Lỗi đã phát hiện và cách xử lý: Phát hiện lỗi thiếu C++ Build Tools ở Python 3.14 khi cài đặt môi trường. Đã linh hoạt bóc tách code và tự test độc lập các module không bị ảnh hưởng.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: Text xuất ra từ OCR (Tesseract) đôi khi bị sai chính tả nhẹ nếu file PDF gốc bị mờ hoặc có dấu mộc đỏ đè lên.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: Viết thêm hàm tiền xử lý ảnh (chuyển sang trắng đen, tăng độ tương phản, xóa mộc) bằng `OpenCV` hoặc `Pillow` trước khi OCR để tăng độ chính xác của text.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 25/09/2026
- Tên thành viên: Hoàng Văn Sơn
