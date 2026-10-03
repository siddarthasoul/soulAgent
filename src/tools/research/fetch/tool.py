import time

import requests

from common.types.research import FetchedPage


class WebFetchTool:
    DEFAULT_TIMEOUT = 15
    MAX_RETRIES = 1
    RETRY_DELAY = 1.0

    def fetch(self, url: str) -> FetchedPage:
        url = url.strip()

        if not url:
            raise ValueError("URL cannot be empty")

        headers = {
            "User-Agent": (
                "Mozilla/5.0 "
                "(X11; Linux x86_64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/154.0.0.0 "
                "Safari/537.36"
            ),
            "Accept": (
                "text/html,"
                "application/xhtml+xml,"
                "application/pdf,"
                "application/xml;q=0.9,"
                "*/*;q=0.8"
            ),
        }

        last_error: Exception | None = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=self.DEFAULT_TIMEOUT,
                    allow_redirects=True,
                )

                response.raise_for_status()

                content_type = response.headers.get(
                    "Content-Type", ""
                ).split(";")[0].strip().lower()

                return FetchedPage(
                    url=response.url,
                    status_code=response.status_code,
                    content_type=content_type,
                    content=response.content,
                )

            except requests.Timeout as exc:
                last_error = exc

            except requests.RequestException as exc:
                last_error = exc

            if attempt < self.MAX_RETRIES:
                time.sleep(self.RETRY_DELAY)

        raise RuntimeError(
            f"Failed to fetch page after "
            f"{self.MAX_RETRIES} attempts: {url}"
        ) from last_error