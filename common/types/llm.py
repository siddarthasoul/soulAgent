from pydantic import BaseModel, Field


class LLMRequest(BaseModel):
    task: str
    messages: list[dict[str, str]] = Field(default_factory=list)
    thinking: bool = False
    response_format: str | None = None


class LLMResponse(BaseModel):
    task: str
    content: str
    model: str

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    latency_ms: float = 0.0