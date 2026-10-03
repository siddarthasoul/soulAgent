import sympy as sp


class CalculusTool:


    def derivative(
        self,
        expression: str,
        variable: str = "x",
        order: int = 1,
    ) -> str:
        if order < 1:
            raise ValueError(
                "Derivative order must be at least 1."
            )

        expr = self._parse(expression)
        symbol = self._symbol(variable)

        result = sp.diff(
            expr,
            symbol,
            order,
        )

        return str(result)

    def integral(
        self,
        expression: str,
        variable: str = "x",
    ) -> str:
        expr = self._parse(expression)
        symbol = self._symbol(variable)

        result = sp.integrate(
            expr,
            symbol,
        )

        return str(result)

    def definite_integral(
        self,
        expression: str,
        lower: float,
        upper: float,
        variable: str = "x",
    ) -> str:
        expr = self._parse(expression)
        symbol = self._symbol(variable)

        result = sp.integrate(
            expr,
            (symbol, lower, upper),
        )

        return str(result)

    def limit(
        self,
        expression: str,
        variable: str,
        point: float,
        direction: str = "both",
    ) -> str:
        expr = self._parse(expression)
        symbol = self._symbol(variable)

        if direction not in {"both", "+", "-"}:
            raise ValueError(
                "Direction must be 'both', '+', or '-'."
            )

        if direction == "both":
            result = sp.limit(
                expr,
                symbol,
                point,
            )
        else:
            result = sp.limit(
                expr,
                symbol,
                point,
                dir=direction,
            )

        return str(result)

    def _parse(self, expression: str) -> sp.Expr:
        if not expression.strip():
            raise ValueError(
                "Expression cannot be empty."
            )

        try:
            return sp.sympify(expression)
        except (sp.SympifyError, TypeError) as exc:
            raise ValueError(
                "Invalid mathematical expression."
            ) from exc

    @staticmethod
    def _symbol(name: str) -> sp.Symbol:
        if not name.isidentifier():
            raise ValueError(
                f"Invalid variable name: {name}"
            )

        return sp.Symbol(name)
