"""XD-PHY-002 and XD-PHY-003: which copper each tool counts (GR-22, D-029).

Xcoil's serpentine analysis integrates `strand` objects only (engine.js l.889 for the eddy loss, `Rs` from the canonical
strands for the resistance). embodic counts every copper path of the layout, so the layer-pair via bus `vbus` adds to
both. The tests split embodic's per-path results by the Xcoil object kind of each path (the mapped layout keeps
Xcoil's object order) and show that the strand-only sum at Xcoil's resistivity equals Xcoil's value, so the vbus copper
is the whole difference. Every Xcoil number comes from a fixture of tests/golden/data/physics.
"""

import math
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any

import pytest
from harness.allow_list import apply_allow_list, load_allow_list
from harness.codec import load_area
from harness.compare import INTEGRATED, Tolerance, compare_scalar, compare_sequence

from embodic.physics import eddy_loss_w, field_table, integrate_path, path_resistance_ohm, symmetry_plane_mm
from m2_physics.test_analyse_layouts import _design, _raw, _stack

pytestmark = pytest.mark.req("REQ-F-11")
AREA = load_area("physics")
ALLOWED = load_allow_list(Path(__file__).parents[1] / "expected_diffs" / "physics.toml")
EXACT_SUM = Tolerance("strand-only sum", rel=1e-12, abs=0.0)
SERPENTINE = "layout-serpentine-default"
SECTOR = "layout-sector-default"
# The object kinds that Xcoil's resistance counts per layout: engine.js analyze (strand), analyzeElements (coil).
XCOIL_COUNTED_KINDS = {SERPENTINE: {"strand"}, SECTOR: {"coil"}}


def _fixture(case: str) -> Mapping[str, Any]:
    return AREA[case.replace("layout-", "analysis-")].calls[0].output


def _per_path(case: str) -> tuple[list[str], list[float], list[float | None], list[float]]:
    """Return per path: Xcoil object kind, eddy loss in W, phase index (None without one), resistance in ohm.

    Both use Xcoil's resistivity from the fixture, so a strand-only sum is comparable with Xcoil's number.
    """
    raw = _raw(case)
    design, stack = _design(raw), _stack(raw)
    board = stack.boards[0]
    kinds = [obj["kind"] for layer in raw["layers"] for obj in layer["objs"]]
    assert len(kinds) == len(board.paths)
    rho = _fixture(case)["rho"]
    rotor = design.rotor
    pole_pairs = rotor.poles // 2
    harmonics = tuple(design.analysis.harmonics)
    omega_e = 2.0 * math.pi * pole_pairs * design.operating.speed_rpm / 60.0
    plane = symmetry_plane_mm(rotor, stack.stack_thickness_mm)
    tables = {z: field_table(rotor, plane, z + rotor.air_gap_mm, harmonics) for z in set(board.copper_z_mm.values())}
    thickness = {layer.name: layer.thickness_mm for layer in design.stackup.copper_layers()}
    eddy = [
        eddy_loss_w(
            integrate_path(
                p.primitives, tables[board.copper_z_mm[p.layer]], pole_pairs, design.analysis.max_segment_mm, 1.0
            ),
            harmonics,
            thickness[p.layer],
            omega_e,
            rho,
        )
        for p in board.paths
    ]
    phase = [None if p.phase is None else "ABC".index(p.phase.value) for p in board.paths]
    resistance = path_resistance_ohm(board.arrays(), thickness, rho).tolist()
    return kinds, eddy, phase, resistance


def _mean_phase_resistance(
    selected: Callable[[str], bool], kinds: Iterable[str], phase: Iterable[float | None], resistance: Iterable[float]
) -> float:
    per_phase = [0.0, 0.0, 0.0]
    for kind, ph, r in zip(kinds, phase, resistance, strict=True):
        if ph is not None and selected(kind):
            per_phase[int(ph)] += r
    return math.fsum(per_phase) / 3.0


def test_serpentine_strand_only_eddy_loss_equals_xcoil() -> None:
    """Defect caught: an eddy kernel or field table that differs from Xcoil's on the strands themselves.

    The strand-only sum at Xcoil's resistivity must equal Xcoil's pEddy within 1e-12. Counting the vbus paths as well
    (the mutation `lambda k: True`) breaks this equality, which is how the test tells a real port error from XD-PHY-002.
    """
    kinds, eddy, _, _ = _per_path(SERPENTINE)
    strand_only = math.fsum(w for kind, w in zip(kinds, eddy, strict=True) if kind == "strand")
    verdict = compare_scalar(_fixture(SERPENTINE)["pEddy"], strand_only, EXACT_SUM)
    assert verdict.ok, verdict


def test_serpentine_strand_only_resistance_equals_xcoil() -> None:
    """Defect caught: a path resistance (EQ-10) that differs from Xcoil's on the strands themselves."""
    kinds, _, phase, resistance = _per_path(SERPENTINE)
    strand_only = _mean_phase_resistance(lambda k: k == "strand", kinds, phase, resistance)
    expected = math.fsum(_fixture(SERPENTINE)["phaseRtrace"]) / 3.0
    verdict = compare_scalar(expected, strand_only, EXACT_SUM)
    assert verdict.ok, verdict


def test_sector_coil_only_resistance_equals_xcoil() -> None:
    """Defect caught: a path resistance (EQ-10) that differs from Xcoil's on the sector coils (arcs and lines)."""
    kinds, _, phase, resistance = _per_path(SECTOR)
    coil_only = _mean_phase_resistance(lambda k: k in XCOIL_COUNTED_KINDS[SECTOR], kinds, phase, resistance)
    expected = math.fsum(_fixture(SECTOR)["phaseRtrace"]) / 3.0
    verdict = compare_scalar(expected, coil_only, EXACT_SUM)
    assert verdict.ok, verdict


def test_serpentine_full_sums_differ_by_the_vbus_copper_inside_the_recorded_margins() -> None:
    """Defect caught: an XD-PHY-002 or XD-PHY-003 margin that hides more than the vbus copper.

    The full sums (every winding path; the test circuit leaves the `ic` interconnect paths out, as analyse() does)
    exceed Xcoil's values, and both differences are admitted by their allow-list entries. The vbus paths alone account
    for the eddy difference: full minus strand-only equals vbus-only.
    """
    kinds, eddy, phase, resistance = _per_path(SERPENTINE)
    x = _fixture(SERPENTINE)
    full = {
        "loss_eddy": math.fsum(eddy),
        "resistance_trace_phase": _mean_phase_resistance(lambda k: k != "ic", kinds, phase, resistance),
    }
    xcoil = {"loss_eddy": x["pEddy"], "resistance_trace_phase": math.fsum(x["phaseRtrace"]) / 3.0}
    verdict = apply_allow_list(compare_sequence([xcoil], [full], INTEGRATED), "analysis-serpentine-default", ALLOWED)
    assert verdict.ok, verdict
    assert {d.allow_id for d in verdict.diffs} == {"XD-PHY-002", "XD-PHY-003"}
    vbus_eddy = math.fsum(w for kind, w in zip(kinds, eddy, strict=True) if kind == "vbus")
    strand_eddy = math.fsum(w for kind, w in zip(kinds, eddy, strict=True) if kind == "strand")
    assert vbus_eddy > 0.0
    assert full["loss_eddy"] == pytest.approx(strand_eddy + vbus_eddy, rel=1e-12, abs=0.0)
    ic_eddy = math.fsum(w for kind, w in zip(kinds, eddy, strict=True) if kind == "ic")
    assert ic_eddy == 0.0, "the interconnect paths carry no eddy loss, so only vbus separates the sums"
