from dataclasses import dataclass, field


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str
    extra_snippets: list[str] = field(default_factory=list)
    age: str | None = None
    source_domain: str | None = None
    published_at: str | None = None
    is_official: bool | None = None
    relevance_score: float | None = None


@dataclass(frozen=True)
class FetchedPage:
    url: str
    status_code: int
    content_type: str
    content: bytes


@dataclass(frozen=True)
class ExtractedContent:
    url: str
    title: str | None
    text: str


@dataclass(frozen=True)
class StoredSource:
    source_id: str

    url: str
    title: str | None

    content: str
    content_type: str

    source_domain: str | None

    published_at: str | None
    stored_at: str

    is_official: bool | None = None

    relevance_score: float | None = None




@dataclass(frozen=True)
class ResearchSource:

    result: SearchResult
    extracted: ExtractedContent | None
    cached: bool


@dataclass(frozen=True)
class ResearchResult:
    """Complete output of the research collection stage."""

    query: str
    sources: list[ResearchSource]
    top_sources: list[ResearchSource]
    formatted_output: str