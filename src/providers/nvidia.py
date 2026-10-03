import time

from openai import OpenAI

from common.core.env import env
from common.types.llm import LLMRequest, LLMResponse
from src.providers.base import (
    LLMAuthenticationError,
    LLMConnectionError,
    LLMProvider,
    LLMRequestError,
    LLMTimeoutError,
)


class NvidiaProvider(LLMProvider):

    def __init__(self) -> None:
        self.client = OpenAI(
            base_url=env.NVIDIA_BASE_URL,
            api_key=env.NVIDIA_API_KEY,
        )

        self.model = env.NVIDIA_MODEL

    def generate(self, request: LLMRequest) -> LLMResponse:
        start_time = time.perf_counter()

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=request.messages,
                temperature=1,
                top_p=0.95,
                max_tokens=16384,
                extra_body={
                    "chat_template_kwargs": {
                        "enable_thinking": True
                    }
                },
                stream=False,
            )

        except Exception as exc:
            self._handle_error(exc)

        latency_ms = (time.perf_counter() - start_time) * 1000

        usage = completion.usage

        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0

        return LLMResponse(
            task=request.task,
            content=completion.choices[0].message.content or "",
            model=completion.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=latency_ms,
        )

    @staticmethod
    def _handle_error(exc: Exception) -> None:

        error_name = type(exc).__name__

        if error_name == "AuthenticationError":
            raise LLMAuthenticationError(
                "NVIDIA API authentication failed."
            ) from exc

        if error_name in {"APIConnectionError", "ConnectionError"}:
            raise LLMConnectionError(
                "Could not connect to NVIDIA API."
            ) from exc

        if error_name == "APITimeoutError":
            raise LLMTimeoutError(
                "NVIDIA API request timed out."
            ) from exc

        raise LLMRequestError(
            f"NVIDIA API request failed: {exc}"
        ) from exc