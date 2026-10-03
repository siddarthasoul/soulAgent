from pathlib import Path

from common.types.visualization import VisualizationRequest
from src.tools.visualization.structuredVisual.graph.models import GraphRequest
from src.tools.visualization.structuredVisual.graph.tool import GraphTool
from src.tools.visualization.structuredVisual.diagram.models import FlowRequest
from src.tools.visualization.structuredVisual.diagram.tool import FlowTool
from src.tools.visualization.structuredVisual.process.models import ProcessRequest
from src.tools.visualization.structuredVisual.process.tool import ProcessTool
from src.tools.visualization.structuredVisual.sequence.models import SequenceRequest
from src.tools.visualization.structuredVisual.sequence.tool import SequenceTool


class VisualizationTool:

    def __init__(self) -> None:
        self.graph_tool = GraphTool()
        self.flow_tool = FlowTool()
        self.process_tool = ProcessTool()
        self.sequence_tool = SequenceTool()

    def run(
        self,
        request: VisualizationRequest,
        output_path: str | Path,
    ) -> Path:

        if request.type == "math_graph":

            graph_request = GraphRequest.model_validate(
                {
                    **request.content,
                    "title": request.title,
                }
            )

            return self.graph_tool.run(
                request=graph_request,
                output_path=output_path,
            )

        if request.type == "flow":

            flow_request = FlowRequest.model_validate(
                {
                    **request.content,
                    "title": request.title,
                }
            )

            return self.flow_tool.run(
                request=flow_request,
                output_path=output_path,
            )

        if request.type == "process":

            process_request = ProcessRequest.model_validate(
                {
                    **request.content,
                    "title": request.title,
                }
            )

            return self.process_tool.run(
                request=process_request,
                output_path=output_path,
            )

        if request.type == "sequence":

            sequence_request = SequenceRequest.model_validate(
                {
                    **request.content,
                    "title": request.title,
                }
            )

            return self.sequence_tool.run(
                request=sequence_request,
                output_path=output_path,
            )

        raise ValueError(
            f"Unsupported visualization type: {request.type}"
        )
