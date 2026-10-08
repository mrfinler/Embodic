"""UT-EXP-01 and UT-IO-06 for SVG: the drawing parses and holds exactly the Layout's copper, vias, pads and holes."""

import json
import math
import re
import xml.etree.ElementTree as ET
from collections.abc import Callable
from pathlib import Path

import pytest
from fontTools.ttLib import TTFont

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
    assert stamp.get("engine_version") == outcome.versions.embodic
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
        swatches = {g.get("data-phase"): g for g in _classes(root, "legend-eye")}
        assert [swatches[p].find(f"{SVG}path") is not None for p in "ABC"] == [False, True, True], mode
        assert swatches["A"].find(f"{SVG}circle") is not None, mode
        legend = " ".join(t.text or "" for t in root.iter(f"{SVG}text"))
        assert all(f"Phase {p}" in legend for p in "ABC")


def _clip_discs(root: ET.Element) -> dict[str, tuple[float, float, float]]:
    return {
        clip.get("id", ""): tuple(float(clip[0].get(k, "nan")) for k in ("cx", "cy", "r"))
        for clip in root.iter(f"{SVG}clipPath")
    }


@pytest.mark.parametrize("mode", list(PhaseRenderMode))
def test_d08_drawing_labels_every_coil_and_fills_every_eye_clipped(
    mode: PhaseRenderMode, outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path
) -> None:
    """Ruling a 1-2 (F1). Catches a drawing whose phases and polarities rest on the legend alone, in either mode."""
    _, root = _written(outcome_of("spiral_12c10p_d08"), tmp_path, mode)
    labels = [t.text for t in _classes(root, "coil-label")]
    # D08 coil polarities from compute on main c4c9e8f (verified by running geometry_scene)
    assert sorted(labels) == sorted("A1+ A2− A3− A4+ B1− B2+ B3+ B4− C1+ C2− C3− C4+".split())
    eyes = _classes(root, "eye")
    discs = _clip_discs(root)
    assert len(eyes) == 12
    for eye in eyes:
        clip = re.fullmatch(r"url\(#(.+)\)", eye.get("clip-path", ""))
        assert clip is not None and clip.group(1) in discs
        hatch = eye.find(f"{SVG}path")
        assert (hatch is None) == (eye.get("data-phase") == "A")
        if hatch is not None:
            cx, cy, r = discs[clip.group(1)]
            points = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", hatch.get("d", ""))]
            for x, y in zip(points[::2], points[1::2], strict=True):
                assert math.hypot(x - cx, y - cy) <= r + 1e-5  # chords end on the circle; the file rounds to 1e-6 mm


def test_d08_hatch_pitch_is_0_4_mm_at_1_to_1(outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path) -> None:
    """Design_spec 3.3. Catches the screen pitch (4 px) or the old 0.8 mm pattern leaking into the file."""
    _, root = _written(outcome_of("spiral_12c10p_d08"), tmp_path, PhaseRenderMode.GREYSCALE_HATCH)
    hatch = next(e for e in _classes(root, "eye") if e.get("data-phase") == "B").find(f"{SVG}path")
    assert hatch is not None
    starts = [tuple(map(float, m)) for m in re.findall(r"M (-?[\d.]+) (-?[\d.]+)", hatch.get("d", ""))]
    (x0, y0), (x1, y1) = starts[0], starts[1]
    # chords at 45 degrees: neighbouring chords are offset along (-sin 45, cos 45)
    offset = abs(-(x1 - x0) * math.sin(math.pi / 4) + (y1 - y0) * math.cos(math.pi / 4))
    assert offset == pytest.approx(0.4, abs=1e-6)


def test_drawings_never_dash_copper_or_legend_bars(
    example_id: str, outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path
) -> None:
    """Design_spec 3.3 and F2. Catches a dashed or dotted line, which reads as an open circuit."""
    for mode in PhaseRenderMode:
        _, root = _written(outcome_of(example_id), tmp_path, mode)
        assert not [e for e in root.iter() if e.get("stroke-dasharray")], mode


def test_footer_fits_inside_the_drawing(
    example_id: str, outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path
) -> None:
    """F3. Catches a footer cut at the right edge ("DRC FAILE"); measured with fontTools, not the writer's reader."""
    _, root = _written(outcome_of(example_id), tmp_path, PhaseRenderMode.COLOUR)
    x_min, _, width, _ = map(float, root.get("viewBox", "").split())
    (stamp,) = _classes(root, "stamp")
    font = TTFont(resource_root() / "fonts" / "Inter" / "InterVariable.ttf")
    cmap, hmtx = font.getBestCmap(), font["hmtx"]
    size = float(root.find(f"{SVG}g[@id='legend']").get("font-size"))
    text_mm = sum(hmtx[cmap[ord(c)]][0] for c in stamp.text or "") * size / font["head"].unitsPerEm
    assert float(stamp.get("x", "nan")) + text_mm <= x_min + width
