from pathlib import Path
from textwrap import wrap
from xml.sax.saxutils import escape

from src.tools.visualization.structuredVisual.diagram.models import (
    FlowRequest,
)


class FlowRenderer:

    NODE_MIN_WIDTH = 180
    NODE_MAX_WIDTH = 300
    NODE_HEIGHT = 70

    HORIZONTAL_GAP = 120
    VERTICAL_GAP = 100

    SIDE_MARGIN = 80
    TOP_MARGIN = 100

    def render(
        self,
        request: FlowRequest,
        output_path: str | Path,
    ) -> Path:

        output_path = Path(output_path)

        # ---------------------------------------------------------
        # Calculate node sizes
        # ---------------------------------------------------------

        node_sizes: dict[str, tuple[int, int]] = {}

        for node in request.nodes:
            node_sizes[node.id] = (
                self._calculate_width(node.label),
                self.NODE_HEIGHT,
            )

        # ---------------------------------------------------------
        # Build graph relationships
        # ---------------------------------------------------------

        outgoing: dict[str, list[str]] = {
            node.id: []
            for node in request.nodes
        }

        incoming: dict[str, list[str]] = {
            node.id: []
            for node in request.nodes
        }

        for edge in request.edges:
            outgoing[edge.source].append(edge.target)
            incoming[edge.target].append(edge.source)

        # ---------------------------------------------------------
        # Create automatic levels
        # ---------------------------------------------------------

        levels = self._create_levels(
            request,
            outgoing,
            incoming,
        )

        # ---------------------------------------------------------
        # Create positions
        # ---------------------------------------------------------

        positions = self._create_positions(
            levels,
            node_sizes,
        )

        # ---------------------------------------------------------
        # Canvas
        # ---------------------------------------------------------

        width, height = self._calculate_canvas_size(
            positions,
            node_sizes,
        )

        svg: list[str] = []

        svg.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{width}" '
            f'height="{height}" '
            f'viewBox="0 0 {width} {height}">'
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
            f'width="{width}" '
            f'height="{height}" '
            f'fill="white"/>'
        )

        # ---------------------------------------------------------
        # Title
        # ---------------------------------------------------------

        if request.title:

            svg.append(
                f'<text '
                f'x="{width / 2}" '
                f'y="45" '
                f'text-anchor="middle" '
                f'font-family="Arial" '
                f'font-size="24" '
                f'font-weight="bold">'
                f'{escape(request.title)}'
                f'</text>'
            )

        # ---------------------------------------------------------
        # Draw edges first
        # ---------------------------------------------------------

        for edge in request.edges:

            self._draw_edge(
                svg,
                edge,
                positions,
                node_sizes,
            )

        # ---------------------------------------------------------
        # Draw nodes
        # ---------------------------------------------------------

        for node in request.nodes:

            self._draw_node(
                svg,
                node,
                positions[node.id],
                node_sizes[node.id],
            )

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
    # Node width
    # =============================================================

    def _calculate_width(
        self,
        label: str,
    ) -> int:

        width = 120 + len(label) * 8

        return max(
            self.NODE_MIN_WIDTH,
            min(
                width,
                self.NODE_MAX_WIDTH,
            ),
        )

    # =============================================================
    # Create graph levels
    # =============================================================

    def _create_levels(
        self,
        request: FlowRequest,
        outgoing: dict[str, list[str]],
        incoming: dict[str, list[str]],
    ) -> list[list[str]]:

        node_ids = [
            node.id
            for node in request.nodes
        ]

        if not node_ids:
            return []

        # ---------------------------------------------------------
        # Find root nodes
        # ---------------------------------------------------------

        roots = [
            node_id
            for node_id in node_ids
            if not incoming[node_id]
        ]

        # ---------------------------------------------------------
        # Cyclic graph:
        # no root exists, so use first node.
        # ---------------------------------------------------------

        if not roots:
            roots = [node_ids[0]]

        # ---------------------------------------------------------
        # Breadth-first traversal
        # ---------------------------------------------------------

        levels: dict[str, int] = {}
        queue: list[str] = []

        for root in roots:

            levels[root] = 0
            queue.append(root)

        index = 0

        while index < len(queue):

            current = queue[index]
            index += 1

            current_level = levels[current]

            for target in outgoing[current]:

                # -------------------------------------------------
                # IMPORTANT:
                #
                # Never update an already visited node.
                #
                # This prevents:
                #
                # A -> B -> C -> A
                #
                # from becoming:
                #
                # A=0, B=1, C=2, A=3, B=4...
                # -------------------------------------------------

                if target in levels:
                    continue

                levels[target] = current_level + 1
                queue.append(target)

        # ---------------------------------------------------------
        # Handle disconnected nodes
        # ---------------------------------------------------------

        max_level = (
            max(levels.values())
            if levels
            else 0
        )

        for node_id in node_ids:

            if node_id not in levels:

                max_level += 1
                levels[node_id] = max_level

        # ---------------------------------------------------------
        # Convert dictionary to levels
        # ---------------------------------------------------------

        result: list[list[str]] = []

        max_level = max(levels.values())

        for level in range(max_level + 1):

            result.append(
                [
                    node_id
                    for node_id in node_ids
                    if levels[node_id] == level
                ]
            )

        return result

    # =============================================================
    # Position nodes
    # =============================================================

    def _create_positions(
        self,
        levels: list[list[str]],
        node_sizes: dict[str, tuple[int, int]],
    ) -> dict[str, tuple[float, float]]:

        positions: dict[str, tuple[float, float]] = {}

        for level_index, level in enumerate(levels):

            if not level:
                continue

            # -----------------------------------------------------
            # Calculate total width
            # -----------------------------------------------------

            total_width = sum(
                node_sizes[node_id][0]
                for node_id in level
            )

            total_width += (
                max(0, len(level) - 1)
                * self.HORIZONTAL_GAP
            )

            # -----------------------------------------------------
            # Center the complete level
            # -----------------------------------------------------

            current_x = (
                self.SIDE_MARGIN
                + (
                    total_width
                    - self.HORIZONTAL_GAP
                ) / 2
                - sum(
                    node_sizes[node_id][0]
                    for node_id in level
                ) / 2
            )

            # Simpler and more stable starting position
            current_x = self.SIDE_MARGIN

            # -----------------------------------------------------
            # Place nodes
            # -----------------------------------------------------

            for node_id in level:

                width, height = node_sizes[node_id]

                positions[node_id] = (
                    current_x,
                    self.TOP_MARGIN
                    + level_index
                    * (
                        self.NODE_HEIGHT
                        + self.VERTICAL_GAP
                    ),
                )

                current_x += (
                    width
                    + self.HORIZONTAL_GAP
                )

        return positions

    # =============================================================
    # Draw node
    # =============================================================

    def _draw_node(
        self,
        svg: list[str],
        node,
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
            f'rx="12" '
            f'fill="white" '
            f'stroke="#222" '
            f'stroke-width="2"/>'
        )

        lines = wrap(
            node.label,
            width=25,
        )

        start_y = (
            y
            + height / 2
            - ((len(lines) - 1) * 9)
        )

        for index, line in enumerate(lines[:3]):

            svg.append(
                f'<text '
                f'x="{x + width / 2}" '
                f'y="{start_y + index * 18}" '
                f'text-anchor="middle" '
                f'font-family="Arial" '
                f'font-size="14" '
                f'font-weight="bold">'
                f'{escape(line)}'
                f'</text>'
            )

    # =============================================================
    # Draw edge
    # =============================================================

    def _draw_edge(
        self,
        svg: list[str],
        edge,
        positions,
        node_sizes,
    ) -> None:

        source_x, source_y = positions[edge.source]
        target_x, target_y = positions[edge.target]

        source_width, source_height = node_sizes[
            edge.source
        ]

        target_width, target_height = node_sizes[
            edge.target
        ]

        # ---------------------------------------------------------
        # Centers
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
        # Same node
        # ---------------------------------------------------------

        if edge.source == edge.target:

            loop_x = (
                source_x
                + source_width
                + 50
            )

            start_y = source_y + 20
            end_y = source_y + 50

            path = (
                f"M {source_x + source_width} {start_y} "
                f"C {loop_x} {start_y}, "
                f"{loop_x} {end_y}, "
                f"{source_x + source_width} {end_y}"
            )

            label_x = loop_x
            label_y = source_y + 10

        # ---------------------------------------------------------
        # Normal downward edge
        # ---------------------------------------------------------

        elif target_center_y > source_center_y:

            start_x = source_center_x
            start_y = source_y + source_height

            end_x = target_center_x
            end_y = target_y

            middle_y = (
                start_y
                + (end_y - start_y) / 2
            )

            path = (
                f"M {start_x} {start_y} "
                f"C {start_x} {middle_y}, "
                f"{end_x} {middle_y}, "
                f"{end_x} {end_y}"
            )

            label_x = (
                start_x + end_x
            ) / 2

            label_y = middle_y - 8

        # ---------------------------------------------------------
        # Backward / upward edge
        # ---------------------------------------------------------

        else:

            if target_center_x > source_center_x:

                start_x = source_x + source_width
                start_y = source_center_y

                end_x = target_x
                end_y = target_center_y

            else:

                start_x = source_x
                start_y = source_center_y

                end_x = target_x + target_width
                end_y = target_center_y

            curve_offset = 80

            direction = (
                1
                if end_x > start_x
                else -1
            )

            control_x_1 = (
                start_x
                + curve_offset * direction
            )

            control_x_2 = (
                end_x
                - curve_offset * direction
            )

            path = (
                f"M {start_x} {start_y} "
                f"C {control_x_1} {start_y}, "
                f"{control_x_2} {end_y}, "
                f"{end_x} {end_y}"
            )

            label_x = (
                start_x + end_x
            ) / 2

            label_y = (
                start_y + end_y
            ) / 2 - 10

        # ---------------------------------------------------------
        # Arrow
        # ---------------------------------------------------------

        svg.append(
            f'<path '
            f'd="{path}" '
            f'fill="none" '
            f'stroke="#222" '
            f'stroke-width="2" '
            f'marker-end="url(#arrow)"/>'
        )

        # ---------------------------------------------------------
        # Edge label
        # ---------------------------------------------------------

        if edge.label:

            svg.append(
                f'<text '
                f'x="{label_x}" '
                f'y="{label_y}" '
                f'text-anchor="middle" '
                f'font-family="Arial" '
                f'font-size="12">'
                f'{escape(edge.label)}'
                f'</text>'
            )

    # =============================================================
    # Canvas
    # =============================================================

    def _calculate_canvas_size(
        self,
        positions,
        node_sizes,
    ) -> tuple[int, int]:

        if not positions:
            return (
                400,
                300,
            )

        max_x = 0
        max_y = 0

        for node_id, (x, y) in positions.items():

            width, height = node_sizes[node_id]

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