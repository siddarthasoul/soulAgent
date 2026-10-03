import ast
import re
from typing import Any

import pint

from src.tools.calculator.tool import MathTool


class PhysicsTool:

    _IDENTIFIER_PATTERN = re.compile(
        r"^[A-Za-z_][A-Za-z0-9_]*$"
    )

    def __init__(self) -> None:
        self.math = MathTool()
        self.units = pint.UnitRegistry()

    def solve(
        self,
        expression: str,
        values: dict[str, float],
        units: dict[str, str] | None = None,
    ) -> Any:

        self._validate_expression(expression)
        self._validate_values(values)

        if units is None:
            return self._solve_without_units(
                expression=expression,
                values=values,
            )

        return self._solve_with_units(
            expression=expression,
            values=values,
            units=units,
        )

    def _solve_without_units(
        self,
        expression: str,
        values: dict[str, float],
    ) -> float:

        resolved_expression = self._resolve_variables(
            expression=expression,
            values=values,
        )

        return self.math.run(
            tool="calculator",
            operation="run",
            arguments={
                "expression": resolved_expression,
            },
        )

    def _solve_with_units(
        self,
        expression: str,
        values: dict[str, float],
        units: dict[str, str],
    ) -> Any:

        self._validate_units(
            values=values,
            units=units,
        )

        quantities = {
            name: value * self.units(units[name])
            for name, value in values.items()
        }

        tree = ast.parse(
            expression,
            mode="eval",
        )

        self._validate_unit_expression(tree)

        return self._evaluate_quantity(
            tree.body,
            quantities,
        )

    def _evaluate_quantity(
        self,
        node: ast.AST,
        values: dict[str, Any],
    ) -> Any:

        if isinstance(node, ast.Constant):

            if isinstance(node.value, bool):
                raise ValueError(
                    "Boolean values are not allowed."
                )

            if isinstance(node.value, (int, float)):
                return node.value

            raise ValueError(
                "Only numeric constants are allowed."
            )

        if isinstance(node, ast.Name):

            if node.id in values:
                return values[node.id]

            raise ValueError(
                f"Unknown variable: {node.id}"
            )

        if isinstance(node, ast.BinOp):

            left = self._evaluate_quantity(
                node.left,
                values,
            )

            right = self._evaluate_quantity(
                node.right,
                values,
            )

            if isinstance(node.op, ast.Add):
                return left + right

            if isinstance(node.op, ast.Sub):
                return left - right

            if isinstance(node.op, ast.Mult):
                return left * right

            if isinstance(node.op, ast.Div):
                return left / right

            if isinstance(node.op, ast.Pow):

                if not isinstance(right, (int, float)):
                    raise ValueError(
                        "Exponent must be dimensionless."
                    )

                return left ** right

            raise ValueError(
                f"Unsupported operator: "
                f"{type(node.op).__name__}"
            )

        if isinstance(node, ast.UnaryOp):

            value = self._evaluate_quantity(
                node.operand,
                values,
            )

            if isinstance(node.op, ast.UAdd):
                return +value

            if isinstance(node.op, ast.USub):
                return -value

            raise ValueError(
                f"Unsupported unary operator: "
                f"{type(node.op).__name__}"
            )

        raise ValueError(
            f"Unsupported expression: "
            f"{type(node).__name__}"
        )

    def _validate_unit_expression(
        self,
        tree: ast.Expression,
    ) -> None:

        for node in ast.walk(tree):

            if isinstance(node, ast.Call):
                raise ValueError(
                    "Functions are not supported in "
                    "unit-aware expressions yet."
                )

            if isinstance(node, ast.Name):

                if not self._IDENTIFIER_PATTERN.match(
                    node.id
                ):
                    raise ValueError(
                        f"Invalid variable name: {node.id}"
                    )

    def _validate_units(
        self,
        values: dict[str, float],
        units: dict[str, str],
    ) -> None:

        if not isinstance(units, dict):
            raise ValueError(
                "Units must be a dictionary."
            )

        missing = values.keys() - units.keys()

        if missing:
            raise ValueError(
                f"Missing units for variables: "
                f"{sorted(missing)}"
            )

        for name, unit in units.items():

            if name not in values:
                raise ValueError(
                    f"Unit provided for unknown variable: "
                    f"{name}"
                )

            if not isinstance(unit, str) or not unit.strip():
                raise ValueError(
                    f"Invalid unit for '{name}'."
                )

            try:
                self.units(unit)
            except Exception as exc:
                raise ValueError(
                    f"Invalid unit '{unit}' "
                    f"for '{name}'."
                ) from exc

    def _validate_expression(
        self,
        expression: str,
    ) -> None:

        if not isinstance(expression, str):
            raise ValueError(
                "Expression must be a string."
            )

        if not expression.strip():
            raise ValueError(
                "Expression cannot be empty."
            )

    def _validate_values(
        self,
        values: dict[str, float],
    ) -> None:

        if not isinstance(values, dict):
            raise ValueError(
                "Values must be a dictionary."
            )

        for name, value in values.items():

            if not isinstance(name, str):
                raise ValueError(
                    "Variable names must be strings."
                )

            if not self._IDENTIFIER_PATTERN.match(name):
                raise ValueError(
                    f"Invalid variable name: {name}"
                )

            if isinstance(value, bool) or not isinstance(
                value,
                (int, float),
            ):
                raise ValueError(
                    f"Value for '{name}' must be numeric."
                )

    def _resolve_variables(
        self,
        expression: str,
        values: dict[str, float],
    ) -> str:

        tree = ast.parse(
            expression,
            mode="eval",
        )

        names = {
            node.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Name)
        }

        allowed_names = {
            "pi",
            "e",
            "sqrt",
            "sin",
            "cos",
            "tan",
            "asin",
            "acos",
            "atan",
            "log",
            "log10",
            "exp",
            "abs",
            "floor",
            "ceil",
        }

        variables = names - allowed_names

        missing = variables - values.keys()

        if missing:
            raise ValueError(
                f"Missing values for variables: "
                f"{sorted(missing)}"
            )

        resolved_expression = expression

        for name, value in values.items():

            resolved_expression = re.sub(
                rf"\b{re.escape(name)}\b",
                str(value),
                resolved_expression,
            )

        return resolved_expression