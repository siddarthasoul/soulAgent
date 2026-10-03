from enum import Enum
from pydantic import BaseModel


class VisualizationType(str, Enum):
    MATH_GRAPH = "math_graph"
    FLOW = "flow"
    SEQUENCE = "sequence"
    PROCESS = "process"


class VisualizationRequest(BaseModel):
    type: VisualizationType
    title: str
    content: dict