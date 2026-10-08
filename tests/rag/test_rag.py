from sentence_transformers import SentenceTransformer

from src.providers.ollama import OllamaProvider
from src.rag.generation.generator import RAGGenerator
from src.rag.retrieval.retriever import Retriever
from src.rag.reranking.reranker import Reranker
from src.rag.relevance import RelevanceGate
from src.rag.service import RAGService


def print_retrieved_results(
    retriever: Retriever,
    query: str,
    top_k: int = 5,
    candidate_k: int = 20,
) -> None:

    results = retriever.search(
        query=query,
        top_k=top_k,
        candidate_k=candidate_k,
    )

    print("\n" + "-" * 80)
    print("RETRIEVED KNOWLEDGE")
    print("-" * 80)

    if not results:
        print("No relevant chunks found.")
        return

    for index, item in enumerate(results, start=1):

        result = item["result"]
        score = item["rerank_score"]
        payload = result.payload

        print(f"\n[RESULT {index}]")
        print(f"Rerank score : {score:.4f}")
        print(f"Agent        : {payload.get('agent', 'N/A')}")
        print(f"Category     : {payload.get('category', 'N/A')}")
        print(f"Source       : {payload.get('source', 'N/A')}")

        content = payload.get("content", "").strip()

        print("\nContent:")
        print(content[:1000])


def main() -> None:

    print("=" * 80)
    print("GENERIC RAG MULTI-QUERY TEST")
    print("=" * 80)

    # ------------------------------------------------------------------
    # 1. Embedding model
    # ------------------------------------------------------------------

    print("\n[1] Loading embedding model...")

    embedding_model = SentenceTransformer(
        "BAAI/bge-small-en-v1.5",
        device="cuda",
    )

    # ------------------------------------------------------------------
    # 2. Reranker
    # ------------------------------------------------------------------

    print("[2] Loading reranker...")

    reranker = Reranker(
        model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
        device="cuda",
    )

    # ------------------------------------------------------------------
    # 3. Retriever
    # ------------------------------------------------------------------

    print("[3] Creating retriever...")

    retriever = Retriever(
        model=embedding_model,
        reranker=reranker,
    )

    # ------------------------------------------------------------------
    # 4. Generator
    # ------------------------------------------------------------------

    print("[4] Creating RAG generator...")

    relevance_gate = RelevanceGate(min_score=0.0)
    # ------------------------------------------------------------------
    # 5. RAG service
    # ------------------------------------------------------------------

    rag = RAGService(
        retriever=retriever,
        relevance_gate=relevance_gate,
    )

    # ------------------------------------------------------------------
    # 6. Test queries
    # ------------------------------------------------------------------

    queries = [
        # Basic mathematical knowledge
        "What is calculus?",

        # Conceptual
        "What is the difference between differential calculus and integral calculus?",

        # Deeper mathematical reasoning
        "Why is the derivative interpreted as the instantaneous rate of change?",

        # Textbook-style
        "What is a limit in calculus and why is it important?",

        # Relationship between concepts
        "How are differentiation and integration related?",

        # Physics + mathematics
        "How is calculus used to describe motion and acceleration?",

        # Agent-style research question
        "Explain Newton's second law mathematically and describe how calculus is used to derive the relationship between force, velocity, and position.",

        # Multi-concept reasoning
        "A particle moves with changing velocity. Which mathematical concepts are needed to determine its acceleration and displacement?",

        # Potentially harder textbook question
        "Explain the fundamental theorem of calculus and why it connects differentiation and integration.",
    ]

    # ------------------------------------------------------------------
    # 7. Run tests
    # ------------------------------------------------------------------

    for number, query in enumerate(queries, start=1):

        print("\n\n")
        print("=" * 80)
        print(f"QUERY {number}")
        print("=" * 80)

        print(query)

        # --------------------------------------------------------------
        # Retrieval inspection
        # --------------------------------------------------------------

        print_retrieved_results(
            retriever=retriever,
            query=query,
            top_k=5,
            candidate_k=20,
        )

        # --------------------------------------------------------------
        # RAG generation
        # --------------------------------------------------------------

        print("\n" + "-" * 80)
        print("RAG ANSWER")
        print("-" * 80)

        answer = rag.generate(
            query=query,
            top_k=5,
            candidate_k=20,
        )

        print(answer)

    print("\n")
    print("=" * 80)
    print("ALL RAG TESTS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()