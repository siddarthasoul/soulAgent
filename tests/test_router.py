from src.router.query_router import QueryRouter


router = QueryRouter()

queries = [
    "What is a neural network?",
    "Solve 2x + 5 = 15.",
    "What is the derivative of x^2?",
    "What are the latest changes in Qwen3?",
    "Why is my Docker container unable to connect to PostgreSQL?",
    "Write a Python function to reverse a linked list.",
    "Explain how TCP three-way handshake works.",
    "Research the latest NVIDIA Nemotron models and compare their context lengths.",
    "Build a system that reads PDFs, creates embeddings, stores them in Qdrant, and answers questions.",
    "Hi bro, how are you?",
]


for i, query in enumerate(queries, start=1):
    print("\n" + "=" * 70)
    print(f"TEST {i}")
    print("=" * 70)
    print(f"Query: {query}")

    response = router.route(query)

    print("\nRouter output:")
    print(response.content)