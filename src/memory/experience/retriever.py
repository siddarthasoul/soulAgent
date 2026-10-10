import re

from src.memory.experience.models import (
    ExperienceRecord,
)
from src.memory.experience.repository import ExperienceRepository


class ExperienceRetriever:
    """Retrieve past experiences using deterministic keyword matching."""

    def __init__(
        self,
        repository: ExperienceRepository | None = None,
    ) -> None:
        self.repository = repository or ExperienceRepository()

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-zA-Z0-9_]+", text.lower())
            if len(token) > 1
        }

    def search(
        self,
        query: str,
        *,
        problem_pattern: str | None = None,
        verified_only: bool = True,
        limit: int = 5,
    ) -> list[ExperienceRecord]:
        if limit < 1:
            raise ValueError("limit must be at least 1")

        query_tokens = self._tokens(query)

        if not query_tokens and not problem_pattern:
            return []

        candidates = (
            self.repository.list_verified()
            if verified_only
            else self.repository.list_experiences()
        )

        scored: list[tuple[int, ExperienceRecord]] = []

        for experience in candidates:
            searchable_text = " ".join(
                [
                    experience.query,
                    experience.problem_pattern,
                    experience.diagnosis,
                    experience.action,
                ]
            )
            experience_tokens = self._tokens(searchable_text)

            keyword_score = len(query_tokens & experience_tokens)

            pattern_match = bool(
                problem_pattern
                and experience.problem_pattern.casefold()
                == problem_pattern.casefold()
            )

            # Reserve a large bonus for an exact problem-pattern match.
            score = keyword_score + (100 if pattern_match else 0)

            if score > 0:
                scored.append((score, experience))

        scored.sort(
            key=lambda item: (
                -item[0],
                item[1].created_at,
                item[1].experience_id,
            )
        )

        return [
            experience
            for _, experience in scored[:limit]
        ]
