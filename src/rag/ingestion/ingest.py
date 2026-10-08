from __future__ import annotations

import json
from pathlib import Path

import torch
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer

from src.rag.chunking.chunker import chunk_text
from src.rag.chunking.ids import create_chunk_id
from src.rag.vectorstore.qdrant import upsert_points


PROJECT_ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE_ROOT = PROJECT_ROOT / "data" / "knowledge"

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBED_BATCH_SIZE = 128
QDRANT_BATCH_SIZE = 256
CHECKPOINT_FILE = "ingestion_checkpoint.json"


def find_document_files() -> list[Path]:
    """Find every processed documents.jsonl under data/knowledge."""
    return sorted(KNOWLEDGE_ROOT.glob("*/processed/documents.jsonl"))


def load_checkpoint(processed_dir: Path) -> set[str]:
    """Load already-ingested document hashes."""
    checkpoint_path = processed_dir / CHECKPOINT_FILE

    if not checkpoint_path.exists():
        return set()

    with checkpoint_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return set(data.get("content_hashes", []))


def save_checkpoint(
    processed_dir: Path,
    content_hashes: set[str],
) -> None:

    checkpoint_path = processed_dir / CHECKPOINT_FILE

    data = {
        "version": 1,
        "content_hashes": sorted(content_hashes),
    }

    temporary_path = checkpoint_path.with_suffix(".tmp")

    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    temporary_path.replace(checkpoint_path)


def ingest_documents() -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"

    model = SentenceTransformer(
        EMBEDDING_MODEL,
        device=device,
    )

    print(f"Embedding device: {model.device}", flush=True)

    total_documents = 0
    total_skipped = 0
    total_chunks = 0
    total_batches = 0

    document_files = find_document_files()

    print(f"Knowledge files found: {len(document_files)}", flush=True)

    for documents_path in document_files:
        processed_dir = documents_path.parent
        checkpoint = load_checkpoint(processed_dir)

        print()
        print("=" * 70, flush=True)
        print(f"Processing: {documents_path}", flush=True)
        print(f"Checkpoint entries: {len(checkpoint)}", flush=True)
        print("=" * 70, flush=True)

        pending_records: list[dict] = []
        pending_remaining: dict[str, int] = {}

        def flush_pending() -> None:
            nonlocal total_chunks
            nonlocal total_documents
            nonlocal total_batches

            if not pending_records:
                return

            total_batches += 1
            batch_number = total_batches
            batch_size = len(pending_records)

            print()
            print(
                f"[Batch {batch_number}] Starting: {batch_size} chunks",
                flush=True,
            )

            texts = [record["chunk"].content for record in pending_records]

            print(
                f"[Batch {batch_number}] Embedding on {model.device}...",
                flush=True,
            )

            vectors = model.encode(
                texts,
                batch_size=EMBED_BATCH_SIZE,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            )

            print(
                f"[Batch {batch_number}] "
                f"Embedding complete: {len(vectors)} vectors",
                flush=True,
            )

            points = []

            for record, vector in zip(pending_records, vectors):
                chunk = record["chunk"]
                document = record["document"]
                content_hash = record["content_hash"]

                point_id = create_chunk_id(
                    content_hash,
                    chunk.chunk_index,
                )

                payload = {
                    "agent": document["agent"],
                    "category": document["category"],
                    "source": document["source"],
                    "file": document["file"],
                    "document_id": document["id"],
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "content_hash": content_hash,
                }

                points.append(
                    models.PointStruct(
                        id=point_id,
                        vector=vector.tolist(),
                        payload=payload,
                    )
                )

            print(
                f"[Batch {batch_number}] "
                f"Point IDs created: {len(points)}",
                flush=True,
            )

            uploaded_points = 0

            for start in range(0, len(points), QDRANT_BATCH_SIZE):
                batch = points[start:start + QDRANT_BATCH_SIZE]

                print(
                    f"[Batch {batch_number}] "
                    f"Qdrant upsert: {len(batch)} points...",
                    flush=True,
                )

                upsert_points(batch)
                uploaded_points += len(batch)

                print(
                    f"[Batch {batch_number}] "
                    f"Qdrant upsert complete: "
                    f"{uploaded_points}/{len(points)}",
                    flush=True,
                )

            total_chunks += len(points)

            completed_hashes = set()

            for record in pending_records:
                content_hash = record["content_hash"]
                pending_remaining[content_hash] -= 1

                if pending_remaining[content_hash] == 0:
                    completed_hashes.add(content_hash)

            for content_hash in completed_hashes:
                checkpoint.add(content_hash)
                total_documents += 1
                del pending_remaining[content_hash]

            if completed_hashes:
                save_checkpoint(processed_dir, checkpoint)

                print(
                    f"[Batch {batch_number}] "
                    f"Checkpoint saved: {len(checkpoint)} documents",
                    flush=True,
                )

            print(
                f"[Batch {batch_number}] COMPLETE | "
                f"chunks uploaded: {len(points)} | "
                f"total chunks: {total_chunks}",
                flush=True,
            )

            pending_records.clear()

        with documents_path.open("r", encoding="utf-8") as file:
            for line in file:
                document = json.loads(line)

                content = document.get("content", "").strip()
                content_hash = document.get("content_hash")

                if not content or not content_hash:
                    continue

                if content_hash in checkpoint:
                    total_skipped += 1
                    continue

                chunks = chunk_text(
                    content,
                    chunk_size=150,
                    overlap=30,
                )

                if not chunks:
                    continue

                print(
                    f"Document: [{document['agent']}] "
                    f"{document['id']} -> {len(chunks)} chunks",
                    flush=True,
                )

                pending_remaining[content_hash] = len(chunks)

                for chunk in chunks:
                    pending_records.append(
                        {
                            "chunk": chunk,
                            "document": document,
                            "content_hash": content_hash,
                        }
                    )

                    if len(pending_records) >= EMBED_BATCH_SIZE:
                        flush_pending()

        flush_pending()

        print()
        print(f"Finished: {documents_path}", flush=True)
        print(
            f"Checkpoint now contains: {len(checkpoint)} documents",
            flush=True,
        )

    print()
    print("=" * 70)
    print("INGESTION COMPLETE")
    print("=" * 70)
    print(f"Documents ingested : {total_documents}")
    print(f"Documents skipped  : {total_skipped}")
    print(f"Chunks ingested    : {total_chunks}")
    print(f"Embedding batches  : {total_batches}")
    print("=" * 70)


if __name__ == "__main__":
    ingest_documents()
