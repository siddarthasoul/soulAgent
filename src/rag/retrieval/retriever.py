from __future__ import annotations

from sentence_transformers import SentenceTransformer

from src.rag.vectorstore.qdrant import search_points
from src.rag.reranking.reranker import Reranker


class Retriever:
    def __init__(
        self,
        model: SentenceTransformer,
        reranker: Reranker | None = None,
    ) -> None:
        self.model = model
        self.reranker = reranker

    def search(
        self,
        query: str,
        top_k: int = 5,
        candidate_k: int | None = None,
        agent: str | None = None,
        category: str | None = None,
    ) -> list:

        query = query.strip()

        if not query:
            return []

        if candidate_k is None:
            candidate_k = max(top_k * 4, 20)

        vector = self.model.encode(
            query,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        ).tolist()

        candidates = search_points(
            vector=vector,
            limit=candidate_k,
            agent=agent,
            category=category,
        )

        if self.reranker is None:
            return candidates[:top_k]

        return self.reranker.rerank(
            query=query,
            results=candidates,
            top_k=top_k,
        )