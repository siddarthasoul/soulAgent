from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import sympy as sp

from src.tools.visualization.structuredVisual.graph.models import (
    GraphRequest,
    XYData,
    BarData,
)


class GraphRenderer:

    def render(
        self,
        request: GraphRequest,
        output_path: str | Path,
    ) -> Path:

        output_path = Path(output_path)

        fig, ax = plt.subplots()

        if request.type == "function":
            self._render_function(ax, request)

        elif request.type == "line":
            self._render_line(ax, request.data)

        elif request.type == "scatter":
            self._render_scatter(ax, request.data)

        elif request.type == "bar":
            self._render_bar(ax, request.data)

        elif request.type == "histogram":
            self._render_histogram(ax, request.data)

        self._configure_axes(ax, request)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        fig.savefig(
            output_path,
            bbox_inches="tight",
        )

        plt.close(fig)

        return output_path

    def _render_function(
        self,
        ax,
        request: GraphRequest,
    ) -> None:

        if request.x_min is None or request.x_max is None:
            raise ValueError(
                "Function graph requires x_min and x_max."
            )

        expression_text = request.data.strip()

        # Convert "y = x**2" → "x**2"
        if "=" in expression_text:
            expression_text = expression_text.split(
                "=",
                1,
            )[1].strip()


        expression_text = expression_text.replace( "^", "**",)

        x = sp.symbols("x")

        expression = sp.sympify( 
            expression_text, 
            locals={ 
                "x": x, 
                "e": sp.E,
                }, 
            )

        function = sp.lambdify(
            x,
            expression,
            modules=["numpy"],
        )

        x_values = np.linspace(
            request.x_min,
            request.x_max,
            500,
        )

        y_values = function(x_values)

        ax.plot(
            x_values,
            y_values,
        )

    def _render_line(
        self,
        ax,
        data: XYData,
    ) -> None:
        ax.plot(data.x, data.y)

    def _render_scatter(
        self,
        ax,
        data: XYData,
    ) -> None:
        ax.scatter(data.x, data.y)

    def _render_bar(
        self,
        ax,
        data: BarData,
    ) -> None:
        ax.bar(data.labels, data.values)

    def _render_histogram(
        self,
        ax,
        data: list[float],
    ) -> None:
        ax.hist(data)

    def _configure_axes(
        self,
        ax,
        request: GraphRequest,
    ) -> None:

        if request.title:
            ax.set_title(request.title)

        if request.x_label:
            ax.set_xlabel(request.x_label)

        if request.y_label:
            ax.set_ylabel(request.y_label)

        if (
            request.x_min is not None
            or request.x_max is not None
        ):
            ax.set_xlim(
                request.x_min,
                request.x_max,
            )

        if (
            request.y_min is not None
            or request.y_max is not None
        ):
            ax.set_ylim(
                request.y_min,
                request.y_max,
            )

        if not request.legend:
            legend = ax.get_legend()

            if legend:
                legend.remove()
