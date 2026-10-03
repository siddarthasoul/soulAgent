from pathlib import Path

from src.tools.visualization.structuredVisual.sequence.models import (
    SequenceRequest,
)
from src.tools.visualization.structuredVisual.sequence.renderer import (
    SequenceRenderer,
)
from src.tools.visualization.structuredVisual.sequence.validators import (
    validate_sequence,
)


class SequenceTool:

    def __init__(self) -> None:

        self.renderer = SequenceRenderer()

    def run(
        self,
        request: SequenceRequest,
        output_path: str | Path,
    ) -> Path:

        validate_sequence(request)

        return self.renderer.render(
            request=request,
            output_path=output_path,
        )