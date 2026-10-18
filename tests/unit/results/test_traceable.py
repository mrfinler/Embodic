"""UT-RES-02 (ADR-0003 worked example), UT-RES-05, UT-RES-06, UT-RES-07 and TR-03 at runtime: traced() results."""

import dataclasses

import pytest
from tests.unit.results.registries import raw_documents, with_all_tests_passed

from embodic.model.fields import FieldKind
from embodic.model.provenance import Provenance
from embodic.results.registry import Registry, parse_registry
from embodic.results.status import MetricBound, Status, ValidityEffect
from embodic.results.traceable import InputRef, evaluate_validity, intermediate, traced, traced_validity_metric
from embodic.units import Unit

THICKNESS = "/stackup/layers/0/thickness_mm"


def ref(pointer, value, unit, provenance, kind=FieldKind.DESIGN, label=None):
    """Return an input reference; property inputs default to the `assumption` label."""
    if kind is FieldKind.PROPERTY and label is None:
        label = Status.ASSUMPTION
    return InputRef(pointer=pointer, value=value, unit=unit, provenance=provenance, kind=kind, label=label)


R_INPUTS = (
    ref(THICKNESS, 0.035, Unit.MM, Provenance.EXAMPLE, FieldKind.PROPERTY),
    ref("/operating/winding_temperature_degc", 20.0, Unit.DEGC, Provenance.EXAMPLE),
    ref("/winding/coil/trace_width_mm", 0.6, Unit.MM, Provenance.USER),
    InputRef(pointer="constant:rho_20", value=1.7241e-8, unit=None, provenance=None, kind=None, label=Status.INFERRED),
    InputRef(pointer="result:track_length_mm", value=812.0, unit=Unit.MM, provenance=None, kind=None, label=None),
)


def ec05(registry: Registry):
    """Return the EC-05 check of EQ-05."""
    return registry.equation("EQ-05").validity_checks[0]


@pytest.mark.req("REQ-T-03", "REQ-T-05")
@pytest.mark.parametrize(
    ("quantity", "eq_ids", "e_edge", "passed", "badge"),
    [
        ("resistance_phase_operating_ohm", ("EQ-10", "EQ-11", "EQ-07"), None, True, Status.INFERRED),
        ("resistance_phase_operating_ohm", ("EQ-10", "EQ-11", "EQ-07"), None, False, Status.NOT_TESTED),
        ("ke_phase_v_s_per_rad", ("EQ-06", "EQ-04", "EQ-05", "EQ-07", "EQ-09"), 0.053, True, Status.INFERRED),
        ("ke_phase_v_s_per_rad", ("EQ-06", "EQ-04", "EQ-05", "EQ-07", "EQ-09"), 0.053, False, Status.NOT_TESTED),
        ("ke_phase_v_s_per_rad", ("EQ-06", "EQ-04", "EQ-05", "EQ-07", "EQ-09"), 0.124, True, Status.UNRESOLVED),
        ("mass_copper_g", ("EQ-16",), None, True, Status.ASSUMPTION),
        ("mass_copper_g", ("EQ-16",), None, False, Status.NOT_TESTED),
        ("temperature_rise_k", ("EQ-17",), None, True, Status.ASSUMPTION),
        ("inductance_estimate_h", ("EQ-14",), None, True, Status.UNRESOLVED),
    ],
)
def test_traceable_adr_0003_worked_example(contract_registry, quantity, eq_ids, e_edge, passed, badge):
    """Catches drift from ADR-0003's table: R and Ke reach inferred once tests pass, EQ-16/EQ-17 stay assumption.

    EQ-14 stays unresolved, and EC-05 above 10 % (the D09-like 10 mm rotor, 12.4 %) caps Ke.
    """
    registry = with_all_tests_passed(contract_registry) if passed else contract_registry
    validity = [evaluate_validity(ec05(registry), "EQ-05", e_edge)] if e_edge is not None else []
    result = traced(quantity, 1.0, Unit.ONE, eq_ids=eq_ids, inputs=R_INPUTS, registry=registry, validity=validity)
    assert result.status is badge


@pytest.mark.req("REQ-T-08")
def test_traceable_ec05_below_cap_adds_one_sided_addon_and_limitation(contract_registry):
    """Catches EC-05 capping below its threshold or dropping the +e_edge add-on (DEF-18)."""
    flag = evaluate_validity(ec05(contract_registry), "EQ-05", 0.053)
    assert flag.effect is ValidityEffect.LIMITATION
    assert flag.one_sided_addon == 0.053
    capped = evaluate_validity(ec05(contract_registry), "EQ-05", 0.124)
    assert (capped.effect, capped.one_sided_addon) == (ValidityEffect.CAP, None)


@pytest.mark.req("REQ-T-03", "REQ-F-21")
@pytest.mark.parametrize("provenance", list(Provenance))
def test_traceable_input_provenance_never_moves_the_badge(contract_registry, provenance):
    """Catches D-007 regressions: who typed a value, or whether it is measured, must not change badge or reasons."""
    registry = with_all_tests_passed(contract_registry)
    baseline = traced("r", 1.0, Unit.OHM, eq_ids=["EQ-10"], inputs=R_INPUTS, registry=registry)
    changed = (ref(THICKNESS, 0.035, Unit.MM, provenance, FieldKind.PROPERTY), *R_INPUTS[1:])
    result = traced("r", 1.0, Unit.OHM, eq_ids=["EQ-10"], inputs=changed, registry=registry)
    assert (result.status, result.status_reasons) == (baseline.status, baseline.status_reasons)
    assert result.status is Status.VERIFIED  # EQ-10 is verified and its tests passed; assumed inputs cannot lower it


@pytest.mark.req("REQ-T-03")
def test_traceable_tag_lists_exactly_the_assumed_inputs_dominant_first(packaged):
    """UT-RES-05: catches a user design input or a result reference in the tag, or a missing property or constant."""
    result = traced("r", 1.0, Unit.OHM, eq_ids=["EQ-10"], inputs=R_INPUTS, registry=packaged)
    assert [(a.item, a.reason, a.label, a.dominant) for a in result.assumed_inputs] == [
        (THICKNESS, "unmeasured_property", Status.ASSUMPTION, True),
        ("winding temperature T", "equation_assumption", Status.ASSUMPTION, True),
        ("PCB copper resistivity = IACS (G6)", "equation_assumption", Status.ASSUMPTION, True),
        ("/operating/winding_temperature_degc", "example", Status.ASSUMPTION, False),
        ("constant:rho_20", "registry_constant", Status.INFERRED, False),
    ]
    assert result.assumed_inputs[0].value_text == "0.0350\u00a0mm"


def registry_with_thickness_field() -> Registry:
    """Return the packaged registry where EQ-10's thickness assumption names the field a measurement retires."""
    equations, evidence = raw_documents()
    eq10 = next(e for e in equations["equations"] if e["id"] == "EQ-10")
    eq10["dominant_assumptions"][0] = {
        "text": "finished copper thickness t",
        "fields": ["/stackup/layers/*/thickness_mm"],
    }
    return parse_registry(equations, evidence, version="test")


@pytest.mark.req("REQ-T-06")
def test_traceable_measured_input_retires_itself_and_its_equation_assumption():
    """UT-RES-06: catches a measured thickness still listed, or its equation-level twin listed in its place."""
    registry = registry_with_thickness_field()
    unmeasured = traced("r", 1.0, Unit.OHM, eq_ids=["EQ-10"], inputs=R_INPUTS, registry=registry)
    measured_inputs = (ref(THICKNESS, 0.035, Unit.MM, Provenance.MEASURED, FieldKind.PROPERTY), *R_INPUTS[1:])
    measured = traced("r", 1.0, Unit.OHM, eq_ids=["EQ-10"], inputs=measured_inputs, registry=registry)

    unmeasured_items = [(a.item, a.dominant) for a in unmeasured.assumed_inputs]
    assert (THICKNESS, True) in unmeasured_items
    assert all(item != "finished copper thickness t" for item, _ in unmeasured_items)
    measured_items = {a.item for a in measured.assumed_inputs}
    assert THICKNESS not in measured_items
    assert "finished copper thickness t" not in measured_items
    assert len(measured.assumed_inputs) == len(unmeasured.assumed_inputs) - 1
    assert measured.status is unmeasured.status


@pytest.mark.req("REQ-T-16")
def test_traceable_ec05_metric_is_assumption_and_transfer_joins_affected_tags(contract_registry):
    """UT-RES-07: catches e_edge badged by its equation alone, missing DEF-23 labels, or Ke's tag without transfer."""
    registry = with_all_tests_passed(contract_registry)
    check = ec05(registry)
    e_edge = traced_validity_metric("edge_leakage_fraction", check, "EQ-05", 0.053, inputs=(), registry=registry)
    assert e_edge.status is Status.ASSUMPTION
    assert e_edge.label == "lower bound"
    (flag,) = e_edge.validity
    assert flag.metric_bound is MetricBound.LOWER_BOUND
    assert (flag.calibration_status, flag.transfer_status, flag.threshold_status) == (
        Status.INFERRED,
        Status.ASSUMPTION,
        Status.ASSUMPTION,
    )
    above = traced_validity_metric("edge_leakage_fraction", check, "EQ-05", 0.124, inputs=(), registry=registry)
    assert above.status is Status.ASSUMPTION

    ke = traced("ke", 1.0, Unit.V_S_PER_RAD, eq_ids=["EQ-06", "EQ-05"], inputs=(), registry=registry, validity=[flag])
    transfer = [a for a in ke.assumed_inputs if a.item == "EC-05 calibration transferred to this rotor"]
    assert [(a.reason, a.label) for a in transfer] == [("equation_assumption", Status.ASSUMPTION)]


@pytest.mark.req("REQ-T-05")
def test_tr03_no_result_shows_verified_without_a_passing_linked_test(packaged):
    """TR-03 at runtime: in a build where no linked test passed, no verified equation yields a verified badge."""
    verified = [e.id for e in packaged.equations.values() if e.status is Status.VERIFIED]
    statuses = {traced("q", 1.0, Unit.ONE, eq_ids=[eq], inputs=[], registry=packaged).status for eq in verified}
    assert statuses == {Status.NOT_TESTED}
    passed = with_all_tests_passed(packaged)
    assert traced("q", 1.0, Unit.ONE, eq_ids=["EQ-13"], inputs=[], registry=passed).status is Status.VERIFIED


@pytest.mark.req("REQ-T-02", "REQ-T-04")
def test_traceable_carries_registry_evidence_label_and_tolerance(packaged):
    """Catches evidence IDs copied by hand instead of from the registry, or a lost 'estimate' label (REQ-T-05)."""
    result = traced("l", 1e-6, Unit.H, eq_ids=["EQ-14"], inputs=[], registry=packaged)
    assert result.evidence_ids == ("EV-31", "EV-44", "EV-19")
    assert result.label == "estimate"
    assert result.tolerance is not None
    assert result.tolerance.against.startswith("none claimed")


@pytest.mark.req("REQ-T-02")
def test_traceable_computed_result_without_equation_is_refused(packaged):
    """Catches a computed number that would reach the UI with no EQ-ID to link."""
    with pytest.raises(ValueError, match="needs at least one EQ-ID"):
        traced("q", 1.0, Unit.ONE, eq_ids=[], inputs=[], registry=packaged)


@pytest.mark.req("REQ-T-13")
def test_traceable_how_computed_names_status_reasons_inputs_and_tag(packaged):
    """Catches a disclosure missing the reasons, the input provenance or the tag count."""
    text = traced("r", 1.0, Unit.OHM, eq_ids=["EQ-10"], inputs=R_INPUTS, registry=packaged).how_computed()
    assert "Status: not tested (EQ-10 verified; EQ-10 tests not passed in this build)" in text
    assert f"{THICKNESS} = 0.0350\u00a0mm (example)" in text
    assert "Assumed inputs (5):" in text
    assert "Tolerance: +/-8 % vs measured DC resistance" in text


@pytest.mark.req("REQ-T-02")
def test_traceable_is_frozen(packaged):
    """Catches a mutable result whose badge a view could overwrite."""
    result = traced("q", 1.0, Unit.ONE, eq_ids=["EQ-01"], inputs=[], registry=packaged)
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.status = Status.VERIFIED


def _ke(registry: Registry):
    """Return a phase Ke whose chain is the field model, the flux linkage and the phase assembly."""
    return traced("ke_phase", 1.0, Unit.V_S_PER_RAD, eq_ids=("EQ-06", "EQ-07", "EQ-05"), inputs=(), registry=registry)


@pytest.mark.req("REQ-T-05")
def test_traced_chain_is_own_equations_then_each_input_chain_once(packaged):
    """Catches DEF-UE18-01 by construction: a result built from Ke that drops Ke's equations or lists one twice."""
    resistance = traced("r", 1.0, Unit.OHM, eq_ids=("EQ-10", "EQ-11"), inputs=(), registry=packaged)
    km = traced(
        "km",
        1.0,
        Unit.ONE,
        eq_ids=("EQ-26", "EQ-10"),
        inputs=(),
        registry=packaged,
        built_from=(_ke(packaged), resistance),
    )
    assert km.eq_ids == ("EQ-26", "EQ-10", "EQ-06", "EQ-07", "EQ-05", "EQ-11")


@pytest.mark.req("REQ-T-05")
def test_traced_badge_takes_the_weakest_equation_of_an_input_chain(packaged):
    """Catches a `verified` Kt whose Ke rests on the `inferred` field model (fix_wave_f2.md A.5, V3)."""
    registry = with_all_tests_passed(packaged)
    alone = traced("kt", 1.0, Unit.N_M_PER_A, eq_ids=("EQ-09",), inputs=(), registry=registry)
    built = traced(
        "kt", 1.0, Unit.N_M_PER_A, eq_ids=("EQ-09",), inputs=(), registry=registry, built_from=(_ke(registry),)
    )
    assert (alone.status, built.status) == (Status.VERIFIED, Status.INFERRED)


@pytest.mark.req("REQ-T-05")
def test_intermediate_names_its_equations_once_for_every_result_built_from_it(packaged):
    """Catches an unreported intermediate (a flux-linkage array, a phasor) whose equations a result fails to inherit."""
    field = intermediate("EQ-05", "EQ-04")
    flux = intermediate("EQ-06", built_from=(field,))
    emf = intermediate("EQ-07", built_from=(flux,))
    ke = traced("ke_phase", 1.0, Unit.V_S_PER_RAD, eq_ids=("EQ-06",), inputs=(), registry=packaged, built_from=(emf,))
    assert emf.eq_ids == ("EQ-07", "EQ-06", "EQ-05", "EQ-04")
    assert ke.eq_ids == ("EQ-06", "EQ-07", "EQ-05", "EQ-04")
