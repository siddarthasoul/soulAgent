from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter
from html import unescape
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]

KNOWLEDGE_ROOT = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
)


SUPPORTED_AGENTS = {
    "chat",
    "chemistry",
    "math",
    "physics",
    "research",
    "coding",
    "visualization",
}



SUPPORTED_EXTENSIONS = {
    ".md",
    ".txt",
    ".rst",
    ".json",
    ".jsonl",
    ".csv",
    ".html",
    ".htm",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".ipynb",
    ".pdf",
}




IGNORED_DIRECTORIES = {
    ".git",
    ".github",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".cache",
    "cache",
    "build",
    "dist",
    ".next",
    "coverage",
    "target",
}


IGNORED_FILES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "poetry.lock",
    "uv.lock",
}



RESEARCH_REQUIRED_FIELDS = {
    "source_id",
    "url",
    "title",
    "snippet",
    "extra_snippets",
    "source_domain",
    "published_at",
    "is_official",
    "relevance_score",
    "content_type",
    "fetched_at",
    "content_hash",
    "content",
}



def clean_text(text: str) -> str:


    text = text.replace("\x00", "")

    text = unicodedata.normalize(
        "NFKC",
        text,
    )

    text = text.replace(
        "\r\n",
        "\n",
    )

    text = text.replace(
        "\r",
        "\n",
    )

    text = "\n".join(
        line.rstrip()
        for line in text.split("\n")
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()




def clean_html(text: str) -> str:

    text = re.sub(
        r"<(script|style)\b[^>]*>.*?</\1>",
        " ",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(
        r"<br\s*/?>",
        "\n",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"</(p|div|section|article|h[1-6]|li)>",
        "\n",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"<[^>]+>",
        " ",
        text,
    )

    text = unescape(text)

    return clean_text(text)



def normalize_url(url: Any) -> str:

    if not isinstance(
        url,
        str,
    ):
        return ""

    url = url.strip()

    match = re.fullmatch(
        r"\[([^\]]+)\]\(([^)]+)\)",
        url,
    )

    if match:
        return match.group(2).strip()

    return url




def read_text_file(
    path: Path,
) -> str:

    return clean_text(
        path.read_text(
            encoding="utf-8",
            errors="replace",
        )
    )




def extract_json(
    path: Path,
) -> str:

    data = json.loads(
        path.read_text(
            encoding="utf-8",
            errors="replace",
        )
    )

    return clean_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        )
    )




def extract_jsonl(
    path: Path,
) -> list[dict[str, Any]]:

    documents: list[dict[str, Any]] = []

    with path.open(
        "r",
        encoding="utf-8",
        errors="replace",
    ) as file:

        for line_number, line in enumerate(
            file,
            start=1,
        ):

            line = line.strip()

            if not line:
                continue

            try:
                data = json.loads(line)

            except json.JSONDecodeError:
                continue

            if isinstance(
                data,
                dict,
            ):

                content = data.get(
                    "content"
                )

                if content is None:
                    content = data.get(
                        "text"
                    )

                if content is None:
                    content = json.dumps(
                        data,
                        ensure_ascii=False,
                    )

                content = clean_text(
                    str(content)
                )

                if not content:
                    continue

                metadata = {
                    key: value
                    for key, value in data.items()
                    if key not in {
                        "content",
                        "text",
                    }
                }

                documents.append(
                    {
                        "content": content,
                        "jsonl_line": line_number,
                        **metadata,
                    }
                )

            else:

                content = clean_text(
                    json.dumps(
                        data,
                        ensure_ascii=False,
                    )
                )

                if content:

                    documents.append(
                        {
                            "content": content,
                            "jsonl_line": line_number,
                        }
                    )

    return documents



def extract_csv(
    path: Path,
) -> str:

    with path.open(
        "r",
        encoding="utf-8",
        errors="replace",
        newline="",
    ) as file:

        rows = list(
            csv.DictReader(file)
        )

    output: list[str] = []

    for index, row in enumerate(
        rows,
        start=1,
    ):

        output.append(
            f"Row {index}:"
        )

        for key, value in row.items():

            if value is not None:

                output.append(
                    f"{key}: {value}"
                )

        output.append("")

    return clean_text(
        "\n".join(output)
    )




def extract_notebook(
    path: Path,
) -> str:

    notebook = json.loads(
        path.read_text(
            encoding="utf-8",
            errors="replace",
        )
    )

    sections: list[str] = []

    for index, cell in enumerate(
        notebook.get("cells", []),
        start=1,
    ):

        source = "".join(
            cell.get(
                "source",
                [],
            )
        )

        if not source.strip():
            continue

        sections.append(
            f"[Cell {index} - "
            f"{cell.get('cell_type', 'unknown')}]\n"
            f"{source}"
        )

    return clean_text(
        "\n\n".join(sections)
    )




def extract_pdf(
    path: Path,
) -> list[dict[str, Any]]:

    try:

        import fitz

    except ImportError as exc:

        raise RuntimeError(
            "PyMuPDF is required for PDF extraction.\n"
            "Install with:\n"
            "pip install pymupdf"
        ) from exc

    documents: list[dict[str, Any]] = []

    with fitz.open(path) as pdf:

        for page_number, page in enumerate(
            pdf,
            start=1,
        ):

            content = clean_text(
                page.get_text()
            )

            if not content:
                continue

            documents.append(
                {
                    "content": content,
                    "page": page_number,
                }
            )

    return documents



def should_ignore(
    path: Path,
) -> bool:

    if any(
        part in IGNORED_DIRECTORIES
        for part in path.parts
    ):
        return True

    if path.name in IGNORED_FILES:
        return True

    if path.name.endswith(
        (
            ".min.js",
            ".min.css",
        )
    ):
        return True

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return True

    return False



def get_category(
    path: Path,
    source_root: Path,
) -> str:

    relative = path.relative_to(
        source_root
    )

    if not relative.parts:
        return "uncategorized"

    return relative.parts[0]



def create_document_id(
    agent: str,
    source: str,
    file: str,
    content: str,
    extra: str = "",
) -> str:

    raw = (
        f"{agent}|"
        f"{source}|"
        f"{file}|"
        f"{extra}|"
        f"{content}"
    )

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()



def get_file_signature(
    path: Path,
) -> dict[str, Any]:

    stat = path.stat()

    return {
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }




def is_research_record(
    data: dict[str, Any],
) -> bool:

    return RESEARCH_REQUIRED_FIELDS.issubset(
        data.keys()
    )


def classify_research_content(
    content: str,
) -> tuple[str, str]:

    if not content:

        return (
            "rejected",
            "empty_content",
        )

    lowered = content.lower()

    if len(content) < 500:

        loading_patterns = [
            "loading",
            "please wait",
            "enable javascript",
            "javascript is required",
        ]

        if any(
            pattern in lowered
            for pattern in loading_patterns
        ):

            return (
                "rejected",
                "loading_or_placeholder",
            )

        return (
            "rejected",
            "content_too_short",
        )

    return (
        "valid",
        "",
    )



def normalize_research_record(
    data: dict[str, Any],
    source_file: str,
) -> dict[str, Any]:

    content = clean_text(
        str(
            data.get(
                "content",
                "",
            )
        )
    )

    title = clean_text(
        str(
            data.get(
                "title",
                "",
            )
        )
    )

    quality_status, quality_reason = (
        classify_research_content(
            content
        )
    )

    if quality_status != "valid":

        return {
            "_rejected": True,
            "quality_status": quality_status,
            "quality_reason": quality_reason,
            "title": title,
            "source_file": source_file,
            "source_id": data.get(
                "source_id"
            ),
            "url": normalize_url(
                data.get(
                    "url",
                    "",
                )
            ),
            "content_length": len(content),
        }

    extra_snippets = data.get(
        "extra_snippets",
        [],
    )

    if not isinstance(
        extra_snippets,
        list,
    ):
        extra_snippets = []

    extra_snippets = [
        clean_text(str(item))
        for item in extra_snippets
        if isinstance(
            item,
            str,
        )
        and item.strip()
    ]

    content_hash = data.get(
        "content_hash"
    )

    if not content_hash:

        content_hash = hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()

    return {
        "title": title,
        "snippet": clean_text(
            str(
                data.get(
                    "snippet",
                    "",
                )
            )
        ),
        "extra_snippets": extra_snippets,
        "source_id": data.get(
            "source_id"
        ),
        "url": normalize_url(
            data.get(
                "url",
                "",
            )
        ),
        "source_domain": data.get(
            "source_domain"
        ),
        "published_at": data.get(
            "published_at"
        ),
        "is_official": data.get(
            "is_official"
        ),
        "relevance_score": data.get(
            "relevance_score"
        ),
        "content_type": data.get(
            "content_type"
        ),
        "fetched_at": data.get(
            "fetched_at"
        ),
        "content_hash": content_hash,
        "content": content,
        "quality_status": "valid",
        "source_file": source_file,
    }




def is_oatutor_source(
    category: str,
    file: str,
) -> bool:

    category_lower = category.lower()

    file_lower = file.lower()

    return (
        "oatutor" in category_lower
        or "oatutor" in file_lower
    )




def filter_oatutor_document(
    document: dict[str, Any],
) -> tuple[bool, str]:

    step_title = document.get(
        "stepTitle"
    )

    step_body = document.get(
        "stepBody"
    )

    step_answer = document.get(
        "stepAnswer"
    )

    answer_latex = document.get(
        "answerLatex"
    )

    question = document.get(
        "question"
    )

    problem = document.get(
        "problem"
    )

    solution = document.get(
        "solution"
    )

    explanation = document.get(
        "explanation"
    )

    def has_text(value: Any) -> bool:

        return (
            isinstance(value, str)
            and bool(value.strip())
        )

    def has_value(value: Any) -> bool:

        if value is None:
            return False

        if isinstance(value, str):
            return bool(value.strip())

        if isinstance(value, (list, tuple, dict)):
            return bool(value)

        return True


    if has_text(step_title) and (
        has_text(step_body)
        or has_value(step_answer)
        or has_text(answer_latex)
    ):

        return (
            True,
            "oatutor_math_step",
        )



    if (
        has_text(question)
        or has_text(problem)
    ) and (
        has_text(solution)
        or has_text(explanation)
        or has_value(step_answer)
        or has_text(answer_latex)
    ):

        return (
            True,
            "oatutor_problem_solution",
        )



    educational_keys = {
        "question",
        "problem",
        "solution",
        "explanation",
        "hint",
        "steps",
        "answer",
        "answerLatex",
        "stepAnswer",
        "stepTitle",
        "stepBody",
    }

    useful_keys = (
        educational_keys
        .intersection(
            document.keys()
        )
    )

    if len(useful_keys) >= 2:

        return (
            True,
            "oatutor_educational_content",
        )

    return (
        False,
        "oatutor_metadata_or_noise",
    )




def extract_file(
    path: Path,
    source_root: Path,
    agent: str,
) -> list[dict[str, Any]]:

    extension = path.suffix.lower()

    relative_path = (
        path.relative_to(
            source_root
        ).as_posix()
    )

    base_metadata = {
        "file": relative_path,
        "file_type": extension.lstrip("."),
    }


    if extension == ".pdf":

        pages = extract_pdf(path)

        return [
            {
                **base_metadata,
                **page,
            }
            for page in pages
        ]


    if extension == ".jsonl":

        return [
            {
                **base_metadata,
                **item,
            }
            for item in extract_jsonl(path)
        ]


    if extension == ".json":

        raw = json.loads(
            path.read_text(
                encoding="utf-8",
                errors="replace",
            )
        )


        if (
            agent == "research"
            and isinstance(raw, dict)
            and is_research_record(raw)
        ):

            normalized = (
                normalize_research_record(
                    raw,
                    relative_path,
                )
            )

            return [
                {
                    **base_metadata,
                    **normalized,
                }
            ]

        if (
            agent == "math"
            and is_oatutor_source(
                get_category(
                    path,
                    source_root,
                ),
                relative_path,
            )
            and isinstance(raw, dict)
        ):

            return [
                {
                    **base_metadata,
                    **raw,
                }
            ]


        return [
            {
                **base_metadata,
                "content": extract_json(path),
            }
        ]



    if extension == ".csv":

        return [
            {
                **base_metadata,
                "content": extract_csv(path),
            }
        ]



    if extension == ".ipynb":

        return [
            {
                **base_metadata,
                "content": extract_notebook(path),
            }
        ]


    if extension in {
        ".html",
        ".htm",
    }:

        raw = path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        return [
            {
                **base_metadata,
                "content": clean_html(raw),
            }
        ]



    return [
        {
            **base_metadata,
            "content": read_text_file(path),
        }
    ]



def should_keep(
    agent: str,
    document: dict[str, Any],
) -> tuple[bool, str]:

    category = document.get(
        "category",
        "",
    )

    file = document.get(
        "file",
        "",
    ).replace(
        "\\",
        "/",
    )


    if (
        agent == "math"
        and is_oatutor_source(
            str(category),
            file,
        )
    ):

        return filter_oatutor_document(
            document
        )


    if agent == "chat":

        if category in {
            "general",
            "science",
            "history",
            "geography",
            "culture",
        }:

            return True, category

        if category == "programming":

            if "cpython/Doc/" in file:

                return True, "programming"

            return (
                False,
                "programming_source_code",
            )

        if category == "technology":

            if (
                "mdn-content/files/en-us/"
                in file
            ):

                return True, "technology"

            if "/Documentation/" in file:

                return True, "technology"

            return (
                False,
                "technology_source_code",
            )

        return False, "unknown"


    return True, "default"



def source_output_key(
    relative_path: str,
) -> str:

    return hashlib.sha256(
        relative_path.encode("utf-8")
    ).hexdigest()[:24]


def load_checkpoint(
    path: Path,
) -> dict[str, Any]:

    if not path.exists():

        return {
            "version": 2,
            "files": {},
        }

    try:

        checkpoint = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        if not isinstance(
            checkpoint,
            dict,
        ):

            return {
                "version": 2,
                "files": {},
            }

        checkpoint.setdefault(
            "files",
            {},
        )

        return checkpoint

    except Exception:

        return {
            "version": 2,
            "files": {},
        }


def save_checkpoint(
    path: Path,
    checkpoint: dict[str, Any],
) -> None:

    temporary = path.with_suffix(
        ".tmp"
    )

    temporary.write_text(
        json.dumps(
            checkpoint,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    temporary.replace(path)


def save_document_index(
    path: Path,
    documents: dict[str, dict[str, Any]],
) -> None:


    index = {
        "version": 1,
        "documents": documents,
    }

    temporary = path.with_suffix(".tmp")

    temporary.write_text(
        json.dumps(
            index,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    temporary.replace(path)


def rebuild_document_index(
    output_path: Path,
    index_path: Path,
) -> int:

    documents: dict[str, dict[str, Any]] = {}

    if not output_path.exists():
        save_document_index(
            index_path,
            documents,
        )
        return 0

    with output_path.open(
        "r",
        encoding="utf-8",
    ) as source:

        for line in source:

            if not line.strip():
                continue

            try:
                document = json.loads(line)

            except json.JSONDecodeError:
                continue

            content_hash = document.get(
                "content_hash"
            )

            if not content_hash:
                content = document.get(
                    "content",
                    "",
                )

                if not content:
                    continue

                content_hash = hashlib.sha256(
                    content.encode("utf-8")
                ).hexdigest()

            documents[content_hash] = {
                "document_id": document.get("id"),
                "source": document.get("source"),
                "file": document.get("file"),
                "agent": document.get("agent"),
                "category": document.get("category"),
            }

    save_document_index(
        index_path,
        documents,
    )

    return len(documents)



def rebuild_combined_output(
    files_state: dict[str, Any],
    processed_root: Path,
    source_output_root: Path,
    output_path: Path,
) -> int:

    seen_content_hashes: set[str] = set()

    document_count = 0

    temporary_output = output_path.with_suffix(
        ".tmp"
    )

    with temporary_output.open(
        "w",
        encoding="utf-8",
    ) as output:

        for relative in sorted(
            files_state
        ):

            state = files_state[
                relative
            ]

            source_output = (
                processed_root
                / state.get(
                    "source_output",
                    "",
                )
            )

            if not source_output.exists():
                continue

            with source_output.open(
                "r",
                encoding="utf-8",
            ) as source:

                for line in source:

                    if not line.strip():
                        continue

                    try:

                        document = json.loads(
                            line
                        )

                    except json.JSONDecodeError:

                        continue

                    content_hash = (
                        document.get(
                            "content_hash"
                        )
                    )

                    if (
                        content_hash
                        and content_hash
                        in seen_content_hashes
                    ):

                        continue

                    if content_hash:

                        seen_content_hashes.add(
                            content_hash
                        )

                    output.write(
                        json.dumps(
                            document,
                            ensure_ascii=False,
                        )
                        + "\n"
                    )

                    document_count += 1

    temporary_output.replace(
        output_path
    )

    return document_count



def rebuild_rejected_output(
    files_state: dict[str, Any],
    source_output_root: Path,
    rejected_path: Path,
) -> int:

    rejected_count = 0

    temporary_rejected = (
        rejected_path.with_suffix(
            ".tmp"
        )
    )

    with temporary_rejected.open(
        "w",
        encoding="utf-8",
    ) as output:

        for relative in sorted(
            files_state
        ):

            rejected_file = (
                source_output_root
                / (
                    f"{source_output_key(relative)}"
                    ".rejected.jsonl"
                )
            )

            if not rejected_file.exists():
                continue

            with rejected_file.open(
                "r",
                encoding="utf-8",
            ) as source:

                for line in source:

                    if not line.strip():
                        continue

                    output.write(line)
                    rejected_count += 1

    temporary_rejected.replace(
        rejected_path
    )

    return rejected_count



def process_agent(
    agent: str,
    force: bool = False,
) -> None:

    if agent not in SUPPORTED_AGENTS:

        raise ValueError(
            f"Unknown agent: {agent}"
        )

    source_root = (
        KNOWLEDGE_ROOT
        / agent
        / "sources"
    )

    processed_root = (
        KNOWLEDGE_ROOT
        / agent
        / "processed"
    )

    source_output_root = (
        processed_root
        / "_sources"
    )

    checkpoint_path = (
        processed_root
        / "checkpoint.json"
    )

    output_path = (
        processed_root
        / "documents.jsonl"
    )

    rejected_path = (
        processed_root
        / "rejected.jsonl"
    )

    document_index_path = (
        processed_root
        / "document_index.json"
    )

    if not source_root.exists():

        raise FileNotFoundError(
            f"Source directory not found:\n"
            f"{source_root}"
        )

    processed_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    source_output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    checkpoint = load_checkpoint(
        checkpoint_path
    )

    files_state = checkpoint.setdefault(
        "files",
        {},
    )

    current_files: set[str] = set()

    stats = Counter()


    for path in sorted(
        source_root.rglob("*")
    ):

        if not path.is_file():
            continue

        if should_ignore(path):
            continue

        relative = (
            path.relative_to(
                source_root
            ).as_posix()
        )

        current_files.add(relative)

        try:

            signature = get_file_signature(
                path
            )

        except OSError:

            stats["stat_errors"] += 1
            continue

        old_state = files_state.get(
            relative
        )

        source_key = source_output_key(
            relative
        )

        source_output = (
            source_output_root
            / f"{source_key}.jsonl"
        )

        source_rejected = (
            source_output_root
            / f"{source_key}.rejected.jsonl"
        )

        if (
            not force
            and old_state
            and old_state.get("size")
            == signature["size"]
            and old_state.get("mtime_ns")
            == signature["mtime_ns"]
            and source_output.exists()
        ):

            stats["skipped"] += 1

            continue

        stats["processed_files"] += 1

        category = get_category(
            path,
            source_root,
        )

        documents: list[
            dict[str, Any]
        ] = []

        rejected: list[
            dict[str, Any]
        ] = []


        try:

            extracted = extract_file(
                path=path,
                source_root=source_root,
                agent=agent,
            )

            for item in extracted:


                if item.get(
                    "_rejected"
                ):

                    rejected.append(
                        {
                            "file": relative,
                            "category": category,
                            **{
                                key: value
                                for key, value
                                in item.items()
                                if key != "_rejected"
                            },
                        }
                    )

                    continue



                is_oatutor = (
                    agent == "math"
                    and is_oatutor_source(
                        category,
                        relative,
                    )
                )

                if is_oatutor:

                    title = clean_text(
                        str(
                            item.get(
                                "stepTitle",
                                item.get(
                                    "question",
                                    item.get(
                                        "problem",
                                        "",
                                    ),
                                ),
                            )
                        )
                    )

                    body = clean_text(
                        str(
                            item.get(
                                "stepBody",
                                "",
                            )
                        )
                    )

                    answer = item.get(
                        "stepAnswer"
                    )

                    answer_latex = clean_text(
                        str(
                            item.get(
                                "answerLatex",
                                "",
                            )
                        )
                    )

                    solution = clean_text(
                        str(
                            item.get(
                                "solution",
                                "",
                            )
                        )
                    )

                    explanation = clean_text(
                        str(
                            item.get(
                                "explanation",
                                "",
                            )
                        )
                    )

                    content_parts: list[str] = []

                    if title:
                        content_parts.append(
                            f"Problem: {title}"
                        )

                    if body:
                        content_parts.append(
                            f"Details: {body}"
                        )

                    if solution:
                        content_parts.append(
                            f"Solution: {solution}"
                        )

                    if explanation:
                        content_parts.append(
                            f"Explanation: {explanation}"
                        )

                    if answer is not None:

                        if isinstance(
                            answer,
                            list,
                        ):

                            answer_text = "\n".join(
                                clean_text(
                                    str(value)
                                )
                                for value in answer
                            )

                        else:

                            answer_text = clean_text(
                                str(answer)
                            )

                        if answer_text:
                            content_parts.append(
                                f"Answer: {answer_text}"
                            )

                    if answer_latex:
                        content_parts.append(
                            f"Answer LaTeX: {answer_latex}"
                        )

                    content = clean_text(
                        "\n".join(
                            content_parts
                        )
                    )

                else:

                    content = clean_text(
                        str(
                            item.get(
                                "content",
                                "",
                            )
                        )
                    )


                if not content:

                    rejected.append(
                        {
                            "file": relative,
                            "category": category,
                            "quality_status": "rejected",
                            "quality_reason": "empty_content",
                        }
                    )

                    continue



                keep, reason = should_keep(
                    agent,
                    {
                        **item,
                        "category": category,
                    },
                )

                if not keep:

                    rejected.append(
                        {
                            "file": relative,
                            "category": category,
                            "quality_status": "filtered",
                            "quality_reason": reason,
                            "content_length": len(
                                content
                            ),
                        }
                    )

                    continue


                extra = str(
                    item.get(
                        "page",
                        item.get(
                            "jsonl_line",
                            item.get(
                                "id",
                                "",
                            ),
                        ),
                    )
                )

                source_name = item.get(
                    "source"
                )

                if not source_name:

                    if len(
                        path.parts
                    ) > len(
                        source_root.parts
                    ):

                        source_name = path.parts[
                            len(
                                source_root.parts
                            )
                        ]

                    else:

                        source_name = "unknown"

                document_id = (
                    create_document_id(
                        agent=agent,
                        source=str(
                            source_name
                        ),
                        file=relative,
                        content=content,
                        extra=extra,
                    )
                )

                content_hash = hashlib.sha256(
                    content.encode("utf-8")
                ).hexdigest()


                excluded_fields = {
                    "_rejected",
                    "content",
                }

                if is_oatutor:

                    excluded_fields.update(
                        {
                            "stepBody",
                            "stepAnswer",
                            "stepTitle",
                            "answerLatex",
                            "solution",
                            "explanation",
                        }
                    )

                record = {
                    "id": document_id,
                    "agent": agent,
                    "category": category,
                    "source": source_name,
                    **{
                        key: value
                        for key, value
                        in item.items()
                        if key not in excluded_fields
                    },
                    "content": content,
                    "content_hash": content_hash,
                    "quality_status": item.get(
                        "quality_status",
                        "valid",
                    ),
                }

                documents.append(
                    record
                )

        except Exception as exc:

            rejected.append(
                {
                    "file": relative,
                    "category": category,
                    "quality_status": "error",
                    "quality_reason": "extraction_error",
                    "error": str(exc),
                }
            )

            stats["errors"] += 1



        temporary = source_output.with_suffix(
            ".tmp"
        )

        with temporary.open(
            "w",
            encoding="utf-8",
        ) as output:

            for document in documents:

                output.write(
                    json.dumps(
                        document,
                        ensure_ascii=False,
                    )
                    + "\n"
                )

        temporary.replace(
            source_output
        )


        temporary_rejected = (
            source_rejected.with_suffix(
                ".tmp"
            )
        )

        with temporary_rejected.open(
            "w",
            encoding="utf-8",
        ) as output:

            for item in rejected:

                output.write(
                    json.dumps(
                        item,
                        ensure_ascii=False,
                    )
                    + "\n"
                )

        temporary_rejected.replace(
            source_rejected
        )


        files_state[relative] = {
            "size": signature["size"],
            "mtime_ns": signature["mtime_ns"],
            "source_output": (
                source_output
                .relative_to(
                    processed_root
                )
                .as_posix()
            ),
            "documents": len(
                documents
            ),
            "rejected": len(
                rejected
            ),
        }

        stats[
            "documents_created"
        ] += len(documents)

        stats[
            "rejected_created"
        ] += len(rejected)


        if (
            stats["processed_files"] % 100
            == 0
        ):

            save_checkpoint(
                checkpoint_path,
                checkpoint,
            )

            print(
                f"[checkpoint] "
                f"processed={stats['processed_files']:,} "
                f"skipped={stats['skipped']:,} "
                f"documents={stats['documents_created']:,}"
            )



    for relative in list(
        files_state
    ):

        if relative in current_files:
            continue

        old_state = files_state.pop(
            relative
        )

        old_output = (
            processed_root
            / old_state.get(
                "source_output",
                "",
            )
        )

        if old_output.exists():
            old_output.unlink()

        old_rejected = (
            source_output_root
            / (
                f"{source_output_key(relative)}"
                ".rejected.jsonl"
            )
        )

        if old_rejected.exists():
            old_rejected.unlink()

        stats["removed"] += 1


    changed = (
        force
        or stats["processed_files"] > 0
        or stats["removed"] > 0
    )


    document_count = 0
    rejected_count = 0

    if changed:

        document_count = (
            rebuild_combined_output(
                files_state=files_state,
                processed_root=processed_root,
                source_output_root=source_output_root,
                output_path=output_path,
            )
        )

        rejected_count = (
            rebuild_rejected_output(
                files_state=files_state,
                source_output_root=source_output_root,
                rejected_path=rejected_path,
            )
        )


        indexed_documents = (
            rebuild_document_index(
                output_path=output_path,
                index_path=document_index_path,
            )
        )

        print(
            f"[document-index] "
            f"unique_documents={indexed_documents:,}"
        )

    else:


        if output_path.exists():

            with output_path.open(
                "r",
                encoding="utf-8",
            ) as file:

                document_count = sum(
                    1
                    for line in file
                    if line.strip()
                )

        if rejected_path.exists():

            with rejected_path.open(
                "r",
                encoding="utf-8",
            ) as file:

                rejected_count = sum(
                    1
                    for line in file
                    if line.strip()
                )


    if not document_index_path.exists():

        indexed_documents = (
            rebuild_document_index(
                output_path=output_path,
                index_path=document_index_path,
            )
        )

        print(
            f"[document-index] "
            f"created={indexed_documents:,}"
        )


    checkpoint["version"] = 2
    checkpoint["agent"] = agent

    checkpoint["last_run"] = {
        "processed_files": stats[
            "processed_files"
        ],
        "skipped": stats[
            "skipped"
        ],
        "documents": document_count,
        "rejected": rejected_count,
        "removed": stats[
            "removed"
        ],
    }

    save_checkpoint(
        checkpoint_path,
        checkpoint,
    )


    print()
    print("=" * 80)
    print(
        "SOULAGENT KNOWLEDGE PROCESSOR"
    )
    print("=" * 80)

    print(
        f"Agent             : {agent}"
    )

    print(
        f"Sources            : {source_root}"
    )

    print(
        f"Processed output   : {output_path}"
    )

    print(
        f"Files processed    : "
        f"{stats['processed_files']:,}"
    )

    print(
        f"Files skipped      : "
        f"{stats['skipped']:,}"
    )

    print(
        f"Documents          : "
        f"{document_count:,}"
    )

    print(
        f"Rejected           : "
        f"{rejected_count:,}"
    )

    print(
        f"Removed sources    : "
        f"{stats['removed']:,}"
    )

    print(
        f"Errors             : "
        f"{stats['errors']:,}"
    )

    print(
        f"Checkpoint         : "
        f"{checkpoint_path}"
    )

    print(
        f"Changed             : "
        f"{changed}"
    )

    print("=" * 80)


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Universal SoulAgent knowledge "
            "extractor and normalizer."
        )
    )

    parser.add_argument(
        "--agent",
        required=True,
        choices=sorted(
            SUPPORTED_AGENTS
        ),
        help="Agent knowledge corpus.",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Reprocess every source file "
            "for this agent."
        ),
    )

    args = parser.parse_args()

    process_agent(
        agent=args.agent,
        force=args.force,
    )


if __name__ == "__main__":
    main()