"""D-058d: the chain of every analyse() result includes the chains of the results and intermediates it is built from.

interfaces.md "Chain of a result": the badge takes the weakest equation over the whole chain, so a result that leaves
out an equation of something it is computed from shows a badge that ignores that equation. BUILT_FROM states what each
result is computed from in analyse(); the D08 example (arc magnets), the default spiral (block magnets) and the wave
example (it has a DC link, so the drive results exist) cover every result.
"""

import dataclasses
import functools
from collections.abc import Iterator

import pytest

from embodic.api import compute
from embodic.io.examples import load_example
from embodic.io.project import project_from_example, project_provenance
from embodic.results import AnalysisResult, Traceable, load_registry

pytestmark = pytest.mark.req("REQ-T-05")
D08, BLOCK_MAGNETS, WITH_DRIVE = "spiral_12c10p_d08", "spiral_12c16p_default", "wave_16p_example"
DRIVE_INPUTS = ("ke_line", "inductance_estimate", "resistance_line")
LOSSES = ("loss_copper", "loss_eddy", "loss_circulating", "loss_delta_circulating", "loss_interconnect")
BUILT_FROM = {
    "ke_line": ("ke_phase_v_s_per_rad",),
    "kt": ("ke_phase_v_s_per_rad",),
    "kv": ("ke_phase_v_s_per_rad",),
    "torque": ("ke_phase_v_s_per_rad",),
    "emf_phase_rms": ("ke_phase_v_s_per_rad",),
    "output_power": ("torque",),
    "motor_constant": ("torque", "loss_copper"),
    "utilisation_factor_k_u": ("ke_phase_v_s_per_rad",),
    "inductance_estimate": ("utilisation_factor_k_u",),  # U-M8g: inductance_estimate_h takes k_u
    "resistance_line": ("resistance_phase_operating",),
    "loss_copper": ("resistance_phase_operating",),
    "loss_total": LOSSES,
    "efficiency": ("output_power", "loss_total"),
    "temperature_rise": ("loss_total",),
    "torque_speed_rpm": ("ke_line",),  # the axis is linspace(0, 1.15 n_0) (fix_wave_f4.md A.7)
    "torque_speed_torque": DRIVE_INPUTS,
    "torque_speed_power": DRIVE_INPUTS,
    "base_speed": DRIVE_INPUTS,
    "no_load_speed": ("ke_line",),
}
FLUX_LINKAGE = {"EQ-06", "EQ-05"}  # path flux linkage in the field
PHASE_ASSEMBLY = {"EQ-07"}  # series and parallel members of a phase (EQ-10 formula: "parallel combination per EQ-07")
INHERITS = {
    "loss_circulating": FLUX_LINKAGE,  # EQ-07 P_c is formed from the path EMFs E_i
    "phase_circulating_loss": FLUX_LINKAGE,
    "resistance_phase_20c": PHASE_ASSEMBLY,
    "resistance_phase_operating": PHASE_ASSEMBLY,
    "phase_resistance_20c": PHASE_ASSEMBLY,
    "phase_resistance_operating": PHASE_ASSEMBLY,
}


def _traceables(value: object) -> Iterator[Traceable]:
    if isinstance(value, Traceable):
        yield value
    elif dataclasses.is_dataclass(value) and not isinstance(value, type):
        for field in dataclasses.fields(value):
            yield from _traceables(getattr(value, field.name))
    elif isinstance(value, tuple):
        for item in value:
            yield from _traceables(item)


@functools.cache
def _analysis(example: str) -> AnalysisResult:
    project = project_from_example(load_example(example))
    outcome = compute(project.design, project_provenance(project), registry=load_registry())
    assert outcome is not None and outcome.analysis is not None
    return outcome.analysis


@pytest.fixture(scope="module", params=(D08, BLOCK_MAGNETS, WITH_DRIVE))
def chains(request: pytest.FixtureRequest) -> dict[str, set[tuple[str, ...]]]:
    """Return every chain of one example by quantity; per-phase and per-layer results share a quantity."""
    found: dict[str, set[tuple[str, ...]]] = {}
    for t in _traceables(_analysis(request.param)):
        found.setdefault(t.quantity, set()).add(t.eq_ids)
    return found


def _only(chains: dict[str, set[tuple[str, ...]]], quantity: str) -> tuple[str, ...]:
    (chain,) = chains[quantity]
    return chain


def test_a_result_holds_the_chain_of_every_result_it_is_built_from(chains) -> None:
    """Defect caught: DEF-UE18-01 and its kin, e.g. inductance_estimate without the Ke equations of k_u (U-M8g)."""
    missing = {
        (result, source): sorted(set(_only(chains, source)) - set(_only(chains, result)))
        for result, sources in BUILT_FROM.items()
        if result in chains
        for source in sources
        if set(_only(chains, source)) - set(_only(chains, result))
    }
    assert missing == {}


def test_a_result_holds_the_equations_of_its_unreported_intermediates(chains) -> None:
    """Defect caught: a circulating loss without the flux linkage it is formed from, a phase R without EQ-07 (U-M8g)."""
    missing = {
        quantity: sorted(expected - set(chain))
        for quantity, expected in INHERITS.items()
        for chain in chains[quantity]
        if expected - set(chain)
    }
    assert missing == {}


def test_every_chain_lists_each_equation_once(chains) -> None:
    """Defect caught: a union that repeats an EQ-ID, which the How-computed disclosure would print twice."""
    repeated = {q: c for q, found in chains.items() for c in found if len(set(c)) != len(c)}
    assert repeated == {}


def test_the_field_chain_holds_eq04_only_where_the_pole_arc_ratio_comes_from_it() -> None:
    """Defect caught: Ke of a block-magnet rotor without EQ-04 (U-M8g), or EQ-04 on an arc magnet's given ratio.

    pole_arc_ratio_mm evaluates EQ-04 for a block magnet and returns the input ratio for an arc magnet.
    """
    analyses = {example: _analysis(example) for example in (D08, BLOCK_MAGNETS)}
    with_eq04 = {
        example: ["EQ-04" in t.eq_ids for t in (a.ke_phase_v_s_per_rad, a.layers[0].b1_peak_mid_radius_t)]
        for example, a in analyses.items()
    }
    assert with_eq04 == {D08: [False, False], BLOCK_MAGNETS: [True, True]}


def test_every_quantity_the_tables_name_exists() -> None:
    """Defect caught: a misspelt or renamed quantity in BUILT_FROM or INHERITS that the checks above would skip."""
    quantities = {t.quantity for t in _traceables(_analysis(WITH_DRIVE))}
    named = {*BUILT_FROM, *(s for sources in BUILT_FROM.values() for s in sources), *INHERITS}
    assert named - quantities == set()
