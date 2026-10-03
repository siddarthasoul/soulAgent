from common.prompts.agents.chat import CHAT_AGENT_SYSTEM_PROMPT
from common.types.llm import LLMRequest
from src.providers.base import LLMProvider
from src.providers.ollama import OllamaProvider


class ChatAgent:

    def __init__(
        self,
        provider: LLMProvider | None = None,
    ) -> None:
        self.provider = provider or OllamaProvider()

    def run(
        self,
        user_message: str,
    ) -> str:

        request = LLMRequest(
            task="Answer the user's message naturally.",
            messages=[
                {
                    "role": "system",
                    "content": CHAT_AGENT_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ],
        )

        response = self.provider.generate(request)

        return response.content
