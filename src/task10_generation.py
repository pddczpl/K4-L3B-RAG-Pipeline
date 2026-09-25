"""
Task 10 — Generation có citation.

Hướng dẫn:
    1. Retrieve top-k chunks.
    2. Reorder để giảm lost-in-the-middle.
    3. Format context kèm title và source.
    4. Gọi provider được chọn trong .env.
    5. Trả answer, sources và retrieval_source.

Nếu context không đủ hoặc provider lỗi, trả safe refusal; không bịa thông tin.
"""

import os

from dotenv import load_dotenv

from .task9_retrieval_pipeline import retrieve


load_dotenv()

TOP_K = 5
TOP_P = 0.9
TEMPERATURE = 0.3

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.5-flash-lite")

SYSTEM_PROMPT = """Bạn là trợ lý tuyển sinh đại học. Trả lời chỉ từ context được cung cấp.
Mỗi khẳng định phải có citation dạng [Document X]. Nếu thiếu evidence, hãy từ chối xác minh một cách lịch sự.
Trả lời bằng tiếng Việt."""


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Đưa chunks quan trọng về đầu và cuối context (giảm lost-in-the-middle)."""
    if len(chunks) <= 2:
        return list(chunks)
    # Front: phần tử chẵn, Back: phần tử lẻ đảo ngược
    front = chunks[::2]
    back = chunks[1::2]
    return front + back[::-1]


def format_context(chunks: list[dict]) -> str:
    """Tạo context có title và source label rõ ràng cho LLM cite."""
    parts = []
    for index, chunk in enumerate(chunks, 1):
        metadata = chunk.get("metadata", {})
        parts.append(
            f"[Document {index} | Title: {metadata.get('title', 'N/A')} | "
            f"Source: {metadata.get('source', 'N/A')}]\n{chunk.get('content', '')}"
        )
    return "\n\n---\n\n".join(parts)


def call_llm(system_prompt: str, user_message: str) -> str:
    """Gọi OpenAI, Gemini hoặc Anthropic theo cấu hình."""
    provider = os.getenv("LLM_PROVIDER", LLM_PROVIDER).lower().strip()
    model = os.getenv("LLM_MODEL", LLM_MODEL)

    if provider == "gemini":
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY")
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model or "gemini-2.0-flash",
            contents=f"{system_prompt}\n\n{user_message}",
            config=genai.types.GenerateContentConfig(
                temperature=TEMPERATURE,
                top_p=TOP_P,
            ),
        )
        return response.text.strip()

    elif provider == "openai":
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=model or "gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=TEMPERATURE,
            top_p=TOP_P,
        )
        return response.choices[0].message.content.strip()

    elif provider == "anthropic":
        from anthropic import Anthropic

        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model=model or "claude-sonnet-4-20250514",
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            temperature=TEMPERATURE,
            top_p=TOP_P,
        )
        return response.content[0].text.strip()

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """Trả về GenerationResult chuẩn contract."""
    try:
        chunks = retrieve(query, top_k=top_k)
    except Exception:
        chunks = []

    # Không có context → safe refusal
    if not chunks:
        return {
            "answer": "Tôi không thể xác minh thông tin này từ nguồn hiện có.",
            "sources": [],
            "retrieval_source": "none",
        }

    reordered = reorder_for_llm(chunks)
    context = format_context(reordered)
    user_message = f"Context:\n{context}\n\nQuestion: {query}"

    try:
        answer = call_llm(SYSTEM_PROMPT, user_message)
    except Exception as exc:
        answer = (
            f"Tôi tìm được {len(chunks)} tài liệu liên quan nhưng không thể tạo phản hồi: {exc}"
        )

    # Xác định retrieval_source theo contract
    raw_source = chunks[0].get("retrieval_method", "hybrid")
    if raw_source == "pageindex":
        retrieval_source = "pageindex"
    elif raw_source in ("dense", "bm25", "hybrid"):
        retrieval_source = "hybrid"
    else:
        retrieval_source = "none"

    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": retrieval_source,
    }


if __name__ == "__main__":
    result = generate_with_citation("Phương thức xét tuyển đại học năm 2024?")
    print("=== Answer ===")
    print(result["answer"])
    print(f"\n=== Sources ({len(result['sources'])}) ===")
    for s in result["sources"]:
        print(f"  {s['id']} | score={s['score']:.4f}")
