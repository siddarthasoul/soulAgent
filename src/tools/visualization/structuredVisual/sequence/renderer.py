from pathlib import Path
from xml.sax.saxutils import escape

from src.tools.visualization.structuredVisual.sequence.models import (
    SequenceRequest,
)


class SequenceRenderer:

    PARTICIPANT_WIDTH = 140
    PARTICIPANT_HEIGHT = 50

    PARTICIPANT_GAP = 80

    TOP_MARGIN = 100
    MESSAGE_GAP = 80

    SIDE_MARGIN = 60

    def render(
        self,
        request: SequenceRequest,
        output_path: str | Path,
    ) -> Path:

        output_path = Path(output_path)

        participant_count = len(
            request.participants
        )

        message_count = len(
            request.messages
        )

        width = self._calculate_width(
            participant_count
        )

        height = self._calculate_height(
            message_count
        )

        participant_positions = (
            self._create_positions(
                request
            )
        )

        svg = []

        svg.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">'
        )

        # ---------------------------------------------------------
        # Background
        # ---------------------------------------------------------

        svg.append(
            '<rect width="100%" height="100%" '
            'fill="white"/>'
        )

        # ---------------------------------------------------------
        # Title
        # ---------------------------------------------------------

        if request.title:

            svg.append(
                f'<text x="{width / 2}" y="35" '
                f'text-anchor="middle" '
                f'font-family="Arial" '
                f'font-size="20" '
                f'font-weight="bold">'
                f'{escape(request.title)}'
                f'</text>'
            )

        # ---------------------------------------------------------
        # Participant boxes
        # ---------------------------------------------------------

        for participant in request.participants:

            x = participant_positions[
                participant.id
            ]

            self._draw_participant(
                svg,
                x,
                participant.label,
            )

        # ---------------------------------------------------------
        # Lifelines
        # ---------------------------------------------------------

        lifeline_top = (
            self.TOP_MARGIN
            + self.PARTICIPANT_HEIGHT
        )

        lifeline_bottom = (
            lifeline_top
            + message_count
            * self.MESSAGE_GAP
            + 40
        )

        for participant in request.participants:

            x = participant_positions[
                participant.id
            ]

            center_x = (
                x
                + self.PARTICIPANT_WIDTH / 2
            )

            svg.append(
                f'<line '
                f'x1="{center_x}" '
                f'y1="{lifeline_top}" '
                f'x2="{center_x}" '
                f'y2="{lifeline_bottom}" '
                f'stroke="#777" '
                f'stroke-width="1" '
                f'stroke-dasharray="6,5"/>'
            )

        # ---------------------------------------------------------
        # Messages
        # ---------------------------------------------------------

        message_y = (
            lifeline_top + 50
        )

        for message in request.messages:

            source_x = (
                participant_positions[
                    message.source
                ]
                + self.PARTICIPANT_WIDTH / 2
            )

            target_x = (
                participant_positions[
                    message.target
                ]
                + self.PARTICIPANT_WIDTH / 2
            )

            self._draw_message(
                svg,
                source_x,
                target_x,
                message_y,
                message.message,
            )

            message_y += self.MESSAGE_GAP

        svg.append("</svg>")

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            "\n".join(svg),
            encoding="utf-8",
        )

        return output_path

    # =============================================================
    # Participant positions
    # =============================================================

    def _create_positions(
        self,
        request: SequenceRequest,
    ) -> dict[str, float]:

        positions = {}

        x = self.SIDE_MARGIN

        for participant in request.participants:

            positions[participant.id] = x

            x += (
                self.PARTICIPANT_WIDTH
                + self.PARTICIPANT_GAP
            )

        return positions

    # =============================================================
    # Participant
    # =============================================================

    def _draw_participant(
        self,
        svg: list[str],
        x: float,
        label: str,
    ) -> None:

        y = self.TOP_MARGIN

        svg.append(
            f'<rect '
            f'x="{x}" '
            f'y="{y}" '
            f'width="{self.PARTICIPANT_WIDTH}" '
            f'height="{self.PARTICIPANT_HEIGHT}" '
            f'rx="8" '
            f'fill="white" '
            f'stroke="#222" '
            f'stroke-width="1.5"/>'
        )

        svg.append(
            f'<text '
            f'x="{x + self.PARTICIPANT_WIDTH / 2}" '
            f'y="{y + 30}" '
            f'text-anchor="middle" '
            f'font-family="Arial" '
            f'font-size="14" '
            f'font-weight="bold">'
            f'{escape(label)}'
            f'</text>'
        )

    # =============================================================
    # Message
    # =============================================================

    def _draw_message(
        self,
        svg: list[str],
        source_x: float,
        target_x: float,
        y: float,
        message: str,
    ) -> None:

        direction = (
            1
            if target_x > source_x
            else -1
        )

        arrow_size = 8

        end_x = (
            target_x
            - direction * 8
        )

        svg.append(
            f'<line '
            f'x1="{source_x}" '
            f'y1="{y}" '
            f'x2="{end_x}" '
            f'y2="{y}" '
            f'stroke="#222" '
            f'stroke-width="1.5"/>'
        )

        # ---------------------------------------------------------
        # Arrow head
        # ---------------------------------------------------------

        if direction > 0:

            points = (
                f"{end_x},{y} "
                f"{end_x - arrow_size},{y - 5} "
                f"{end_x - arrow_size},{y + 5}"
            )

        else:

            points = (
                f"{end_x},{y} "
                f"{end_x + arrow_size},{y - 5} "
                f"{end_x + arrow_size},{y + 5}"
            )

        svg.append(
            f'<polygon '
            f'points="{points}" '
            f'fill="#222"/>'
        )

        # ---------------------------------------------------------
        # Message label
        # ---------------------------------------------------------

        label_x = (
            source_x + target_x
        ) / 2

        svg.append(
            f'<text '
            f'x="{label_x}" '
            f'y="{y - 10}" '
            f'text-anchor="middle" '
            f'font-family="Arial" '
            f'font-size="13">'
            f'{escape(message)}'
            f'</text>'
        )

    # =============================================================
    # Size
    # =============================================================

    def _calculate_width(
        self,
        participant_count: int,
    ) -> int:

        return int(
            self.SIDE_MARGIN * 2
            + participant_count
            * self.PARTICIPANT_WIDTH
            + max(
                0,
                participant_count - 1,
            )
            * self.PARTICIPANT_GAP
        )

    def _calculate_height(
        self,
        message_count: int,
    ) -> int:

        return int(
            self.TOP_MARGIN
            + self.PARTICIPANT_HEIGHT
            + message_count
            * self.MESSAGE_GAP
            + 100
        )