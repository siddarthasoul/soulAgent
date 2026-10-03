from typing import Any

from pydantic import BaseModel, Field

class PhysicsToolRequest(BaseModel):
    operation: str
    arguments: dict[str, Any] = Field(
    default_factory=dict
)