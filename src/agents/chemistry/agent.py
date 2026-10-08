import json

from common.prompts.agents.chemistry import CHEMISTRY_AGENT_SYSTEM_PROMPT
from common.types.chemistry import ChemistryToolRequest
from common.types.llm import LLMRequest

from src.providers.base import LLMProvider
from src.providers.ollama import OllamaProvider
from src.core.context import AgentContext


class ChemistryAgent:

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

        chemistry_tool = None

        if context is not None and context.tools.has("chemistry"):
            chemistry_tool = context.tools.get("chemistry")

        if use_tool:
            task = (
                "Create a valid ChemistryTool request "
                "for the user's chemistry task."
            )
        else:
            task = (
                "Explain the user's chemistry question directly. "
                "Do not create a tool request."
            )

        messages = [
            {
                "role": "system",
                "content": CHEMISTRY_AGENT_SYSTEM_PROMPT,
            }
        ]

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
                            "Use the following internal chemistry "
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
            task=task,
            messages=messages,
        )

        response = self.provider.generate(request)

        if not use_tool:
            return response.content

        if chemistry_tool is None:
            raise RuntimeError(
                "Chemistry tool is not available in AgentContext."
            )

        tool_request = self._parse_tool_request(
            response.content
        )

        if tool_request.operation == "solve":
            result = chemistry_tool.solve(
                **tool_request.arguments
            )

        elif tool_request.operation == "visualize":
            result = chemistry_tool.visualize(
                **tool_request.arguments
            )

        else:
            raise ValueError(
                f"Unsupported chemistry operation: "
                f"{tool_request.operation}"
            )

        return str(result)

    @staticmethod
    def _parse_tool_request(
        content: str,
    ) -> ChemistryToolRequest:

        if not isinstance(content, str) or not content.strip():
            raise ValueError(
                "ChemistryAgent received empty or invalid LLM content."
            )

        try:
            data = json.loads(content)

        except json.JSONDecodeError as exc:
            raise ValueError(
                "ChemistryAgent could not parse a valid JSON "
                "tool request."
            ) from exc

        return ChemistryToolRequest.model_validate(data)
