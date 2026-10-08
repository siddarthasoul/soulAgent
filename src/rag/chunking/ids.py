from __future__ import annotations

import hashlib
import uuid


def create_chunk_id(
    content_hash: str,
    chunk_index: int,
) -> str:

    value = f"{content_hash}:{chunk_index}"

    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()

    return str(
        uuid.UUID(digest[:32])
    )