import ast
import math
import operator


class CalculatorTool:

    _BINARY_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.FloorDiv: operator.floordiv,
    }

    _UNARY_OPERATORS = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    _FUNCTIONS = {
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "abs": abs,
        "floor": math.floor,
        "ceil": math.ceil,
    }

    _CONSTANTS = {
        "pi": math.pi,
        "e": math.e,
    }

    def run(self, expression: str) -> float:
        """
        Evaluate a mathematical expression safely.

        Examples:
            2 + 3
            (10 + 5) * 2
            sqrt(144)
            sin(pi / 2)
            log10(1000)
            2 ** 10
        """

        if not expression.strip():
            raise ValueError("Expression cannot be empty.")

        try:
            tree = ast.parse(expression, mode="eval")
        except SyntaxError as exc:
            raise ValueError(
                "Invalid mathematical expression."
            ) from exc

        result = self._evaluate(tree.body)

        if not math.isfinite(result):
            raise ValueError(
                "Calculation produced a non-finite result."
            )

        return float(result)

    def _evaluate(self, node: ast.AST) -> float:

        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                raise ValueError(
                    "Boolean values are not allowed."
                )

            if isinstance(node.value, (int, float)):
                return float(node.value)

            raise ValueError(
                "Only numeric values are allowed."
            )

        if isinstance(node, ast.Name):
            if node.id in self._CONSTANTS:
                return self._CONSTANTS[node.id]

            raise ValueError(
                f"Unknown constant: {node.id}"
            )

        if isinstance(node, ast.BinOp):
            function = self._BINARY_OPERATORS.get(
                type(node.op)
            )

            if function is None:
                raise ValueError(
                    f"Unsupported operator: "
                    f"{type(node.op).__name__}"
                )

            left = self._evaluate(node.left)
            right = self._evaluate(node.right)

            try:
                result = function(left, right)
            except (ZeroDivisionError, OverflowError) as exc:
                raise ValueError(
                    "Invalid mathematical operation."
                ) from exc

            return float(result)

        if isinstance(node, ast.UnaryOp):
            function = self._UNARY_OPERATORS.get(
                type(node.op)
            )

            if function is None:
                raise ValueError(
                    f"Unsupported unary operator: "
                    f"{type(node.op).__name__}"
                )

            value = self._evaluate(node.operand)

            return float(function(value))

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError(
                    "Only supported mathematical functions "
                    "can be called."
                )

            function = self._FUNCTIONS.get(node.func.id)

            if function is None:
                raise ValueError(
                    f"Unsupported function: {node.func.id}"
                )

            if node.keywords:
                raise ValueError(
                    "Keyword arguments are not supported."
                )

            arguments = [
                self._evaluate(argument)
                for argument in node.args
            ]

            try:
                result = function(*arguments)
            except (ValueError, TypeError, ZeroDivisionError, OverflowError) as exc:
                raise ValueError(
                    "Invalid arguments for mathematical function."
                ) from exc

            return float(result)

        raise ValueError(
            f"Unsupported expression: "
            f"{type(node).__name__}"
        )
