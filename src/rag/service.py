from __future__ import annotations

from src.rag.retrieval.retriever import Retriever
from src.rag.relevance import RelevanceGate

class RAGService:

    def __init__(
        self,
        retriever: Retriever,
        relevance_gate: RelevanceGate,
    ) -> None:
        self.retriever = retriever
        self.relevance_gate = relevance_gate

    def generate(
        self,
        query: str,
        top_k: int = 5,
        candidate_k: int | None = None,
        agent: str | None = None,
        category: str | None = None,
    ) -> str:

        query = query.strip()

        if not query:
            return ""

        results = self.retriever.search(
            query=query,
            top_k=top_k,
            candidate_k=candidate_k,
            agent=agent,
            category=category,
        )

        results = self.relevance_gate.filter(results)

        if not results:
            return ""

        context_parts = []

        for index, item in enumerate(results, start=1):

            result = item["result"]

            content = result.payload.get(
                "content",
                "",
            ).strip()

            if not content:
                continue

            context_parts.append(
                f"[Knowledge {index}]\n{content}"
            )

        context = "\n\n".join(context_parts)

        if not context:
            return ""

        return context