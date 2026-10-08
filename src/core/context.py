from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from src.tools.registry import ToolRegistry


@dataclass
class AgentContext:
    request_id: str | None = None
    user_message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    tools: ToolRegistry = field(default_factory=ToolRegistry)