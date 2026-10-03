from pathlib import Path

from src.tools.visualization.structuredVisual.diagram.models import (
    FlowRequest,
)
from src.tools.visualization.structuredVisual.diagram.renderer import (
    FlowRenderer,
)
from src.tools.visualization.structuredVisual.diagram.validators import (
    validate_flow,
)


class FlowTool:

    def __init__(self) -> None:
        self.renderer = FlowRenderer()

    def run(
        self,
        request: FlowRequest,
        output_path: str | Path,
    ) -> Path:

        validate_flow(request)

        return self.renderer.render(
            request=request,
            output_path=output_path,
        )