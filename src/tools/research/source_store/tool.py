import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from common.types.research import SearchResult


CACHE_TTL_SECONDS = 60 * 60 * 24  # 1 day


class SourceStore:
    """
    Stores research sources in two layers:

    1. Cache
       - Fast access for research.
       - Controlled by TTL.
       - Can be refreshed.

    2. Corpus
       - Permanent research data.
       - Historical versions are preserved.
       - Duplicate content is not stored twice.
       - Future RAG/training can use this data.
    """

    def __init__(
        self,
        root: str = "data/research/cache",
        corpus_root: str = "data/knowledge/research/sources",
    ) -> None:
        self.root = Path(root)
        self.corpus_root = Path(corpus_root)

        self.root.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.corpus_root.mkdir(
            parents=True,
            exist_ok=True,
        )

    def save(
        self,
        result: SearchResult,
        content: str,
        content_type: str = "text/plain",
    ) -> str:
        """
        Save a research source to:

        - cache
        - permanent corpus

        Returns the source ID.
        """

        source_id = self._make_source_id(result.url)
        fetched_at = datetime.now(timezone.utc).isoformat()

        content_hash = self._make_content_hash(content)

        data = {
            "source_id": source_id,
            "url": result.url,
            "title": result.title,
            "snippet": result.snippet,
            "extra_snippets": result.extra_snippets,
            "source_domain": result.source_domain,
            "published_at": result.published_at,
            "is_official": result.is_official,
            "relevance_score": result.relevance_score,
            "content_type": content_type,
            "fetched_at": fetched_at,
            "content_hash": content_hash,
            "content": content,
        }

        # ---------------------------------------------------------
        # 1. Save/update cache
        # ---------------------------------------------------------

        cache_path = self.root / f"{source_id}.json"

        cache_path.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        # ---------------------------------------------------------
        # 2. Save permanent corpus snapshot
        # ---------------------------------------------------------

        corpus_path = self._get_corpus_path(
            result=result,
            content_hash=content_hash,
        )

        if not corpus_path.exists():
            corpus_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            corpus_path.write_text(
                json.dumps(
                    data,
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            print(
                f"[SourceStore] New corpus snapshot: "
                f"{corpus_path}"
            )
        else:
            print(
                f"[SourceStore] Duplicate content skipped: "
                f"{result.url}"
            )

        return source_id

    def get(
        self,
        url: str,
    ) -> dict | None:
        """
        Get the latest cached version of a URL.
        """

        source_id = self._make_source_id(url)
        path = self.root / f"{source_id}.json"

        if not path.exists():
            return None

        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )


    def is_fresh(
        self,
        url: str,
    ) -> bool:


        cached_source = self.get(url)

        if cached_source is None:
            return False

        fetched_at = cached_source.get("fetched_at")

        if not fetched_at:
            return False

        try:
            fetched_time = datetime.fromisoformat(
                fetched_at
            )

            now = datetime.now(timezone.utc)

            age_seconds = (
                now - fetched_time
            ).total_seconds()

            return age_seconds < CACHE_TTL_SECONDS

        except (ValueError, TypeError):
            return False

    

    def exists(
        self,
        url: str,
    ) -> bool:
        """
        Check whether a URL exists in cache.
        """

        source_id = self._make_source_id(url)

        return (
            self.root / f"{source_id}.json"
        ).exists()

    def delete(
        self,
        url: str,
    ) -> None:
        """
        Delete only the cache.

        Permanent corpus data is never deleted here.
        """

        source_id = self._make_source_id(url)
        path = self.root / f"{source_id}.json"

        if path.exists():
            path.unlink()

    def _get_corpus_path(
        self,
        result: SearchResult,
        content_hash: str,
    ) -> Path:
        """
        Create a permanent corpus path:

        corpus/
        └── domain/
            └── page-name/
                └── content-hash.json

        The content hash prevents duplicate content.
        """

        domain = self._make_domain_name(
            result.url
        )

        page_name = self._make_page_name(
            result
        )

        return (
            self.corpus_root
            / domain
            / page_name
            / f"{content_hash}.json"
        )

    @staticmethod
    def _make_domain_name(
        url: str,
    ) -> str:
        """
        Convert:

        https://www.python.org/doc/...

        into:

        python.org
        """

        hostname = urlparse(url).hostname

        if not hostname:
            return "unknown-domain"

        hostname = hostname.lower()

        if hostname.startswith("www."):
            hostname = hostname[4:]

        return hostname

    @staticmethod
    def _make_page_name(
        result: SearchResult,
    ) -> str:
        """
        Create a readable page directory name.

        Uses title when available.
        Falls back to URL path.
        """

        title = result.title.strip()

        if title:
            value = title
        else:
            path = urlparse(result.url).path.strip("/")

            value = path or "root"

        value = value.lower()

        value = re.sub(
            r"[^a-z0-9]+",
            "-",
            value,
        )

        value = value.strip("-")

        if not value:
            return "unknown-page"

        return value[:120]

    @staticmethod
    def _make_content_hash(
        content: str,
    ) -> str:
        """
        Hash the actual extracted content.

        Same content => same hash.
        Different content => different hash.
        """

        return hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _make_source_id(
        url: str,
    ) -> str:
        """
        Stable ID for a URL.

        Same URL => same cache file.
        """

        return hashlib.sha256(
            url.strip().encode("utf-8")
        ).hexdigest()