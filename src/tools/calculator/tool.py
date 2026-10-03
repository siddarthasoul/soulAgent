from typing import Any

from src.tools.calculator.AlgebraTool.tool import AlgebraTool
from src.tools.calculator.CalculatorTool.tool import CalculatorTool
from src.tools.calculator.CalculusTool.tool import CalculusTool
from src.tools.calculator.MatrixTool.tool import MatrixTool
from src.tools.calculator.VectorTool.tool import VectorTool


class MathTool:

    def __init__(self) -> None:
        self.calculator = CalculatorTool()
        self.algebra = AlgebraTool()
        self.calculus = CalculusTool()
        self.vector = VectorTool()
        self.matrix = MatrixTool()

    def run(
        self,
        tool: str,
        operation: str,
        arguments: dict[str, Any],
    ) -> Any:

        self._validate(tool, operation, arguments)

        handler = self._get_handler(tool)

        method = getattr(handler, operation)

        return method(**arguments)

    def _get_handler(self, tool: str) -> Any:

        handlers = {
            "calculator": self.calculator,
            "algebra": self.algebra,
            "calculus": self.calculus,
            "vector": self.vector,
            "matrix": self.matrix,
        }

        handler = handlers.get(tool)

        if handler is None:
            raise ValueError(
                f"Unsupported math tool: {tool}"
            )

        return handler

    def _validate(
        self,
        tool: str,
        operation: str,
        arguments: dict[str, Any],
    ) -> None:

        if not isinstance(tool, str) or not tool.strip():
            raise ValueError(
                "Tool name is required."
            )

        if not isinstance(operation, str) or not operation.strip():
            raise ValueError(
                "Operation is required."
            )

        if not isinstance(arguments, dict):
            raise ValueError(
                "Arguments must be a dictionary."
            )

        handler = self._get_handler(tool)

        if not hasattr(handler, operation):
            raise ValueError(
                f"Unsupported operation '{operation}' "
                f"for tool '{tool}'."
            )

        method = getattr(handler, operation)

        if not callable(method):
            raise ValueError(
                f"'{operation}' is not a callable operation."
            )