"""Xcoil serpentine parameters to an embodic design, by ``tools/golden/param_map/serpentine.json``.

The base is the Xcoil-defaults example of ``tests/unit/model/designs.py``. Each mapped Xcoil key is applied to its
pointers; the derived rows (stack-up, neutral pad, outline) follow the file's ``derived`` section.
"""

import json
import math
from collections.abc import Mapping
from dataclasses import replace
from functools import cache
from pathlib import Path
from typing import Any

from tests.unit.model.designs import serpentine_design

from embodic.model.design import DesignParameters
from embodic.model.outline import CircleOutline, OutlineSpec
from embodic.model.stackup import generate_even_stackup
from embodic.model.vocabulary import ConnectionTopology
from embodic.model.winding_specs import CornerStyle, LayerOrder, PairConnection, SideStyle, StackMode, TerminalSide

PARAM_MAP = Path(__file__).resolve().parents[3] / "tools" / "golden" / "param_map" / "serpentine.json"
ENUMS = {
    "/winding/side_style": SideStyle,
    "/winding/corner_style": CornerStyle,
    "/winding/terminal_side": TerminalSide,
    "/winding/pair_connection": PairConnection,
    "/winding/layer_order": LayerOrder,
    "/winding/stack_mode": StackMode,
    "/connection/topology": ConnectionTopology,
}
OUTLINE_SCALE, BORE_SCALE = 1.2, 0.85  # Xcoil outlineScale and innerScale defaults
ANALYSIS_SEGMENT_MM = 0.5  # Xcoil analyze discretises with hMax 0.5 mm (engine.js l.887)


@cache
def field_map() -> tuple[Mapping[str, Any], ...]:
    """Return the ``fields`` rows of the committed parameter map."""
    return tuple(json.loads(PARAM_MAP.read_text(encoding="utf-8"))["fields"])


def _convert(row: Mapping[str, Any], value: Any, pointer: str) -> Any:
    match row.get("transform"):
        case "deg_to_rad":
            return value * math.pi / 180
        case "zero_is_none":
            return value if value > 0 else None
        case "enum":
            return ENUMS[pointer](row["enum"][value])
        case _:
            return value


def _set(node: Any, parts: list[str], value: Any) -> Any:
    """Return ``node`` with the dataclass field at ``parts`` replaced."""
    head, *rest = parts
    return replace(node, **{head: value if not rest else _set(getattr(node, head), rest, value)})


def design_from_xcoil(p: Mapping[str, Any], r_min_all: float, r_max_all: float) -> DesignParameters:
    """Return the design that Xcoil parameters ``p`` (all keys, as normalised) describe.

    ``r_min_all`` and ``r_max_all`` are the copper envelope Xcoil reported; they set the outline as Xcoil does.
    """
    design = serpentine_design()
    for row in field_map():
        for pointer in row["pointers"]:
            design = _set(design, pointer.strip("/").split("/"), _convert(row, p[row["xcoil"]], pointer))
    per_phase = p["stackMode"] == "perPhase"
    count = p["layersPerPhase"] * (1 if per_phase else p["phases"])
    stackup = generate_even_stackup(count, p["copperOzOuter"] * 0.0348, p["boardThickness"])
    outline = OutlineSpec(
        board=CircleOutline(radius_mm=OUTLINE_SCALE * r_max_all),
        bore=CircleOutline(radius_mm=BORE_SCALE * r_min_all),
        screws=(),
    )
    analysis = replace(design.analysis, max_segment_mm=ANALYSIS_SEGMENT_MM)
    design = replace(design, stackup=stackup, outline=outline, analysis=analysis)
    return replace(design, connection=replace(design.connection, neutral_pad=True))
