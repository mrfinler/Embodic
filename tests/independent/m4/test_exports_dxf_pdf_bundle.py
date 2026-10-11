"""Items 1b to 1e: DXF (ezdxf as a parser), PDF (pypdf, pdftotext), bundle ZIP, DRC refusal."""

import math
import re
import subprocess
import zipfile
from collections import Counter, defaultdict
from dataclasses import fields

import ezdxf
import pypdf
import pytest

from conftest import EXAMPLE_STEMS, ROOT, drc_all_passed, example_document, layer_tallies, outcome_of
from embodic.io.bundle import write_bundle
from embodic.io.dxf_writer import write_dxf
from embodic.io.exporters import ExportKind, PhaseRenderMode
from embodic.io.report import write_report_pdf
from embodic.io.svg_writer import write_svg

pytestmark = pytest.mark.req("REQ-F-09", "REQ-F-16", "REQ-F-29", "REQ-F-33")

NBSP = "\u00a0"
COINCIDENT_MM = 1e-6
PREFIX = {"": 1.0, "n": 1e-9, "µ": 1e-6, "m": 1e-3, "k": 1e3, "M": 1e6}
# Own table of the unit text the UI prints for each canonical unit code of the key results.
UNIT_TEXT = {
    "V_s_per_rad": "V·s/rad",
    "N_m_per_A": "N·m/A",
    "rpm_per_V": "rpm/V",
    "one": "(dimensionless)",
    "ohm": "Ω",
    "V": "V",
    "N_m": "N·m",
    "W": "W",
    "N_m_per_sqrt_W": "N·m/√W",
    "A_per_mm2": "A/mm²",
    "mm": "mm",
    "H": "H",
    "A": "A",
    "g": "g",
    "K": "K",
}
FONT_FILES = (
    "Inter/Inter-Regular.ttf",
    "Inter/Inter-SemiBold.ttf",
    "JetBrainsMono/JetBrainsMono-Regular.ttf",
)
COLOPHON = "Set in Inter and JetBrains Mono, SIL Open Font License 1.1."


def dxf_of(stem: str, part: str, folder):
    """Write one DXF part of an example once per session and parse it with ezdxf."""
    path = folder / f"{stem}_{part}.dxf"
    if not path.exists():
        result = write_dxf(outcome_of(stem), path, part, allow_drc_errors=True)
        assert hasattr(result, "path"), result
    return ezdxf.readfile(path)


def xy(v) -> tuple[float, float]:
    """Return the plane coordinates of an ezdxf vector."""
    return (v.x, v.y)


def entity_length(e) -> float:
    """Return the length of a LINE, ARC or CIRCLE entity, mm."""
    kind = e.dxftype()
    if kind == "LINE":
        return math.dist(xy(e.dxf.start), xy(e.dxf.end))
    if kind == "ARC":
        span = (e.dxf.end_angle - e.dxf.start_angle) % 360.0
        return e.dxf.radius * math.radians(span or 360.0)
    if kind == "CIRCLE":
        return 2 * math.pi * e.dxf.radius
    raise AssertionError(kind)


@pytest.mark.parametrize("stem", EXAMPLE_STEMS)
def test_complete_dxf_has_every_primitive_and_the_copper_length_of_each_layer(stem, export_dir):
    """Catches a dropped, duplicated or reversed-sweep entity (length off), or a layer mix-up."""
    doc = dxf_of(stem, "complete", export_dir)
    count: Counter = Counter()
    length: defaultdict = defaultdict(float)
    for e in doc.modelspace():
        copper = re.match(r"CU\d+_([^_]+)_", e.dxf.layer)
        if copper:
            layer = copper.group(1)
            count[layer] += 1
            length[layer] += entity_length(e)
    layout = outcome_of(stem).boards.boards[0]
    want_count: Counter = Counter()
    want_length: defaultdict = defaultdict(float)
    for (layer, _phase), t in layer_tallies(layout).items():
        want_count[layer] += t.lines + t.arcs
        want_length[layer] += t.length_mm
    assert count == want_count
    for layer in want_length:
        assert abs(length[layer] - want_length[layer]) <= 1e-6, (layer, length[layer] - want_length[layer])
    layers = Counter(e.dxf.layer for e in doc.modelspace())
    assert layers["VIA_PAD"] == len(layout.vias) and layers["VIA_DRILL"] == len(layout.vias)
    assert layers["PAD_DRILL"] == sum(1 for p in layout.pads if p.drill_mm > 0)


def end_points(e) -> list[tuple[float, float]]:
    """Return the two end points of a LINE or ARC; a CIRCLE has none."""
    if e.dxftype() == "LINE":
        return [xy(e.dxf.start), xy(e.dxf.end)]
    if e.dxftype() == "ARC":
        return [xy(e.start_point), xy(e.end_point)]
    return []


@pytest.mark.parametrize("stem", EXAMPLE_STEMS)
def test_outline_dxf_is_closed_and_holds_board_and_bore(stem, export_dir):
    """Catches a gap or overlap in the outline (an open loop a fab rejects) or a missing bore."""
    entities = list(dxf_of(stem, "outline", export_dir).modelspace())
    ends = [p for e in entities for p in end_points(e)]
    for p in ends:
        shared = sum(1 for q in ends if math.dist(p, q) <= COINCIDENT_MM)
        assert shared == 2, f"end point {p} shared by {shared} entity ends"
    design = example_document(stem)["design"]["outline"]
    radii = {round(e.dxf.radius, 6) for e in entities if e.dxftype() in ("ARC", "CIRCLE")}
    if design["bore"]["shape"] == "circle":
        assert round(design["bore"]["radius_mm"], 6) in radii
    if design["board"]["shape"] == "circle":
        assert round(design["board"]["radius_mm"], 6) in radii


@pytest.mark.parametrize("stem", ["wave_16p_example", "serpentine_16p_example"])
def test_screws_dxf_has_one_circle_per_hole_at_the_design_diameter(stem, export_dir):
    """Catches a screws file with a missing hole or the screw size instead of the clearance diameter."""
    entities = list(dxf_of(stem, "screws", export_dir).modelspace())
    spec = example_document(stem)["design"]["outline"]["screws"][0]
    assert [e.dxftype() for e in entities] == ["CIRCLE"] * spec["count"]
    assert {round(2 * e.dxf.radius, 9) for e in entities} == {spec["hole_diameter_mm"]}


def pdf_of(stem: str, folder):
    """Write the report of an example once per session."""
    path = folder / f"{stem}_report.pdf"
    if not path.exists():
        result = write_report_pdf(outcome_of(stem), path)
        assert hasattr(result, "path"), result
    return path


def key_result_rows(path) -> list[str]:
    """Return the rows of the Key results table on page 1."""
    text = pypdf.PdfReader(path).pages[0].extract_text()
    lines = text.splitlines()
    start = lines.index("Quantity Value Status") + 1
    end = lines.index("DRC summary")
    return lines[start:end]


def scalar_traceables(analysis):
    """Yield the scalar Traceable fields of an AnalysisResult in declaration order."""
    for f in fields(analysis):
        value = getattr(analysis, f.name)
        if hasattr(value, "unit") and isinstance(value.value, float):
            yield f.name, value


def three_significant(x: float) -> float:
    """Round to three significant figures."""
    return 0.0 if x == 0 else float(f"{x:.3g}")


@pytest.mark.parametrize("stem", EXAMPLE_STEMS)
def test_key_results_print_each_value_to_three_figures_with_unit_and_status(stem, export_dir):
    """Catches a value off by a prefix, more or fewer figures, a plain space joiner, a wrong unit or status."""
    rows = key_result_rows(pdf_of(stem, export_dir))
    expected = list(scalar_traceables(outcome_of(stem).analysis))
    assert len(rows) == len(expected) == 30
    for row, (name, t) in zip(rows, expected, strict=True):
        m = re.search(r" (−?[0-9.]+)\u00a0(\S+) " + re.escape(str(t.status)) + r"(?: \((.+)\))?$", row)
        assert m, (name, row, str(t.status))
        if t.label:
            assert m.group(3) == t.label, (name, row)
        number, unit = m.group(1), m.group(2)
        base = UNIT_TEXT[str(t.unit)]
        prefix = unit[: len(unit) - len(base)]
        assert unit.endswith(base) and prefix in PREFIX, (name, unit, base)
        shown = float(number.replace("−", "-"))
        assert shown == three_significant(t.value / PREFIX[prefix]), (name, number, t.value)
        assert len(number.replace("−", "").replace(".", "").lstrip("0")) <= 3, (name, number)
        if prefix:
            assert 1 <= abs(shown) < 1000, (name, number, unit)


def embedded_font_files(path) -> list[bytes]:
    """Return each distinct FontFile2 stream embedded in the PDF."""
    reader = pypdf.PdfReader(path)
    found = []
    for page in reader.pages:
        for font in page["/Resources"].get("/Font", {}).values():
            font = font.get_object()
            for descendant in font.get("/DescendantFonts", []):
                descriptor = descendant.get_object()["/FontDescriptor"].get_object()
                data = descriptor["/FontFile2"].get_object().get_data()
                if data not in found:
                    found.append(data)
    return found


@pytest.mark.parametrize("stem", ["spiral_12c10p_d08", "wave_16p_example"])
def test_pdf_embeds_exactly_the_bundled_font_files(stem, export_dir):
    """Catches a subset, a substituted system font, the old variable Inter or a missing face."""
    want = sorted((ROOT / "resources" / "fonts" / f).read_bytes() for f in FONT_FILES)
    assert sorted(embedded_font_files(pdf_of(stem, export_dir))) == want


@pytest.mark.parametrize("stem", ["spiral_12c10p_d08", "wave_16p_example"])
def test_colophon_is_the_last_line_of_the_report(stem, export_dir):
    """Catches a colophon that sits before other text or appears twice (ruling f)."""
    text = subprocess.run(
        ["pdftotext", "-layout", str(pdf_of(stem, export_dir)), "-"], capture_output=True, text=True, check=True
    ).stdout
    lines = [ln.strip() for ln in text.replace("\f", "\n").splitlines() if ln.strip()]
    assert lines[-1] == COLOPHON
    assert text.count(COLOPHON) == 1


def test_bundle_holds_the_selected_files_and_a_readme_naming_each(export_dir):
    """Catches a missing member, a stray temp path, or a README that omits a file it ships with."""
    kinds = [
        ExportKind.SVG,
        ExportKind.DXF_COMPLETE,
        ExportKind.DXF_OUTLINE,
        ExportKind.PDF_REPORT,
        ExportKind.PROJECT_JSON,
    ]
    path = export_dir / "d08_bundle.zip"
    result = write_bundle(outcome_of("spiral_12c10p_d08"), kinds, path)
    assert isinstance(result, tuple), result
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        readme = z.read("README.txt").decode("utf-8")
    assert len(names) == len(kinds) + 1 and "README.txt" in names
    assert all("/" not in n for n in names), names
    for name in names:
        if name != "README.txt":
            assert name in readme, f"README names {name}"
    assert sorted(names) == sorted(str(s.path) for s in result)


WAVE = "wave_16p_example"
GATED = {
    "svg": lambda o, p, ok: write_svg(o, p / "w.svg", allow_drc_errors=ok),
    "dxf_complete": lambda o, p, ok: write_dxf(o, p / "w_c.dxf", "complete", allow_drc_errors=ok),
    "dxf_outline": lambda o, p, ok: write_dxf(o, p / "w_o.dxf", "outline", allow_drc_errors=ok),
    "dxf_screws": lambda o, p, ok: write_dxf(o, p / "w_s.dxf", "screws", allow_drc_errors=ok),
    "bundle": lambda o, p, ok: write_bundle(
        o, [ExportKind.SVG, ExportKind.PDF_REPORT], p / "w.zip", allow_drc_errors=ok
    ),
}


@pytest.mark.parametrize("writer", sorted(GATED))
def test_wave_export_is_refused_without_confirmation_and_stamped_false_with_it(writer, tmp_path):
    """Catches a writer that ships a failing design unasked, or one that stamps drc_passed=true on it."""
    outcome = outcome_of(WAVE)
    assert not drc_all_passed(outcome), "precondition: the wave example fails DRC (186 violations)"
    refused = GATED[writer](outcome, tmp_path, False)
    assert getattr(refused, "reason", None) == "drc_errors_not_confirmed"
    assert list(tmp_path.iterdir()) == [], "a refusal writes nothing"
    written = GATED[writer](outcome, tmp_path, True)
    files = list(tmp_path.iterdir())
    assert files and not hasattr(written, "reason")
    for f in files:
        if f.suffix == ".zip":
            with zipfile.ZipFile(f) as z:
                blob = b"".join(z.read(n) for n in z.namelist() if n.endswith(".svg"))
        else:
            blob = f.read_bytes()
        assert re.search(rb'drc_passed=?"?false', blob.replace(b"\n", b"")), f.name
        assert b"drc_passed=true" not in blob and b'drc_passed="true"' not in blob


def test_wave_pdf_documents_the_failed_drc_instead_of_refusing(tmp_path):
    """D-038d: the report never refuses for DRC. Catches a report that hides the failure (stamp true)."""
    result = write_report_pdf(outcome_of(WAVE), tmp_path / "w.pdf", mode=PhaseRenderMode.GREYSCALE_HATCH)
    assert result.pages >= 1
    first = pypdf.PdfReader(tmp_path / "w.pdf").pages[0].extract_text()
    assert "drc_passed false" in first
