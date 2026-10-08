from __future__ import annotations

from typing import Any, Callable


class ToolRegistry:
    """
    Central registry for tools available to the agent system.

    This first version only handles registration and lookup.
    Execution will be added separately.
    """

    def __init__(self) -> None:
        self._tools: dict[str, Callable[..., Any]] = {}

    def register(
        self,
        name: str,
        tool: Callable[..., Any],
    ) -> None:
        if name in self._tools:
            raise ValueError(
                f"Tool already registered: {name}"
            )

        self._tools[name] = tool

    def get(
        self,
        name: str,
    ) -> Callable[..., Any]:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(
                f"Tool not found: {name}"
            ) from exc

    def has(self, name: str) -> bool:
        return name in self._tools

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())