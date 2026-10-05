"""analyse() on the three Xcoil layouts of tests/golden/data/m1_layout, each as a one-board BoardStack.

The mapper returns no element list, so `_series_circuit` builds one: every phase-tagged path is a one-member group, in
series, in Xcoil's object order (assumption: Xcoil objects run in current direction). The design numbers come from the
fixture's Xcoil params; the winding variant only selects form fields, which analyse() does not read.
"""

import dataclasses
import json
import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
from m1_layout.xcoil_map import layout_from_xcoil

from embodic.geometry.circuit import Circuit, Member, ParallelGroup, PhaseCircuit
from embodic.geometry.layout import BoardStack, Layout
from embodic.model.connection import ConnectionSpec
from embodic.model.design import DesignParameters
from embodic.model.drc_rules import DrcRules
from embodic.model.operating import OperatingPoint
from embodic.model.outline import CircleOutline, OutlineSpec
from embodic.model.rotor import ArcMagnet, RotorSpec, RotorType
from embodic.model.stackup import CopperLayer, DielectricLayer, Stackup
from embodic.model.vias import ViaSpec
from embodic.model.vocabulary import Phase
from embodic.model.winding_specs import SerpentineWindingSpec
from embodic.physics import analyse
from embodic.results import AnalysisResult, Status, Traceable, load_registry

DATA = Path(__file__).parents[1] / "data" / "m1_layout"
CASES = ("layout-sector-default", "layout-serpentine-default", "layout-wave-turns-2")
ROTOR_TYPE = {"double": RotorType.DOUBLE, "singleYoke": RotorType.SINGLE_YOKE, "singleOpen": RotorType.SINGLE_OPEN}
pytestmark = pytest.mark.req("REQ-F-11")


def _raw(case: str) -> Mapping[str, Any]:
    return json.loads((DATA / f"{case}.json").read_text(encoding="utf-8"))["calls"][0]["output"]


def _series_circuit(layout: Layout) -> Circuit:
    phases = []
    for phase in (Phase.A, Phase.B, Phase.C):
        groups = tuple(
            ParallelGroup(members=(Member(path_ids=(p.id,), via_ids=()),))
            for p in layout.paths
            if p.phase is phase and p.id not in layout.circuit.interconnect_path_ids
        )
        phases.append(PhaseCircuit(phase=phase, groups=groups, terminal_net=f"PHASE_{phase.value}"))
    return dataclasses.replace(layout.circuit, phases=tuple(phases))


def _design(raw: Mapping[str, Any], magnet_r_outer_mm: float | None = None) -> DesignParameters:
    p = raw["params"]
    copper = [CopperLayer(name=layer["name"], thickness_mm=layer["copperT"]) for layer in raw["layers"]]
    gap_mm = (p["boardThickness"] - sum(c.thickness_mm for c in copper)) / max(1, len(copper) - 1)
    stack: list[CopperLayer | DielectricLayer] = []
    for i, c in enumerate(copper):
        stack.append(c)
        if i < len(copper) - 1:
            stack.append(DielectricLayer(name=f"D{i + 1}", thickness_mm=gap_mm, material="FR-4"))
    return DesignParameters(
        name="Xcoil fixture",
        phases=p["phases"],
        rotor=RotorSpec(
            poles=p["poles"],
            rotor_type=ROTOR_TYPE[p["rotorType"]],
            magnet=ArcMagnet(
                pole_arc_ratio=p["magnetArcRatio"],
                r_inner_mm=p["magnetRIn"],
                r_outer_mm=magnet_r_outer_mm or p["magnetROut"],
                thickness_mm=p["magnetThickness"],
            ),
            remanence_t=p["Br"],
            recoil_permeability=p["muR"],
            air_gap_mm=p["airgap"],
            back_iron_thickness_mm=p["magnetThickness"],
        ),
        winding=SerpentineWindingSpec(
            r_inner_mm=p["rIn"],
            r_outer_mm=p["rOut"],
            turns=p["turns"],
            trace_width_mm=p["traceWidth"],
            clearance_mm=p["clearance"],
            layers_per_phase=1,
        ),
        stackup=Stackup(layers=tuple(stack)),
        vias=ViaSpec(drill_mm=p["viaDrill"], pad_mm=p["viaPad"], plating_um=25.0),
        connection=ConnectionSpec(ring_width_mm=1.0, terminal_pad_mm=p["terminalPad"], terminal_drill_mm=1.2),
        outline=OutlineSpec(board=CircleOutline(radius_mm=48.0), bore=CircleOutline(radius_mm=18.7)),
        operating=OperatingPoint(
            speed_rpm=p["rpm"],
            line_current_rms_a=p["currentRms"],
            winding_temperature_degc=p["tempC"],
            ambient_temperature_degc=p["ambientC"],
            convection_h_w_m2k=p["hConv"],
        ),
        drc_rules=DrcRules(
            trace_clearance_mm=0.15,
            via_clearance_mm=0.15,
            edge_clearance_mm=0.3,
            hole_clearance_mm=0.3,
            min_trace_width_mm=0.15,
            min_drill_mm=0.3,
            min_annular_ring_mm=0.1,
        ),
    )


def _stack(raw: Mapping[str, Any]) -> BoardStack:
    layout = layout_from_xcoil(raw)
    layout = dataclasses.replace(layout, circuit=_series_circuit(layout))
    return BoardStack(boards=(layout,), board_thickness_mm=raw["params"]["boardThickness"], board_gap_mm=0.0)


def _traceables(result: object, where: str = "result") -> list[tuple[str, object]]:
    found: list[tuple[str, object]] = []
    for f in dataclasses.fields(result):  # type: ignore[arg-type]
        value = getattr(result, f.name)
        if isinstance(value, tuple) and value and dataclasses.is_dataclass(value[0]):
            for i, item in enumerate(value):
                found += _traceables(item, f"{where}.{f.name}[{i}]")
        elif dataclasses.is_dataclass(value) and not isinstance(value, Traceable):
            found += _traceables(value, f"{where}.{f.name}")
        elif f.name not in {"registry_version", "phase", "layer"} and value is not None:
            found.append((f"{where}.{f.name}", value))
    return found


@pytest.fixture(scope="module")
def results() -> Mapping[str, AnalysisResult]:
    """Run analyse() once per mapped layout."""
    registry = load_registry()
    out = {}
    for case in CASES:
        raw = _raw(case)
        result = analyse(_design(raw), _stack(raw), {}, registry)
        assert result is not None
        out[case] = result
    return out


@pytest.mark.parametrize("case", CASES)
def test_every_result_field_is_a_traceable_with_an_eq_id(results: Mapping[str, AnalysisResult], case: str) -> None:
    """Defect caught: a bare float, or a Traceable without an equation, reaching the AnalysisResult."""
    for where, value in _traceables(results[case]):
        assert isinstance(value, Traceable), f"{where} is {type(value).__name__}, not a Traceable"
        assert value.eq_ids, f"{where} has no EQ id"
        assert all(e.startswith("EQ-") for e in value.eq_ids), where


@pytest.mark.parametrize("case", CASES)
def test_three_balanced_phases_produce_emf_and_finite_results(results: Mapping[str, AnalysisResult], case: str) -> None:
    """Defect caught: a phase that picks up no flux (wrong sign, z or span) or a NaN leaking into a result."""
    r = results[case]
    ke = [p.ke_peak_v_s_per_rad.value for p in r.phases]
    assert len(ke) == 3 and min(ke) > 0.0
    assert (max(ke) - min(ke)) / r.ke_phase_v_s_per_rad.value < 0.05
    for where, t in _traceables(r):
        assert isinstance(t, Traceable)
        values = t.value if isinstance(t.value, tuple) else (t.value,)
        assert all(math.isfinite(v) for v in values), where


def test_star_line_constant_is_sqrt3_of_the_phase_constant(results: Mapping[str, AnalysisResult]) -> None:
    """Defect caught: analyse() feeding EQ-09 a different Ke than the one it reports."""
    r = results["layout-sector-default"]
    assert r.ke_line_v_s_per_rad.value == pytest.approx(math.sqrt(3.0) * r.ke_phase_v_s_per_rad.value, rel=1e-12)


def test_inductance_and_ipc_carry_their_labels(results: Mapping[str, AnalysisResult]) -> None:
    """Defect caught: EQ-14 or EQ-15 shown without its estimate or guideline label, or above unresolved."""
    r = results["layout-serpentine-default"]
    assert r.inductance_estimate_h.label == "estimate"
    assert r.inductance_estimate_h.status is Status.UNRESOLVED
    assert r.ipc_guideline_current_a.label == "guideline (unverified)"


def test_edge_leakage_metric_is_labelled_per_def23(results: Mapping[str, AnalysisResult]) -> None:
    """Defect caught: e_edge shown as verified, or its flag losing the lower-bound and transfer labels (UT-RES-07)."""
    e = results["layout-sector-default"].edge_leakage_fraction
    assert e.label == "lower bound"
    flag = next(f for f in e.validity if f.code == "EC-05")
    assert flag.transfer_status is Status.ASSUMPTION
    assert flag.metric_bound.value == "lower_bound"


def test_ec05_above_the_cap_downgrades_emf_results_to_unresolved() -> None:
    """Defect caught: an e_edge above the 10 % cap (D-017) leaving Ke and torque at their equation badge.

    Narrowing the magnet span to 22-26 mm puts every EMF-producing chord within one decay length of a magnet edge.
    """
    registry = load_registry()
    raw = _raw("layout-sector-default")
    wide = analyse(_design(raw), _stack(raw), {}, registry)
    narrow = analyse(_design(raw, magnet_r_outer_mm=26.0), _stack(raw), {}, registry)
    assert wide is not None and narrow is not None
    assert wide.edge_leakage_fraction.value <= 0.10
    assert next(f for f in wide.ke_phase_v_s_per_rad.validity if f.code == "EC-05").effect.value == "limitation"
    assert narrow.edge_leakage_fraction.value > 0.10
    for t in (narrow.ke_phase_v_s_per_rad, narrow.torque_n_m, narrow.kt_n_m_per_a, narrow.emf_waveform_v):
        assert t.status is Status.UNRESOLVED, t.quantity
        assert any("EC-05" in reason or "validity" in reason for reason in t.status_reasons), t.status_reasons
    assert narrow.resistance_phase_20c_ohm.status is not Status.UNRESOLVED


@pytest.mark.parametrize("case", CASES)
def test_line_peak_differs_from_the_fundamental_by_at_most_the_harmonic_sum(
    results: Mapping[str, AnalysisResult], case: str
) -> None:
    """Defect caught: the line peak taken from the phase waveform (factor sqrt(3) off) or left in V instead of V*s/rad.

    With line harmonics A_n, |peak - A_1| <= sum_{n>1} A_n <= sqrt(N - 1) * sqrt(sum_{n>1} A_n^2) (Cauchy-Schwarz), and
    the root-sum-square over A_1 is thd_line, so |peak / ke_line - 1| <= sqrt(N - 1) * thd_line.
    """
    r = results[case]
    n_other = len(_design(_raw(case)).analysis.harmonics) - 1
    deviation = abs(r.ke_line_peak_v_s_per_rad.value / r.ke_line_v_s_per_rad.value - 1.0)
    assert 0.0 < deviation <= math.sqrt(n_other) * r.thd_line.value, (deviation, r.thd_line.value)
    assert r.ke_line_peak_v_s_per_rad.unit is r.ke_line_v_s_per_rad.unit
    assert r.ke_line_peak_v_s_per_rad.eq_ids == ("EQ-18", "EQ-09", "EQ-06")
