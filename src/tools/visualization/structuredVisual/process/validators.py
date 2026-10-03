from src.tools.visualization.structuredVisual.process.models import (
    ProcessRequest,
)


def validate_process(
    request: ProcessRequest,
) -> None:

    if not request.steps:
        raise ValueError(
            "Process diagram requires at least one step."
        )

    step_ids = {
        step.id
        for step in request.steps
    }

    if len(step_ids) != len(request.steps):
        raise ValueError(
            "Process step IDs must be unique."
        )

    for step in request.steps:

        if not step.label.strip():
            raise ValueError(
                f"Process step '{step.id}' "
                "must have a label."
            )