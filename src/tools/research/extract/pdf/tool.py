import fitz

from common.types.research import ExtractedContent


class PDFExtractor:

    @staticmethod
    def extract(
        url: str,
        content: bytes,
    ) -> ExtractedContent:

        if not content:
            raise ValueError("PDF content is empty")

        try:
            document = fitz.open(
                stream=content,
                filetype="pdf",
            )

        except Exception as exc:
            raise RuntimeError(
                f"Failed to open PDF: {url}"
            ) from exc

        pages: list[str] = []

        try:
            for page in document:
                text = page.get_text("text")

                if text.strip():
                    pages.append(text.strip())

            metadata = document.metadata or {}

            title = metadata.get("title")

        finally:
            document.close()

        return ExtractedContent(
            url=url,
            title=title or None,
            text="\n\n".join(pages),
        )