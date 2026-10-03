from enum import Enum

from pydantic import BaseModel


class GraphType(str, Enum):
    FUNCTION = "function"
    LINE = "line"
    SCATTER = "scatter"
    BAR = "bar"
    HISTOGRAM = "histogram"


class XYData(BaseModel):
    x: list[float]
    y: list[float]


class BarData(BaseModel):
    labels: list[str]
    values: list[float]


class GraphRequest(BaseModel):
    type: GraphType
    data: str | XYData | BarData | list[float]

    x_min: float | None = None
    x_max: float | None = None
    y_min: float | None = None
    y_max: float | None = None

    title: str | None = None
    x_label: str | None = None
    y_label: str | None = None
    legend: bool = True