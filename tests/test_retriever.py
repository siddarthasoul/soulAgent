from sentence_transformers import SentenceTransformer

from src.rag.retrieval.retriever import Retriever
from src.rag.reranking.reranker import Reranker


MODEL_NAME = "BAAI/bge-small-en-v1.5"


def main() -> None:
    model = SentenceTransformer(
        "BAAI/bge-small-en-v1.5",
        device="cuda",
    )

    reranker = Reranker(
        device="cuda",
    )

    retriever = Retriever(
        model=model,
        reranker=reranker,
    )

    query = "What is Newton's second law?"

    results = retriever.search(
        query=query,
        top_k=5,
        candidate_k=50,
    )

    print("\n" + "=" * 80)
    print("QUERY")
    print("=" * 80)
    print(query)

    print("\n" + "=" * 80)
    print("RERANKED RESULTS")
    print("=" * 80)

    for index, item in enumerate(results, start=1):
        result = item["result"]
        rerank_score = item["rerank_score"]

        print(f"\n--- Result {index} ---")
        print(f"Vector score : {result.score:.4f}")
        print(f"Rerank score : {rerank_score:.4f}")
        print(f"Agent        : {result.payload.get('agent')}")
        print(f"Category     : {result.payload.get('category')}")
        print(f"Source       : {result.payload.get('source')}")
        print(f"Chunk        : {result.payload.get('chunk_index')}")
        print(f"Content:\n{result.payload.get('content')}")


if __name__ == "__main__":
    main()