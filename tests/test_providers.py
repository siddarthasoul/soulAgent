from src.providers.ollama import OllamaProvider
from src.providers.gemini import GeminiProvider
from src.providers.nvidia import NvidiaProvider

from common.types.llm import LLMRequest


request = LLMRequest(
    task="Explain what a neural network is in simple words.",
    messages=[
        {
            "role": "user",
            "content": "Explain what a neural network is in simple words.",
        }
    ],
)


def test_provider(name, provider):
    print(f"\n{'=' * 50}")
    print(f"Testing: {name}")
    print("=" * 50)

    try:
        response = provider.generate(request)

        print("SUCCESS")
        print(f"Model:          {response.model}")
        print(f"Task:           {response.task}")
        print(f"Response:       {response.content}")
        print(f"Input tokens:   {response.input_tokens}")
        print(f"Output tokens:  {response.output_tokens}")
        print(f"Total tokens:   {response.total_tokens}")
        print(f"Latency:        {response.latency_ms:.2f} ms")

    except Exception as exc:
        print("FAILED")
        print(f"Error type: {type(exc).__name__}")
        print(f"Error: {exc}")


test_provider("Ollama", OllamaProvider())
test_provider("Gemini", GeminiProvider())
test_provider("NVIDIA", NvidiaProvider())