from dataclasses import replace

from common.types.research import SearchResult


class SourceRanker:

    def rank(
        self,
        query: str,
        results: list[SearchResult],
    ) -> list[SearchResult]:

        query_terms = self._tokenize(query)

        ranked: list[SearchResult] = []

        for result in results:

            relevance = self._calculate_relevance(
                query_terms,
                result,
            )

            quality = self._calculate_quality(
                result,
            )

            official = self._calculate_official_score(
                result,
            )

            freshness = self._calculate_freshness(
                result,
            )

            final_score = (
                relevance * 0.50
                + quality * 0.25
                + official * 0.15
                + freshness * 0.10
            )

            ranked.append(
                replace(
                    result,
                    relevance_score=round(
                        final_score,
                        4,
                    ),
                )
            )

        ranked.sort(
            key=lambda result: (
                result.relevance_score or 0.0
            ),
            reverse=True,
        )

        return ranked

    @staticmethod
    def _tokenize(
        text: str,
    ) -> set[str]:

        return {
            word.lower()
            for word in text.split()
            if len(word) > 2
        }

    def _calculate_relevance(
        self,
        query_terms: set[str],
        result: SearchResult,
    ) -> float:

        if not query_terms:
            return 0.0

        text = " ".join(
            [
                result.title,
                result.snippet,
                *result.extra_snippets,
            ]
        ).lower()

        matched = sum(
            1
            for term in query_terms
            if term in text
        )

        return min(
            matched / len(query_terms),
            1.0,
        )

    @staticmethod
    def _calculate_quality(
        result: SearchResult,
    ) -> float:

        domain = (
            result.source_domain or ""
        ).lower()

        high_quality_domains = {
            "gov.in",
            "gov",
            "edu",
            "ac.in",
            "who.int",
            "nature.com",
            "science.org",
            "arxiv.org",
        }

        if any(
            domain == item
            or domain.endswith("." + item)
            for item in high_quality_domains
        ):
            return 1.0

        return 0.5

    @staticmethod
    def _calculate_official_score(
        result: SearchResult,
    ) -> float:

        if result.is_official is True:
            return 1.0

        if result.is_official is False:
            return 0.0

        return 0.5

    @staticmethod
    def _calculate_freshness(
        result: SearchResult,
    ) -> float:

        if result.published_at:
            return 1.0

        if result.age:
            return 0.8

        return 0.5