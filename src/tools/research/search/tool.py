from urllib.parse import urlparse

import requests

from common.core.env import env
from common.types.research import SearchResult


class BraveSearchTool:
    BASE_URL = "https://api.search.brave.com/res/v1/web/search"

    def __init__(self) -> None:
        self.api_key = env.BRAVE_SEARCH_API_KEY

        if not self.api_key:
            raise ValueError("BRAVE_SEARCH_API_KEY is not set")

    def search(
        self,
        query: str,
        count: int = 10,
    ) -> list[SearchResult]:

        query = query.strip()

        if not query:
            raise ValueError("Search query cannot be empty")

        if not 1 <= count <= 20:
            raise ValueError("count must be between 1 and 20")

        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.api_key,
        }

        params = {
            "q": query,
            "count": count,
            "country": "IN",
            "search_lang": "en",
            "safesearch": "moderate",
            "spellcheck": True,
            "extra_snippets": True,
            "result_filter": "web",
        }

        try:
            response = requests.get(
                self.BASE_URL,
                headers=headers,
                params=params,
                timeout=15,
            )
            response.raise_for_status()

        except requests.Timeout as exc:
            raise RuntimeError(
                "Brave Search request timed out"
            ) from exc

        except requests.RequestException as exc:
            raise RuntimeError(
                f"Brave Search request failed: {exc}"
            ) from exc

        data = response.json()

        return self._normalize_results(data)

    @staticmethod
    def _normalize_results(
        data: dict,
    ) -> list[SearchResult]:

        web_results = data.get("web", {}).get("results", [])

        results: list[SearchResult] = []

        for result in web_results:

            url = result.get("url", "")

            if not url:
                continue

            domain = urlparse(url).netloc

            results.append(
                SearchResult(
                    title=result.get("title", ""),
                    url=url,
                    snippet=result.get("description", ""),
                    extra_snippets=result.get(
                        "extra_snippets",
                        [],
                    ),
                    age=result.get("age"),
                    source_domain=domain,
                )
            )

        return results