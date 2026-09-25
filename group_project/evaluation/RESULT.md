# RAG evaluation results

## Run information

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | 2026-09-25 |
| Framework and version              | Custom Evaluation / Ragas 0.4.3 |
| Evaluator model                    | gemini-2.0-flash |
| Generator model                    | gemini-2.0-flash |
| Embedding model                    | BAAI/bge-m3 (1024d) |
| Corpus version/commit              | Standardized News (5 documents, 2516 chunks) |
| Golden dataset size                | 17 |
| `top_k`                            | 5 |
| Fallback threshold and calibration | 0.3 (dense cosine similarity) |

## Configurations

- **Config A — dense-only:** ChromaDB vector search sử dụng cosine distance chuyển đổi sang similarity (max(0, 1 - distance)), không qua BM25 hay RRF.
- **Config B — hybrid + RRF:** Dense retrieval (ChromaDB) kết hợp BM25L lexical search, gộp kết quả bằng Reciprocal Rank Fusion (k=60), fallback sang PageIndex/keyword khi best dense score < 0.3.

Hai config phải dùng cùng golden dataset, generator, evaluator, prompt và `top_k`; chỉ thay retrieval strategy.

## Overall scores

| Metric            | Config A | Config B | Delta B−A |
| ----------------- | -------: | -------: | --------: |
| Faithfulness      |   0.8235 |   0.8941 |   +0.0706 |
| Answer relevance  |   0.8529 |   0.9176 |   +0.0647 |
| Context recall    |   0.7647 |   0.8824 |   +0.1177 |
| Context precision |   0.7843 |   0.8627 |   +0.0784 |
| **Average**       |   0.8064 |   0.8892 |   +0.0828 |

## A/B comparison

- Cấu hình tốt hơn: Config B (hybrid + RRF)
- Evidence: Config B vượt trội hơn Config A trên cả 4 metric với điểm trung bình 0.8892 so với 0.8064 (tăng +0.0828, tương đương cải thiện hơn 10%). Đặc biệt, Context Recall tăng mạnh nhất (+0.1177) do BM25 bổ trợ tốt các từ khóa chuyên ngành, năm, mốc thời gian (như 1981, 2002, 2015, Ba chung) mà dense search đơn thuần có thể bỏ sót khi embedding vector bị phân tán.
- Trade-off về latency/cost: Config B có độ trễ cao hơn Config A do phải thực thi đồng thời cả vector search và BM25 index matching, sau đó tính điểm RRF. Tuy nhiên, thời gian tăng thêm chỉ khoảng 20-30ms trên tập dữ liệu hiện tại, hoàn toàn chấp nhận được so với chất lượng thông tin truy xuất vượt trội.

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage             | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------------------- | ---------- |
|   1 | Nhà nước phân bổ chỉ tiêu tuyển sinh đại học dựa trên căn cứ gì? | Config A | 0.70 | 0.80 | 0.50 | 0.60 | retrieval | Dense search trả về các đoạn chung về ngân sách giáo dục thay vì đoạn cụ thể về việc tính toán nhu cầu địa phương |
|   2 | Tình trạng thất nghiệp của cử nhân, thạc sĩ tại Việt Nam như thế nào? | Config A | 0.75 | 0.85 | 0.60 | 0.65 | retrieval | Từ khóa số liệu thống kê (26.000 người, quý II đến IV/2015) bị phân tán giữa nhiều chunk, dense retrieval xếp các chunk tổng quan lên đầu |
|   3 | Quy chế tuyển sinh đại học do cơ quan nào ban hành? | Config B | 0.85 | 0.80 | 0.70 | 0.75 | generation | LLM tổng hợp câu trả lời đúng Bộ GD&ĐT nhưng thiếu citation chi tiết trỏ về điều khoản cụ thể trong nguồn |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | Bổ sung tối thiểu 3 văn bản pháp lý chính sách (PDF/DOCX) vào landing/legal và chuẩn hóa sang standardized/legal | Hiện tại corpus chỉ có 5 bài viết báo chí/tổng quan, thiếu các thông tư và quy chế tuyển sinh chính thức dạng điều khoản pháp luật, khiến context recall ở các câu hỏi chính sách sâu bị giới hạn | Cải thiện Context Recall lên > 0.92 và giảm thiểu safe refusal | Chạy lại test acceptance và đánh giá trên golden dataset mở rộng |
|        2 | Tinh chỉnh chunk size và overlap (thử nghiệm chunk size 700, overlap 100) | Một số câu hỏi số liệu và mốc thời gian bị cắt ngang giữa hai chunk kế tiếp | Tăng Context Precision và Faithfulness thêm ~3-5% | Đo lường lại metric trên các worst performers |
|        3 | Hiệu chỉnh threshold fallback (calibrated threshold) | Điểm cosine tương đồng của bge-m3 dao động từ 0.35-0.70 đối với query in-domain, threshold 0.3 hiện tại hiếm khi kích hoạt fallback ngoại trừ out-of-domain query | Giúp phân biệt chính xác truy vấn hợp lệ và câu hỏi ngoài phạm vi | Kiểm tra tỷ lệ kích hoạt fallback trên bộ query in/out domain (5 in-domain, 5 out-domain) |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| BM25L thay thế BM25Okapi | BM25Okapi (điểm số bị 0 do corpus nhỏ hoặc IDF bão hòa) | +100% BM25 recall trên short documents | Chi phí tính toán không đổi | BM25L có delta parameter giúp xử lý tốt các tập dữ liệu nhỏ và chunk ngắn |
| Document Reordering (Lost-in-the-middle) | Giữ nguyên thứ tự chunk xếp theo score giảm dần | Faithfulness +0.03, giảm hiện tượng hallucination ở context dài | Không tốn chi phí gọi thêm API | Đưa các chunk có độ liên quan cao nhất về hai đầu (đầu và cuối) context giúp LLM chú ý tốt hơn |
