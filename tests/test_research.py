from src.tools.research.tool import ResearchTool


def print_source(
    index: int,
    source,
) -> None:

    result = source.result
    extracted = source.extracted

    print()
    print("=" * 80)
    print(f"SOURCE {index}")
    print("=" * 80)

    print(f"Title:      {result.title}")
    print(f"URL:        {result.url}")
    print(f"Domain:     {result.source_domain}")
    print(f"Score:      {result.relevance_score}")
    print(f"Cached:     {source.cached}")

    if extracted:
        print(f"Extracted:  {len(extracted.text)} characters")
        print(f"Extract title: {extracted.title}")

        preview = extracted.text[:500].replace(
            "\n",
            " ",
        )

        print(f"Preview:    {preview}...")

    else:
        print("Extracted:  None")


def run_research_test() -> None:

    print("=" * 80)
    print("RESEARCH TOOL TEST")
    print("=" * 80)

    query = "What is Python programming language?"

    print()
    print(f"Query: {query}")
    print("Search count: 5")
    print("Top sources: 2")

    research_tool = ResearchTool()

    # ------------------------------------------------------------------
    # FIRST RUN
    # ------------------------------------------------------------------

    print()
    print("=" * 80)
    print("FIRST RUN")
    print("=" * 80)

    result = research_tool.research(
        query=query,
        count=5,
        top_k=2,
    )

    print()
    print(f"Query: {result.query}")
    print(f"Total sources: {len(result.sources)}")
    print(f"Top sources: {len(result.top_sources)}")

    if not result.sources:
        raise RuntimeError(
            "Research returned no sources"
        )

    if len(result.top_sources) != 2:
        raise RuntimeError(
            f"Expected 2 top sources, "
            f"got {len(result.top_sources)}"
        )

    print()
    print("ALL COLLECTED SOURCES")

    for index, source in enumerate(
        result.sources,
        start=1,
    ):
        print_source(
            index,
            source,
        )

    print()
    print("=" * 80)
    print("TOP 2 SOURCES")
    print("=" * 80)

    for index, source in enumerate(
        result.top_sources,
        start=1,
    ):
        print_source(
            index,
            source,
        )

    # ------------------------------------------------------------------
    # RANKING CHECK
    # ------------------------------------------------------------------

    print()
    print("=" * 80)
    print("RANKING CHECK")
    print("=" * 80)

    scores = [
        source.result.relevance_score
        for source in result.sources
    ]

    print(f"Scores: {scores}")

    valid_scores = [
        score
        for score in scores
        if score is not None
    ]

    if not valid_scores:
        raise RuntimeError(
            "No relevance scores were generated"
        )

    if valid_scores != sorted(
        valid_scores,
        reverse=True,
    ):
        raise RuntimeError(
            "Sources are not sorted by relevance score"
        )

    print("Ranking order: OK")

    # ------------------------------------------------------------------
    # COLLECTION CHECK
    # ------------------------------------------------------------------

    print()
    print("=" * 80)
    print("COLLECTION CHECK")
    print("=" * 80)

    extracted_count = sum(
        1
        for source in result.sources
        if source.extracted is not None
    )

    print(
        f"Sources collected: "
        f"{len(result.sources)}"
    )

    print(
        f"Sources with extracted content: "
        f"{extracted_count}"
    )

    if extracted_count == 0:
        raise RuntimeError(
            "No source content was extracted"
        )

    print("Collection: OK")

    # ------------------------------------------------------------------
    # CACHE TEST
    # ------------------------------------------------------------------

    print()
    print("=" * 80)
    print("SECOND RUN — CACHE TEST")
    print("=" * 80)

    second_result = research_tool.research(
        query=query,
        count=5,
        top_k=2,
    )

    print()
    print(
        f"Second run sources: "
        f"{len(second_result.sources)}"
    )

    cached_count = sum(
        1
        for source in second_result.sources
        if source.cached
    )

    print(
        f"Cached sources: "
        f"{cached_count}"
    )

    if cached_count == 0:
        raise RuntimeError(
            "Expected cached sources on second run"
        )

    print("Cache: OK")

    # ------------------------------------------------------------------
    # TOP-K CHECK
    # ------------------------------------------------------------------

    print()
    print("=" * 80)
    print("TOP-K CHECK")
    print("=" * 80)

    if len(second_result.top_sources) != 2:
        raise RuntimeError(
            "top_k=2 did not return exactly 2 sources"
        )

    print(
        "top_k=2: OK"
    )

    # ------------------------------------------------------------------
    # FINAL RESULT
    # ------------------------------------------------------------------

    print()
    print("=" * 80)
    print("RESEARCH TEST PASSED")
    print("=" * 80)

    print()
    print(
        "Pipeline verified:"
    )

    print(
        "Search -> Rank -> Collect -> "
        "Fetch -> Extract -> Store -> Cache -> Top 2"
    )


if __name__ == "__main__":
    run_research_test()