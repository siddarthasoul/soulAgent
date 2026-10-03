from pathlib import Path

from src.tools.visualization.structuredVisual.graph.models import GraphRequest
from src.tools.visualization.structuredVisual.graph.renderer import GraphRenderer
from src.tools.visualization.structuredVisual.graph.validators import validate_graph


class GraphTool:
    def __init__(self) -> None:
        self.renderer = GraphRenderer()

    def run(
        self,
        request: GraphRequest,
        output_path: str | Path,
    ) -> Path:
        validate_graph(request)

        return self.renderer.render(
            request=request,
            output_path=output_path,
        )