"""
Task 8 — PageIndex vectorless fallback.

Hướng dẫn:
    1. Đọc PAGEINDEX_API_KEY từ .env.
    2. Upload tài liệu ở định dạng PageIndex hỗ trợ.
    3. Cache document IDs để không upload lại.
    4. Parse kết quả thành SearchResult có method pageindex.

PageIndex là dịch vụ ngoài: cần timeout và xử lý lỗi để pipeline không crash.

Nếu PAGEINDEX_API_KEY rỗng, dùng fallback bằng keyword matching trên standardized
corpus để pipeline luôn hoạt động tin cậy.
"""

import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CACHE_PATH = Path(__file__).parent.parent / ".pageindex_cache.json"


def _load_standardized_docs() -> list[dict]:
    """Đọc tất cả .md trong data/standardized/ thành danh sách document."""
    docs: list[dict] = []
    for md_path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        if md_path.name.startswith("."):
            continue
        content = md_path.read_text(encoding="utf-8").strip()
        if not content:
            continue
        doc_type = "legal" if "legal" in md_path.parts else "news"
        docs.append({
            "id": md_path.relative_to(STANDARDIZED_DIR).as_posix(),
            "content": content,
            "metadata": {
                "source": md_path.name,
                "title": md_path.stem,
                "doc_type": doc_type,
                "url": None,
            },
        })
    return docs


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def upload_documents() -> None:
    """Upload tài liệu và lưu document IDs để tái sử dụng."""
    if not PAGEINDEX_API_KEY:
        return

    try:
        from pageindex import PageIndex

        client = PageIndex(api_key=PAGEINDEX_API_KEY)
        cache = _load_cache()
        docs = _load_standardized_docs()

        for doc in docs:
            source = doc["metadata"]["source"]
            if source in cache:
                continue

            md_path = STANDARDIZED_DIR / doc["id"]
            if md_path.exists():
                result = client.upload(str(md_path))
                cache[source] = result.get("document_id") or result.get("id") or source
            else:
                cache[source] = source

        _save_cache(cache)
        print(f"PageIndex: {len(cache)} documents uploaded/cached")

    except Exception as exc:
        print(f"PageIndex upload failed: {exc}")


def _simple_keyword_score(query: str, text: str) -> float:
    """Tính keyword overlap score đơn giản."""
    query_tokens = set(re.findall(r"\w+", query.lower()))
    text_tokens = re.findall(r"\w+", text.lower())
    if not query_tokens or not text_tokens:
        return 0.0
    text_token_set = set(text_tokens)
    matches = query_tokens & text_token_set
    return len(matches) / len(query_tokens) if query_tokens else 0.0


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Trả về pageindex SearchResult."""
    if top_k <= 0 or not query.strip():
        return []

    # Nhánh 1: PageIndex API
    if PAGEINDEX_API_KEY:
        try:
            from pageindex import PageIndex

            client = PageIndex(api_key=PAGEINDEX_API_KEY)
            cache = _load_cache()
            doc_ids = list(cache.values()) if cache else None

            response = client.query(query, document_ids=doc_ids, top_k=top_k)
            nodes = response.get("results") or response.get("nodes") or []

            results = []
            for rank, node in enumerate(nodes[:top_k]):
                results.append({
                    "id": node.get("id") or f"pageindex-{rank}",
                    "content": node.get("text") or node.get("content", ""),
                    "score": float(node.get("score", 1.0 / (rank + 1))),
                    "metadata": {
                        "source": node.get("source") or node.get("metadata", {}).get("source", "pageindex"),
                        "title": node.get("title") or node.get("metadata", {}).get("title", "PageIndex"),
                        "doc_type": node.get("metadata", {}).get("doc_type", "news"),
                        "url": node.get("url") or node.get("metadata", {}).get("url"),
                        "chunk_index": rank,
                    },
                    "retrieval_method": "pageindex",
                })
            return sorted(results, key=lambda x: x["score"], reverse=True)

        except Exception as exc:
            print(f"PageIndex query failed ({exc}), falling back to local search")

    # Nhánh 2: Local keyword fallback
    docs = _load_standardized_docs()
    scored: list[tuple[float, int, dict]] = []
    for idx, doc in enumerate(docs):
        score = _simple_keyword_score(query, doc["content"])
        if score > 0:
            scored.append((score, idx, doc))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for rank, (score, _, doc) in enumerate(scored[:top_k]):
        results.append({
            "id": f"pageindex-{doc['id']}",
            "content": doc["content"][:2000],
            "score": score,
            "metadata": {
                **doc["metadata"],
                "chunk_index": rank,
            },
            "retrieval_method": "pageindex",
        })

    return results


if __name__ == "__main__":
    for r in pageindex_search("phương thức xét tuyển", top_k=3):
        print(f"  {r['id']}  score={r['score']:.4f}")
