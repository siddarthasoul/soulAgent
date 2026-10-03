import sympy as sp

from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)


_TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
)


class AlgebraTool:

    def simplify(
        self,
        expression: str,
    ) -> str:

        expr = self._parse(expression)

        return str(sp.simplify(expr))

    def expand(
        self,
        expression: str,
    ) -> str:

        expr = self._parse(expression)

        return str(sp.expand(expr))

    def factor(
        self,
        expression: str,
    ) -> str:

        expr = self._parse(expression)

        return str(sp.factor(expr))

    def solve(
        self,
        equation: str,
        variable: str = "x",
    ) -> list[str]:

        symbol = self._symbol(variable)

        equation = equation.strip()

        if not equation:
            raise ValueError(
                "Equation cannot be empty."
            )

        if "=" in equation:
            left, right = equation.split("=", 1)

            expr = (
                self._parse(left)
                - self._parse(right)
            )
        else:
            expr = self._parse(equation)

        solutions = sp.solve(expr, symbol)

        return [str(solution) for solution in solutions]

    def substitute(
        self,
        expression: str,
        values: dict[str, float],
    ) -> str:

        expr = self._parse(expression)

        substitutions = {
            self._symbol(name): value
            for name, value in values.items()
        }

        result = expr.subs(substitutions)

        return str(result)

    def _parse(
        self,
        expression: str,
    ) -> sp.Expr:

        if not isinstance(expression, str):
            raise ValueError(
                "Expression must be a string."
            )

        if not expression.strip():
            raise ValueError(
                "Expression cannot be empty."
            )

        expression = expression.replace("^", "**")
        
        try:
            return parse_expr(
                expression,
                transformations=_TRANSFORMATIONS,
            )

        except (
            SyntaxError,
            TypeError,
            ValueError,
            sp.SympifyError,
        ) as exc:

            raise ValueError(
                "Invalid algebraic expression."
            ) from exc

    @staticmethod
    def _symbol(
        name: str,
    ) -> sp.Symbol:

        if not isinstance(name, str):
            raise ValueError(
                "Variable name must be a string."
            )

        if not name.isidentifier():
            raise ValueError(
                f"Invalid variable name: {name}"
            )

        return sp.Symbol(name)