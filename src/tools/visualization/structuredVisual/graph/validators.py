from src.tools.visualization.structuredVisual.graph.models import GraphRequest, XYData, BarData


def validate_graph(request: GraphRequest) -> None:

    if request.type == "function":
        if not isinstance(request.data, str) or not request.data.strip():
            raise ValueError("Function graph requires an expression.")

        if request.x_min is None or request.x_max is None:
            raise ValueError("Function graph requires x_min and x_max.")

        if request.x_min >= request.x_max:
            raise ValueError("x_min must be smaller than x_max.")

    elif request.type in {"line", "scatter"}:
        _validate_xy_data(request.data)

    elif request.type == "bar":
        _validate_bar_data(request.data)

    elif request.type == "histogram":
        if not isinstance(request.data, list) or not request.data:
            raise ValueError("Histogram requires a non-empty data list.")


def _validate_xy_data(data: object) -> None:
    if not isinstance(data, XYData):
        raise ValueError("Line and scatter graphs require x/y data.")

    if len(data.x) != len(data.y):
        raise ValueError("x and y must have the same length.")

    if not data.x:
        raise ValueError("Graph data cannot be empty.")


def _validate_bar_data(data: object) -> None:
    if not isinstance(data, BarData):
        raise ValueError("Bar graphs require labels and values.")

    if len(data.labels) != len(data.values):
        raise ValueError("labels and values must have the same length.")

    if not data.labels:
        raise ValueError("Bar data cannot be empty.")