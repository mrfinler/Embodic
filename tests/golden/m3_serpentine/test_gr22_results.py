"""GR-22: Ke, R and eddy loss of the ported layouts against Xcoil's analyze (REQ-F-34).

Xcoil's serpentine analysis integrates and sums the ``strand`` objects only (engine.js l.889, l.927; XD-PHY-002 and
XD-PHY-003 in expected_diffs/physics.toml). embodic counts every copper path in its eddy loss. The checks therefore
compare the same elements: Ke from the whole analysis, and eddy loss and trace resistance over the strand paths at
Xcoil's resistivity, each within 1e-9 relative.
"""

import math
from collections.abc import Mapping
from typing import Any

import pytest
from harness import INTEGRATED, GoldenCase, compare_scalar, load_area

from embodic.errors import Unbuildable
from embodic.generators import build_layout
from embodic.geometry.layout import BoardStack, Layout
from embodic.model.design import DesignParameters
from embodic.model.provenance import derive_provenance
from embodic.physics import (
    analyse,
    eddy_loss_w,
    field_table,
    integrate_path,
    path_resistance_ohm,
    symmetry_plane_mm,
)
from embodic.results import AnalysisResult, Registry, load_registry

from .design_map import design_from_xcoil

pytestmark = pytest.mark.req("REQ-F-34")

AREA = load_area("serpentine")
BUILT = [c for c in AREA.values() if c.case_id.startswith("layout-") and "layers" in c.calls[0].output]
# The seeded sets repeat what the presets cover; they run in the nightly profile (slow), the presets on every commit.
CASES = [pytest.param(c, marks=pytest.mark.slow) if "seeded" in c.tags else c for c in BUILT]
RHO_CU_20, ALPHA_CU = 1.724e-8, 0.00393  # Xcoil engine.js l.12-13: annealed copper at 20 C, 1/K


@pytest.fixture(scope="module")
def registry() -> Registry:
    """Return the shipped equation registry."""
    return load_registry()


def _raw(case: GoldenCase) -> Mapping[str, Any]:
    (call,) = case.calls
    return call.output


def _built(case: GoldenCase, registry: Registry) -> tuple[DesignParameters, BoardStack]:
    raw = _raw(case)
    design = design_from_xcoil(raw["params"], raw["rMinAll"], raw["rMaxAll"])
    stack = build_layout(design, registry)
    assert not isinstance(stack, Unbuildable)
    return design, stack


def _strand_paths(layout: Layout) -> list[int]:
    return [p.id for p in layout.paths if p.element is not None]


def _xcoil_rho(raw: Mapping[str, Any]) -> float:
    return RHO_CU_20 * (1 + ALPHA_CU * (raw["params"]["tempC"] - 20))


def _strand_eddy_w(design: DesignParameters, stack: BoardStack, rho: float) -> float:
    rotor, options = design.rotor, design.analysis
    pole_pairs, harmonics = rotor.poles // 2, tuple(options.harmonics)
    omega_e = 2.0 * math.pi * pole_pairs * design.operating.speed_rpm / 60.0
    plane = symmetry_plane_mm(rotor, stack.stack_thickness_mm)
    thickness = {layer.name: layer.thickness_mm for layer in design.stackup.copper_layers()}
    total = []
    for layout in stack.boards:
        tables = {
            z: field_table(rotor, plane, z + rotor.air_gap_mm, harmonics) for z in set(layout.copper_z_mm.values())
        }
        for path in layout.paths:
            if path.element is None:
                continue
            fields = integrate_path(
                path.primitives, tables[layout.copper_z_mm[path.layer]], pole_pairs, options.max_segment_mm, 1.0
            )
            total.append(eddy_loss_w(fields, harmonics, thickness[path.layer], omega_e, rho))
    return math.fsum(total)


def _strand_resistance_ohm(design: DesignParameters, stack: BoardStack, rho: float) -> float:
    """Mean over phases of the series-parallel strand resistance (Xcoil Rtrace); via and link groups are left out."""
    thickness = {layer.name: layer.thickness_mm for layer in design.stackup.copper_layers()}
    per_phase = []
    for layout in stack.boards:
        resistance = dict(
            zip((p.id for p in layout.paths), path_resistance_ohm(layout.arrays(), thickness, rho), strict=True)
        )
        strands = set(_strand_paths(layout))
        for circuit in layout.circuit.phases:
            groups = [
                g
                for g in circuit.groups
                if any(m.path_ids for m in g.members) and all(i in strands for m in g.members for i in m.path_ids)
            ]
            per_phase.append(
                math.fsum(
                    1.0 / math.fsum(1.0 / math.fsum(resistance[i] for i in m.path_ids) for m in g.members)
                    for g in groups
                )
            )
    return math.fsum(per_phase) / len(per_phase)


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.case_id)
def test_gr22_strand_eddy_loss_equals_xcoil(case: GoldenCase, registry: Registry, golden_report: Any) -> None:
    """Catches a wrong strand position, layer height or board offset: eddy loss over the same elements, 1e-9 rel."""
    raw = _raw(case)
    design, stack = _built(case, registry)
    mine = _strand_eddy_w(design, stack, _xcoil_rho(raw))
    golden_report.check(case.case_id, compare_scalar(raw["analysis"]["pEddy"], mine, INTEGRATED))


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.case_id)
def test_gr22_strand_resistance_equals_xcoil(case: GoldenCase, registry: Registry, golden_report: Any) -> None:
    """Catches a wrong series-parallel grouping of the strands: Xcoil's Rtrace over the same elements, 1e-9 rel."""
    raw = _raw(case)
    design, stack = _built(case, registry)
    golden = math.fsum(ph["Rtrace"] for ph in raw["analysis"]["phases"]) / len(raw["analysis"]["phases"])
    golden_report.check(
        case.case_id, compare_scalar(golden, _strand_resistance_ohm(design, stack, _xcoil_rho(raw)), INTEGRATED)
    )


def _analysis(design: DesignParameters, stack: BoardStack, registry: Registry) -> AnalysisResult:
    result = analyse(design, stack, derive_provenance(design, None, ()), registry)
    assert result is not None
    return result


def _mean_ke(result: AnalysisResult) -> float:
    return math.fsum(p.ke_peak_v_s_per_rad.value for p in result.phases) / len(result.phases)


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.case_id)
def test_gr22_phase_constant_equals_xcoil(case: GoldenCase, registry: Registry, golden_report: Any) -> None:
    """Catches a wrong copper element, phase shift or board z: Ke of the stack as built (DEF-M3a-01), 1e-9 rel."""
    raw = _raw(case)
    design, stack = _built(case, registry)
    golden_report.check(
        case.case_id, compare_scalar(raw["analysis"]["Ke1"], _mean_ke(_analysis(design, stack, registry)), INTEGRATED)
    )
