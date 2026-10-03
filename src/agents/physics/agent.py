import json
import re

from common.prompts.agents.physics import PHYSICS_AGENT_SYSTEM_PROMPT
from common.types.llm import LLMRequest
from common.types.physics import PhysicsToolRequest

from src.providers.base import LLMProvider
from src.providers.ollama import OllamaProvider
from src.tools.physics.tool import PhysicsTool


class PhysicsAgent:

    def __init__(
        self,
        provider: LLMProvider | None = None,
    ) -> None:
        self.provider = provider or OllamaProvider()
        self.physics_tool = PhysicsTool()

    def run(
        self,
        user_message: str,
        use_tool: bool = False,
    ) -> str:

        if use_tool:
            tool_request = self._extract_kinematics(user_message)

            if tool_request is not None:
                result = self.physics_tool.solve(
                    **tool_request.arguments
                )
                return str(result)

        request = LLMRequest(
            task="Solve or explain the user's physics problem.",
            messages=[
                {
                    "role": "system",
                    "content": PHYSICS_AGENT_SYSTEM_PROMPT,
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

        result = self.physics_tool.solve(
            **tool_request.arguments
        )

        return str(result)

    @staticmethod
    def _extract_kinematics(
        user_message: str,
    ) -> PhysicsToolRequest | None:

        pattern = re.search(
            r"from\s+(-?\d+(?:\.\d+)?)\s*m/s"
            r"\s+to\s+(-?\d+(?:\.\d+)?)\s*m/s"
            r"\s+in\s+(-?\d+(?:\.\d+)?)\s*seconds?",
            user_message,
            re.IGNORECASE,
        )

        if not pattern:
            return None

        initial_velocity = float(pattern.group(1))
        final_velocity = float(pattern.group(2))
        time = float(pattern.group(3))

        return PhysicsToolRequest(
            operation="solve",
            arguments={
                "expression": "(vf - vi) / t",
                "values": {
                    "vi": initial_velocity,
                    "vf": final_velocity,
                    "t": time,
                },
                "units": {
                    "vi": "m/s",
                    "vf": "m/s",
                    "t": "s",
                },
            },
        )

    @staticmethod
    def _parse_tool_request(
        content: str,
    ) -> PhysicsToolRequest:

        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "PhysicsAgent could not parse "
                "a valid JSON tool request."
            ) from exc

        return PhysicsToolRequest.model_validate(data)
