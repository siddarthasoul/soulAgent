from pydantic import BaseModel


class FlowNode(BaseModel):
    id: str
    label: str


class FlowEdge(BaseModel):
    source: str
    target: str
    label: str | None = None


class FlowRequest(BaseModel):
    nodes: list[FlowNode]
    edges: list[FlowEdge]

    title: str | None = None