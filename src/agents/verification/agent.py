import json
from common.prompts.agents.verification import (
    VERIFICATION_AGENT_SYSTEM_PROMPT,
)
from common.types.llm import LLMRequest
from common.types.verification import VerificationResult
from src.providers.base import LLMProvider
from src.providers.nvidia import NvidiaProvider


class VerificationAgent:
    def __init__(
        self,
        provider: LLMProvider | None = None,
    ) -> None:
        self.provider = provider or NvidiaProvider()

    def verify(
        self,
        query: str,
        result: str,
    ) -> VerificationResult:

        request = LLMRequest(
            task=(
                "Verify the result against the user's query. "
                "Return a repair instruction if it is incorrect."
            ),
            response_format="json",
            messages=[
                {
                    "role": "system",
                    "content": VERIFICATION_AGENT_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        f"User query:\n{query}\n\n"
                        f"Result to verify:\n{result}"
                    ),
                },
            ],
        )

        response = self.provider.generate(request)

        data = json.loads(response.content)

        return VerificationResult.model_validate(data)