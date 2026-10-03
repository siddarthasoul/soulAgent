import json

from common.prompts.agents.chemistry import CHEMISTRY_AGENT_SYSTEM_PROMPT
from common.types.chemistry import ChemistryToolRequest
from common.types.llm import LLMRequest

from src.providers.base import LLMProvider
from src.providers.ollama import OllamaProvider
from src.tools.chemistry.tool import ChemistryTool


class ChemistryAgent:

    def __init__(
        self,
        provider: LLMProvider | None = None,
    ) -> None:

        self.provider = provider or OllamaProvider()
        self.chemistry_tool = ChemistryTool()

    def run(
        self,
        user_message: str,
        use_tool: bool = False,
    ) -> str:

        if use_tool:
            task = "Create a valid ChemistryTool request for the user's chemistry task."
        else:
            task = "Explain the user's chemistry question directly. Do not create a tool request."

        request = LLMRequest(
            task=task,
            messages=[
                {
                    "role": "system",
                    "content": CHEMISTRY_AGENT_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ],
        )

        response = self.provider.generate(request)

        if not use_tool:
            return response.content

        tool_request = self._parse_tool_request(
            response.content
        )

        if tool_request.operation == "solve":
            result = self.chemistry_tool.solve(
                **tool_request.arguments
            )

        elif tool_request.operation == "visualize":
            result = self.chemistry_tool.visualize(
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
            raise ValueError( "ChemistryAgent received empty or invalid LLM content." )

        try:
            data = json.loads(content)

        except json.JSONDecodeError as exc:
            raise ValueError(
                "ChemistryAgent could not parse a valid JSON "
                "tool request."
            ) from exc

        return ChemistryToolRequest.model_validate(data)