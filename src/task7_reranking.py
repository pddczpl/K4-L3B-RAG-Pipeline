"""
Task 7 — Reciprocal Rank Fusion.

RRF gộp nhiều bảng xếp hạng mà không cộng trực tiếp cosine score với BM25
score. Công thức: RRF(d) = sum(1 / (k + rank)), rank bắt đầu từ 1.

Lưu ý: RRF score chỉ phản ánh thứ hạng, không dùng để quyết định fallback.

-> Dùng Jina hoặc self host hoặc bất cứ công cụ nào bạn quen
"""


def rerank_rrf(
    ranked_lists: list[list[dict]],
    top_k: int = 5,
    k: int = 60,
) -> list[dict]:
    """Fuse nhiều ranked lists và trả hybrid SearchResult."""
    if top_k <= 0 or not ranked_lists:
        return []

    scores: dict[str, float] = {}
    items: dict[str, dict] = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, 1):
            item_id = item["id"]
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)
            if item_id not in items:
                items[item_id] = item

    ranked_ids = sorted(scores, key=lambda doc_id: scores[doc_id], reverse=True)

    results = []
    for item_id in ranked_ids[:top_k]:
        result = items[item_id].copy()
        result["score"] = scores[item_id]
        result["retrieval_method"] = "hybrid"
        results.append(result)

    return results


if __name__ == "__main__":
    dense = [
        {"id": "c-0", "content": "a", "score": 0.9, "metadata": {"source": "s", "title": "t", "doc_type": "news", "url": None, "chunk_index": 0}, "retrieval_method": "dense"},
        {"id": "c-1", "content": "b", "score": 0.8, "metadata": {"source": "s", "title": "t", "doc_type": "news", "url": None, "chunk_index": 1}, "retrieval_method": "dense"},
    ]
    bm25 = [
        {"id": "c-1", "content": "b", "score": 7.0, "metadata": {"source": "s", "title": "t", "doc_type": "news", "url": None, "chunk_index": 1}, "retrieval_method": "bm25"},
        {"id": "c-2", "content": "c", "score": 5.0, "metadata": {"source": "s", "title": "t", "doc_type": "news", "url": None, "chunk_index": 2}, "retrieval_method": "bm25"},
    ]
    fused = rerank_rrf([dense, bm25], top_k=3, k=60)
    for r in fused:
        print(f"  {r['id']}  score={r['score']:.6f}  method={r['retrieval_method']}")
