"""Item 1a: every SVG, parsed with xml.etree, against the Layout counts of `embodic.api.compute`."""

import math
import re
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import UTC, datetime, timedelta

import pytest

import embodic
from conftest import EXAMPLE_STEMS, FULL_TURN, example_document, layer_tallies, outcome_of
from embodic.io.exporters import PhaseRenderMode
from embodic.io.svg_writer import write_svg

SVG = "{http://www.w3.org/2000/svg}"
META = "{urn:embodic:export:1}"
MINUS = "−"
pytestmark = pytest.mark.req("REQ-F-16", "REQ-N-14", "REQ-N-23")

PAINT_ATTRIBUTES = {"stroke", "fill", "fill-opacity", "stroke-opacity", "opacity", "style", "data-render-mode"}


def svg_of(stem: str, mode: PhaseRenderMode, folder) -> ET.Element:
    """Write one SVG of an example once per session and parse it."""
    path = folder / f"{stem}_{mode.value}.svg"
    if not path.exists():
        result = write_svg(outcome_of(stem), path, mode=mode, allow_drc_errors=True)
        assert hasattr(result, "path"), result
    return ET.parse(path).getroot()


def by_id(root: ET.Element, ident: str) -> ET.Element:
    """Return the single element with an id."""
    found = [e for e in root.iter() if e.get("id") == ident]
    assert len(found) == 1, f"one element with id {ident}, found {len(found)}"
    return found[0]


def segment_commands(d: str) -> Counter:
    """Count the path commands of an SVG path data string."""
    return Counter(c for c in re.findall(r"[A-Za-z]", d) if c not in "eE")


@pytest.mark.parametrize("stem", EXAMPLE_STEMS)
@pytest.mark.parametrize("mode", list(PhaseRenderMode))
def test_copper_vias_pads_holes_per_board_layer_and_phase_equal_the_layout(stem, mode, export_dir):
    """Catches a writer that drops or duplicates a path, a primitive, a via, a pad or a screw hole."""
    root = svg_of(stem, mode, export_dir)
    for k, layout in enumerate(outcome_of(stem).boards.boards, start=1):
        expected = layer_tallies(layout)
        seen: dict[tuple[str, str], list[int]] = {}
        for layer in layout.copper_layers:
            group = by_id(root, f"b{k}-cu-{layer}")
            for phase_group in group:
                key = (layer, phase_group.get("data-phase"))
                row = seen.setdefault(key, [0, 0, 0])
                for copper in phase_group:
                    row[0] += 1
                    cmds = Counter()
                    for p in copper.iter(f"{SVG}path"):
                        cmds += segment_commands(p.get("d"))
                    row[1] += cmds["L"]
                    row[2] += cmds["A"]
        want = {key: [t.paths, t.lines, t.arcs + t.full_circles] for key, t in expected.items() if t.paths}
        assert seen == want, f"board {k}: (paths, L, A) per (layer, phase)"
        vias = [e for e in by_id(root, f"b{k}-vias") if e.get("class") == "via"]
        pads = [e for e in by_id(root, f"b{k}-pads") if e.get("class") == "pad"]
        holes = [e for e in root.iter() if e.get("class") == "hole"]
        assert (len(vias), len(pads)) == (len(layout.vias), len(layout.pads))
        assert len(holes) == sum(len(b.outline.holes) for b in outcome_of(stem).boards.boards)


@pytest.mark.parametrize("stem", ["wave_16p_example", "serpentine_16p_example"])
def test_screw_holes_sit_where_the_design_puts_them(stem, export_dir):
    """Catches a hole at the wrong pitch radius, angle or diameter (design: `/outline/screws`)."""
    root = svg_of(stem, PhaseRenderMode.COLOUR, export_dir)
    spec = example_document(stem)["design"]["outline"]["screws"][0]
    want = sorted(
        (
            round(
                spec["pitch_radius_mm"]
                * math.cos(math.radians(spec["angle_offset_deg"]) + i * FULL_TURN / spec["count"]),
                3,
            ),
            round(
                spec["pitch_radius_mm"]
                * math.sin(math.radians(spec["angle_offset_deg"]) + i * FULL_TURN / spec["count"]),
                3,
            ),
            spec["hole_diameter_mm"] / 2,
        )
        for i in range(spec["count"])
    )
    got = sorted(
        (round(float(e.get("cx")), 3), round(float(e.get("cy")), 3), float(e.get("r")))
        for e in root.iter()
        if e.get("class") == "hole"
    )
    assert got == want


def expected_spiral_labels(layout) -> Counter:
    """Derive the spiral coil labels from the Layout: phase, number in element order, sign."""
    coils = sorted({(p.phase.value, p.element, p.polarity) for p in layout.paths if p.polarity != 0 and p.phase})
    number: Counter = Counter()
    labels: Counter = Counter()
    for phase, _element, polarity in coils:
        number[phase] += 1
        labels[f"{phase}{number[phase]}{'+' if polarity > 0 else MINUS}"] += 1
    return labels


# By hand: 16 poles x 3 phases = 48 belts; polarity alternates pole to pole, so 8 of each phase and sign.
WAVE_BELTS = Counter({f"{ph}{s}": 8 for ph in "ABC" for s in ("+", MINUS)})
# Ruling b / D-039 d: 4 per phase, no sign.
SERPENTINE_LABELS = Counter({ph: 4 for ph in "ABC"})


def label_texts(root: ET.Element) -> Counter:
    """Count the coil-label texts of an SVG."""
    return Counter(e.text for e in root.iter() if e.get("class") == "coil-label")


@pytest.mark.parametrize("stem", ["spiral_12c10p_d08", "spiral_12c14p", "spiral_12c16p_default"])
@pytest.mark.parametrize("mode", list(PhaseRenderMode))
def test_every_spiral_coil_has_its_label_and_a_clipped_eye(stem, mode, export_dir):
    """Catches a missing or misnumbered coil label, a hyphen for U+2212, or a label without its eye fill."""
    root = svg_of(stem, mode, export_dir)
    want = expected_spiral_labels(outcome_of(stem).boards.boards[0])
    assert sum(want.values()) == 12, "by hand: every spiral example has 12 coils"
    assert label_texts(root) == want
    clips = {e.get("id") for e in root.iter(f"{SVG}clipPath")}
    eyes = [e for e in root.iter() if e.get("class") == "eye"]
    refs = [re.fullmatch(r"url\(#(.+)\)", e.get("clip-path") or "") for e in eyes]
    assert len(eyes) == 12 and all(m and m.group(1) in clips for m in refs), "12 eyes, each clipped to its disc"


@pytest.mark.parametrize("mode", list(PhaseRenderMode))
def test_serpentine_has_four_labels_per_phase(mode, export_dir):
    """Catches a serpentine drawing that names a phase fewer or more than four times (ruling b)."""
    assert label_texts(svg_of("serpentine_16p_example", mode, export_dir)) == SERPENTINE_LABELS


@pytest.mark.parametrize("mode", list(PhaseRenderMode))
def test_wave_has_one_label_per_belt(mode, export_dir):
    """Catches a wave drawing that leaves a belt unnamed (brief 1a: per belt, D-039 d)."""
    assert label_texts(svg_of("wave_16p_example", mode, export_dir)) == WAVE_BELTS


@pytest.mark.parametrize("stem", EXAMPLE_STEMS)
def test_metadata_holds_version_hash_time_and_drc_verdict(stem, export_dir):
    """Catches a stamp with another design's hash, a stale version, a missing time or a wrong verdict."""
    outcome = outcome_of(stem)
    stamps = list(svg_of(stem, PhaseRenderMode.COLOUR, export_dir).iter(f"{META}export"))
    assert len(stamps) == 1
    stamp = stamps[0].attrib
    assert stamp["embodic_version"] == embodic.__version__
    assert stamp["design_hash"] == outcome.design_hash
    when = datetime.strptime(stamp["generated_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    assert timedelta(0) <= datetime.now(UTC) - when < timedelta(hours=1)
    verdict = all(len(r.violations) == 0 for r in outcome.drc)
    assert stamp["drc_passed"] == ("true" if verdict else "false")


def without_paint(e: ET.Element) -> tuple:
    """Return an element tree with the paint attributes and the time stamp left out."""
    attrs = tuple(sorted((k, v) for k, v in e.attrib.items() if k not in PAINT_ATTRIBUTES and k != "generated_utc"))
    return (e.tag, attrs, (e.text or "").strip(), tuple(without_paint(c) for c in e))


@pytest.mark.parametrize("stem", EXAMPLE_STEMS)
def test_greyscale_and_colour_differ_only_in_paint(stem, export_dir):
    """Catches a render mode that moves, adds or drops geometry or text instead of changing ink."""
    colour = svg_of(stem, PhaseRenderMode.COLOUR, export_dir)
    grey = svg_of(stem, PhaseRenderMode.GREYSCALE_HATCH, export_dir)
    assert without_paint(colour) == without_paint(grey)
