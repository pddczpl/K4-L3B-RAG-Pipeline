# Individual contribution report

## Thông tin

- Họ và tên: Nguyễn Ngọc Linh
- Mã học viên: 2A202602480
- Nhóm: Trung thu
- Repository/branch: https://github.com/pddczpl/K4-L3B-RAG-Pipeline

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 4 - Chunking, embedding và indexing | Đọc các tài liệu Markdown trong `data/standardized/`, chia tài liệu bằng `RecursiveCharacterTextSplitter` với chunk size 500 và overlap 50, tạo embedding bằng Sentence Transformers, sau đó upsert chunks vào ChromaDB dùng cosine distance. | `src/task4_chunking_indexing.py` | Done |
| Task 5 - Semantic search | Dùng chung hàm `embed_texts()` của Task 4 để embed query, truy vấn ChromaDB, chuyển cosine distance thành similarity score, giữ metadata và trả kết quả theo contract `SearchResult`, sắp xếp score giảm dần. | `src/task5_semantic_search.py` | Done |
| Task 6 - Lexical search | Xây dựng BM25 index trên cùng corpus chunks, tính điểm BM25 cho query, lọc và sắp xếp kết quả theo score giảm dần, trả về `SearchResult` với `retrieval_method="bm25"`. | `src/task6_lexical_search.py` | Done |

## Quyết định kỹ thuật quan trọng

1. **Dùng RecursiveCharacterTextSplitter với chunk size 500 và overlap 50:**
   **Lý do/evidence:** Cách chia này giữ các đoạn văn bản ở kích thước phù hợp cho embedding và tạo overlap giữa các chunk để hạn chế mất ngữ cảnh ở ranh giới. ID chunk được tạo ổn định theo dạng `<document-id>::chunk-<index>`.
   **Trade-off:** Chunk nhỏ giúp retrieval cụ thể hơn nhưng có thể làm tăng số lượng vectors và chi phí indexing; overlap giúp giữ ngữ cảnh nhưng tạo thêm dữ liệu trùng lặp.

2. **Dùng chung embedding model cho indexing và semantic search:**
   **Lý do/evidence:** Task 4 cung cấp `embed_texts()` và Task 5 sử dụng lại hàm này cho query. ChromaDB được cấu hình với cosine distance, sau đó Task 5 chuyển distance thành similarity bằng `max(0.0, 1.0 - distance)`.
   **Trade-off:** Embedding ngữ nghĩa giúp tìm được nội dung tương đồng dù không trùng từ khóa, nhưng có thể kém hiệu quả với mã tài liệu hoặc từ khóa chính xác; đây là lý do pipeline có thêm BM25 ở Task 6.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng:
- Kết quả trước/sau nếu có:
- Lỗi đã phát hiện và cách xử lý:

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: Chưa có kết quả chạy test hoặc evaluation được ghi nhận trong báo cáo này; việc đo chất lượng retrieval trên bộ golden queries vẫn cần được bổ sung.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện:

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc được phân công và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 25/9/2026
- Tên thành viên: Nguyễn Ngọc Linh
