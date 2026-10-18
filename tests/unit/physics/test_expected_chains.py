"""fix_wave_f4.md section B and D-060c, d: the chain, validity flags and label of every analyse() result.

A result takes the equations, the validity flags and the trust labels of what it is built from, not bound labels
(fix_wave_f4.md A.4, ADR-0003 decision 2). EXPECTED_D08 is section B with one change from D-060d: layers[k].z_mm is
derived from the stack-up alone and holds no equation. Chains are written without the "EQ-" prefix, as in section B.
"""

import dataclasses
import functools
from collections.abc import Iterator

import pytest

from embodic.api import compute
from embodic.io.examples import load_example
from embodic.io.project import project_from_example, project_provenance
from embodic.results import AnalysisResult, Registry, Status, Traceable, load_registry

pytestmark = pytest.mark.req("REQ-T-05")
D08 = "spiral_12c10p_d08"
EXAMPLES = (D08, "spiral_12c16p_default", "spiral_12c14p", "serpentine_16p_example", "wave_16p_example")
PHASE_EMF = ("07", "06", "05")
PHASE_R = ("10", "11", "07")
SUM = ("26", "10", "11", "07", "09", "12", "05", "06", "19", "23")
EXPECTED_D08: dict[str, tuple[str, ...]] = {
    "ke_phase_v_s_per_rad": ("06", "07", "05"),
    "ke_line_v_s_per_rad": ("09", "06", "07", "05"),
    "ke_line_peak_v_s_per_rad": ("18", *PHASE_EMF),
    "kt_n_m_per_a": ("09", "06", "07", "05"),
    "kv_rpm_per_v": ("09", "06", "07", "05"),
    "winding_factor_1": ("27", "06", "07", "05"),
    "resistance_phase_20c_ohm": PHASE_R,
    "resistance_phase_operating_ohm": PHASE_R,
    "resistance_line_ohm": ("23", "10", "11", "07"),
    "emf_phase_rms_v": ("06", "07", "05"),
    "torque_n_m": ("09", "06", "07", "05"),
    "loss_copper_w": ("10", "11", "07", "09"),
    "loss_eddy_w": ("12", "05", "10"),
    "loss_circulating_w": ("07", "06", "05", "10", "11"),
    "loss_delta_circulating_w": ("19",),
    "loss_interconnect_w": ("23", "10", "09"),
    "loss_total_w": SUM,
    "output_power_w": ("26", "09", "06", "07", "05"),
    "efficiency": ("26", "09", "06", "07", "05", "10", "11", "12", "19", "23"),
    "motor_constant_n_m_per_sqrt_w": ("26", "09", "06", "07", "05", "10", "11"),
    "thd_phase": ("18", *PHASE_EMF),
    "thd_line": ("18", *PHASE_EMF),
    "current_density_a_per_mm2": ("22", "09"),
    "skin_depth_mm": ("13", "10"),
    "inductance_estimate_h": ("14", "27", "06", "07", "05"),
    "ipc_guideline_current_a": ("15", "09"),
    "mass_copper_g": ("16",),
    "mass_laminate_g": ("16",),
    "temperature_rise_k": ("17", *SUM),
    "edge_leakage_fraction": ("05",),
    **{f"layers[{k}].z_mm": () for k in range(2)},
    **{f"layers[{k}].b1_peak_mid_radius_t": ("05",) for k in range(2)},
    **{f"phases[{k}].ke_peak_v_s_per_rad": ("06", "07", "05") for k in range(3)},
    **{f"phases[{k}].emf_phasor_angle_rad": ("06", "07", "05") for k in range(3)},
    **{f"phases[{k}].resistance_20c_ohm": PHASE_R for k in range(3)},
    **{f"phases[{k}].resistance_operating_ohm": PHASE_R for k in range(3)},
    **{f"phases[{k}].circulating_loss_w": ("07", "06", "05", "10", "11") for k in range(3)},
    "emf_waveform_v": ("18", *PHASE_EMF),
}
DRIVE_FULL = ("20", "14", "27", "06", "07", "05", "09", "23", "10", "11")
BLOCK_STAR = {
    "ke_line_peak_v_s_per_rad": ("18", "07", "06", "05", "04"),
    "edge_leakage_fraction": ("05", "04"),
    "loss_delta_circulating_w": ("19",),
    "loss_interconnect_w": ("23", "10", "09"),
}
ARC_STAR_DRIVE = {
    "ke_line_peak_v_s_per_rad": ("18", *PHASE_EMF),
    "edge_leakage_fraction": ("05",),
    "loss_delta_circulating_w": ("19",),
    "loss_interconnect_w": ("23", "10", "09"),
    "torque_speed.speed_rpm": ("20", "09", "06", "07", "05"),
    "torque_speed.torque_n_m": DRIVE_FULL,
    "torque_speed.power_w": DRIVE_FULL,
    "torque_speed.no_load_speed_rpm": ("20", "09", "06", "07", "05"),
    "torque_speed.base_speed_rpm": DRIVE_FULL,
}
EXPECTED_OTHER = {
    "spiral_12c16p_default": BLOCK_STAR,
    "spiral_12c14p": BLOCK_STAR,
    "serpentine_16p_example": ARC_STAR_DRIVE,
    "wave_16p_example": ARC_STAR_DRIVE,
}
LABELS_D08 = {
    "loss_delta_circulating_w": "upper bound",
    "inductance_estimate_h": "estimate",
    "ipc_guideline_current_a": "guideline (unverified)",
    "edge_leakage_fraction": "lower bound",
}


def _walk(value: object, path: str = "") -> Iterator[tuple[str, Traceable]]:
    if isinstance(value, Traceable):
        yield path, value
    elif isinstance(value, tuple):
        for i, item in enumerate(value):
            yield from _walk(item, f"{path}[{i}]")
    elif dataclasses.is_dataclass(value) and not isinstance(value, type):
        for f in dataclasses.fields(value):
            yield from _walk(getattr(value, f.name), f"{path}.{f.name}" if path else f.name)


def _analysis(example: str, registry: Registry) -> AnalysisResult:
    project = project_from_example(load_example(example))
    outcome = compute(project.design, project_provenance(project), registry=registry)
    assert outcome is not None and outcome.analysis is not None
    return outcome.analysis


@functools.cache
def _results(example: str) -> dict[str, Traceable]:
    return dict(_walk(_analysis(example, load_registry())))


def _short(eq_ids: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(e.removeprefix("EQ-") for e in eq_ids)


def _all_passed_with_ec05_capping() -> Registry:
    """Return the shipped registry with EC-05's threshold at 0, so e_edge caps, and every linked test passed."""
    registry = load_registry()
    eq05 = registry.equation("EQ-05")
    capping = dataclasses.replace(eq05.validity_checks[0], threshold=0.0)
    equations = {**registry.equations, "EQ-05": dataclasses.replace(eq05, validity_checks=(capping,))}
    linked = frozenset(t for e in registry.equations.values() for t in e.tests)
    return dataclasses.replace(registry, equations=equations, passed_tests=linked)


def test_every_d08_chain_is_the_section_b_chain() -> None:
    """Defect caught: DEF-UE20-03 to -05 and D-060d, e.g. EQ-09 on the line peak or EQ-05 on a stack-up z."""
    results = _results(D08)
    assert set(results) == set(EXPECTED_D08)
    differ = {p: _short(t.eq_ids) for p, t in results.items() if _short(t.eq_ids) != EXPECTED_D08[p]}
    assert differ == {}


@pytest.mark.parametrize("example", sorted(EXPECTED_OTHER))
def test_the_rows_section_b_names_for_the_other_examples(example: str) -> None:
    """Defect caught: DEF-UE20-06 (no EQ-04 on a block magnet's e_edge), DEF-UE20-07 (R and L on the speed axis)."""
    results = _results(example)
    expected = EXPECTED_OTHER[example]
    differ = {p: _short(results[p].eq_ids) for p in expected if _short(results[p].eq_ids) != expected[p]}
    assert differ == {}


@pytest.mark.parametrize("example", EXAMPLES)
def test_a_result_carries_ec05_exactly_when_its_chain_holds_the_field(example: str) -> None:
    """Defect caught: DEF-UE20-01, a result built from the EQ-05 field without the EC-05 flag, or a 0 W with it."""
    mismatched = {
        p: (_short(t.eq_ids), [f.code for f in t.validity])
        for p, t in _results(example).items()
        if ("EQ-05" in t.eq_ids) != any(f.code == "EC-05" for f in t.validity)
    }
    assert mismatched == {}


def test_an_e_edge_above_the_cap_caps_every_result_built_from_the_field() -> None:
    """Defect caught: DEF-UE20-01, loss_eddy or output_power keeping `inferred` while ke_phase reads `unresolved`.

    The e_edge metric itself keeps its own badge: the threshold caps the other results, not the trust in the metric.
    """
    results = dict(_walk(_analysis(D08, _all_passed_with_ec05_capping())))
    from_field = {p: t.status for p, t in results.items() if "EQ-05" in t.eq_ids and p != "edge_leakage_fraction"}
    assert len(from_field) == 30
    assert {p for p, s in from_field.items() if s is not Status.UNRESOLVED} == set()
    assert results["edge_leakage_fraction"].status is Status.ASSUMPTION


def test_only_the_d08_results_whose_own_equation_names_a_label_carry_it() -> None:
    """Defect caught: DEF-UE20-02, 'upper bound' of EQ-19 on loss_total, efficiency and temperature_rise."""
    labels = {p: t.label for p, t in _results(D08).items() if t.label is not None}
    assert labels == LABELS_D08


@pytest.mark.parametrize("example", EXAMPLES)
def test_a_bound_label_stays_on_the_quantity_its_equation_computes(example: str) -> None:
    """Defect caught: DEF-UE20-02 in any example, a sum or a ratio labelled as a bound of one of its terms."""
    bounded = {p for p, t in _results(example).items() if t.label == "upper bound"}
    assert bounded == {"loss_delta_circulating_w"}


def test_the_drive_estimate_label_travels_with_its_equation() -> None:
    """Defect caught: the trust label 'estimate' of EQ-20 lost when bound labels stop travelling."""
    drive = {p: t.label for p, t in _results("wave_16p_example").items() if p.startswith("torque_speed.")}
    assert set(drive.values()) == {"estimate"} and len(drive) == 5


def test_the_tag_lists_the_magnet_shape_and_the_ambient_temperature() -> None:
    """Defect caught: DEF-UE20-08, the pole-arc ratio, block width or ambient temperature read but not listed."""
    d08, block = _results(D08), _results("spiral_12c16p_default")
    arc_inputs = {i.pointer for i in d08["ke_phase_v_s_per_rad"].inputs}
    block_inputs = {i.pointer for i in block["ke_phase_v_s_per_rad"].inputs}
    assert ("/rotor/magnet/pole_arc_ratio" in arc_inputs, "/rotor/magnet/width_mm" in arc_inputs) == (True, False)
    assert ("/rotor/magnet/pole_arc_ratio" in block_inputs, "/rotor/magnet/width_mm" in block_inputs) == (False, True)
    assert "/rotor/magnet/pole_arc_ratio" in {a.item for a in d08["ke_phase_v_s_per_rad"].assumed_inputs}
    assert "/operating/ambient_temperature_degc" in {i.pointer for i in d08["ipc_guideline_current_a"].inputs}


def test_a_layer_z_is_derived_with_no_equation_and_not_tested() -> None:
    """Defect caught: D-060d, a stack-up z that takes EQ-05's badge and the EC-05 flag of the field."""
    for registry in (load_registry(), _all_passed_with_ec05_capping()):
        for layer in _analysis(D08, registry).layers:
            t = layer.z_mm
            assert (t.kind_tag, t.eq_ids, t.validity, t.status) == ("derived", (), (), Status.NOT_TESTED)
