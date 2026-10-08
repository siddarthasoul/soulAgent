from __future__ import annotations

from sentence_transformers import CrossEncoder


class Reranker:

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        device: str = "cuda",
    ) -> None:
        self.model = CrossEncoder(
            model_name,
            device=device,
        )

    def rerank(
        self,
        query: str,
        results: list,
        top_k: int = 5,
    ) -> list:

        if not query.strip() or not results:
            return []

        pairs = [
            (
                query,
                result.payload.get("content", "")[:3000],
            )
            for result in results
        ]

        scores = self.model.predict(pairs)

        ranked = sorted(
            zip(results, scores),
            key=lambda item: float(item[1]),
            reverse=True,
        )

        final_results = []

        for result, score in ranked[:top_k]:

            final_results.append(
                {
                    "result": result,
                    "rerank_score": float(score),
                }
            )

        return final_results