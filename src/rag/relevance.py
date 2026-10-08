from __future__ import annotations


class RelevanceGate:
    def __init__(
        self,
        min_score: float = 0.0,
    ) -> None:
        self.min_score = min_score

    def filter(self, results: list) -> list:
        if not results:
            return []

        return [
            item
            for item in results
            if item.get("rerank_score", 0.0) >= self.min_score
        ]