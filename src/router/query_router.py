import json

from common.prompts.router.query_router import QUERY_ROUTER_SYSTEM_PROMPT
from common.types.llm import LLMRequest
from common.types.router import QueryRoute
from src.providers.base import LLMProvider
from src.providers.ollama import OllamaProvider


class QueryRouter:

    def __init__(self, provider: LLMProvider | None = None) -> None:
        self.provider = provider or OllamaProvider()

    def route(self, user_message: str) -> QueryRoute:

        request = LLMRequest(
            task="Classify the user's query.",
            messages=[
                {
                    "role": "system",
                    "content": QUERY_ROUTER_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ],
        )

        response = self.provider.generate(request)

        data = json.loads(response.content)

        return QueryRoute.model_validate(data)