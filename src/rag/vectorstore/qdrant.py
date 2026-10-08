from __future__ import annotations

from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models
from common.core.env import env
from qdrant_client.http import models
from typing import Any

COLLECTION_NAME = "soulagent_knowledge"
VECTOR_SIZE = 384


def create_knowledge_collection() -> None:
    """Create the SoulAgent knowledge collection."""
    client = get_client()

    try:
        if collection_exists(COLLECTION_NAME):
            return

        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=VECTOR_SIZE,
                distance=models.Distance.COSINE,
            ),
        )
    finally:
        client.close()





def get_client() -> QdrantClient:
    """Create and return a Qdrant client."""
    return QdrantClient(
        host=env.QDRANT_HOST,
        port=env.QDRANT_PORT,
    )


def check_connection() -> bool:
    """Return True when Qdrant is reachable."""
    client = get_client()

    try:
        client.get_collections()
        return True
    finally:
        client.close()


def collection_exists(collection_name: str) -> bool:
    """Check whether a collection exists."""
    client = get_client()

    try:
        collections = client.get_collections()

        return any(
            collection.name == collection_name
            for collection in collections.collections
        )
    finally:
        client.close()



def delete_collection(collection_name: str) -> None:
    """Delete a collection."""
    client = get_client()

    try:
        if collection_exists(collection_name):
            client.delete_collection(collection_name=collection_name)
    finally:
        client.close()


def get_collection_info(collection_name: str) -> Any:
    """Return information about a collection."""
    client = get_client()

    try:
        return client.get_collection(
            collection_name=collection_name,
        )
    finally:
        client.close()


def count_points(collection_name: str) -> int:
    """Return the number of points stored in a collection."""
    client = get_client()

    try:
        result = client.count(
            collection_name=collection_name,
            exact=True,
        )
        return result.count
    finally:
        client.close()



def upsert_point(
    point_id: str | int,
    vector: list[float],
    payload: dict[str, Any],
) -> None:
    """Insert or update one vector point."""
    client = get_client()

    try:
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            ],
        )
    finally:
        client.close()


def upsert_points(
    points: list[models.PointStruct],
) -> None:
    """Insert or update multiple vector points."""
    if not points:
        return

    client = get_client()
    try:
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
        )
    finally:
        client.close()
        

def search_points(
    vector: list[float],
    limit: int = 5,
    agent: str | None = None,
    category: str | None = None,
) -> list[Any]:
    client = get_client()

    try:
        filter_conditions = []

        if agent is not None:
            filter_conditions.append(
                models.FieldCondition(
                    key="agent",
                    match=models.MatchValue(value=agent),
                )
            )

        if category is not None:
            filter_conditions.append(
                models.FieldCondition(
                    key="category",
                    match=models.MatchValue(value=category),
                )
            )

        query_filter = None

        if filter_conditions:
            query_filter = models.Filter(
                must=filter_conditions,
            )

        result = client.query_points(
            collection_name=COLLECTION_NAME,
            query=vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )

        return result.points

    finally:
        client.close()