"""UT-RES-03, TR-03, TR-04: registry loading, integrity, lookups and the gates on linked tests."""

import copy
import dataclasses
import re
from pathlib import Path

import pytest
from tests.unit.results.registries import raw_documents

from embodic.model.fields import FIELDS
from embodic.model.schema import pattern_of
from embodic.model.vocabulary import TopologyKind
from embodic.results.registry import RegistryFormatError, parse_registry
from embodic.results.status import MetricBound, Status
from embodic.units import Unit

SRC = Path(__file__).resolve().parents[3] / "src" / "embodic"
# U-E2 registry: equations still without an EV-ID (registry content, owner Agent 2).
UNSOURCED = {"EQ-18", "EQ-19", "EQ-23", "EQ-24", "EQ-25", "EQ-26", "EQ-28", "EQ-29", "EQ-30"}
# U-E2: three constants from EV-53, three labelled `assumption` without a source.
CONSTANTS = {
    "copper_resistivity_20c_ohm_m": (1.7241e-08, Unit.OHM_M, Status.VERIFIED),
    "copper_temp_coeff_per_k": (0.00393, Unit.PER_K, Status.VERIFIED),
    "copper_density_g_per_cm3": (8.89, Unit.G_PER_CM3, Status.VERIFIED),
    "laminate_density_g_per_cm3": (1.85, Unit.G_PER_CM3, Status.ASSUMPTION),
    "ndfeb_density_g_per_cm3": (7.5, Unit.G_PER_CM3, Status.ASSUMPTION),
    "steel_density_g_per_cm3": (7.85, Unit.G_PER_CM3, Status.ASSUMPTION),
}


@pytest.mark.req("REQ-T-04")
def test_registry_packaged_counts_and_versions(packaged):
    """Catches a loader that drops entries or a version not tied to the synced files."""
    assert len(packaged.equations) == 30
    assert len(packaged.evidence) == 86  # the phase2_scope entries of the 94 in the source register
    assert re.fullmatch(r"v1\+[0-9a-f]{12}\.[0-9a-f]{12}", packaged.version)
    assert packaged.passed_tests == frozenset()


@pytest.mark.req("REQ-T-04")
def test_registry_packaged_issues_are_exactly_the_known_gaps(packaged):
    """Catches a dangling or dropped EV-ID, an untyped EC-05 field, or a gap the loader stops reporting (UT-RES-03)."""
    by_code: dict[str, list[str]] = {}
    for issue in packaged.issues:
        by_code.setdefault(issue.code, []).append(str(issue.value))
    assert by_code == {"INTERNAL_REGISTRY_EQUATION_UNSOURCED": sorted(UNSOURCED)}


@pytest.mark.req("REQ-T-04")
def test_registry_missing_evidence_is_an_issue_not_an_exception():
    """Catches a loader that raises on a dangling EV-ID instead of reporting it."""
    equations, evidence = raw_documents()
    equations["equations"][0]["sources"] = ["EV-03", "EV-999"]
    registry = parse_registry(equations, evidence, version="test")
    missing = [i for i in registry.issues if i.code == "INTERNAL_REGISTRY_EVIDENCE_MISSING"]
    assert [(i.value, i.pointers) for i in missing] == [("EV-999", ("/equations/EQ-01/sources",))]


@pytest.mark.req("REQ-T-04")
@pytest.mark.parametrize("document", ["equations", "entries"])
def test_registry_duplicate_id_is_a_format_error(document):
    """Catches a later duplicate silently replacing the first entry with the same ID."""
    equations, evidence = raw_documents()
    target = equations if document == "equations" else evidence
    target[document].append(copy.deepcopy(target[document][0]))
    with pytest.raises(RegistryFormatError, match="appears twice"):
        parse_registry(equations, evidence, version="test")


@pytest.mark.req("REQ-T-04")
def test_registry_unknown_status_is_a_format_error():
    """Catches a misspelt status label being accepted as some default."""
    equations, evidence = raw_documents()
    equations["equations"][4]["status"] = "verifed"
    with pytest.raises(RegistryFormatError, match="EQ-05"):
        parse_registry(equations, evidence, version="test")


@pytest.mark.req("REQ-T-04")
def test_registry_lookups_by_eq_ev_and_topology(packaged):
    """Catches lookups that return the wrong entry or ignore `applies_to`."""
    assert packaged.equation("EQ-10").name.startswith("DC resistance")
    assert packaged.evidence["EV-53"].document == "NBS-HB100"
    spiral = {e.id for e in packaged.equations_for(TopologyKind.SPIRAL)}
    wave = {e.id for e in packaged.equations_for(TopologyKind.WAVE)}
    assert spiral - wave == {"EQ-02", "EQ-25"}
    assert wave - spiral == {"EQ-24"}
    with pytest.raises(KeyError):
        packaged.equation("EQ-99")


@pytest.mark.req("REQ-T-04")
def test_registry_is_frozen_after_load(packaged):
    """Catches a registry that callers can mutate, which would let one result change another's badge."""
    with pytest.raises(TypeError):
        packaged.equations["EQ-01"] = packaged.equations["EQ-02"]
    with pytest.raises(dataclasses.FrozenInstanceError):
        packaged.passed_tests = frozenset({"x"})


@pytest.mark.req("REQ-T-16")
def test_registry_packaged_ec05_fields_are_read_as_typed(packaged):
    """Catches the loader falling back to a weakest value for an EC-05 field the U-E2 registry types."""
    check = packaged.equation("EQ-05").validity_checks[0]
    assert check.threshold == 0.10
    assert check.metric_bound is MetricBound.LOWER_BOUND
    assert check.calibration_status is Status.INFERRED
    assert (check.transfer_status, check.threshold_status) == (Status.ASSUMPTION, Status.ASSUMPTION)
    assert (check.independent_oracles, check.dependent_oracles) == (("OR-01",), ("OR-07", "OR-08"))


@pytest.mark.req("REQ-T-16")
def test_registry_ec05_contract_fields_are_read_as_typed(contract_registry):
    """Catches the loader ignoring typed DEF-23 fields once Agent 2 adds them."""
    check = contract_registry.equation("EQ-05").validity_checks[0]
    assert check.threshold == 0.10
    assert check.metric_bound is MetricBound.LOWER_BOUND
    assert check.calibration_status is Status.INFERRED
    assert check.dependent_oracles == ("OR-07", "OR-08")
    assert not [i for i in contract_registry.issues if i.code == "INTERNAL_REGISTRY_FIELD_UNTYPED"]


@pytest.mark.req("REQ-T-16")
def test_registry_packaged_ec05_carries_the_typed_def23_fields(packaged):
    """Catches a DEF-23 field of EC-05 written back as prose (DEF-M2b-01, closed by U-E2)."""
    assert not [i for i in packaged.issues if i.code == "INTERNAL_REGISTRY_FIELD_UNTYPED"]


@pytest.mark.req("REQ-T-04")
@pytest.mark.parametrize("name", sorted(CONSTANTS))
def test_registry_packaged_constants_carry_value_unit_and_status(packaged, name):
    """Catches a U-E2 constant dropped, or one whose value, unit or label changed without a registry revision."""
    constant = packaged.constant(name)
    assert (constant.value, Unit(constant.unit), constant.status) == CONSTANTS[name]


@pytest.mark.req("REQ-T-03")
def test_registry_assumption_fields_name_field_table_pointers(packaged):
    """Catches a dominant assumption whose `fields` pattern matches no FIELDS pointer, so no input can retire it."""
    pointers = {spec.pointer for spec in FIELDS}
    patterns = {pattern for eq in packaged.equations.values() for a in eq.assumptions for pattern in a.fields}
    assert patterns
    assert {pattern_of(p) for p in patterns} <= pointers


@pytest.mark.req("REQ-T-05")
def test_registry_test_state_needs_every_linked_test(packaged):
    """Catches test_state raising an equation when only some of its tests passed."""
    tests = packaged.equation("EQ-10").tests
    partial = dataclasses.replace(packaged, passed_tests=frozenset(tests[:-1]))
    complete = dataclasses.replace(packaged, passed_tests=frozenset(tests))
    assert partial.test_state("EQ-10") is Status.NOT_TESTED
    assert complete.test_state("EQ-10") is Status.VERIFIED


@pytest.mark.req("REQ-T-05")
def test_tr03_every_verified_equation_links_a_test(packaged):
    """TR-03 structure: a verified equation without a linked test could never reach its badge honestly."""
    unlinked = [e.id for e in packaged.equations.values() if e.status is Status.VERIFIED and not e.tests]
    assert unlinked == []


@pytest.mark.req("REQ-T-04")
def test_tr04_every_eq_and_ev_id_in_source_code_exists_in_the_registry(packaged):
    """TR-04: an EQ-ID or EV-ID written in src/embodic must resolve, or the UI would show a dead link."""
    text = "\n".join(p.read_text(encoding="utf-8") for p in SRC.rglob("*.py"))
    eq_ids = set(re.findall(r"\bEQ-\d{2}\b", text))
    ev_ids = set(re.findall(r"\bEV-\d{2}\b", text))
    assert eq_ids
    assert eq_ids - packaged.equations.keys() == set()
    assert ev_ids - packaged.evidence.keys() == set()


@pytest.mark.req("REQ-T-04")
def test_tr04_registry_test_links_belong_to_their_equation(packaged):
    """TR-04: every linked test ID is EQT-<nn>-<kind> of its own equation, so no link points at another's test."""
    stray = [
        (e.id, t)
        for e in packaged.equations.values()
        for t in e.tests
        if not re.fullmatch(rf"EQT-{e.id.removeprefix('EQ-')}-[A-Z0-9]+", t)
    ]
    assert stray == []
