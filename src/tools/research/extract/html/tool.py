import re

from bs4 import BeautifulSoup, Tag

from common.types.research import ExtractedContent


class HTMLExtractor:
    """
    Extract readable text from HTML pages.

    Responsibilities:
        - Remove obvious non-content HTML elements.
        - Extract a useful page title.
        - Select the most likely content root.
        - Preserve natural spaces between HTML text nodes.
        - Normalize whitespace.
        - Remove simple standalone boilerplate.

    This extractor intentionally avoids site-specific rules.
    """

    NOISE_TAGS = (
        "script",
        "style",
        "noscript",
        "svg",
        "canvas",
        "iframe",
        "nav",
        "footer",
        "header",
        "form",
        "aside",
        "dialog",
        "menu",
        "template",
    )

    CONTENT_ROOT_SELECTORS = (
        "article",
        "main",
        '[role="main"]',
        '[itemprop="articleBody"]',
    )

    BOILERPLATE_PATTERNS = (
        re.compile(
            r"^skip to (main )?content$",
            re.IGNORECASE,
        ),
        re.compile(
            r"^jump to content$",
            re.IGNORECASE,
        ),
        re.compile(
            r"^table of contents$",
            re.IGNORECASE,
        ),
        re.compile(
            r"^cookie settings$",
            re.IGNORECASE,
        ),
        re.compile(
            r"^privacy settings$",
            re.IGNORECASE,
        ),
        re.compile(
            r"^accept cookies$",
            re.IGNORECASE,
        ),
    )

    @staticmethod
    def extract(
        url: str,
        content: bytes,
    ) -> ExtractedContent:
        if not content:
            raise ValueError("HTML content is empty")

        soup = BeautifulSoup(
            content,
            "html.parser",
        )

        HTMLExtractor._remove_noise(soup)

        title = HTMLExtractor._extract_title(soup)

        content_root = HTMLExtractor._find_content_root(
            soup
        )

        text = HTMLExtractor._extract_text(
            content_root
        )

        return ExtractedContent(
            url=url,
            title=title,
            text=text,
        )

    @staticmethod
    def _remove_noise(
        soup: BeautifulSoup,
    ) -> None:
        """
        Remove HTML elements that are inherently
        non-content.

        We only remove known HTML element types here.

        We intentionally do not remove arbitrary elements
        based on class/id names because doing so can change
        the relationship between adjacent text nodes.
        """

        for tag in soup.find_all(
            HTMLExtractor.NOISE_TAGS
        ):
            tag.decompose()

    @staticmethod
    def _extract_title(
        soup: BeautifulSoup,
    ) -> str | None:
        """
        Extract the page title.

        Priority:
            1. <title>
            2. <h1>
        """

        if soup.title:
            title = HTMLExtractor._get_clean_text(
                soup.title
            )

            if title:
                return title

        heading = soup.find("h1")

        if heading:
            title = HTMLExtractor._get_clean_text(
                heading
            )

            if title:
                return title

        return None

    @staticmethod
    def _find_content_root(
        soup: BeautifulSoup,
    ) -> Tag:
        """
        Find the most likely main content region.

        Priority:
            article
            main
            role="main"
            articleBody
            body
            entire document
        """

        for selector in HTMLExtractor.CONTENT_ROOT_SELECTORS:
            root = soup.select_one(selector)

            if root:
                return root

        if soup.body:
            return soup.body

        return soup

    @staticmethod
    def _extract_text(
        root: Tag,
    ) -> str:
        """
        Extract text directly from the selected content root.

        BeautifulSoup inserts a space between separate
        HTML text nodes.

        Example:

            <span>language</span><span>known</span>

        becomes:

            language known
        """

        text = root.get_text(
            separator=" ",
            strip=True,
        )

        return HTMLExtractor._clean_text(
            text
        )

    @staticmethod
    def _get_clean_text(
        element: Tag,
    ) -> str:
        """
        Extract and normalize text from one HTML element.
        """

        text = element.get_text(
            separator=" ",
            strip=True,
        )

        return HTMLExtractor._normalize_whitespace(
            text
        )

    @staticmethod
    def _clean_text(
        text: str,
    ) -> str:
        """
        Final text normalization.
        """

        text = text.replace(
            "\r\n",
            "\n",
        )

        text = text.replace(
            "\r",
            "\n",
        )

        text = text.replace(
            "\u00a0",
            " ",
        )

        lines = []

        for line in text.splitlines():
            line = HTMLExtractor._normalize_whitespace(
                line
            )

            if not line:
                continue

            if HTMLExtractor._is_boilerplate(line):
                continue

            lines.append(line)

        return "\n\n".join(lines).strip()

    @staticmethod
    def _normalize_whitespace(
        text: str,
    ) -> str:
        """
        Normalize whitespace without trying to guess
        missing word boundaries.
        """

        text = text.replace(
            "\u00a0",
            " ",
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    @staticmethod
    def _is_boilerplate(
        text: str,
    ) -> bool:
        """
        Remove only exact standalone boilerplate phrases.

        We intentionally do not remove arbitrary sentences
        because they may contain legitimate article content.
        """

        normalized = text.strip()

        return any(
            pattern.fullmatch(normalized)
            for pattern in HTMLExtractor.BOILERPLATE_PATTERNS
        )
