import json
import re

from common.prompts.agents.physics import PHYSICS_AGENT_SYSTEM_PROMPT
from common.types.llm import LLMRequest
from common.types.physics import PhysicsToolRequest

from src.providers.base import LLMProvider
from src.providers.ollama import OllamaProvider
from src.core.context import AgentContext


class PhysicsAgent:

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

        physics_tool = None

        if context is not None and context.tools.has("physics"):
            physics_tool = context.tools.get("physics")
 
        

        if use_tool:

            if physics_tool is None:
                raise RuntimeError( "Physics tool is not available in AgentContext." )

            tool_request = self._extract_kinematics(user_message)

            if tool_request is not None:
                result = physics_tool.solve(
                    **tool_request.arguments
                )
                return str(result)

        messages = [ { "role": "system", "content": PHYSICS_AGENT_SYSTEM_PROMPT, } ]

        if not use_tool and context is not None:
            rag_context = context.metadata.get( "rag_context", "", )

            if rag_context:
                messages.append( { 
                    "role":
                      "system", "content":
                        ( "Use the following internal physics " "knowledge when relevant:\n\n"
                          f"{rag_context}" ), 
                          } )

        messages.append( { "role": "user", "content": user_message, } )

        request = LLMRequest(
            task=(
                "Solve the user's physics problem using a PhysicsTool request."
                if use_tool
                else "Explain the user's physics question directly. "
                    "Do not create a tool request."
            ),
            messages=messages
        )

        response = self.provider.generate(request)

        if not use_tool:
            return response.content

        tool_request = self._parse_tool_request(
            response.content
        )

        result = physics_tool.solve(
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
