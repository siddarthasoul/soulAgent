import json

from common.prompts.agents.math import MATH_AGENT_SYSTEM_PROMPT
from common.types.llm import LLMRequest
from common.types.math import MathToolRequest

from src.providers.base import LLMProvider
from src.providers.ollama import OllamaProvider
from src.core.context import AgentContext

class MathAgent:

    def __init__(
        self,
        provider: LLMProvider | None = None,
    ) -> None:
        self.provider = provider or OllamaProvider()


    def run(
        self,
        user_message: str,
        use_tool: bool = False,
        context: AgentContext | None = None,
    ) -> str:

        messages = [
            {
                "role": "system",
                "content": MATH_AGENT_SYSTEM_PROMPT,
            }
        ]

    # Use prepared RAG context only for explanations.
        if not use_tool and context is not None:
            rag_context = context.metadata.get(
                "rag_context",
                "",
            )

            if rag_context:
                messages.append(
                    {
                        "role": "system",
                        "content": (
                            "Use the following internal mathematical "
                            "knowledge when relevant:\n\n"
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
            task="Solve or explain the user's mathematical problem.",
            messages=messages,
        )

        response = self.provider.generate(request)

        if not use_tool:
            return response.content

        if context is None or not context.tools.has("math"):
            raise RuntimeError(
                "Math tool is not available in AgentContext."
            )

        tool_request = self._parse_tool_request(
            response.content
        )

        math_tool = context.tools.get("math")

        result = math_tool.run(
            tool=tool_request.tool,
            operation=tool_request.operation,
            arguments=tool_request.arguments,
        )

        return str(result)



    @staticmethod
    def _parse_tool_request(
        content: str,
    ) -> MathToolRequest:

        try:
            start = content.index("{")
            end = content.rindex("}") + 1

            json_content = content[start:end]

            data = json.loads(json_content)

        except (ValueError, json.JSONDecodeError) as exc:
            raise ValueError(
                "MathAgent could not extract valid JSON "
                "from the LLM response."
            ) from exc

        return MathToolRequest.model_validate(data)
