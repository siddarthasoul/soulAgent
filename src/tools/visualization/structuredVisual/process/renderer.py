from pathlib import Path
from textwrap import wrap
from xml.sax.saxutils import escape

from src.tools.visualization.structuredVisual.process.models import (
    ProcessRequest,
)


class ProcessRenderer:

    BOX_MIN_WIDTH = 220
    BOX_MAX_WIDTH = 360
    BOX_HEIGHT = 90

    HORIZONTAL_GAP = 100
    VERTICAL_GAP = 80

    SIDE_MARGIN = 80
    TOP_MARGIN = 100

    def render(
        self,
        request: ProcessRequest,
        output_path: str | Path,
    ) -> Path:

        output_path = Path(output_path)

        # ---------------------------------------------------------
        # Calculate box sizes
        # ---------------------------------------------------------

        box_sizes = {}

        for step in request.steps:

            width = self._calculate_width(
                step.label,
                step.description,
            )

            box_sizes[step.id] = (
                width,
                self.BOX_HEIGHT,
            )

        # ---------------------------------------------------------
        # Create layout
        # ---------------------------------------------------------

        positions = self._create_positions(
            request,
            box_sizes,
        )

        # ---------------------------------------------------------
        # Calculate canvas
        # ---------------------------------------------------------

        canvas_width, canvas_height = self._calculate_canvas_size(
            positions,
            box_sizes,
        )

        svg: list[str] = []

        svg.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{canvas_width}" '
            f'height="{canvas_height}" '
            f'viewBox="0 0 {canvas_width} {canvas_height}">'
        )

        # ---------------------------------------------------------
        # Definitions
        # ---------------------------------------------------------

        svg.append(
            """
            <defs>

                <marker
                    id="arrow"
                    markerWidth="10"
                    markerHeight="10"
                    refX="9"
                    refY="3"
                    orient="auto"
                    markerUnits="strokeWidth"
                >
                    <path
                        d="M0,0 L0,6 L9,3 z"
                        fill="#222"
                    />
                </marker>

            </defs>
            """
        )

        # ---------------------------------------------------------
        # Background
        # ---------------------------------------------------------

        svg.append(
            f'<rect '
            f'width="{canvas_width}" '
            f'height="{canvas_height}" '
            f'fill="white"/>'
        )

        # ---------------------------------------------------------
        # Title
        # ---------------------------------------------------------

        if request.title:

            svg.append(
                f'<text '
                f'x="{canvas_width / 2}" '
                f'y="45" '
                f'text-anchor="middle" '
                f'font-family="Arial" '
                f'font-size="24" '
                f'font-weight="bold">'
                f'{escape(request.title)}'
                f'</text>'
            )

        # ---------------------------------------------------------
        # Draw arrows FIRST
        # ---------------------------------------------------------

        for index in range(len(request.steps) - 1):

            source = request.steps[index]
            target = request.steps[index + 1]

            self._draw_arrow(
                svg,
                source,
                target,
                positions,
                box_sizes,
            )

        # ---------------------------------------------------------
        # Draw boxes
        # ---------------------------------------------------------

        for step in request.steps:

            self._draw_box(
                svg,
                step,
                positions[step.id],
                box_sizes[step.id],
            )

        # ---------------------------------------------------------
        # Close SVG
        # ---------------------------------------------------------

        svg.append("</svg>")

        # ---------------------------------------------------------
        # Save
        # ---------------------------------------------------------

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
    # Calculate box width
    # =============================================================

    def _calculate_width(
        self,
        label: str,
        description: str | None,
    ) -> int:

        longest = len(label)

        if description:
            longest = max(
                longest,
                len(description),
            )

        width = 160 + longest * 8

        return max(
            self.BOX_MIN_WIDTH,
            min(
                width,
                self.BOX_MAX_WIDTH,
            ),
        )

    # =============================================================
    # Layout
    # =============================================================

    def _create_positions(
        self,
        request: ProcessRequest,
        box_sizes: dict[str, tuple[int, int]],
    ) -> dict[str, tuple[float, float]]:

        positions = {}

        x = self.SIDE_MARGIN

        for index, step in enumerate(request.steps):

            width, height = box_sizes[step.id]

            # -----------------------------------------------------
            # Zig-zag process layout
            # -----------------------------------------------------

            if index % 4 == 0:
                y = self.TOP_MARGIN + 100

            elif index % 4 == 1:
                y = self.TOP_MARGIN + 100 + height + self.VERTICAL_GAP

            elif index % 4 == 2:
                y = self.TOP_MARGIN + 100

            else:
                y = self.TOP_MARGIN + 100 - height - self.VERTICAL_GAP

            positions[step.id] = (
                x,
                y,
            )

            x += (
                width
                + self.HORIZONTAL_GAP
            )

        return positions

    # =============================================================
    # Draw box
    # =============================================================

    def _draw_box(
        self,
        svg: list[str],
        step,
        position: tuple[float, float],
        size: tuple[int, int],
    ) -> None:

        x, y = position
        width, height = size

        svg.append(
            f'<rect '
            f'x="{x}" '
            f'y="{y}" '
            f'width="{width}" '
            f'height="{height}" '
            f'rx="14" '
            f'fill="white" '
            f'stroke="#222" '
            f'stroke-width="2"/>'
        )

        # ---------------------------------------------------------
        # Label
        # ---------------------------------------------------------

        label_lines = wrap(
            step.label,
            width=25,
        )

        label_y = y + 30

        for line in label_lines[:2]:

            svg.append(
                f'<text '
                f'x="{x + width / 2}" '
                f'y="{label_y}" '
                f'text-anchor="middle" '
                f'font-family="Arial" '
                f'font-size="16" '
                f'font-weight="bold">'
                f'{escape(line)}'
                f'</text>'
            )

            label_y += 20

        # ---------------------------------------------------------
        # Description
        # ---------------------------------------------------------

        if step.description:

            description_lines = wrap(
                step.description,
                width=38,
            )

            description_y = y + height - 28

            for line in description_lines[:2]:

                svg.append(
                    f'<text '
                    f'x="{x + width / 2}" '
                    f'y="{description_y}" '
                    f'text-anchor="middle" '
                    f'font-family="Arial" '
                    f'font-size="12">'
                    f'{escape(line)}'
                    f'</text>'
                )

                description_y += 15

    # =============================================================
    # Draw arrow
    # =============================================================

    def _draw_arrow(
        self,
        svg: list[str],
        source,
        target,
        positions,
        box_sizes,
    ) -> None:

        source_x, source_y = positions[source.id]
        target_x, target_y = positions[target.id]

        source_width, source_height = box_sizes[source.id]
        target_width, target_height = box_sizes[target.id]

        # ---------------------------------------------------------
        # Box centers
        # ---------------------------------------------------------

        source_center_x = (
            source_x
            + source_width / 2
        )

        source_center_y = (
            source_y
            + source_height / 2
        )

        target_center_x = (
            target_x
            + target_width / 2
        )

        target_center_y = (
            target_y
            + target_height / 2
        )

        # ---------------------------------------------------------
        # Horizontal connection
        # ---------------------------------------------------------

        if abs(source_center_y - target_center_y) < 10:

            if target_center_x > source_center_x:

                start_x = source_x + source_width
                end_x = target_x

            else:

                start_x = source_x
                end_x = target_x + target_width

            y = source_center_y

            svg.append(
                f'<line '
                f'x1="{start_x}" '
                f'y1="{y}" '
                f'x2="{end_x}" '
                f'y2="{y}" '
                f'stroke="#222" '
                f'stroke-width="2" '
                f'marker-end="url(#arrow)"/>'
            )

            return

        # ---------------------------------------------------------
        # Vertical / diagonal connection
        # ---------------------------------------------------------

        if target_center_y > source_center_y:

            start_x = source_center_x
            start_y = source_y + source_height

            end_x = target_center_x
            end_y = target_y

        else:

            start_x = source_center_x
            start_y = source_y

            end_x = target_center_x
            end_y = target_y + target_height

        # ---------------------------------------------------------
        # Use a curved path
        # ---------------------------------------------------------

        middle_y = (
            start_y
            + (end_y - start_y) / 2
        )

        svg.append(
            f'<path '
            f'd="M {start_x} {start_y} '
            f'C {start_x} {middle_y}, '
            f'{end_x} {middle_y}, '
            f'{end_x} {end_y}" '
            f'fill="none" '
            f'stroke="#222" '
            f'stroke-width="2" '
            f'marker-end="url(#arrow)"/>'
        )

    # =============================================================
    # Canvas size
    # =============================================================

    def _calculate_canvas_size(
        self,
        positions,
        box_sizes,
    ) -> tuple[int, int]:

        max_x = 0
        max_y = 0

        for node_id, (x, y) in positions.items():

            width, height = box_sizes[node_id]

            max_x = max(
                max_x,
                int(x + width),
            )

            max_y = max(
                max_y,
                int(y + height),
            )

        return (
            max_x + self.SIDE_MARGIN,
            max_y + self.SIDE_MARGIN,
        )