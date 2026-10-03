from src.tools.visualization.structuredVisual.sequence.models import (
    SequenceRequest,
)


def validate_sequence(
    request: SequenceRequest,
) -> None:

    if not request.participants:
        raise ValueError(
            "Sequence diagram requires at least one participant."
        )

    participant_ids = {
        participant.id
        for participant in request.participants
    }

    if len(participant_ids) != len(
        request.participants
    ):
        raise ValueError(
            "Sequence participant IDs must be unique."
        )

    for message in request.messages:

        if message.source not in participant_ids:
            raise ValueError(
                f"Unknown source participant: "
                f"{message.source}"
            )

        if message.target not in participant_ids:
            raise ValueError(
                f"Unknown target participant: "
                f"{message.target}"
            )

        if not message.message.strip():
            raise ValueError(
                "Sequence message cannot be empty."
            )