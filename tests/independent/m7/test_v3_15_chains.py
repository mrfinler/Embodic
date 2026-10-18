"""V3-15: chains, validity flags and labels of every result of the five examples, against Agent 4's data-flow graph.

Expected values come from reading the value expressions of `src/embodic/physics/analyse.py` on main 260191f
(l.258-460 and l.460-720: which computed quantity each value reads), the registry labels
(`resources/evidence/equations.v1.json`) and the rulings of `docs/phase3/engineering/fix_wave_f4.md` (A.1 to A.8,
D-060c, D-060d). They are not taken from the engine's `built_from` arguments or from an engine run. GRAPH below is
that reading: one node per computed quantity, with the equations that compute it and the quantities its value is
computed from. A result's expected chain is its own equations plus every equation upstream, as a set; the badge reads
the set, and the first EQ-ID gives the tolerance (`traceable.py` l.159), so the test also checks that one.
"""

import dataclasses
from collections.abc import Iterator

import pytest

from embodic.api import compute
from embodic.io.examples import load_example
from embodic.io.project import project_from_example
from embodic.model.rotor import BlockMagnet
from embodic.results import Traceable

pytestmark = pytest.mark.req("REQ-T-03")

EXAMPLES = ("spiral_12c10p_d08", "spiral_12c14p", "spiral_12c16p_default", "serpentine_16p_example", "wave_16p_example")

# Node -> (own EQ numbers, nodes its value is computed from). "field" gains 04 for a block magnet (A.5, A.8).
GRAPH: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "rho": (("10",), ()),  # copper_resistivity_ohm_m at the winding temperature
    "field": (("05",), ()),  # field_table: B_z harmonics at each copper z
    "flux": (("06",), ("field",)),  # integrate_path: flux linkage per path
    "path_r": (("10",), ("rho",)),  # path_resistance_ohm
    "via_r": (("11",), ("rho",)),  # _via_resistance
    "phase_emf": (("07",), ("flux",)),  # solve_phase_circuit, summed over boards
    "phase_r": (("07",), ("path_r", "via_r")),
    "i_ph": (("09",), ()),  # I_line or I_line / sqrt(3)
    "ic_r": (("23",), ("path_r", "rho")),  # interconnect_resistance(board, phases, r_op, thickness, rho_op)
    "line_emf": (("18",), ("phase_emf",)),  # _line_phasors
    "ideal": (("27",), ("field",)),  # _ideal_integral over the field
    "ke_phase_v_s_per_rad": (("06",), ("phase_emf",)),
    "ke_line_v_s_per_rad": (("09",), ("ke_phase_v_s_per_rad",)),
    "kt_n_m_per_a": (("09",), ("ke_phase_v_s_per_rad",)),
    "kv_rpm_per_v": (("09",), ("ke_phase_v_s_per_rad",)),
    "ke_line_peak_v_s_per_rad": (("18",), ("line_emf",)),
    "torque_n_m": (("09",), ("ke_phase_v_s_per_rad", "i_ph")),
    "winding_factor_1": (("27",), ("ke_phase_v_s_per_rad", "ideal")),
    "inductance_estimate_h": (("14",), ("winding_factor_1",)),
    "resistance_phase_20c_ohm": (("10", "11"), ("phase_r",)),
    "resistance_phase_operating_ohm": (("10", "11"), ("phase_r",)),
    "resistance_line_ohm": (("23",), ("resistance_phase_operating_ohm", "ic_r")),
    "loss_copper_w": (("10",), ("resistance_phase_operating_ohm", "i_ph")),
    "loss_eddy_w": (("12",), ("field", "rho")),
    "loss_circulating_w": (("07",), ("flux", "path_r", "via_r")),
    "loss_delta_circulating_w": (("19",), ()),  # star and open: the constant 0.0 (A.6); all five examples are star
    "loss_interconnect_w": (("23",), ("ic_r", "i_ph")),
    "loss_total_w": (
        ("26",),
        ("loss_copper_w", "loss_eddy_w", "loss_circulating_w", "loss_delta_circulating_w", "loss_interconnect_w"),
    ),
    "output_power_w": (("26",), ("torque_n_m",)),
    "efficiency": (("26",), ("output_power_w", "loss_total_w")),
    "motor_constant_n_m_per_sqrt_w": (("26",), ("torque_n_m", "loss_copper_w", "i_ph")),
    "thd_phase": (("18",), ("phase_emf",)),
    "thd_line": (("18",), ("line_emf",)),
    "emf_waveform_v": (("18",), ("phase_emf",)),
    "emf_phase_rms_v": (("06",), ("ke_phase_v_s_per_rad",)),
    "current_density_a_per_mm2": (("22",), ("i_ph",)),
    "skin_depth_mm": (("13",), ("rho",)),
    "ipc_guideline_current_a": (("15", "09"), ()),
    "mass_copper_g": (("16",), ()),
    "mass_laminate_g": (("16",), ()),
    "temperature_rise_k": (("17",), ("loss_total_w",)),
    "edge_leakage_fraction": (("05",), ("field",)),  # the EC-05 metric, weights |B_z,1 r dr| of the field (A.5)
    "layers.z_mm": ((), ()),  # D-060d: from the stack-up inputs, no equation
    "layers.b1_peak_mid_radius_t": (("05",), ("field",)),  # field_harmonic at the mid radius (A.8)
    "phases.ke_peak_v_s_per_rad": (("06",), ("phase_emf",)),
    "phases.emf_phasor_angle_rad": (("06",), ("phase_emf",)),
    "phases.resistance_20c_ohm": (("10", "11"), ("phase_r",)),
    "phases.resistance_operating_ohm": (("10", "11"), ("phase_r",)),
    "phases.circulating_loss_w": (("07",), ("flux", "path_r", "via_r")),
    "torque_speed.speed_rpm": (("20",), ("ke_line_v_s_per_rad",)),  # linspace(0, 1.15 n_0) (A.7)
    "torque_speed.no_load_speed_rpm": (("20",), ("ke_line_v_s_per_rad",)),
    "torque_speed.torque_n_m": (
        ("20",),
        ("inductance_estimate_h", "ke_line_v_s_per_rad", "resistance_line_ohm"),
    ),
    "torque_speed.power_w": (("20",), ("torque_speed.torque_n_m", "torque_speed.speed_rpm")),
    "torque_speed.base_speed_rpm": (("20",), ("torque_speed.torque_n_m", "torque_speed.speed_rpm")),
}
INTERMEDIATES = {"rho", "field", "flux", "path_r", "via_r", "phase_emf", "phase_r", "i_ph", "ic_r", "line_emf", "ideal"}
# Flags evaluated on a node (analyse.py: edge_flag on the field, skin_validity on the path resistance and on the eddy
# loss, the interconnect flag on the interconnect resistance). edge_leakage_fraction carries EC-05 as its own metric.
FLAG_NODES = {
    "EC-05": {"field", "edge_leakage_fraction"},
    "RANGE_SKIN_DEPTH": {"path_r", "loss_eddy_w"},
}
# Registry labels (equations.v1.json): a bound label stays on its own equation's result, a trust label travels (A.4).
BOUND_LABELS = {"19": "upper bound"}
TRUST_LABELS = {"14": "estimate", "15": "guideline (unverified)", "20": "estimate"}


def upstream(node: str) -> set[str]:
    """Return the node and every node its value is computed from, directly or not."""
    seen, todo = set(), [node]
    while todo:
        current = todo.pop()
        if current not in seen:
            seen.add(current)
            todo.extend(GRAPH[current][1])
    return seen


def expected_chain(node: str, block: bool) -> set[str]:
    """Return the EQ numbers of a result: its own and every upstream node's, with 04 where a block field is read."""
    nodes = upstream(node)
    eqs = {eq for n in nodes for eq in GRAPH[n][0]}
    return eqs | ({"04"} if block and "field" in nodes else set())


def expected_flags(node: str, raised: set[str]) -> set[str]:
    """Return the flag codes a result must carry, given the codes that this design raises at their node."""
    nodes = upstream(node)
    return {code for code in raised if nodes & FLAG_NODES[code]}


def expected_label(node: str, block: bool) -> str | None:
    """Return the label a result must show: its own bound label, else the first trust label of its chain."""
    own = GRAPH[node][0]
    bound = [BOUND_LABELS[eq] for eq in own if eq in BOUND_LABELS]
    if bound:
        return bound[0]
    if node == "edge_leakage_fraction":
        return "lower bound"  # the EC-05 metric bound (traceable.py l.243)
    trust = {TRUST_LABELS[eq] for eq in expected_chain(node, block) if eq in TRUST_LABELS}
    assert len(trust) <= 1, (node, trust)
    return next(iter(trust), None)


def results(outcome) -> Iterator[tuple[str, Traceable]]:
    """Yield (GRAPH node, Traceable) for every result of an outcome, layers and phases included."""
    analysis = outcome.analysis
    for field in dataclasses.fields(analysis):
        value = getattr(analysis, field.name)
        if isinstance(value, Traceable):
            yield field.name, value
        elif field.name in ("layers", "phases"):
            for item in value:
                for sub in dataclasses.fields(item):
                    inner = getattr(item, sub.name)
                    if isinstance(inner, Traceable):
                        yield f"{field.name}.{sub.name}", inner
        elif field.name == "torque_speed" and value is not None:
            for sub in dataclasses.fields(value):
                yield f"torque_speed.{sub.name}", getattr(value, sub.name)


def computed(example_id: str, **operating):
    """Return the outcome of one packaged example, with operating fields replaced when given, and its magnet kind."""
    design = project_from_example(load_example(example_id)).design
    if operating:
        design = dataclasses.replace(design, operating=dataclasses.replace(design.operating, **operating))
    outcome = compute(design, {})
    assert outcome is not None and outcome.analysis is not None, example_id
    return outcome, isinstance(design.rotor.magnet, BlockMagnet)


@pytest.fixture(scope="module", params=EXAMPLES)
def example(request):
    """Return (example id, outcome, block magnet) for each packaged example."""
    outcome, block = computed(request.param)
    return request.param, outcome, block


def test_v3_15_every_result_is_a_node_of_the_graph(example):
    """Catches a result the graph does not model, or a modelled result the outcome lacks; both leave a chain unchecked.

    The torque-speed results exist only with a DC-link voltage (serpentine and wave examples).
    """
    example_id, outcome, _ = example
    nodes = {node for node, _ in results(outcome)}
    drive = outcome.design.operating.dc_link_v is not None
    want = {n for n in GRAPH if n not in INTERMEDIATES and (drive or not n.startswith("torque_speed."))}
    assert nodes == want, (example_id, sorted(nodes ^ want))


def test_v3_15_each_chain_holds_exactly_the_equations_of_its_data_flow_and_starts_with_its_own(example):
    """Catches a chain that drops a source's equation (DEF-UE18-01) or holds one the value never used (A.3, A.6)."""
    example_id, outcome, block = example
    wrong = []
    for node, result in results(outcome):
        chain = [eq.removeprefix("EQ-") for eq in result.eq_ids]
        want = expected_chain(node, block)
        if set(chain) != want or len(chain) != len(set(chain)):
            wrong.append((node, sorted(chain), sorted(want)))
        elif GRAPH[node][0] and chain[0] != GRAPH[node][0][0]:
            wrong.append((node, "first EQ-ID", chain[0], GRAPH[node][0][0]))
    assert wrong == [], example_id


def test_v3_15_ec05_travels_to_every_result_computed_from_the_field_and_to_no_other(example):
    """Catches DEF-UE20-01 (a field-derived result without the EC-05 flag) and a flag on a field-free result."""
    example_id, outcome, _ = example
    wrong = []
    for node, result in results(outcome):
        codes = [f.code for f in result.validity]
        want = expected_flags(node, {"EC-05"})
        if set(codes) != want or len(codes) != len(set(codes)):
            wrong.append((node, codes, sorted(want)))
    assert wrong == [], example_id


def test_v3_15_bound_labels_stay_on_their_own_result_and_trust_labels_travel(example):
    """Catches DEF-UE20-02 ('upper bound' on efficiency, total loss or temperature rise) and a lost 'estimate'."""
    example_id, outcome, block = example
    wrong = [
        (node, result.label, expected_label(node, block))
        for node, result in results(outcome)
        if result.label != expected_label(node, block)
    ]
    assert wrong == [], example_id


def test_v3_15_the_skin_depth_flag_travels_with_the_resistances():
    """Catches RANGE_SKIN_DEPTH kept on the path resistance and the eddy loss only (A.4, DEF-UE20-01).

    D08 at 20 times its speed. The skin depth goes with 1 / sqrt(f), so delta / 3 falls below the widest trace; the
    first assertion checks that the probe design really raises the flag's condition.
    """
    base, _ = computed("spiral_12c10p_d08")
    outcome, block = computed("spiral_12c10p_d08", speed_rpm=base.design.operating.speed_rpm * 20.0)
    widest = max(p.width_mm for b in outcome.boards.boards for path in b.paths for p in path.primitives)
    assert outcome.analysis.skin_depth_mm.value / 3.0 < widest
    wrong = []
    for node, result in results(outcome):
        codes = {f.code for f in result.validity}
        if ("RANGE_SKIN_DEPTH" in codes) != bool(expected_flags(node, {"RANGE_SKIN_DEPTH"})):
            wrong.append((node, sorted(codes)))
    assert wrong == []
    assert not block


def test_v3_15_the_tag_inputs_hold_the_pointers_that_def_ue20_08_found_missing(example):
    """Catches the pole-arc ratio or block width missing from the EMF inputs and the ambient temperature from IPC."""
    example_id, outcome, block = example
    analysis = outcome.analysis
    shape = "/rotor/magnet/width_mm" if block else "/rotor/magnet/pole_arc_ratio"
    assert shape in {i.pointer for i in analysis.ke_phase_v_s_per_rad.inputs}, example_id
    ipc = {i.pointer for i in analysis.ipc_guideline_current_a.inputs}
    assert "/operating/ambient_temperature_degc" in ipc, example_id
