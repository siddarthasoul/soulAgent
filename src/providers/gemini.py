import time

from google import genai
from google.genai import types

from common.core.env import env
from common.types.llm import LLMRequest, LLMResponse

from src.providers.base import (
    LLMAuthenticationError,
    LLMConnectionError,
    LLMProvider,
    LLMRequestError,
    LLMTimeoutError,
)


class GeminiProvider(LLMProvider):

    def __init__(self) -> None:
        self.model = env.GEMINI_MODEL
        self.client = genai.Client(
            api_key=env.GEMINI_API_KEY
        )

    def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:

        start_time = time.perf_counter()

        try:
            system_instruction = None
            contents = []

            for message in request.messages:
                role = message["role"]
                content = message["content"]

                if role == "system":
                    system_instruction = content

                elif role == "user":
                    contents.append(
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_text(
                                    text=content
                                )
                            ],
                        )
                    )

                elif role == "assistant":
                    contents.append(
                        types.Content(
                            role="model",
                            parts=[
                                types.Part.from_text(
                                    text=content
                                )
                            ],
                        )
                    )

            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type=(
                    "application/json"
                    if request.response_format == "json"
                    else None
                ),
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )

        except Exception as exc:
            self._handle_error(exc)

        latency_ms = (
            time.perf_counter() - start_time
        ) * 1000

        usage = response.usage_metadata

        input_tokens = (
            usage.prompt_token_count
            if usage and usage.prompt_token_count
            else 0
        )

        output_tokens = (
            usage.candidates_token_count
            if usage and usage.candidates_token_count
            else 0
        )

        return LLMResponse(
            task=request.task,
            content=response.text or "",
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=latency_ms,
        )

    @staticmethod
    def _handle_error(
        exc: Exception,
    ) -> None:

        error_name = type(exc).__name__

        if error_name in {
            "AuthenticationError",
            "PermissionDeniedError",
        }:
            raise LLMAuthenticationError(
                "Gemini API authentication failed."
            ) from exc

        if error_name in {
            "APIConnectionError",
            "ConnectionError",
        }:
            raise LLMConnectionError(
                "Could not connect to Gemini API."
            ) from exc

        if error_name in {
            "APITimeoutError",
            "TimeoutError",
        }:
            raise LLMTimeoutError(
                "Gemini API request timed out."
            ) from exc

        raise LLMRequestError(
            f"Gemini API request failed: {exc}"
        ) from exc