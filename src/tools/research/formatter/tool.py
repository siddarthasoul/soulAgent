from common.types.research import ResearchSource


class ResearchFormatter:
    """
    Converts top research sources into clean,
    readable output for the agent.
    """

    @staticmethod
    def format(
        query: str,
        sources: list[ResearchSource],
        max_chars: int = 800,
    ) -> str:
        sections = [
            f"# Research Results",
            f"Query: {query}",
            "",
        ]

        for index, source in enumerate(sources, start=1):
            result = source.result
            extracted = source.extracted

            if extracted is None:
                continue

            content = " ".join(extracted.text.split())

            if len(content) > max_chars:
                content = content[:max_chars].rstrip() + "..."

            sections.extend(
                [
                    f"## {index}. {result.title}",
                    f"Source: {result.source_domain or 'Unknown'}",
                    f"URL: {result.url}",
                    "",
                    content,
                    "",
                ]
            )

        return "\n".join(sections).strip()