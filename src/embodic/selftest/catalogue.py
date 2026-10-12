"""The 45 self-test checks of interfaces.md section 14, in its order.

Each expected value and tolerance is a literal copied from the named pytest test, because the wheel carries neither
`docs/` nor `tests/`. UT-SLF-02 keeps the CF-09 rows and the design hashes equal to their sources.
"""

import functools
import math
import zipfile
from collections.abc import Callable
from pathlib import Path

import numpy as np

from embodic.api import compute
from embodic.errors import Severity
from embodic.geometry.arrays import LayoutArrays
from embodic.geometry.details import SpiralDetail
from embodic.io.bundle import write_bundle
from embodic.io.examples import load_example
from embodic.io.exporters import ExportKind
from embodic.io.project import ProjectFile, load_project, project_provenance, save_project
from embodic.model.rotor import ArcMagnet, RotorSpec, RotorType
from embodic.model.vocabulary import ConnectionTopology
from embodic.outcome import ComputeOutcome
from embodic.physics import (
    copper_resistivity_ohm_m,
    field_harmonic,
    line_resistance_ohm,
    path_resistance_ohm,
    phase_constants,
    via_resistance_ohm,
)
from embodic.selftest.model import SelfTestCheck, SelfTestGroup, SelfTestValue
from embodic.winding import assign_phases
from embodic.winding.winding_factors import distribution_factor

KERNELS = "tests/unit/physics/test_kernels.py"
SPIRAL_GENERATE = "tests/unit/generators/test_spiral_generate.py"
EXAMPLES_TEST = "tests/unit/embodic_io/project/test_examples.py"
RHO20_OHM_M, ALPHA20_PER_K = 1.7241e-8, 0.00393  # test_kernels.py l.27-28 (registry EQ-10, EV-53)
CF11, D08 = "spiral_12c16p_default", "spiral_12c10p_d08"

# CF-09 rows of docs/phase2/engineering/oracle_cases.json: (Q, poles, pattern, kd1).
CF09_ROWS: tuple[tuple[int, int, str, float], ...] = (
    (12, 10, "AabBCcaABbcC", 0.9659258262890683),
    (12, 14, "ACcbBAacCBba", 0.9659258262890683),
    (12, 16, "ACBACBACBACB", 1.0),
    (18, 16, "AabBbcCcaAabBbcCca", 0.9597950805239388),
    (24, 14, "ABCbcabABCAcabcBCABabcaC", 0.9576621969425487),
    (24, 22, "AaABbBbcCcCAaAabBbBCcCca", 0.9576621969425487),
    (24, 26, "AacCcCBbBbaAaACcCcbBbBAa", 0.9576621969425487),
    (9, 8, "AabBbcCca", 0.9597950805239388),
    (15, 16, "AaACcCcCBbBbBAa", 0.9566772233505626),
)
# EXAMPLE_HASHES of test_examples.py (l.34), in the order the catalogue lists the examples.
EXAMPLE_HASHES: tuple[tuple[str, str], ...] = (
    ("spiral_12c16p_default", "sha256:ac4fab5db06f9e8f733dc495080deeddfe0bcf58faa31ebb7ec841c1b27d9c09"),
    ("spiral_12c14p", "sha256:4a1997029f7063676bdb9eab703c462f4240d84916a5ddf3deec044fa4391bc1"),
    ("spiral_12c10p_d08", "sha256:327919a0eef55ce2c458635f6160047af7654ebd0a04e818ee225fd5f69615d8"),
    ("serpentine_16p_example", "sha256:8ec4c23449a0be2bf4ee6ba337b72b2e93e5906e6b53ba8ba7c441d4872dd1ca"),
    ("wave_16p_example", "sha256:3131a61975766c38984df5065b01f255875b79ebcfa831624c10c5db5d5c82e8"),
)
COMPUTES_SOURCE = {
    "spiral_12c16p_default": f"{EXAMPLES_TEST}::test_ut_io_08_example_validates_and_computes_drc_clean",
    "spiral_12c14p": f"{EXAMPLES_TEST}::test_ut_io_08_example_validates_and_computes_drc_clean",
    "spiral_12c10p_d08": f"{EXAMPLES_TEST}::test_ut_io_08_example_validates_and_computes_drc_clean",
    "serpentine_16p_example": (
        "tests/unit/generators/serpentine/test_serpentine_example.py::test_the_example_validates_and_computes_drc_clean"
    ),
    "wave_16p_example": (
        "tests/unit/ui/results/test_rail_cards.py::test_drc_card_of_the_wave_example_counts_186_failures"
    ),
}
Measure = Callable[[Path], SelfTestValue]
BUNDLE_MEMBERS = ("README.txt", "motor.dxf", "motor.embodic.json", "motor.svg", "motor_outline.dxf", "motor_report.pdf")


@functools.cache
def _computed(example_id: str) -> tuple[ProjectFile, ComputeOutcome]:
    """Compute a packaged example once per run: eight checks read the default spiral (run_selftests forgets it)."""
    ref, design = load_example(example_id)
    project = ProjectFile(design=design, origin=ref)
    outcome = compute(design, project_provenance(project))
    assert outcome is not None, "compute without a cancel token always returns an outcome"
    return project, outcome


def forget_computed() -> None:
    """Drop the computed examples, so the next run computes them again and memory is freed."""
    _computed.cache_clear()


def _rotor() -> RotorSpec:
    magnet = ArcMagnet(pole_arc_ratio=0.85, r_inner_mm=18.0, r_outer_mm=38.0, thickness_mm=3.0)
    return RotorSpec(
        poles=2,
        rotor_type=RotorType.DOUBLE,
        magnet=magnet,
        remanence_t=1.3,
        recoil_permeability=1.05,
        air_gap_mm=0.8,
        back_iron_thickness_mm=5.0,
    )


def _cf01(_: Path) -> float:
    bz, _bt = field_harmonic(1, np.array([1e5]), np.array([0.0]), _rotor(), 1.1, np.array(0.85))
    return float(bz[0])


def _track_resistance_of(temperature_c: float, index: int) -> Measure:
    """Path `index` of a 1000 mm line and a 90 degree arc of r 30 mm, 0.5 mm wide and 34.8 um thick."""

    def resistance(_: Path) -> float:
        arrays = LayoutArrays(
            lines={"F.Cu": np.array([[0.0, 0.0, 1000.0, 0.0, 0.5]])},
            arcs={"F.Cu": np.array([[0.0, 0.0, 30.0, 0.0, math.pi / 2, 0.5]])},
            path_index={"F.Cu": np.array([0, 1], dtype=np.int64)},
            prim_index={"F.Cu": np.array([0, 0], dtype=np.int64)},
            vias=np.zeros((0, 4)),
        )
        rho = copper_resistivity_ohm_m(temperature_c, RHO20_OHM_M, ALPHA20_PER_K)
        return float(path_resistance_ohm(arrays, {"F.Cu": 0.0348}, rho)[index])

    return resistance


def _via(_: Path) -> float:
    rho20 = copper_resistivity_ohm_m(20.0, RHO20_OHM_M, ALPHA20_PER_K)
    return via_resistance_ohm(0.3, 25.0, 1.6, rho20, 1)


def _pattern_of(q: int, poles: int) -> Measure:
    def pattern(_: Path) -> str:
        return "".join(c.phase.value if c.polarity == 1 else c.phase.value.lower() for c in assign_phases(q, poles))

    return pattern


def _kd1_of(q: int, poles: int) -> Measure:
    return lambda _: distribution_factor(assign_phases(q, poles), 1, q)


def _hash_of(example_id: str) -> Measure:
    return lambda _: _computed(example_id)[1].design_hash


def _computes_of(example_id: str) -> Measure:
    def computes(_: Path) -> bool:
        outcome = _computed(example_id)[1]
        return outcome.analysis is not None and not any(i.severity is Severity.ERROR for i in outcome.issues)

    return computes


def _spiral_detail(example_id: str) -> SpiralDetail:
    boards = _computed(example_id)[1].boards
    detail = boards.boards[0].detail if boards is not None else None
    if not isinstance(detail, SpiralDetail):
        raise TypeError(f"{example_id} built no spiral board")
    return detail


def _track_length_of(example_id: str) -> Measure:
    return lambda _: float(_spiral_detail(example_id).track_length_per_coil_layer_mm["X"])


def _turns(_: Path) -> int:
    return _spiral_detail(CF11).turns_achieved


def _drc_violations(_: Path) -> int:
    (report,) = _computed(CF11)[1].drc or ()
    return report.violation_count


def _drc_least_trace_gap(_: Path) -> float:
    (report,) = _computed(CF11)[1].drc or ()
    least = next(s.measured_min_mm for s in report.summaries if s.kind.value == "trace_trace")
    if least is None:
        raise ValueError("the check measured no track pair")
    return least


def _roundtrip(scratch: Path) -> bool:
    project, _ = _computed(CF11)
    first, second = scratch / "a.embodic.json", scratch / "b.embodic.json"
    save_project(first, ProjectFile(design=project.design, origin=project.origin, ui_state={"zoom": 1.5}))
    loaded, _issues = load_project(first)
    assert isinstance(loaded, ProjectFile), "a saved complete design loads as a project"
    save_project(second, loaded)
    return first.read_bytes() == second.read_bytes()


def _bundle(scratch: Path) -> tuple[str, ...]:
    bundle = scratch / "motor.zip"
    kinds = [ExportKind.SVG, ExportKind.DXF_COMPLETE, ExportKind.DXF_OUTLINE, ExportKind.PDF_REPORT]
    write_bundle(_computed(CF11)[1], [*kinds, ExportKind.PROJECT_JSON], bundle, allow_drc_errors=True)
    with zipfile.ZipFile(bundle) as archive:
        return tuple(sorted(archive.namelist()))


def _check(
    check_id: str,
    group: SelfTestGroup,
    title: str,
    source_test: str,
    expected: SelfTestValue,
    measure: Measure,
    *,
    unit: str = "",
    rel_tol: float = 0.0,
    abs_tol: float = 0.0,
) -> SelfTestCheck:
    return SelfTestCheck(
        id=check_id,
        group=group,
        title=title,
        source_test=source_test,
        expected=expected,
        unit=unit,
        measure=measure,
        rel_tol=rel_tol,
        abs_tol=abs_tol,
    )


CF = SelfTestGroup.CLOSED_FORM
CF04 = f"{KERNELS}::test_cf04_track_resistance_at_20_and_60_degc"
CF06 = f"{KERNELS}::test_cf06_star_and_delta_constants"
CF06_LINE = "tests/unit/physics/test_closed_forms_m2e2.py::test_eq23_cf06_star_and_delta"
CF09_PATTERN = "tests/unit/winding/test_star_of_slots.py::test_cf09_patterns_and_balance"
CF09_KD1 = "tests/unit/winding/test_winding_factors.py::test_ut_wnd_05_cf09_distribution_factor"
CF11_SOURCE = f"{SPIRAL_GENERATE}::test_default_track_length_matches_cf11"
DRC_SOURCE = f"{SPIRAL_GENERATE}::test_default_example_passes_drc"
STAR, DELTA = ConnectionTopology.STAR, ConnectionTopology.DELTA

SELFTESTS: tuple[SelfTestCheck, ...] = (
    _check(
        "ST-CF01",
        CF,
        "Field fundamental B_z1 of the CF-01 rotor",
        f"{KERNELS}::test_cf01_field_fundamental_equals_the_1d_magnetic_circuit",
        1.162077823241657,
        _cf01,
        unit="T",
        rel_tol=1e-9,
    ),
    _check(
        "ST-CF04-R20",
        CF,
        "Resistance of a 1000 mm track at 20 °C",
        CF04,
        0.9908620689655171,
        _track_resistance_of(20.0, 0),
        unit="ohm",
        rel_tol=1e-12,
    ),
    _check(
        "ST-CF04-R60",
        CF,
        "Resistance of a 1000 mm track at 60 °C",
        CF04,
        1.1466255862068966,
        _track_resistance_of(60.0, 0),
        unit="ohm",
        rel_tol=1e-12,
    ),
    _check(
        "ST-CF04-ARC",
        CF,
        "Resistance of a 90° arc of radius 30 mm at 20 °C",
        CF04,
        0.04669327494874277,
        _track_resistance_of(20.0, 1),
        unit="ohm",
        rel_tol=1e-12,
    ),
    _check(
        "ST-CF04-VIA",
        CF,
        "Resistance of one via barrel",
        f"{KERNELS}::test_cf04_and_ut_phy_11_via_barrel_resistance",
        0.001277202792190775,
        _via,
        unit="ohm",
        rel_tol=1e-12,
    ),
    _check(
        "ST-CF06-KE",
        CF,
        "Line back-EMF constant, star",
        CF06,
        0.017320508075688773,
        lambda _: phase_constants(0.01, STAR, 3, 10).ke_line_v_s_per_rad,
        unit="V·s/rad",
        rel_tol=1e-12,
    ),
    _check(
        "ST-CF06-KT-STAR",
        CF,
        "Torque constant, star",
        CF06,
        0.021213203435596423,
        lambda _: phase_constants(0.01, STAR, 3, 10).kt_n_m_per_a,
        unit="N·m/A",
        rel_tol=1e-12,
    ),
    _check(
        "ST-CF06-KT-DELTA",
        CF,
        "Torque constant, delta",
        CF06,
        0.01224744871391589,
        lambda _: phase_constants(0.01, DELTA, 3, 10).kt_n_m_per_a,
        unit="N·m/A",
        rel_tol=1e-12,
    ),
    _check(
        "ST-CF06-RLL-STAR",
        CF,
        "Line-to-line resistance, star",
        CF06_LINE,
        2.2,
        lambda _: line_resistance_ohm([1.0, 1.1, 1.2], STAR),
        unit="ohm",
        rel_tol=1e-9,
    ),
    _check(
        "ST-CF06-RLL-DELTA",
        CF,
        "Line-to-line resistance, delta",
        CF06_LINE,
        0.731313131,
        lambda _: line_resistance_ohm([1.0, 1.1, 1.2], DELTA),
        unit="ohm",
        rel_tol=1e-9,
    ),
    *(
        _check(
            f"ST-CF09-{q}-{poles}-PATTERN",
            CF,
            f"Phase pattern of {q} coils and {poles} poles",
            CF09_PATTERN,
            pattern,
            _pattern_of(q, poles),
        )
        for q, poles, pattern, _kd1 in CF09_ROWS
    ),
    *(
        _check(
            f"ST-CF09-{q}-{poles}-KD1",
            CF,
            f"Distribution factor k_d1 of {q} coils and {poles} poles",
            CF09_KD1,
            kd1,
            _kd1_of(q, poles),
            abs_tol=1e-9,
        )
        for q, poles, _pattern_text, kd1 in CF09_ROWS
    ),
    _check(
        "ST-CF11-LENGTH",
        CF,
        "Track length per coil layer of the 12-coil 16-pole spiral",
        CF11_SOURCE,
        415.4808,
        _track_length_of(CF11),
        unit="mm",
        abs_tol=5e-5,
    ),
    _check("ST-CF11-TURNS", CF, "Turns of the 12-coil 16-pole spiral", CF11_SOURCE, 10, _turns),
    _check(
        "ST-CF10-LENGTH",
        CF,
        "Track length per coil layer of the D08 spiral",
        f"{SPIRAL_GENERATE}::test_d08_builds_three_turns_with_the_half_closing",
        160.2750,
        _track_length_of(D08),
        unit="mm",
        abs_tol=5e-5,
    ),
    *(
        _check(
            f"ST-EX-{example_id}-HASH",
            SelfTestGroup.EXAMPLES,
            f"Design hash of {example_id}",
            f"{EXAMPLES_TEST}::test_ut_io_08_the_packaged_design_hashes_are_pinned",
            pinned,
            _hash_of(example_id),
        )
        for example_id, pinned in EXAMPLE_HASHES
    ),
    *(
        _check(
            f"ST-EX-{example_id}-COMPUTES",
            SelfTestGroup.EXAMPLES,
            f"{example_id} computes without an error",
            COMPUTES_SOURCE[example_id],
            True,
            _computes_of(example_id),
        )
        for example_id, _pinned in EXAMPLE_HASHES
    ),
    _check(
        "ST-DRC-DEFAULT-CLEAN",
        SelfTestGroup.DRC,
        "Design rule violations of the 12-coil 16-pole spiral",
        DRC_SOURCE,
        0,
        _drc_violations,
    ),
    _check(
        "ST-DRC-DEFAULT-TRACE",
        SelfTestGroup.DRC,
        "Least track-to-track clearance of the 12-coil 16-pole spiral",
        DRC_SOURCE,
        0.2,
        _drc_least_trace_gap,
        unit="mm",
        abs_tol=1e-6,
    ),
    _check(
        "ST-IO-ROUNDTRIP",
        SelfTestGroup.EXPORT,
        "Save, load and save gives the same bytes",
        "tests/unit/embodic_io/project/test_project.py::test_ut_io_01_save_load_save_is_byte_identical",
        True,
        _roundtrip,
    ),
    _check(
        "ST-EXP-BUNDLE",
        SelfTestGroup.EXPORT,
        "Bundle of drawings, report and project file",
        "tests/unit/embodic_io/exporters/test_report_readme_bundle.py::"
        "test_ut_exp_05_bundle_holds_selected_files_and_readme",
        BUNDLE_MEMBERS,
        _bundle,
    ),
)
