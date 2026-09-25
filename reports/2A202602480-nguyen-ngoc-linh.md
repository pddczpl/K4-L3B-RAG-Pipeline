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
  - `pytest tests/test_contracts.py -q -k "chunk_documents_preserves_identity_and_metadata or semantic_search_uses_shared_embedding_and_contract or lexical_search_returns_bm25_contract"`
  - `test_chunk_documents_preserves_identity_and_metadata`: kiểm tra chunk có ID duy nhất, giữ metadata và có `chunk_index` hợp lệ.
  - `test_semantic_search_uses_shared_embedding_and_contract`: kiểm tra semantic search sử dụng embedding chung, truy vấn collection và trả kết quả `dense` đúng contract.
  - `test_lexical_search_returns_bm25_contract`: kiểm tra BM25 trả kết quả đúng contract và xếp kết quả có liên quan lên trước.
- Kết quả trước/sau nếu có: Kết quả chạy test: `3 passed, 12 deselected in 8.40s`.
- Lỗi đã phát hiện và cách xử lý: Không phát hiện lỗi trong ba test liên quan đến Task 4, 5 và 6. Các test dùng mock cho collection/embedding hoặc corpus kiểm thử nên không yêu cầu gọi API bên ngoài.

## Điều còn hạn chế

- Hạn chế 1 - Task 4: Cấu hình chunk size 500 và overlap 50 đã chạy được trên corpus hiện tại, nhưng kết quả đánh giá mới cho thấy một số câu hỏi về số liệu hoặc mốc thời gian vẫn bị phân mảnh giữa các chunk kế tiếp. Vì vậy cần thử nghiệm thêm các cấu hình lớn hơn như chunk size 700 và overlap 100 để cải thiện Context Precision và Faithfulness.
- Hạn chế 2 - Task 5: Dense semantic search dùng BAAI/bge-m3 và ChromaDB hoạt động đúng contract, nhưng khi chạy đánh giá A/B trên 17 golden Q&A thì cấu hình dense-only chỉ đạt average 0.8064, thấp hơn hybrid + RRF là 0.8892. Điểm yếu chính là dense search có thể bỏ sót keyword chính xác, năm, mã hoặc mốc lịch sử; Context Recall của dense-only thấp hơn hybrid 0.1177.
- Hạn chế 3 - Task 6: Lexical search hiện vẫn token hóa đơn giản bằng `lower().split()` và trong file `src/task6_lexical_search.py` đang dùng `BM25Okapi`, nên còn nhạy với dấu câu, biến thể tiếng Việt và trường hợp IDF bị bão hòa trên corpus/chunk ngắn. Kết quả đánh giá nhóm cho thấy hướng tốt hơn là dùng BM25L để hỗ trợ các truy vấn từ khóa ngắn, năm học và tên riêng ổn định hơn.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: Tinh chỉnh tham số chunking của Task 4, calibrate lại dense score của Task 5 trên bộ query in-domain/out-of-domain, và nâng Task 6 từ BM25Okapi/tokenization đơn giản sang BM25L kèm tiền xử lý token tiếng Việt tốt hơn.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc được phân công và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 25/9/2026
- Tên thành viên: Nguyễn Ngọc Linh
