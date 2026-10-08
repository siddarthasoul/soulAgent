from sentence_transformers import SentenceTransformer

from src.rag.retrieval.retriever import Retriever
from src.rag.reranking.reranker import Reranker

# Temporary baseline threshold.
# This is NOT a production relevance threshold.
EVALUATION_THRESHOLD = 0.0


def evaluate_results(
    results: list,
    expected: str,
) -> dict:

    if not results:
        passed = expected == "OUT_OF_KNOWLEDGE_BASE"

        return {
            "expected": expected,
            "top_score": None,
            "average_score": None,
            "minimum_score": None,
            "passed": passed,
        }

    scores = [
        float(item["rerank_score"])
        for item in results
    ]

    top_score = max(scores)
    average_score = sum(scores) / len(scores)
    minimum_score = min(scores)

    if expected == "IN_KNOWLEDGE_BASE":
        passed = top_score >= EVALUATION_THRESHOLD
    else:
        passed = top_score < EVALUATION_THRESHOLD

    return {
        "expected": expected,
        "top_score": top_score,
        "average_score": average_score,
        "minimum_score": minimum_score,
        "passed": passed,
    }


def print_results(
    retriever: Retriever,
    query: str,
    expected: str,
    top_k: int = 5,
    candidate_k: int = 20,
) -> dict:

    results = retriever.search(
        query=query,
        top_k=top_k,
        candidate_k=candidate_k,
    )

    evaluation = evaluate_results(
        results=results,
        expected=expected,
    )

    print("\n" + "-" * 80)
    print("RETRIEVED RESULTS")
    print("-" * 80)

    print(f"Expected      : {expected}")

    if not results:
        print("No results found.")

        print(
            f"Evaluation    : "
            f"{'PASS' if evaluation['passed'] else 'FAIL'}"
        )

        return evaluation

    print(f"Top score     : {evaluation['top_score']:.4f}")
    print(f"Average score : {evaluation['average_score']:.4f}")
    print(f"Minimum score : {evaluation['minimum_score']:.4f}")

    print(
        f"Evaluation    : "
        f"{'PASS' if evaluation['passed'] else 'FAIL'}"
    )

    for index, item in enumerate(results, start=1):

        result = item["result"]
        score = float(item["rerank_score"])
        payload = result.payload

        print(f"\n[RESULT {index}]")
        print(f"Rerank score : {score:.4f}")
        print(f"Agent        : {payload.get('agent', 'N/A')}")
        print(f"Category     : {payload.get('category', 'N/A')}")
        print(f"Source       : {payload.get('source', 'N/A')}")

        content = payload.get("content", "").strip()

        print("\nContent:")
        print(content[:700])

    return evaluation


def print_summary(
    evaluations: list[dict],
) -> None:

    total = len(evaluations)

    if total == 0:
        return

    passed = sum(
        1
        for evaluation in evaluations
        if evaluation["passed"]
    )

    failed = total - passed

    in_kb = [
        evaluation
        for evaluation in evaluations
        if evaluation["expected"] == "IN_KNOWLEDGE_BASE"
    ]

    out_kb = [
        evaluation
        for evaluation in evaluations
        if evaluation["expected"] == "OUT_OF_KNOWLEDGE_BASE"
    ]

    in_kb_passed = sum(
        1
        for evaluation in in_kb
        if evaluation["passed"]
    )

    out_kb_passed = sum(
        1
        for evaluation in out_kb
        if evaluation["passed"]
    )

    overall_accuracy = (passed / total) * 100

    in_kb_accuracy = (
        (in_kb_passed / len(in_kb)) * 100
        if in_kb
        else 0.0
    )

    out_kb_abstention = (
        (out_kb_passed / len(out_kb)) * 100
        if out_kb
        else 0.0
    )

    valid_scores = [
        evaluation["top_score"]
        for evaluation in evaluations
        if evaluation["top_score"] is not None
    ]

    average_top_score = (
        sum(valid_scores) / len(valid_scores)
        if valid_scores
        else 0.0
    )

    print("\n\n")
    print("=" * 80)
    print("RAG EVALUATION SUMMARY")
    print("=" * 80)

    print(f"\nThreshold used        : {EVALUATION_THRESHOLD:.4f}")

    print("\nOverall:")
    print(f"  Total queries       : {total}")
    print(f"  Passed              : {passed}")
    print(f"  Failed              : {failed}")
    print(f"  Accuracy            : {overall_accuracy:.2f}%")

    print("\nIn-Knowledge-Base:")
    print(f"  Queries             : {len(in_kb)}")
    print(f"  Passed              : {in_kb_passed}")
    print(f"  Retrieval success   : {in_kb_accuracy:.2f}%")

    print("\nOut-of-Knowledge-Base:")
    print(f"  Queries             : {len(out_kb)}")
    print(f"  Correctly rejected  : {out_kb_passed}")
    print(f"  Abstention rate     : {out_kb_abstention:.2f}%")

    print("\nScore:")
    print(f"  Average top score   : {average_top_score:.4f}")

    print("\nPer-query result:")

    for index, evaluation in enumerate(evaluations, start=1):

        status = "PASS" if evaluation["passed"] else "FAIL"

        top_score = evaluation["top_score"]

        if top_score is None:
            score_text = "N/A"
        else:
            score_text = f"{top_score:.4f}"

        print(
            f"  Query {index:02d} | "
            f"{evaluation['expected']:<22} | "
            f"Top: {score_text:>7} | "
            f"{status}"
        )

    print("\n" + "=" * 80)
    print("END OF RAG EVALUATION")
    print("=" * 80)


def main() -> None:

    print("=" * 80)
    print("RAG RETRIEVAL EVALUATION")
    print("=" * 80)

    print("\n[1] Loading embedding model...")

    embedding_model = SentenceTransformer(
        "BAAI/bge-small-en-v1.5",
        device="cuda",
    )

    print("[2] Loading reranker...")

    reranker = Reranker(
        model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
        device="cuda",
    )

    print("[3] Creating retriever...")

    retriever = Retriever(
        model=embedding_model,
        reranker=reranker,
    )

    queries = [

        # ------------------------------------------------------------------
        # IN KNOWLEDGE BASE
        # ------------------------------------------------------------------

        {
            "question": "What is a derivative?",
            "expected": "IN_KNOWLEDGE_BASE",
        },

        {
            "question": "What is the fundamental theorem of calculus?",
            "expected": "IN_KNOWLEDGE_BASE",
        },

        {
            "question": "How are differentiation and integration related?",
            "expected": "IN_KNOWLEDGE_BASE",
        },

        {
            "question": "What is a quadratic equation?",
            "expected": "IN_KNOWLEDGE_BASE",
        },

        {
            "question": "How do you solve a system of linear equations?",
            "expected": "IN_KNOWLEDGE_BASE",
        },

        {
            "question": "What is a polynomial function?",
            "expected": "IN_KNOWLEDGE_BASE",
        },

        {
            "question": "What is the Pythagorean theorem?",
            "expected": "IN_KNOWLEDGE_BASE",
        },

        {
            "question": "How do you calculate the area of a circle?",
            "expected": "IN_KNOWLEDGE_BASE",
        },

        {
            "question": "What is conditional probability?",
            "expected": "IN_KNOWLEDGE_BASE",
        },

        {
            "question": (
                "What is the difference between independent "
                "and dependent events?"
            ),
            "expected": "IN_KNOWLEDGE_BASE",
        },

        {
            "question": (
                "How is calculus used to describe motion "
                "and acceleration?"
            ),
            "expected": "IN_KNOWLEDGE_BASE",
        },

        {
            "question": (
                "How is Newton's second law related "
                "to derivatives?"
            ),
            "expected": "IN_KNOWLEDGE_BASE",
        },

        {
            "question": (
                "How can integration be used to calculate "
                "displacement?"
            ),
            "expected": "IN_KNOWLEDGE_BASE",
        },

        {
            "question": (
                "What is the latest version of the "
                "Python programming language?"
            ),
            "expected": "IN_KNOWLEDGE_BASE",
        },

        # ------------------------------------------------------------------
        # OUT OF KNOWLEDGE BASE
        # ------------------------------------------------------------------

        {
            "question": "Who won the FIFA World Cup in 2026?",
            "expected": "OUT_OF_KNOWLEDGE_BASE",
        },

        {
            "question": (
                "What is the current stock price of NVIDIA?"
            ),
            "expected": "OUT_OF_KNOWLEDGE_BASE",
        },

        {
            "question": (
                "What happened in the latest SpaceX launch?"
            ),
            "expected": "OUT_OF_KNOWLEDGE_BASE",
        },

        {
            "question": (
                "What is today's weather in London?"
            ),
            "expected": "OUT_OF_KNOWLEDGE_BASE",
        },

        {
            "question": (
                "Who is the current president of France?"
            ),
            "expected": "OUT_OF_KNOWLEDGE_BASE",
        },
    ]

    evaluations = []

    for number, item in enumerate(queries, start=1):

        query = item["question"]
        expected = item["expected"]

        print("\n\n")
        print("=" * 80)
        print(f"QUERY {number}/{len(queries)}")
        print("=" * 80)

        print(f"\nQuestion:\n{query}")

        evaluation = print_results(
            retriever=retriever,
            query=query,
            expected=expected,
            top_k=5,
            candidate_k=20,
        )

        evaluations.append(evaluation)

    print_summary(evaluations)


if __name__ == "__main__":
    main()