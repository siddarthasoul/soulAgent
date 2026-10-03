from pathlib import Path

from src.tools.visualization.structuredVisual.process.models import (
    ProcessRequest,
)
from src.tools.visualization.structuredVisual.process.renderer import (
    ProcessRenderer,
)
from src.tools.visualization.structuredVisual.process.validators import (
    validate_process,
)


class ProcessTool:

    def __init__(self) -> None:

        self.renderer = ProcessRenderer()

    def run(
        self,
        request: ProcessRequest,
        output_path: str | Path,
    ) -> Path:

        validate_process(request)

        return self.renderer.render(
            request=request,
            output_path=output_path,
        )