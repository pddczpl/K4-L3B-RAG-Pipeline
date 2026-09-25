# Individual contribution report

## Thông tin

- Họ và tên: Phan Danh Đạt
- Mã học viên: 2A202602627
- Nhóm: Trung thu
- Repository/branch: https://github.com/pddczpl/K4-L3B-RAG-Pipeline

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| RRF Reranking | Cài đặt thuật toán Reciprocal Rank Fusion kết hợp thứ hạng từ dense search và lexical search theo công thức chuẩn `sum(1/(k + rank))` với rank từ 1, gộp kết quả theo ID duy nhất và gắn nhãn hybrid. | `src/task7_reranking.py` | Done |
| Vectorless Fallback | Cài đặt module fallback dự phòng 2 tầng: kết nối PageIndex API khi có API key và fallback local keyword matching trên corpus standardized khi dịch vụ ngoài không khả dụng hoặc chưa có key. | `src/task8_pageindex_vectorless.py` | Done |
| Pipeline & Retrieval Integration | Hoàn thiện hàm `retrieve`: gọi song song dense & lexical search, fuse một lần bằng RRF, so sánh ngưỡng `SCORE_THRESHOLD` (0.3) với dense cosine score gốc để kích hoạt fallback an toàn không gây crash. Sửa lỗi BM25L cho corpus nhỏ. | `src/task9_retrieval_pipeline.py`, `src/task6_lexical_search.py` | Done |
| Generation & Lost-in-the-middle | Hoàn thiện reordering chunks (đưa chunk quan trọng về đầu và cuối ngữ cảnh), format context rõ nguồn [Document X], tích hợp Google GenAI SDK (Gemini) và xây dựng safe refusal. | `src/task10_generation.py` | Done |
| Chatbot UI (Streamlit) | Xây dựng giao diện hỏi đáp chuyên đề "Tuyển sinh đại học", tích hợp RAG pipeline end-to-end, hiển thị câu trả lời có citation, collapsible sources kèm score và retrieval method. | `app.py` | Done |
| Golden Dataset & Evaluation | Xây dựng 17 câu hỏi - đáp chuẩn bám sát dữ liệu thực tế đề tài tuyển sinh đại học, viết script đánh giá 4 metric (Faithfulness, Answer Relevance, Context Recall, Context Precision) và so sánh A/B. | `group_project/evaluation/golden_dataset.json`, `src/task11_evaluation.py`, `reports/RESULT.md` | Done |

## Quyết định kỹ thuật quan trọng

Mô tả tối đa hai quyết định mà bạn trực tiếp tham gia:

1. **Quyết định: Sử dụng BM25L thay cho BM25Okapi trong lexical search**  
   **Lý do/evidence:** BM25Okapi truyền thống có nhược điểm là khi corpus nhỏ (hoặc cụm từ xuất hiện trong văn bản ngắn), công thức IDF `log((N - df + 0.5)/(df + 0.5))` có thể trả về giá trị <= 0 dẫn đến toàn bộ điểm số bị triệt tiêu về 0. BM25L bổ sung thêm tham số delta (mặc định 0.5) giữ cho trọng số luôn dương, giúp contract test và việc truy vấn từ khóa ngắn, mã ngành, năm học hoạt động chính xác 100%.  
   **Trade-off:** Cần import lớp `BM25L` từ thư viện `rank_bm25` thay vì cấu hình mặc định, nhưng không tốn thêm tài nguyên tính toán.

2. **Quyết định: Reorder context (Lost-in-the-middle) trước khi đưa vào LLM Prompt**  
   **Lý do/evidence:** Các mô hình ngôn ngữ lớn (LLM) thường gặp hiện tượng "lost-in-the-middle" — dễ bỏ quên thông tin nằm ở giữa một đoạn context dài gồm nhiều chunk. Hàm `reorder_for_llm` phân tách các chunk quan trọng nhất (score cao nhất) chia đều về đầu và cuối danh sách ngữ cảnh.  
   **Trade-off:** Cần thêm một bước sắp xếp mảng nhỏ (O(K) với K=5 rất nhanh), nhưng bảo toàn đầy đủ metadata và ID của các chunk ban đầu, cải thiện độ chính xác câu trả lời và trích dẫn.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng:
  - `pytest tests/test_contracts.py -v`: Toàn bộ 15/15 tests kiểm tra public function signature, document contracts, uniqueness, sort order, fallback behavior, safe refusal đều PASSED.
  - `pytest tests/test_acceptance.py -k "test_golden_dataset_has_15_grounded_cases or test_evaluation_report_is_completed" -v`: Đã PASSED 100% cả 2 tiêu chí đánh giá cho golden dataset và báo cáo kết quả.
  - Các query kiểm thử thực tế trên UI: *"Phương thức tuyển sinh đại học năm 2024 có gì mới?"*, *"Kỳ thi Ba chung gồm những nguyên tắc gì?"*, *"Quy định điểm sàn áp dụng từ năm nào?"*.
- Kết quả trước/sau nếu có:
  - Trước: Pipeline dở dang do các file task 7, 8, 9, 10 trả về `NotImplementedError`, UI Streamlit chỉ hiển thị mock text "TODO: Integration RAG Pipeline here".
  - Sau: Pipeline chạy trơn tru từ retrieval (hybrid/pageindex) đến generation có citation trích dẫn `[Document X]`, UI phản hồi mượt mà kèm expander chi tiết nguồn trích dẫn.
- Lỗi đã phát hiện và cách xử lý:
  - Phát hiện lỗi BM25Okapi trả về mảng điểm toàn số 0 trên corpus thử nghiệm của test contract -> Đã chuyển sang `BM25L`.
  - Phát hiện relative import error khi chạy trực tiếp file python -> Thống nhất hướng dẫn chạy qua `python -m src.taskX`.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: Nguồn tài liệu legal trong `data/landing/legal` chưa được bổ sung đủ 3 file chính thức, hiện mới chỉ có 5 bài news từ Wikipedia được crawl và chunking.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: Bổ sung 3 file văn bản quy chế tuyển sinh PDF chính thức của Bộ Giáo dục & Đào tạo, đồng thời triển khai cơ chế reranking nâng cao sử dụng mô hình cross-encoder (như BGE-Reranker-large) để so sánh với RRF.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 25/09/2026
- Tên thành viên: Phan Danh Đạt
