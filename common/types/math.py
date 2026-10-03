from typing import Any

from pydantic import BaseModel, Field


class MathToolRequest(BaseModel):
    tool: str
    operation: str
    arguments: dict[str, Any] = Field(default_factory=dict)