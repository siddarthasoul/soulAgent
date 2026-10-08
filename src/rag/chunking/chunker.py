from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Chunk:
    content: str
    chunk_index: int


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[Chunk]:
    if not text.strip():
        return []

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    words = text.split()

    chunks: list[Chunk] = []

    start = 0
    chunk_index = 0
    step = chunk_size - overlap

    while start < len(words):
        end = min(start + chunk_size, len(words))

        content = " ".join(words[start:end]).strip()

        if content:
            chunks.append(
                Chunk(
                    content=content,
                    chunk_index=chunk_index,
                )
            )

        chunk_index += 1
        start += step

    return chunks