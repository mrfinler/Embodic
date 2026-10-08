"""UT-EXP-01 and UT-IO-06 for SVG: the drawing parses and holds exactly the Layout's copper, vias, pads and holes."""

import json
import re
import xml.etree.ElementTree as ET
from collections.abc import Callable
from pathlib import Path

import pytest

from embodic.api import ComputeOutcome
from embodic.geometry.primitives import Arc, Line
from embodic.io.exporters import ExportSummary, PhaseRenderMode
from embodic.io.svg_writer import write_svg
from embodic.paths import resource_root

pytestmark = pytest.mark.req("REQ-F-16", "REQ-T-07", "REQ-N-23")

SVG = "{http://www.w3.org/2000/svg}"
EMBODIC = "{urn:embodic:export:1}"


def _classes(root: ET.Element, name: str) -> list[ET.Element]:
    return [e for e in root.iter() if name in e.get("class", "").split()]


def _light_tokens() -> dict[str, str]:
    tokens = json.loads((resource_root() / "themes" / "tokens.json").read_text(encoding="utf-8"))
    return tokens["themes"]["light"]["color"]


def _written(outcome: ComputeOutcome, tmp_path: Path, mode: PhaseRenderMode) -> tuple[ExportSummary, ET.Element]:
    summary = write_svg(outcome, tmp_path / f"board_{mode}.svg", mode=mode, allow_drc_errors=True)
    assert isinstance(summary, ExportSummary), summary
    return summary, ET.parse(summary.path).getroot()


@pytest.mark.parametrize("mode", list(PhaseRenderMode))
def test_ut_exp_01_svg_counts_equal_the_layout(
    example_id: str, mode: PhaseRenderMode, outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path
) -> None:
    """UT-EXP-01. Catches a dropped or doubled path, via, pad or hole, and a primitive lost inside a path's d."""
    outcome = outcome_of(example_id)
    assert outcome.boards is not None
    boards = outcome.boards.boards
    summary, root = _written(outcome, tmp_path, mode)

    assert len(_classes(root, "copper")) == sum(len(b.paths) for b in boards)
    assert len(_classes(root, "via")) == sum(len(b.vias) for b in boards)
    assert len(_classes(root, "pad")) == sum(len(b.pads) for b in boards)
    assert len(_classes(root, "hole")) == sum(len(b.outline.holes) for b in boards)

    commands = " ".join(p.get("d", "") for e in _classes(root, "copper") for p in e.iter(f"{SVG}path"))
    prims = [q for b in boards for path in b.paths for q in path.primitives]
    full_circles = sum(isinstance(q, Arc) and abs(q.sweep_rad) >= 6.283185307 for q in prims)
    assert len(re.findall(r"\bL\b", commands)) == sum(isinstance(q, Line) for q in prims)
    assert len(re.findall(r"\bA\b", commands)) == sum(isinstance(q, Arc) for q in prims) + full_circles
    assert (summary.vias, summary.pads, summary.holes) == (
        sum(len(b.vias) for b in boards),
        sum(len(b.pads) for b in boards),
        sum(len(b.outline.holes) for b in boards),
    )


@pytest.mark.parametrize("mode", list(PhaseRenderMode))
def test_ut_io_06_svg_metadata_holds_the_stamp(
    example_id: str, mode: PhaseRenderMode, outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path
) -> None:
    """UT-IO-06. Catches a missing or wrong REQ-T-07 field in the SVG <metadata>."""
    outcome = outcome_of(example_id)
    _, root = _written(outcome, tmp_path, mode)
    stamp = root.find(f"{SVG}metadata/{EMBODIC}export")
    assert stamp is not None
    assert stamp.get("embodic_version") == outcome.versions.embodic
    assert outcome.versions.numpy in stamp.get("engine_version", "")
    assert stamp.get("registry_version") == outcome.versions.registry
    assert stamp.get("design_hash") == outcome.design_hash
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", stamp.get("generated_utc", ""))
    assert stamp.get("drc_passed") == ("true" if outcome.ok else "false")


def test_ut_exp_01_phases_carry_class_label_and_mode_ink(
    example_id: str, outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path
) -> None:
    """UT-EXP-01. Catches a phase group without class or label, colour ink in greyscale mode, or missing hatches."""
    colours = _light_tokens()
    outcome = outcome_of(example_id)
    for mode in PhaseRenderMode:
        _, root = _written(outcome, tmp_path, mode)
        groups = _classes(root, "phase")
        assert {g.get("data-phase") for g in groups} >= {"A", "B", "C"}
        for group in groups:
            phase = group.get("data-phase")
            if phase == "none":
                continue
            assert f"phase-{phase.lower()}" in group.get("class", "")
            assert group.get("data-label") == f"Phase {phase}"
            key = f"phase-{phase.lower()}" + ("" if mode is PhaseRenderMode.COLOUR else "-grey")
            assert group.get("stroke") == colours[key]
        hatches = {p.get("patternTransform") for p in root.iter(f"{SVG}pattern")}
        if mode is PhaseRenderMode.GREYSCALE_HATCH:
            assert hatches == {"rotate(45)", "rotate(135)"}
        legend = " ".join(t.text or "" for t in root.iter(f"{SVG}text"))
        assert all(f"Phase {p}" in legend for p in "ABC")
