from src.rag.generation.generator import RAGGenerator
from src.providers.ollama import OllamaProvider


def main() -> None:
    generator = RAGGenerator(
        provider=OllamaProvider(),
    )

    query = (
        "What is Newton's second law of motion, "
        "and what does each term in F = ma represent?"
    )

    context = """
Newton's second law of motion states that the net force acting
on an object is equal to the product of its mass and acceleration.

The equation is:

F = ma

F represents the net force acting on the object.
m represents the mass of the object.
a represents the acceleration of the object.
"""

    answer = generator.generate(
        query=query,
        context=context,
    )

    print("=" * 80)
    print("RAG GENERATOR TEST")
    print("=" * 80)
    print(f"\nQuery:\n{query}")
    print(f"\nAnswer:\n{answer}")


if __name__ == "__main__":
    main()
