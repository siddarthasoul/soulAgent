import json

from common.prompts.agents.math import MATH_AGENT_SYSTEM_PROMPT
from common.types.llm import LLMRequest
from common.types.math import MathToolRequest

from src.providers.base import LLMProvider
from src.providers.ollama import OllamaProvider
from src.tools.calculator.tool import MathTool


class MathAgent:

    def __init__(
        self,
        provider: LLMProvider | None = None,
    ) -> None:
        self.provider = provider or OllamaProvider()
        self.math_tool = MathTool()

    def run(
        self,
        user_message: str,
        use_tool: bool = False,
    ) -> str:

        request = LLMRequest(
            task="Solve or explain the user's mathematical problem.",
            messages=[
                {
                    "role": "system",
                    "content": MATH_AGENT_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ],
        )

        response = self.provider.generate(request)

        # print("MathAgent received response from LLM:")
        # print(response)



        if not use_tool:
            return response.content
   
        # print("=" * 80)
        # print("MATH AGENT RAW LLM RESPONSE")
        # print("=" * 80)
        # print(response.content)
        # print("=" * 80)

        tool_request = self._parse_tool_request(
            response.content
        )

        result = self.math_tool.run(
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
