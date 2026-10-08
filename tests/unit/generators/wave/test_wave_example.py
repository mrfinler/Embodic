"""The packaged wave example (D-016): file, validation and the compute summary (REQ-F-35)."""

from pathlib import Path

import pytest

import embodic.generators
from embodic.api import compute
from embodic.errors import Severity
from embodic.generators.wave import generate_wave
from embodic.io.examples import examples_dir, list_examples, load_example
from embodic.io.project import ProjectFile, project_provenance
from embodic.model.validate import validate_design
from embodic.model.vocabulary import TopologyKind
from embodic.model.winding_specs import WaveStyle, WaveWindingSpec

from .make_example import EXAMPLE_ID, write_example

pytestmark = pytest.mark.req("REQ-F-35", "REQ-F-25")

# M1 golden (tests/independent/m1/test_gr19_drc.py) found 191 D-006 violations on Xcoil's own wave layout. Xcoil's
# 4 um DRC slack hides the 180 trace-to-via gaps of 0.199965 mm that D-006 (no slack) reports against 0.2 mm; the 11
# trace-to-trace pairs all involve interconnect copper.
EXPECTED_VIOLATIONS = {"trace_via": 180, "trace_trace": 11}


@pytest.fixture
def wired(monkeypatch: pytest.MonkeyPatch) -> None:
    """Register generate_wave in the dispatch table until the registry wiring of U-M3a and U-M3b is merged."""
    monkeypatch.setattr(
        embodic.generators, "GENERATORS", {**embodic.generators.GENERATORS, TopologyKind.WAVE: generate_wave}
    )


def test_the_wave_example_is_packaged_with_an_example_title() -> None:
    """Catches a missing file, a title without the word "Example" (D-014) or a wrong topology label."""
    info = {i.example_id: i for i in list_examples()}[EXAMPLE_ID]
    assert "Example" in info.title and info.topology is TopologyKind.WAVE


def test_the_packaged_file_equals_the_generator_output(tmp_path: Path) -> None:
    """Catches a hand edit of the packaged example that make_example.py would undo."""
    written = write_example(tmp_path)
    assert written.read_bytes() == (examples_dir() / written.name).read_bytes()


def test_the_example_is_xcoils_default_wave_preset_with_two_turns() -> None:
    """D-016. Catches parameters that drift from engine.js l.19-97 (rIn 22, rOut 40, 0.4/0.2 mm, 16 poles, star)."""
    _, design = load_example(EXAMPLE_ID)
    spec = design.winding
    assert isinstance(spec, WaveWindingSpec)
    assert (spec.r_inner_mm, spec.r_outer_mm, spec.turns, spec.trace_width_mm, spec.clearance_mm) == (
        22.0,
        40.0,
        2,
        0.4,
        0.2,
    )
    assert spec.wave_style is WaveStyle.INVOLUTE and spec.bus_width_mm == 1.0
    assert design.rotor.poles == 16 and design.phases == 3 and len(design.stackup.copper_layers()) == 2
    assert [i for i in validate_design(design) if i.severity is Severity.ERROR] == []


def test_the_example_computes_and_reports_its_d006_violations(wired: None) -> None:
    """The example builds and analyses end to end; its DRC result is the one Xcoil's geometry has under D-006.

    Not DRC-clean, by design of the brief: neither the rule nor the Xcoil parameters were changed to hide it.
    """
    ref, design = load_example(EXAMPLE_ID)
    outcome = compute(design, project_provenance(ProjectFile(design=design, origin=ref)))
    assert outcome is not None and outcome.drc is not None and outcome.analysis is not None
    assert [i.code for i in outcome.issues if i.severity is Severity.ERROR] == []
    (report,) = outcome.drc
    counts: dict[str, int] = {}
    for v in report.violations:
        counts[v.kind.value] = counts.get(v.kind.value, 0) + 1
    assert counts == EXPECTED_VIOLATIONS and not report.passed and not outcome.ok
    assert outcome.analysis.ke_line_peak_v_s_per_rad.value > 0.0
