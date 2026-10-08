from common.prompts.agents.chat import CHAT_AGENT_SYSTEM_PROMPT
from common.types.llm import LLMRequest

from src.providers.base import LLMProvider
from src.providers.ollama import OllamaProvider
from src.core.context import AgentContext


class ChatAgent:

    def __init__(
        self,
        provider: LLMProvider | None = None,
    ) -> None:
        self.provider = provider or OllamaProvider()

    def run(
        self,
        user_message: str,
        context: AgentContext | None = None,
    ) -> str:

        rag_context = ""

        if context is not None:
            rag_context = context.metadata.get(
                "rag_context",
                "",
            )

        messages = [
            {
                "role": "system",
                "content": CHAT_AGENT_SYSTEM_PROMPT,
            }
        ]

        if rag_context:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "Use the following internal knowledge "
                        "when relevant:\n\n"
                        f"{rag_context}"
                    ),
                }
            )

        messages.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        request = LLMRequest(
            task="Answer the user's message using the provided knowledge when relevant.",
            messages=messages,
        )

        response = self.provider.generate(request)

        return response.content
