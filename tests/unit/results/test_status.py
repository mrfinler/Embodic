"""UT-RES-02: the D-007 badge truth table over evidence status, gate, test state and validity cap."""

import itertools

import pytest

from embodic.results.status import (
    STATUS_ORDER_WEAKEST_FIRST,
    ChainLink,
    GateVerdict,
    Status,
    ValidityEffect,
    ValidityFlag,
    combine_status,
    derive_badge,
)

S = Status


def link(evidence: Status, *, gate: GateVerdict = GateVerdict.REUSE, passed: bool = True, eq_id: str = "EQ-90"):
    """Return one chain link; defaults are a reused, tested equation."""
    return ChainLink(eq_id=eq_id, gate=gate, evidence=evidence, tests_passed=passed)


def flag(effect: ValidityEffect) -> ValidityFlag:
    """Return a validity outcome with the given effect."""
    return ValidityFlag(code="EC-90", message="m", eq_id="EQ-90", effect=effect)


@pytest.mark.req("REQ-T-03")
def test_status_order_is_weakest_first_per_adr_0003():
    """Catches a reordered vocabulary: ADR-0003 fixes unresolved < not tested < assumption < inferred < verified."""
    assert [s.value for s in STATUS_ORDER_WEAKEST_FIRST] == [
        "unresolved",
        "not tested",
        "assumption",
        "inferred",
        "verified",
    ]


@pytest.mark.req("REQ-T-03")
@pytest.mark.parametrize(("a", "b"), list(itertools.combinations(STATUS_ORDER_WEAKEST_FIRST, 2)))
def test_status_combine_returns_the_weaker_of_any_pair(a, b):
    """Catches max() in place of min(), or a combine that depends on argument order."""
    assert combine_status(a, b) is a
    assert combine_status(b, a) is a


@pytest.mark.req("REQ-T-03", "REQ-T-05")
@pytest.mark.parametrize(
    ("evidence", "gate", "passed", "effect", "expected"),
    [
        (S.VERIFIED, GateVerdict.REUSE, True, None, S.VERIFIED),
        (S.VERIFIED, GateVerdict.REUSE, False, None, S.NOT_TESTED),
        (S.INFERRED, GateVerdict.REUSE_WITH_CHANGE, True, None, S.INFERRED),
        (S.INFERRED, GateVerdict.REUSE_WITH_CHANGE, False, None, S.NOT_TESTED),
        (S.ASSUMPTION, GateVerdict.REUSE_WITH_CHANGE, True, None, S.ASSUMPTION),
        (S.ASSUMPTION, GateVerdict.REUSE_WITH_CHANGE, False, None, S.NOT_TESTED),
        (S.VERIFIED, GateVerdict.CANNOT_VERIFY_YET, True, None, S.UNRESOLVED),
        (S.VERIFIED, GateVerdict.REPLACE, True, ValidityEffect.LIMITATION, S.VERIFIED),
        (S.VERIFIED, GateVerdict.REPLACE, True, ValidityEffect.CAP, S.UNRESOLVED),
        (S.INFERRED, GateVerdict.REUSE, False, ValidityEffect.CAP, S.UNRESOLVED),
    ],
)
def test_status_badge_truth_table(evidence, gate, passed, effect, expected):
    """Catches each factor dropped from the badge: untested code, gate 'cannot verify yet', or a validity cap."""
    validity = [flag(effect)] if effect else []
    assert derive_badge([link(evidence, gate=gate, passed=passed)], validity)[0] is expected


@pytest.mark.req("REQ-T-03")
def test_status_badge_is_the_weakest_link_of_the_chain():
    """Catches a badge taken from the first or last equation instead of the weakest one."""
    chain = [link(S.VERIFIED, eq_id="EQ-10"), link(S.INFERRED, eq_id="EQ-11"), link(S.VERIFIED, eq_id="EQ-09")]
    status, reasons = derive_badge(chain, [])
    assert status is S.INFERRED
    assert reasons == ("EQ-10 verified", "EQ-11 inferred", "EQ-09 verified")


@pytest.mark.req("REQ-T-03", "REQ-T-13")
def test_status_reasons_name_the_factors_that_hold_the_badge():
    """Catches a disclosure that shows the badge without saying which test state or cap set it."""
    status, reasons = derive_badge([link(S.INFERRED, passed=False, eq_id="EQ-07")], [flag(ValidityEffect.CAP)])
    assert status is S.UNRESOLVED
    assert reasons == ("EQ-07 inferred", "EQ-07 tests not passed in this build", "EC-90 validity limit exceeded")


@pytest.mark.req("REQ-T-03")
def test_status_empty_chain_is_not_tested():
    """Catches a value with no equation (input, count) getting a badge it never earned."""
    assert derive_badge([], []) == (S.NOT_TESTED, ("no equation in the chain",))
