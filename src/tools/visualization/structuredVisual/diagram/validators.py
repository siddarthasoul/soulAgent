from src.tools.visualization.structuredVisual.diagram.models import (
    FlowRequest,
)


def validate_flow(request: FlowRequest) -> None:

    if not request.nodes:
        raise ValueError("Flow diagram requires at least one node.")

    node_ids = {node.id for node in request.nodes}

    if len(node_ids) != len(request.nodes):
        raise ValueError("Flow node IDs must be unique.")

    for edge in request.edges:

        if edge.source not in node_ids:
            raise ValueError(
                f"Unknown source node: {edge.source}"
            )

        if edge.target not in node_ids:
            raise ValueError(
                f"Unknown target node: {edge.target}"
            )