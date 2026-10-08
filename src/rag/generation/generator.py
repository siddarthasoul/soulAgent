from __future__ import annotations

from common.types.llm import LLMRequest
from src.providers.base import LLMProvider

from common.prompts.rag.rag import RAG_SYSTEM_PROMPT



class RAGGenerator:

    def __init__(
        self,
        provider: LLMProvider,
    ) -> None:
        self.provider = provider

    def generate(
        self,
        query: str,
        context: str,
    ) -> str:

        query = query.strip()
        context = context.strip()

        if not query:
            return ""

        request = LLMRequest(
            task="Answer the user's question using retrieved knowledge.",
            messages=[
                {
                    "role": "system",
                    "content": RAG_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        "Retrieved knowledge:\n\n"
                        f"{context}\n\n"
                        "User question:\n\n"
                        f"{query}"
                    ),
                },
            ],
        )

        response = self.provider.generate(request)

        return response.content