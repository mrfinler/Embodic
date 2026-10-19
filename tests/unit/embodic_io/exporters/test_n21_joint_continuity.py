"""REQ-N-21 (V3-01 gap N-21): copper joints stay one point after the SVG and DXF writers quantise.

A joint is a set of Layout end points on one board and copper layer that lie within 1e-6 mm of each other
(`COINCIDENCE_MM`). The files are parsed back and every written point that lies at a joint must be the same number.
A DXF joint that touches an ARC entity cannot be the same number: R12 stores an arc as centre, radius and two angles,
so its end points are derived, and on D08 and the wave example they differ from the neighbouring LINE end by up to
1.4e-9 mm (measured by the U-M7c probe). D-055c rules that such a joint is continuous when its written ends lie
within `COINCIDENCE_MM` of each other.
"""

import dataclasses
import math
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path

import ezdxf
import pytest

from embodic.api import ComputeOutcome
from embodic.geometry.layout import Layout
from embodic.geometry.paths import COINCIDENCE_MM, CopperPath
from embodic.geometry.primitives import Line, PrimitiveRole
from embodic.io.dxf_writer import write_dxf
from embodic.io.exporters import ExportSummary, PhaseRenderMode
from embodic.io.svg_writer import write_svg

pytestmark = pytest.mark.req("REQ-N-21")

SVG = "{http://www.w3.org/2000/svg}"
EXAMPLES = ("spiral_12c10p_d08", "wave_16p_example")
AT_JOINT_MM = 10 * COINCIDENCE_MM  # a written point this close to a joint belongs to it; rounding is at most 1e-6
PATH_TOKEN = re.compile(r"[MLAZ]|-?\d+(?:\.\d+)?(?:e-?\d+)?")
Point = tuple[float, float]


def joints(board: Layout, layer: str, *, lines_only: bool, with_arc: bool = False) -> list[Point]:
    """Return the centre of every point where two or more primitive ends of one layer coincide.

    With ``lines_only`` a joint counts when every primitive that meets there is a Line; with ``with_arc`` when at
    least one is an Arc.
    """
    groups: list[list[tuple[Point, bool]]] = []
    by_cell: dict[tuple[int, int], list[int]] = defaultdict(list)
    for path in board.paths:
        if path.layer != layer:
            continue
        for q in path.primitives:
            for point in (q.start_point(), q.end_point()):
                cx, cy = (math.floor(c / COINCIDENCE_MM) for c in point)
                neighbours = (g for dx in (-1, 0, 1) for dy in (-1, 0, 1) for g in by_cell.get((cx + dx, cy + dy), ()))
                found = next((g for g in neighbours if math.dist(groups[g][0][0], point) <= COINCIDENCE_MM), None)
                if found is None:
                    found = len(groups)
                    groups.append([])
                    by_cell[(cx, cy)].append(found)
                groups[found].append((point, isinstance(q, Line)))
    return [
        (sum(p[0] for p, _ in group) / len(group), sum(p[1] for p, _ in group) / len(group))
        for group in groups
        if len(group) >= 2 and (not lines_only or all(is_line for _, is_line in group))
        if not with_arc or not all(is_line for _, is_line in group)
    ]


def svg_points(d: str) -> list[Point]:
    """Return the numbers a path ``d`` writes: every M and L point and the end of every A."""
    tokens = PATH_TOKEN.findall(d)
    points, i = [], 0
    while i < len(tokens):
        if tokens[i] in "ML":
            points.append((float(tokens[i + 1]), float(tokens[i + 2])))
            i += 3
        elif tokens[i] == "A":
            points.append((float(tokens[i + 6]), float(tokens[i + 7])))
            i += 8
        else:
            i += 1
    return points


def written_svg(outcome: ComputeOutcome, tmp_path: Path) -> dict[tuple[int, str], list[Point]]:
    """Write the SVG and return the copper points of each (board number, layer)."""
    summary = write_svg(outcome, tmp_path / "board.svg", mode=PhaseRenderMode.COLOUR, allow_drc_errors=True)
    assert isinstance(summary, ExportSummary), summary
    root = ET.parse(summary.path).getroot()
    copper: dict[tuple[int, str], list[Point]] = defaultdict(list)
    for group in root.iter(f"{SVG}g"):
        match = re.fullmatch(r"b(\d+)-cu-(\w+)", group.get("id", ""))
        if match:
            for path in group.iter(f"{SVG}path"):
                copper[(int(match[1]), match[2])] += svg_points(path.get("d", ""))
    return copper


def write_complete_dxf(outcome: ComputeOutcome, tmp_path: Path) -> Path:
    """Write the complete DXF of an outcome and return its path."""
    summary = write_dxf(outcome, tmp_path / "board.dxf", "complete", allow_drc_errors=True)
    assert isinstance(summary, ExportSummary), summary
    return summary.path


def dxf_layer(board_number: int, index: int) -> re.Pattern[str]:
    """Return the pattern of the DXF layer names of copper layer ``index`` (from 1) of a board."""
    return re.compile(rf"(?:B{board_number}_)?CU{index}_")


def dxf_ends(outcome: ComputeOutcome, dxf: Path, kinds: tuple[str, ...]) -> dict[tuple[int, str], list[Point]]:
    """Return the end points of the ``kinds`` entities of each (board number, layer); an ARC's are derived by ezdxf."""
    assert outcome.boards is not None
    names = {
        (board_number, layer): dxf_layer(board_number, index)
        for board_number, board in enumerate(outcome.boards.boards, start=1)
        for index, layer in enumerate(board.copper_layers, start=1)
    }
    ends: dict[tuple[int, str], list[Point]] = defaultdict(list)
    for entity in ezdxf.readfile(dxf).modelspace():
        if entity.dxftype() not in kinds:
            continue
        if entity.dxftype() == "LINE":
            points = [tuple(entity.dxf.start)[:2], tuple(entity.dxf.end)[:2]]
        else:
            points = [tuple(entity.start_point)[:2], tuple(entity.end_point)[:2]]
        for key, pattern in names.items():
            if pattern.match(entity.dxf.layer):
                ends[key] += points
    return ends


def written_dxf_lines(outcome: ComputeOutcome, tmp_path: Path) -> dict[tuple[int, str], list[Point]]:
    """Write the complete DXF and return the LINE end points of each (board number, layer)."""
    return dxf_ends(outcome, write_complete_dxf(outcome, tmp_path), ("LINE",))


def disagreeing_joints(
    outcome: ComputeOutcome, written: dict[tuple[int, str], list[Point]], *, lines_only: bool
) -> tuple[int, list[str]]:
    """Return the number of joints checked and a message per joint whose written points are not one number."""
    assert outcome.boards is not None
    checked, bad = 0, []
    for board_number, board in enumerate(outcome.boards.boards, start=1):
        for layer in board.copper_layers:
            for centre in joints(board, layer, lines_only=lines_only):
                near = {p for p in written[(board_number, layer)] if math.dist(p, centre) <= AT_JOINT_MM}
                checked += 1
                if len(near) != 1:
                    bad.append(f"board {board_number} {layer} joint at {centre}: written {sorted(near)}")
    return checked, bad


@pytest.mark.parametrize("example", EXAMPLES)
def test_n21_svg_writes_one_point_for_every_copper_joint(
    example: str, outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path
) -> None:
    """Catches an SVG writer that rounds the ends of a joint apart (a 1-digit gap) or drops the joint."""
    outcome = outcome_of(example)
    checked, bad = disagreeing_joints(outcome, written_svg(outcome, tmp_path), lines_only=False)
    assert checked > 0
    assert bad == []


def with_one_path(outcome: ComputeOutcome, primitives: tuple[Line, ...]) -> ComputeOutcome:
    """Return ``outcome`` with board 1 reduced to a single path of ``primitives`` on its first copper layer."""
    assert outcome.boards is not None
    board = outcome.boards.boards[0]
    chain = CopperPath(
        id=0, layer=board.copper_layers[0], net="A", primitives=primitives, phase=None, element=None, polarity=0
    )
    stub = dataclasses.replace(board, paths=(chain,), vias=(), pads=())
    return dataclasses.replace(outcome, boards=dataclasses.replace(outcome.boards, boards=(stub,)))


@pytest.mark.parametrize(
    ("end_mm", "start_mm"),
    [(1.0000004, 1.0000006), (1.0000006, 1.0000004), (-2.0000006, -2.0000004)],
    ids=["end rounds down", "end rounds up", "negative side"],
)
def test_n21_svg_joint_ends_that_round_apart_are_written_once_from_the_shared_coordinate(
    end_mm: float, start_mm: float, outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path
) -> None:
    """V3-05-01 (D-071c). Catches a writer that takes the joint from the next primitive's own start coordinate.

    The two lines meet 2e-7 mm apart, inside the 1e-6 mm joint bound, and the six-decimal SVG numbers of the two ends
    differ because 1e-6 mm rounding falls between them. The joint must still be one written point.
    """
    first = Line(x1_mm=0.0, y1_mm=0.0, x2_mm=end_mm, y2_mm=0.0, width_mm=0.2, role=PrimitiveRole.SIDE)
    second = Line(x1_mm=start_mm, y1_mm=0.0, x2_mm=2 * start_mm, y2_mm=0.0, width_mm=0.2, role=PrimitiveRole.SIDE)
    assert abs(start_mm - end_mm) < COINCIDENCE_MM
    outcome = with_one_path(outcome_of("spiral_12c10p_d08"), (first, second))
    checked, bad = disagreeing_joints(outcome, written_svg(outcome, tmp_path), lines_only=False)
    assert checked == 1
    assert bad == []


@pytest.mark.parametrize("example", EXAMPLES)
def test_n21_dxf_writes_one_point_for_every_line_to_line_joint(
    example: str, outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path
) -> None:
    """Catches a DXF writer that rounds the two LINE ends of a joint apart; arc joints are not covered (module note)."""
    outcome = outcome_of(example)
    checked, bad = disagreeing_joints(outcome, written_dxf_lines(outcome, tmp_path), lines_only=True)
    assert checked > 0
    assert bad == []


def arc_joint_spreads_mm(outcome: ComputeOutcome, dxf: Path) -> tuple[int, list[float]]:
    """Return how many Layout joints touch an Arc, and for each the spread of its written ends in mm.

    The spread is the largest distance between two LINE or ARC end points of the DXF that lie at the joint.
    """
    assert outcome.boards is not None
    written = dxf_ends(outcome, dxf, ("LINE", "ARC"))
    spreads = []
    for board_number, board in enumerate(outcome.boards.boards, start=1):
        for layer in board.copper_layers:
            for centre in joints(board, layer, lines_only=False, with_arc=True):
                near = [p for p in written[(board_number, layer)] if math.dist(p, centre) <= AT_JOINT_MM]
                assert len(near) >= 2, f"board {board_number} {layer} joint at {centre}: written {near}"
                spreads.append(max(math.dist(a, b) for a in near for b in near))
    return len(spreads), spreads


def shift_one_arc_end(dxf: Path, shifted: Path, layer: re.Pattern[str], joint_mm: Point, by_mm: float) -> None:
    """Save a copy of ``dxf`` where the ARC of ``layer`` that ends nearest ``joint_mm`` ends ``by_mm`` further on."""
    doc = ezdxf.readfile(dxf)
    arcs = [e for e in doc.modelspace() if e.dxftype() == "ARC" and layer.match(e.dxf.layer)]
    arc = min(arcs, key=lambda e: math.dist(tuple(e.end_point)[:2], joint_mm))
    assert math.dist(tuple(arc.end_point)[:2], joint_mm) <= AT_JOINT_MM, "no ARC ends at the joint"
    arc.dxf.end_angle += math.degrees(by_mm / arc.dxf.radius)
    doc.saveas(shifted)


@pytest.mark.parametrize("example", EXAMPLES)
def test_n21_dxf_arc_joints_are_continuous_within_the_coincidence_bound(
    example: str, outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path
) -> None:
    """D-055c. Catches a DXF writer that moves an ARC end off the LINE or ARC end it joins by more than COINCIDENCE_MM.

    An ARC end is derived from the stored centre, radius and angles, so a wrong one shows here and nowhere else.
    U-M7c measured at most 1.4e-9 mm on these examples.
    """
    outcome = outcome_of(example)
    checked, spreads = arc_joint_spreads_mm(outcome, write_complete_dxf(outcome, tmp_path))
    assert checked > 0
    assert max(spreads) <= COINCIDENCE_MM


@pytest.mark.parametrize(
    ("shift_mm", "reported"), [(0.0, False), (0.5 * COINCIDENCE_MM, False), (2 * COINCIDENCE_MM, True)]
)
def test_n21_the_arc_joint_check_reports_an_arc_end_moved_past_the_bound(
    shift_mm: float,
    reported: bool,
    outcome_of: Callable[[str], ComputeOutcome],
    tmp_path: Path,
) -> None:
    """Control for the test above: one ARC end moved 2e-6 mm along its circle is reported, 0.5e-6 mm is not.

    Catches a checker that cannot fail, and a bound that is looser than COINCIDENCE_MM.
    """
    outcome = outcome_of(EXAMPLES[0])
    assert outcome.boards is not None
    dxf = write_complete_dxf(outcome, tmp_path)
    board = outcome.boards.boards[0]
    layer, joint = next(
        (index, c)
        for index, name in enumerate(board.copper_layers, start=1)
        for c in joints(board, name, lines_only=False, with_arc=True)
    )
    shifted = tmp_path / "shifted.dxf"
    shift_one_arc_end(dxf, shifted, dxf_layer(1, layer), joint, shift_mm)
    _, spreads = arc_joint_spreads_mm(outcome, shifted)
    assert (max(spreads) > COINCIDENCE_MM) is reported
