import time

import httpx

from common.core.env import env
from common.types.llm import LLMRequest, LLMResponse
from src.providers.base import (
    LLMConnectionError,
    LLMProvider,
    LLMRequestError,
    LLMTimeoutError,
)


class OllamaProvider(LLMProvider):

    def __init__(self) -> None:
        self.base_url = env.OLLAMA_BASE_URL
        self.model = env.OLLAMA_MODEL

    def generate(self, request: LLMRequest) -> LLMResponse:
        start_time = time.perf_counter()

        payload = {
            "model": self.model,
            "messages": request.messages,
            "stream": False,
        }

        try:
            response = httpx.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120.0,
            )

            response.raise_for_status()

            data = response.json()

        except httpx.TimeoutException as exc:
            raise LLMTimeoutError(
                "Ollama request timed out."
            ) from exc

        except httpx.ConnectError as exc:
            raise LLMConnectionError(
                "Could not connect to Ollama."
            ) from exc

        except httpx.HTTPStatusError as exc:
            raise LLMRequestError(
                f"Ollama returned HTTP {exc.response.status_code}."
            ) from exc

        except httpx.RequestError as exc:
            raise LLMRequestError(
                f"Ollama request failed: {exc}"
            ) from exc

        latency_ms = (time.perf_counter() - start_time) * 1000

        input_tokens = data.get("prompt_eval_count", 0)
        output_tokens = data.get("eval_count", 0)

        return LLMResponse(
            task=request.task,
            content=data["message"]["content"],
            model=data["model"],
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=latency_ms,
        )