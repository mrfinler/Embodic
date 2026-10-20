# Prepared by: Agent 6 - Software Architecture Specialist - model: claude-opus-5-5
"""Run every check that interfaces.md section 14 puts in the self-test catalogue, against the code on disk (U-D13).

The catalogue copies each expected value from a named pytest test. This probe computes the observed value through the
same public functions the self-test will call and prints one line per check, so a reviewer can rerun the claim that
each expected value holds on main. It also times the source hash of section 3.1.

Run from the repository root:
    PYTHONPATH=src .venv/bin/python docs/phase2/architecture/checks/selftest_probe.py

Exit code 0 when every check passes.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import tempfile
import time
import zipfile
from pathlib import Path

import numpy as np

import embodic
from embodic.api import compute
from embodic.geometry.arrays import LayoutArrays
from embodic.io.bundle import write_bundle
from embodic.io.examples import load_example
from embodic.io.exporters import ExportKind
from embodic.io.project import ProjectFile, load_project, project_provenance, save_project
from embodic.model.rotor import ArcMagnet, RotorSpec, RotorType
from embodic.model.vocabulary import ConnectionTopology
from embodic.physics import (
    copper_resistivity_ohm_m,
    field_harmonic,
    line_resistance_ohm,
    path_resistance_ohm,
    phase_constants,
    via_resistance_ohm,
)
from embodic.winding import assign_phases
from embodic.winding.winding_factors import distribution_factor

REPO = Path(__file__).resolve().parents[4]
RHO20, ALPHA20 = 1.7241e-8, 0.00393  # tests/unit/physics/test_kernels.py l.27-28 (registry EQ-10, EV-53)
COMPUTE_SOURCES = {
    "spiral_12c16p_default": "tests/unit/embodic_io/project/test_examples.py::test_ut_io_08_example_validates_and_computes_drc_clean",
    "spiral_12c14p": "tests/unit/embodic_io/project/test_examples.py::test_ut_io_08_example_validates_and_computes_drc_clean",
    "spiral_12c10p_d08": "tests/unit/embodic_io/project/test_examples.py::test_ut_io_08_example_validates_and_computes_drc_clean",
    "serpentine_16p_example": "tests/unit/generators/serpentine/test_serpentine_example.py::test_the_example_validates_and_computes_drc_clean",
    "wave_16p_example": "tests/unit/ui/results/test_rail_cards.py::test_drc_card_of_the_wave_example_counts_186_failures",
}
# One stamp for both saves of ST-IO-ROUNDTRIP. Two clock reads can fall in different seconds, and saved_utc then makes
# the files differ (U-M5h; src/embodic/selftest/catalogue.py l.43 holds the same value as the catalogue's stamp).
ROUNDTRIP_SAVED_UTC = "2026-10-08T12:00:00Z"
EXAMPLE_HASHES = {  # tests/unit/embodic_io/project/test_examples.py l.34
    "spiral_12c16p_default": "sha256:ac4fab5db06f9e8f733dc495080deeddfe0bcf58faa31ebb7ec841c1b27d9c09",
    "spiral_12c14p": "sha256:4a1997029f7063676bdb9eab703c462f4240d84916a5ddf3deec044fa4391bc1",
    "spiral_12c10p_d08": "sha256:327919a0eef55ce2c458635f6160047af7654ebd0a04e818ee225fd5f69615d8",
    "serpentine_16p_example": "sha256:8ec4c23449a0be2bf4ee6ba337b72b2e93e5906e6b53ba8ba7c441d4872dd1ca",
    "wave_16p_example": "sha256:3131a61975766c38984df5065b01f255875b79ebcfa831624c10c5db5d5c82e8",
}


def rotor() -> RotorSpec:
    magnet = ArcMagnet(pole_arc_ratio=0.85, r_inner_mm=18.0, r_outer_mm=38.0, thickness_mm=3.0)
    return RotorSpec(poles=2, rotor_type=RotorType.DOUBLE, magnet=magnet, remanence_t=1.3, recoil_permeability=1.05,
                     air_gap_mm=0.8, back_iron_thickness_mm=5.0)


def track_arrays() -> LayoutArrays:
    return LayoutArrays(
        lines={"F.Cu": np.array([[0.0, 0.0, 1000.0, 0.0, 0.5]])},
        arcs={"F.Cu": np.array([[0.0, 0.0, 30.0, 0.0, math.pi / 2, 0.5]])},
        path_index={"F.Cu": np.array([0, 1], dtype=np.int64)},
        prim_index={"F.Cu": np.array([0, 0], dtype=np.int64)},
        vias=np.zeros((0, 4)),
    )


def cf09_rows() -> list[dict[str, object]]:
    cases = json.loads((REPO / "docs/phase2/engineering/oracle_cases.json").read_text(encoding="utf-8"))["cases"]
    cf09 = next(c for c in cases if c["case_id"] == "CF-09")
    return cf09["expected"][0]["value"]


def example_outcome(example_id: str):
    ref, design = load_example(example_id)
    return ref, design, compute(design, project_provenance(ProjectFile(design=design, origin=ref)))


def checks() -> list[tuple[str, str, object, object, float, float]]:
    """Return (check id, source test, observed, expected, rel tol, abs tol)."""
    rho20 = copper_resistivity_ohm_m(20.0, RHO20, ALPHA20)
    rho60 = copper_resistivity_ohm_m(60.0, RHO20, ALPHA20)
    r20 = path_resistance_ohm(track_arrays(), {"F.Cu": 0.0348}, rho20)
    r60 = path_resistance_ohm(track_arrays(), {"F.Cu": 0.0348}, rho60)
    star = phase_constants(0.01, ConnectionTopology.STAR, 3, 10)
    delta = phase_constants(0.01, ConnectionTopology.DELTA, 3, 10)
    kernels = "tests/unit/physics/test_kernels.py"
    rows: list[tuple[str, str, object, object, float, float]] = [
        ("ST-CF01", f"{kernels}::test_cf01_field_fundamental_equals_the_1d_magnetic_circuit",
         float(field_harmonic(1, np.array([1e5]), np.array([0.0]), rotor(), 1.1, np.array(0.85))[0][0]),
         1.162077823241657, 1e-9, 0.0),
        ("ST-CF04-R20", f"{kernels}::test_cf04_track_resistance_at_20_and_60_degc", float(r20[0]),
         0.9908620689655171, 1e-12, 0.0),
        ("ST-CF04-R60", f"{kernels}::test_cf04_track_resistance_at_20_and_60_degc", float(r60[0]),
         1.1466255862068966, 1e-12, 0.0),
        ("ST-CF04-ARC", f"{kernels}::test_cf04_track_resistance_at_20_and_60_degc", float(r20[1]),
         0.04669327494874277, 1e-12, 0.0),
        ("ST-CF04-VIA", f"{kernels}::test_cf04_and_ut_phy_11_via_barrel_resistance",
         via_resistance_ohm(0.3, 25.0, 1.6, rho20, 1), 0.001277202792190775, 1e-12, 0.0),
        ("ST-CF06-KE", f"{kernels}::test_cf06_star_and_delta_constants", star.ke_line_v_s_per_rad,
         0.017320508075688773, 1e-12, 0.0),
        ("ST-CF06-KT-STAR", f"{kernels}::test_cf06_star_and_delta_constants", star.kt_n_m_per_a,
         0.021213203435596423, 1e-12, 0.0),
        ("ST-CF06-KT-DELTA", f"{kernels}::test_cf06_star_and_delta_constants", delta.kt_n_m_per_a,
         0.01224744871391589, 1e-12, 0.0),
        ("ST-CF06-RLL-STAR", "tests/unit/physics/test_closed_forms_m2e2.py::test_eq23_cf06_star_and_delta",
         line_resistance_ohm([1.0, 1.1, 1.2], ConnectionTopology.STAR), 2.2, 1e-9, 0.0),
        ("ST-CF06-RLL-DELTA", "tests/unit/physics/test_closed_forms_m2e2.py::test_eq23_cf06_star_and_delta",
         line_resistance_ohm([1.0, 1.1, 1.2], ConnectionTopology.DELTA), 0.731313131, 1e-9, 0.0),
    ]
    for row in cf09_rows():
        q, poles = int(row["Q"]), int(row["poles"])
        assignment = assign_phases(q, poles)
        pattern = "".join(c.phase.value if c.polarity == 1 else c.phase.value.lower() for c in assignment)
        rows.append((f"ST-CF09-{q}-{poles}-PATTERN", "tests/unit/winding/test_star_of_slots.py::test_cf09_patterns_and_balance",
                     pattern, row["pattern"], 0.0, 0.0))
        rows.append((f"ST-CF09-{q}-{poles}-KD1",
                     "tests/unit/winding/test_winding_factors.py::test_ut_wnd_05_cf09_distribution_factor",
                     distribution_factor(assignment, 1, q), row["kd1"], 0.0, 1e-9))
    return rows


def example_checks(scratch: Path) -> list[tuple[str, str, object, object, float, float]]:
    rows: list[tuple[str, str, object, object, float, float]] = []
    outcomes = {}
    for example_id, pinned in EXAMPLE_HASHES.items():
        ref, design, outcome = example_outcome(example_id)
        outcomes[example_id] = (ref, design, outcome)
        rows.append((f"ST-EX-{example_id}-HASH",
                     "tests/unit/embodic_io/project/test_examples.py::test_ut_io_08_the_packaged_design_hashes_are_pinned",
                     outcome.design_hash, pinned, 0.0, 0.0))
        errors = [i.code for i in outcome.issues if i.severity.value == "error"]
        rows.append((f"ST-EX-{example_id}-COMPUTES", COMPUTE_SOURCES[example_id], outcome.analysis is not None and not errors,
                     True, 0.0, 0.0))
    _, _, default = outcomes["spiral_12c16p_default"]
    board = default.boards.boards[0]
    rows.append(("ST-CF11-LENGTH", "tests/unit/generators/test_spiral_generate.py::test_default_track_length_matches_cf11",
                 board.detail.track_length_per_coil_layer_mm["X"], 415.4808, 0.0, 5e-5))
    rows.append(("ST-CF11-TURNS", "tests/unit/generators/test_spiral_generate.py::test_default_track_length_matches_cf11",
                 board.detail.turns_achieved, 10, 0.0, 0.0))
    _, _, d08 = outcomes["spiral_12c10p_d08"]
    rows.append(("ST-CF10-LENGTH", "tests/unit/generators/test_spiral_generate.py::test_d08_builds_three_turns_with_the_half_closing",
                 d08.boards.boards[0].detail.track_length_per_coil_layer_mm["X"], 160.2750, 0.0, 5e-5))
    (report,) = default.drc
    least = {s.kind.value: s.measured_min_mm for s in report.summaries}
    rows.append(("ST-DRC-DEFAULT-CLEAN", "tests/unit/generators/test_spiral_generate.py::test_ut_drc_01_default_example_passes_drc",
                 report.violation_count, 0, 0.0, 0.0))
    rows.append(("ST-DRC-DEFAULT-TRACE", "tests/unit/generators/test_spiral_generate.py::test_ut_drc_01_default_example_passes_drc",
                 least["trace_trace"], 0.2, 0.0, 1e-6))
    ref, design, _ = outcomes["spiral_12c16p_default"]
    first, second = scratch / "a.embodic.json", scratch / "b.embodic.json"
    save_project(first, ProjectFile(design=design, origin=ref, ui_state={"zoom": 1.5}), saved_utc=ROUNDTRIP_SAVED_UTC)
    loaded, _issues = load_project(first)
    save_project(second, loaded, saved_utc=ROUNDTRIP_SAVED_UTC)
    rows.append(("ST-IO-ROUNDTRIP",
                 "tests/unit/embodic_io/project/test_project.py::test_ut_io_01_save_load_save_is_byte_identical",
                 first.read_bytes() == second.read_bytes(), True, 0.0, 0.0))
    bundle = scratch / "motor.zip"
    kinds = [ExportKind.SVG, ExportKind.DXF_COMPLETE, ExportKind.DXF_OUTLINE, ExportKind.PDF_REPORT,
             ExportKind.PROJECT_JSON]  # DRAWINGS plus PROJECT_JSON, test_report_readme_bundle.py l.31 and l.191
    write_bundle(default, kinds, bundle, allow_drc_errors=True)
    rows.append(("ST-EXP-BUNDLE",
                 "tests/unit/embodic_io/exporters/test_report_readme_bundle.py::test_ut_exp_05_bundle_holds_selected_files_and_readme",
                 sorted(zipfile.ZipFile(bundle).namelist()),
                 ["README.txt", "motor.dxf", "motor.embodic.json", "motor.svg", "motor_outline.dxf", "motor_report.pdf"],
                 0.0, 0.0))
    return rows


def agrees(observed: object, expected: object, rel: float, abs_: float) -> bool:
    if isinstance(expected, float) and isinstance(observed, int | float):
        return abs(observed - expected) <= max(abs_, rel * abs(expected))
    return observed == expected


def source_sha256(package: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in package.rglob("*.py") if "__pycache__" not in p.parts):
        digest.update(path.relative_to(package).as_posix().encode() + b"\0" + hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def main() -> int:
    failed = 0
    with tempfile.TemporaryDirectory() as work:
        started = time.perf_counter()
        rows = checks() + example_checks(Path(work))
        seconds = time.perf_counter() - started
    for check_id, source, observed, expected, rel, abs_ in rows:
        ok = agrees(observed, expected, rel, abs_)
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {check_id:34} observed={observed!r} expected={expected!r} ({source})")
    package = Path(embodic.__file__).parent
    started = time.perf_counter()
    digest = source_sha256(package)
    hash_ms = (time.perf_counter() - started) * 1000
    count = sum(1 for p in package.rglob("*.py") if "__pycache__" not in p.parts)
    print(f"{len(rows)} checks, {failed} failed, {seconds:.1f} s for all checks")
    print(f"source_sha256 over {count} .py files of {package}: {digest[:16]}... in {hash_ms:.1f} ms")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
