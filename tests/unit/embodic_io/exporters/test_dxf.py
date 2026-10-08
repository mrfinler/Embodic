"""UT-EXP-02 and UT-IO-06 for DXF: ezdxf audits each part clean and finds exactly the Layout's entities."""

import math
import re
from collections import Counter
from collections.abc import Callable
from pathlib import Path

import ezdxf
import pytest

from embodic.api import ComputeOutcome
from embodic.geometry.primitives import Arc
from embodic.io.dxf_writer import write_dxf
from embodic.io.exporters import ExportRefused, ExportSummary

pytestmark = pytest.mark.req("REQ-F-16", "REQ-F-09", "REQ-T-07")

SHARED_MM = 1e-6


def _read(summary: ExportSummary | ExportRefused) -> ezdxf.document.Drawing:
    assert isinstance(summary, ExportSummary), summary
    doc = ezdxf.readfile(summary.path)
    auditor = doc.audit()
    assert len(auditor.errors) == 0, [e.message for e in auditor.errors]
    return doc


def _ends(entity: ezdxf.entities.DXFGraphic) -> list[tuple[float, float]]:
    if entity.dxftype() == "LINE":
        return [tuple(entity.dxf.start)[:2], tuple(entity.dxf.end)[:2]]
    return [tuple(p)[:2] for p in (entity.start_point, entity.end_point)]


def test_ut_exp_02_complete_dxf_counts_equal_the_layout(
    example_id: str, outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path
) -> None:
    """UT-EXP-02. Catches a lost primitive, via, pad or hole in the complete board, and a file ezdxf cannot audit."""
    outcome = outcome_of(example_id)
    assert outcome.boards is not None
    boards = outcome.boards.boards
    doc = _read(write_dxf(outcome, tmp_path / "board.dxf", "complete", allow_drc_errors=True))
    by_layer = Counter((e.dxftype(), e.dxf.layer.split("_")[0]) for e in doc.modelspace())
    copper_layer = re.compile(r"CU\d+$")

    copper = [q for b in boards for p in b.paths for q in p.primitives]
    full = sum(isinstance(q, Arc) and abs(q.sweep_rad) >= 2 * math.pi - 1e-9 for q in copper)
    assert sum(n for (kind, layer), n in by_layer.items() if copper_layer.match(layer) and kind == "LINE") == sum(
        not isinstance(q, Arc) for q in copper
    )
    assert sum(n for (kind, layer), n in by_layer.items() if copper_layer.match(layer) and kind == "ARC") == (
        sum(isinstance(q, Arc) for q in copper) - full
    )
    dxf_arc_mm = sum(
        e.dxf.radius * math.radians((e.dxf.end_angle - e.dxf.start_angle) % 360)
        for e in doc.modelspace()
        if e.dxftype() == "ARC" and copper_layer.match(e.dxf.layer.split("_")[0])
    )
    layout_arc_mm = sum(q.r_mm * abs(q.sweep_rad) for q in copper if isinstance(q, Arc) and abs(q.sweep_rad) < 6.2831)
    assert dxf_arc_mm == pytest.approx(layout_arc_mm, rel=1e-9)  # a clockwise arc drawn the long way round fails
    assert by_layer[("CIRCLE", "VIA")] == 2 * sum(len(b.vias) for b in boards)  # pad and drill
    assert by_layer[("CIRCLE", "SCREW")] == sum(len(b.outline.holes) for b in boards)
    round_pads = sum(p.shape == "round" for b in boards for p in b.pads)
    drilled = sum(p.drill_mm > 0 for b in boards for p in b.pads)
    assert by_layer[("CIRCLE", "PAD")] == round_pads + drilled


def test_ut_exp_02_outline_dxf_is_closed_outline_and_bore_only(
    example_id: str, outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path
) -> None:
    """UT-EXP-02. Catches copper or holes in the outline file, and an open loop (an end point not shared by two)."""
    outcome = outcome_of(example_id)
    assert outcome.boards is not None
    outline = outcome.boards.boards[0].outline
    doc = _read(write_dxf(outcome, tmp_path / "outline.dxf", "outline", allow_drc_errors=True))
    entities = list(doc.modelspace())
    assert {e.dxf.layer for e in entities} <= {"BOARD_OUTLINE", "CUTOUT"}
    assert len(entities) == len(outline.outer) + sum(len(loop) for loop in outline.cutouts)
    points = [p for e in entities for p in _ends(e)]
    for p in points:
        assert sum(math.dist(p, q) <= SHARED_MM for q in points) == 2, p


def test_ut_exp_02_screws_dxf_is_circles_only(
    example_id: str, outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path
) -> None:
    """UT-EXP-02. Catches anything but the screw circles, a wrong hole count, and a screws file with no holes."""
    outcome = outcome_of(example_id)
    assert outcome.boards is not None
    holes = [h for b in outcome.boards.boards for h in b.outline.holes]
    result = write_dxf(outcome, tmp_path / "screws.dxf", "screws", allow_drc_errors=True)
    if not holes:
        assert isinstance(result, ExportRefused) and result.reason == "no_screws"
        assert not (tmp_path / "screws.dxf").exists()
        return
    entities = list(_read(result).modelspace())
    assert {e.dxftype() for e in entities} == {"CIRCLE"}
    assert sorted(
        (round(e.dxf.center.x, 6), round(e.dxf.center.y, 6), round(2 * e.dxf.radius, 6)) for e in entities
    ) == (sorted((round(h.x_mm, 6), round(h.y_mm, 6), round(h.diameter_mm, 6)) for h in holes))


@pytest.mark.parametrize("part", ["complete", "outline", "screws"])
def test_ut_io_06_dxf_header_comment_holds_the_stamp(
    part: str, outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path
) -> None:
    """UT-IO-06. Catches a DXF part without the REQ-T-07 header comment."""
    outcome = outcome_of("serpentine_16p_example")
    summary = write_dxf(outcome, tmp_path / f"{part}.dxf", part)  # type: ignore[arg-type]
    assert isinstance(summary, ExportSummary), summary
    lines = summary.path.read_text(encoding="ascii").splitlines()
    comments = [lines[i + 1] for i in range(0, len(lines) - 1, 2) if lines[i].strip() == "999"]
    assert f"embodic_version={outcome.versions.embodic}" in comments
    assert f"registry_version={outcome.versions.registry}" in comments
    assert f"design_hash={outcome.design_hash}" in comments
    assert "drc_passed=true" in comments
    assert any(c.startswith("engine_version=") for c in comments)
    assert any(c.startswith("generated_utc=") for c in comments)
