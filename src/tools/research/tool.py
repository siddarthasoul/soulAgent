from dataclasses import dataclass

from common.types.research import (
    ExtractedContent,
    ResearchResult,
    ResearchSource,
    SearchResult,
)

from src.tools.research.extract.tool import WebExtractTool
from src.tools.research.fetch.tool import WebFetchTool
from src.tools.research.ranking.tool import SourceRanker
from src.tools.research.search.tool import BraveSearchTool
from src.tools.research.source_store.tool import SourceStore
from src.tools.research.formatter.tool import ResearchFormatter



class ResearchTool:
    """
    Orchestrates the research data pipeline.

    Responsibilities:
        1. Search the web.
        2. Rank all search results.
        3. Keep all useful results for collection/RAG.
        4. Reuse already stored sources when possible.
        5. Fetch missing sources.
        6. Extract HTML/PDF content.
        7. Store extracted sources.
        8. Return all collected sources plus the best sources.

    This class does NOT:
        - generate the final user answer
        - call an LLM for synthesis
        - perform embeddings
        - write directly to Qdrant

    Those are separate layers that can consume ResearchResult later.
    """

    def __init__(
        self,
        search_tool: BraveSearchTool | None = None,
        fetch_tool: WebFetchTool | None = None,
        extract_tool: WebExtractTool | None = None,
        ranker: SourceRanker | None = None,
        store: SourceStore | None = None,
        formatter: ResearchFormatter | None = None,
    ) -> None:
        self.search_tool = search_tool or BraveSearchTool()
        self.fetch_tool = fetch_tool or WebFetchTool()
        self.extract_tool = extract_tool or WebExtractTool()
        self.ranker = ranker or SourceRanker()
        self.store = store or SourceStore()
        self.formatter = formatter or ResearchFormatter()

    def research(
        self,
        query: str,
        count: int = 5,
        top_k: int = 2,
    ) -> ResearchResult:
        """
        Run the collection stage of research.

        count:
            Number of search results to collect.

        top_k:
            Number of successfully collected ranked sources
            selected for later synthesis.

        Example:
            count=5, top_k=2

        means:

            Search 5
                ↓
            Rank 5
                ↓
            Collect/cache all possible sources
                ↓
            Select best 2 successful sources
        """

        query = query.strip()

        if not query:
            raise ValueError("Research query cannot be empty")

        if not 1 <= count <= 20:
            raise ValueError("count must be between 1 and 20")

        if not 1 <= top_k <= count:
            raise ValueError("top_k must be between 1 and count")

        # ---------------------------------------------------------
        # 1. Search
        # ---------------------------------------------------------

        search_results = self.search_tool.search(
            query=query,
            count=count,
        )

        # ---------------------------------------------------------
        # 2. Rank
        # ---------------------------------------------------------

        ranked_results = self.ranker.rank(
            query=query,
            results=search_results,
        )

        # ---------------------------------------------------------
        # 3. Collect every source
        #
        # A failure for one source must NOT stop the whole run.
        # ---------------------------------------------------------

        sources: list[ResearchSource] = []

        for result in ranked_results:
            try:
                source = self._collect_source(result)

            except Exception as exc:
                print(
                    f"[Research] Failed to collect source: "
                    f"{result.url}"
                )
                print(
                    f"[Research] Reason: {exc}"
                )

                source = ResearchSource(
                    result=result,
                    extracted=None,
                    cached=False,
                )

            sources.append(source)

        # ---------------------------------------------------------
        # 4. Select top successful sources
        #
        # Failed sources should not be sent to the future
        # synthesis/LLM layer.
        # ---------------------------------------------------------

        successful_sources = [
            source
            for source in sources
            if source.extracted is not None
        ]

        top_sources = successful_sources[:top_k]

        formatted_output = self.formatter.format(
            query=query,
            sources=top_sources,
        )

        # ---------------------------------------------------------
        # 5. Return complete research result
        # ---------------------------------------------------------

        return ResearchResult(
            query=query,
            sources=sources,
            top_sources=top_sources,
            formatted_output=formatted_output,
        )

    def _collect_source(
        self,
        result: SearchResult,
    ) -> ResearchSource:
        """
        Load a source from cache or fetch/extract/store it.
        """

        # ---------------------------------------------------------
        # 1. Check cache
        # ---------------------------------------------------------

        cached_source = self.store.get(result.url)

        if cached_source is not None and self.store.is_fresh(result.url):
            extracted = ExtractedContent(
                url=cached_source["url"],
                title=cached_source.get("title"),
                text=cached_source.get("content", ""),
            )

            print(
                f"[Research] Cache hit: {result.url}"
            )

            return ResearchSource(
                result=result,
                extracted=extracted,
                cached=True,
            )

        # ---------------------------------------------------------
        # 2. Fetch
        # ---------------------------------------------------------

        print(
            f"[Research] Fetching: {result.url}"
        )

        page = self.fetch_tool.fetch(result.url)

        # ---------------------------------------------------------
        # 3. Extract
        # ---------------------------------------------------------

        extracted = self.extract_tool.extract(page)

        # ---------------------------------------------------------
        # 4. Store
        # ---------------------------------------------------------

        self.store.save(
            result=result,
            content=extracted.text,
            content_type=page.content_type,
        )

        print(
            f"[Research] Stored: {result.url}"
        )

        # ---------------------------------------------------------
        # 5. Return collected source
        # ---------------------------------------------------------

        return ResearchSource(
            result=result,
            extracted=extracted,
            cached=False,
        )