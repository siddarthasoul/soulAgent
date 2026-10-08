import json
from pathlib import Path

from common.prompts.agents.visualization import (
    VISUALIZATION_AGENT_SYSTEM_PROMPT,
)
from common.types.llm import LLMRequest
from common.types.visualization import VisualizationRequest

from src.providers.base import LLMProvider
from src.providers.ollama import OllamaProvider
from src.core.context import AgentContext



class VisualizationAgent:

    def __init__(
        self,
        provider: LLMProvider | None = None,
    ) -> None:
        self.provider = provider or OllamaProvider()

    def run(
        self,
        query: str,
        output_path: str | Path,
        context: AgentContext,
    ) -> Path:


        visualization_tool = context.tools.get("visual")

        

        request = LLMRequest(
            task="Create a structured visualization request.",
            messages=[
                {
                    "role": "system",
                    "content": VISUALIZATION_AGENT_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": query,
                },
            ],
        )

        response = self.provider.generate(request)

        visualization_request = self._parse_request(
            response.content
        )

        return visualization_tool.run(
            request=visualization_request,
            output_path=output_path,
        )

    @staticmethod
    def _parse_request(
        content: str,
    ) -> VisualizationRequest:

        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "VisualizationAgent received invalid JSON from the LLM."
            ) from exc

        return VisualizationRequest.model_validate(data)