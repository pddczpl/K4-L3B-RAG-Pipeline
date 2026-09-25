import os
import re
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Hệ thống RAG Tuyển sinh Đại học",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Cấu hình Model & Provider hiện tại
# ---------------------------------------------------------------------------
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.5-flash-lite")

# Khởi tạo session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

# ---------------------------------------------------------------------------
# Helper: Sinh câu hỏi gợi ý tiếp theo (Follow-up prompts)
# ---------------------------------------------------------------------------
def get_followup_suggestions(query: str, answer: str) -> list[str]:
    """Sử dụng Gemini để sinh 3 câu hỏi gợi ý tiếp theo phù hợp ngữ cảnh."""
    try:
        from google import genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return _default_suggestions(query)

        client = genai.Client(api_key=api_key)
        prompt = (
            f"Dựa vào câu hỏi và câu trả lời sau đây về tuyển sinh và giáo dục đại học tại Việt Nam, "
            f"hãy gợi ý chính xác 3 câu hỏi tiếp theo ngắn gọn (mỗi câu dưới 14 từ) "
            f"mà thí sinh/phụ huynh có khả năng muốn hỏi tiếp.\n"
            f"Chỉ trả về 3 dòng, mỗi dòng bắt đầu bằng dấu gạch ngang '-', không ghi thêm lời dẫn.\n\n"
            f"Câu hỏi: {query}\n"
            f"Câu trả lời: {answer[:400]}\n"
        )
        response = client.models.generate_content(
            model=LLM_MODEL or "gemini-2.0-flash",
            contents=prompt,
        )
        lines = [
            line.strip().lstrip("-*•0123456789. ")
            for line in response.text.strip().split("\n")
            if line.strip()
        ]
        valid_suggestions = [l for l in lines if len(l) > 6][:3]
        return valid_suggestions if len(valid_suggestions) >= 2 else _default_suggestions(query)
    except Exception:
        return _default_suggestions(query)


def _default_suggestions(query: str) -> list[str]:
    """Gợi ý mặc định theo từ khóa khi API không phản hồi."""
    q_lower = query.lower()
    if "điểm sàn" in q_lower or "điểm chuẩn" in q_lower:
        return [
            "Cách tính điểm ưu tiên và cộng điểm khu vực thế nào?",
            "Điểm sàn các khối thi thời kỳ Ba chung là bao nhiêu?",
            "Lịch sử kỳ thi Ba chung gồm những khối thi nào?",
        ]
    elif "phương thức" in q_lower or "xét tuyển" in q_lower:
        return [
            "Những ai thuộc diện được tuyển thẳng vào đại học?",
            "Kỳ thi Đánh giá năng lực và Đánh giá tư duy khác gì nhau?",
            "Từ năm 2015 phương thức xét tuyển đại học thay đổi ra sao?",
        ]
    elif "trường" in q_lower or "đại học" in q_lower:
        return [
            "Sự khác biệt giữa Đại học Quốc gia và Đại học Vùng là gì?",
            "Việt Nam có bao nhiêu mô hình Đại học đa thành viên?",
            "Trường đại học công lập và tư thục khác nhau như thế nào?",
        ]
    return [
        "Các phương thức xét tuyển đại học hiện nay gồm những gì?",
        "Đối tượng nào được ưu tiên tuyển thẳng vào đại học?",
        "Học chế tín chỉ được áp dụng tại Việt Nam từ năm nào?",
    ]


# ---------------------------------------------------------------------------
# Sidebar: Thông số mô hình & Giới thiệu
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Cấu hình Hệ thống")

    st.markdown("### 🤖 Mô hình đang hoạt động")
    st.success(
        f"**💻 Embedding Model (Local):**\n`{EMBEDDING_MODEL}`\n\n"
        f"*(Chạy local qua `sentence-transformers`, vector lưu tại ChromaDB)*"
    )
    st.info(
        f"**☁️ LLM Generator (Cloud API):**\n`{LLM_PROVIDER.upper()}` — `{LLM_MODEL}`\n\n"
        f"*(Gọi Cloud API của Google Gemini kèm trích dẫn citation)*"
    )

    st.divider()

    st.markdown("### 🎛️ Tham số truy xuất (Retrieval)")
    top_k = st.slider("Số lượng Chunks ngữ cảnh (top_k)", min_value=3, max_value=10, value=5)
    st.caption("Số lượng đoạn trích liên quan nhất được chuyển cho LLM tổng hợp câu trả lời.")

    st.divider()

    st.markdown("### 📚 Dữ liệu nạp trong hệ thống")
    st.markdown(
        "- 📑 **5 văn bản chuẩn hóa** về giáo dục và tuyển sinh đại học.\n"
        "- 🧩 **2.516 chunks** đã được vector hóa và lập chỉ mục BM25.\n"
        "- 🛡️ **Chiến lược:** Hybrid Retrieval (Dense bge-m3 + BM25L + RRF k=60 + Fallback threshold 0.3)."
    )

    if st.button("🗑️ Xóa lịch sử trò chuyện", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_query = None
        st.rerun()


# ---------------------------------------------------------------------------
# Header & Phần giới thiệu (Cách thức hoạt động, Phạm vi, Cách prompt đúng)
# ---------------------------------------------------------------------------
st.title("🎓 Trợ Lý RAG Tuyển Sinh Đại Học")
st.caption("Hệ thống hỏi đáp chuyên sâu có trích dẫn nguồn dựa trên công nghệ Hybrid Retrieval-Augmented Generation")

with st.expander("📖 **HƯỚNG DẪN: Cách thức hoạt động • Phạm vi dữ liệu • Cách prompt hiệu quả**", expanded=(len(st.session_state.messages) == 0)):
    tab1, tab2, tab3 = st.tabs([
        "⚙️ Cách thức hoạt động",
        "🎯 Phạm vi kiến thức",
        "💡 Cách đặt câu hỏi (Prompt đúng)"
    ])

    with tab1:
        st.markdown("""
        ### Quy trình xử lý truy vấn 6 bước (Hybrid RAG Pipeline):
        1. **Tiếp nhận câu hỏi**: Người dùng nhập câu hỏi vào hệ thống.
        2. **Truy xuất kép (Hybrid Search)**:
           - **Dense Search (Local):** Dùng mô hình cục bộ `BAAI/bge-m3` trích xuất vector ngữ nghĩa trong ChromaDB.
           - **Lexical Search:** Dùng thuật toán `BM25L` tìm kiếm chính xác các từ khóa, số liệu, năm học, tên viết tắt.
        3. **Hợp nhất thứ hạng (RRF Fusion)**: Áp dụng công thức *Reciprocal Rank Fusion* $\\sum \\frac{1}{k + rank}$ ($k=60$) để xếp hạng lại tài liệu tối ưu nhất.
        4. **Kiểm tra độ tự tin & Fallback**: Nếu điểm cosine similarity gốc của dense search $< 0.3$, hệ thống tự động chuyển sang cơ chế fallback (PageIndex / keyword scan).
        5. **Sắp xếp chống quên (Lost-in-the-middle)**: Tái sắp xếp chunks đưa nội dung quan trọng nhất về đầu và cuối prompt.
        6. **Tạo câu trả lời có kiểm chứng**: Mô hình **Google Gemini** tổng hợp câu trả lời tiếng Việt và gắn mã trích dẫn `[Document X]` tương ứng với nguồn gốc.
        """)

    with tab2:
        col_in, col_out = st.columns(2)
        with col_in:
            st.markdown("""
            #### ✅ Có trong phạm vi hệ thống:
            - **Lịch sử & Quy chế thi**: Thời kỳ trước 2002, kỳ thi *Ba chung* (2002–2014), kỳ thi *THPT Quốc gia* (2015–2019), kỳ thi *Tốt nghiệp THPT* và các kỳ thi riêng (*Đánh giá năng lực, Đánh giá tư duy*).
            - **Khối thi & Môn thi**: Khối A, A1, B, C, D và các khối năng khiếu H, M, N, R, S, T, V.
            - **Điểm chuẩn & Điểm sàn**: Khái niệm, lịch sử điểm sàn các năm, nguyên tắc xét tuyển.
            - **Chính sách ưu tiên**: Cộng điểm khu vực, đối tượng chính sách, tiêu chí tuyển thẳng.
            - **Mô hình đại học**: 13 Đại học đa thành viên (ĐHQG, ĐH Vùng), cơ chế tự chủ, học chế tín chỉ (từ 1993), kiểm định chất lượng, học phí.
            """)
        with col_out:
            st.markdown("""
            #### ❌ Ngoài phạm vi (Hệ thống sẽ từ chối an toàn):
            - Tra cứu điểm chuẩn thời gian thực từng ngành hẹp của mùa tuyển sinh năm 2026 chưa có trong văn bản nạp.
            - Tra cứu điểm thi cá nhân của từng thí sinh cụ thể.
            - Các câu hỏi đời sống, kỹ thuật lập trình hoặc ngoài lĩnh vực giáo dục đại học.
            """)

    with tab3:
        st.markdown("""
        #### 📌 Bí quyết đặt câu hỏi để nhận câu trả lời chính xác nhất:
        - ✅ **Chỉ rõ đối tượng hoặc mốc thời gian**: Ví dụ: *"Kỳ thi Ba chung áp dụng trong giai đoạn nào và có những đợt thi gì?"* thay vì hỏi *"Lịch thi đại học"*.
        - ✅ **Hỏi về quy định, phương thức hoặc điều kiện**: Ví dụ: *"Những đối tượng nào được tuyển thẳng vào đại học theo quy định?"* hoặc *"Điểm sàn đại học được áp dụng từ năm nào?"*.
        - ✅ **So sánh hoặc phân biệt**: Ví dụ: *"Phân biệt mô hình Đại học Quốc gia và Đại học Vùng tại Việt Nam?"*.
        - ⚠️ **Tránh câu hỏi quá cộc lốc**: Những từ khóa đơn lẻ như *"điểm"*, *"học phí"*, *"trường"* sẽ khiến ngữ cảnh bị rộng và độ chính xác giảm.
        """)

st.divider()

# ---------------------------------------------------------------------------
# Starter Suggestions khi chưa có hội thoại
# ---------------------------------------------------------------------------
if len(st.session_state.messages) == 0:
    st.markdown("#### 🌟 Câu hỏi mẫu bạn có thể thử ngay:")
    sample_queries = [
        "Kỳ thi tuyển sinh đại học 'Ba chung' gồm những nguyên tắc gì và tổ chức khi nào?",
        "Từ năm 2015, phương thức tuyển sinh đại học tại Việt Nam thay đổi ra sao?",
        "Những đối tượng thí sinh nào được ưu tiên tuyển thẳng vào đại học?",
        "Quy định về điểm sàn tuyển sinh đại học được áp dụng từ năm nào?",
        "Việt Nam hiện có bao nhiêu mô hình Đại học đa thành viên và gồm những trường nào?",
        "Học chế tín chỉ được áp dụng đầu tiên tại trường đại học nào ở Việt Nam?",
    ]
    cols = st.columns(2)
    for idx, sample_q in enumerate(sample_queries):
        if cols[idx % 2].button(f"👉 {sample_q}", key=f"starter_{idx}", use_container_width=True):
            st.session_state.pending_query = sample_q
            st.rerun()


# ---------------------------------------------------------------------------
# Hiển thị lịch sử chat
# ---------------------------------------------------------------------------
for msg_idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # Hiển thị thông tin retrieval & nguồn trích dẫn
        if message["role"] == "assistant":
            if message.get("retrieval_source") and message["retrieval_source"] != "none":
                st.caption(f"🔍 **Phương thức truy xuất:** `{message['retrieval_source'].upper()}` | **Số chunks ngữ cảnh:** `{len(message.get('sources', []))}`")

            if message.get("sources"):
                with st.expander(f"📚 Xem {len(message['sources'])} đoạn trích nguồn được dùng để đối chiếu"):
                    for i, src in enumerate(message["sources"], 1):
                        meta = src.get("metadata", {})
                        st.markdown(
                            f"**[Tài liệu {i}]** `{meta.get('source', 'N/A')}` — *{meta.get('title', 'N/A')}*  \n"
                            f"📊 Điểm số: `{src.get('score', 0):.4f}` | Phương thức: `{src.get('retrieval_method', 'N/A')}`"
                        )
                        st.text(src.get("content", "").strip()[:400] + "...")
                        st.divider()

            # Hiển thị nút gợi ý follow-up prompts
            followups = message.get("followups", [])
            if followups and msg_idx == len(st.session_state.messages) - 1:
                st.markdown("**💡 Câu hỏi gợi ý tiếp theo:**")
                f_cols = st.columns(len(followups))
                for f_idx, f_query in enumerate(followups):
                    if f_cols[f_idx].button(f_query, key=f"fu_{msg_idx}_{f_idx}", use_container_width=True):
                        st.session_state.pending_query = f_query
                        st.rerun()


# ---------------------------------------------------------------------------
# Xử lý input từ chat box hoặc nút gợi ý
# ---------------------------------------------------------------------------
active_query = None
if st.session_state.pending_query:
    active_query = st.session_state.pending_query
    st.session_state.pending_query = None
else:
    chat_input_val = st.chat_input("Nhập câu hỏi về tuyển sinh đại học (hoặc bấm câu gợi ý bên trên)...")
    if chat_input_val:
        active_query = chat_input_val

if active_query:
    # 1. Thêm câu hỏi của user vào hội thoại
    st.session_state.messages.append({"role": "user", "content": active_query})
    with st.chat_message("user"):
        st.markdown(active_query)

    # 2. Xử lý câu trả lời từ RAG Pipeline
    with st.chat_message("assistant"):
        with st.spinner(f"🔍 Đang truy xuất dữ liệu & tạo phản hồi qua {LLM_PROVIDER.upper()} ({LLM_MODEL})..."):
            try:
                from src.task10_generation import generate_with_citation

                result = generate_with_citation(active_query, top_k=top_k)
                answer = result["answer"]
                sources = result["sources"]
                retrieval_source = result["retrieval_source"]
            except Exception as e:
                answer = f"⚠️ Lỗi xử lý: {e}"
                sources = []
                retrieval_source = "none"

            # 3. Sinh câu hỏi gợi ý tiếp theo
            followup_suggestions = get_followup_suggestions(active_query, answer)

        st.markdown(answer)

        if retrieval_source != "none":
            st.caption(f"🔍 **Phương thức truy xuất:** `{retrieval_source.upper()}` | **Số chunks ngữ cảnh:** `{len(sources)}`")

        if sources:
            with st.expander(f"📚 Xem {len(sources)} đoạn trích nguồn được dùng để đối chiếu"):
                for i, src in enumerate(sources, 1):
                    meta = src.get("metadata", {})
                    st.markdown(
                        f"**[Tài liệu {i}]** `{meta.get('source', 'N/A')}` — *{meta.get('title', 'N/A')}*  \n"
                        f"📊 Điểm số: `{src.get('score', 0):.4f}` | Phương thức: `{src.get('retrieval_method', 'N/A')}`"
                    )
                    st.text(src.get("content", "").strip()[:400] + "...")
                    st.divider()

        # Hiển thị ngay các nút gợi ý follow-up
        if followup_suggestions:
            st.markdown("**💡 Câu hỏi gợi ý tiếp theo:**")
            f_cols = st.columns(len(followup_suggestions))
            for f_idx, f_query in enumerate(followup_suggestions):
                if f_cols[f_idx].button(f_query, key=f"fu_new_{f_idx}", use_container_width=True):
                    st.session_state.pending_query = f_query
                    st.rerun()

    # 4. Lưu vào session state
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
        "retrieval_source": retrieval_source,
        "followups": followup_suggestions,
    })
    st.rerun()
