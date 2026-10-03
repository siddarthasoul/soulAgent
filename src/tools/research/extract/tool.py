from common.types.research import (
    ExtractedContent,
    FetchedPage,
)

from src.tools.research.extract.html.tool import HTMLExtractor
from src.tools.research.extract.pdf.tool import PDFExtractor


class WebExtractTool:

    def extract(
        self,
        page: FetchedPage,
    ) -> ExtractedContent:

        if not page.content:
            raise ValueError("Page content is empty")

        if page.content_type == "text/html":
            return HTMLExtractor.extract(
                url=page.url,
                content=page.content,
            )

        if page.content_type == "application/pdf":
            return PDFExtractor.extract(
                url=page.url,
                content=page.content,
            )

        raise ValueError(
            f"Unsupported content type: "
            f"{page.content_type}"
        )