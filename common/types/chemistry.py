from typing import Any

from pydantic import BaseModel, Field


class ChemistryToolRequest(BaseModel):
    operation: str
    arguments: dict[str, Any] = Field(
        default_factory=dict
    )