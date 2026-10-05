"""Self-tests of Agent 4's exemption model against cases worked by hand from interfaces.md section 7, D-022, D-022c."""

import math

import pytest
from drc_universe import Cls, Item, Rule, contract_exemptions
from records import Arc, Line, disc

pytestmark = pytest.mark.req("REQ-F-40")

W = 0.2


def _trace(path: int, seq: int, prim: Line | Arc, net: str, corner: bool = False) -> Item:
    return Item(f"path:{path}/prim:{seq}", Cls.TRACE, prim, 0, net, path, seq, corner=corner)


def _hairpin() -> list[Item]:
    """main0, fillet0, main1, fillet1, main2: fillet0 belongs to main0 and main1, fillet1 to main1 and main2."""
    a, b = 0.05, 0.5
    prims = [
        Line(0, 0, 10, 0, W),
        Arc(10, a, a, -math.pi / 2, math.pi / 2, W),
        Line(10 + a, a, 10 + a, a + 0.25, W),
        Arc(10 + a - b, a + 0.25, b, 0.0, math.pi / 2, W),
        Line(10 + a - b, a + 0.25 + b, 0, a + 0.25 + b, W),
    ]
    return [_trace(0, k, p, "PHASE_A", corner=isinstance(p, Arc)) for k, p in enumerate(prims)]


def _pair(a: str, b: str) -> frozenset[str]:
    return frozenset((a, b))


def test_rule_1_exempts_a_fillet_from_its_own_mains_only() -> None:
    """Catches the old ``abs(main) <= 1`` rule (DEF-M1V-01), which also exempts fillet1 from main0."""
    got = {k for k, r in contract_exemptions(_hairpin()).items() if r is Rule.NEIGHBOURS}
    m0, f0, m1, f1, m2 = (f"path:0/prim:{k}" for k in range(5))
    expected = {_pair(m0, f0), _pair(m0, m1), _pair(f0, m1), _pair(f0, f1), _pair(m1, f1), _pair(m1, m2), _pair(f1, m2)}
    assert got == expected


N_LINE = Line(0, 0, 10, 0, W)


@pytest.mark.parametrize(("interconnect", "exempt"), [((7,), True), ((), False)])
def test_interconnect_end_on_another_nets_via_is_exempt(interconnect: tuple[int, ...], exempt: bool) -> None:
    """D-022a/c: an N path ending on a PHASE_A via is exempt; the same path not listed as interconnect is not."""
    items = [_trace(7, 0, N_LINE, "N"), Item("via:0", Cls.VIA, disc(10, 0, 0.6), None, "PHASE_A")]
    got = contract_exemptions(items, interconnect).get(_pair("path:7/prim:0", "via:0"))
    assert got is (Rule.INTERCONNECT_END if exempt else None)


@pytest.mark.parametrize(
    ("offset_mm", "interconnect", "expected"),
    [(0.29, (7,), Rule.INTERCONNECT_TAP), (0.31, (7,), None), (0.0, (), None)],
    ids=["tap", "tap-near-miss", "not-interconnect"],
)
def test_via_on_an_interconnect_centreline_is_exempt(
    offset_mm: float, interconnect: tuple[int, ...], expected: Rule | None
) -> None:
    """D-022c: a via centred within pad/2 (0.3 mm) of an interconnect centreline mid-path is exempt from the path.

    It is exempt from every primitive of that path; 0.31 mm off, or on a path that is not an interconnect, it is not.
    """
    items = [
        _trace(7, 0, Line(0, 0, 5, 0, W), "N"),
        _trace(7, 1, Line(5, 0, 10, 0, W), "N"),
        Item("via:0", Cls.VIA, disc(5, offset_mm, 0.6), None, "PHASE_B"),
    ]
    got = contract_exemptions(items, interconnect)
    assert [got.get(_pair(f"path:7/prim:{k}", "via:0")) for k in (0, 1)] == [expected, expected]


@pytest.mark.parametrize(
    ("nets", "interconnect", "land", "expected"),
    [
        (("N", "PHASE_A"), (7,), True, Rule.INTERCONNECT_END),
        (("PHASE_B", "PHASE_A"), (), True, None),
        (("PHASE_A", "PHASE_A"), (), False, Rule.NODE),
        (("N", "PHASE_A"), (7,), False, None),
    ],
    ids=["interconnect-at-via", "other-nets-at-via", "same-net-point", "interconnect-at-bare-point"],
)
def test_rule_3_ends_at_one_node(
    nets: tuple[str, str], interconnect: tuple[int, ...], land: bool, expected: Rule | None
) -> None:
    """Rule 3 with the waiver: it reaches a via node, never a bare coincident point of two different nets."""
    items = [_trace(7, 0, N_LINE, nets[0]), _trace(8, 0, Line(10, 0, 10, 5, W), nets[1])]
    if land:
        items.append(Item("via:0", Cls.VIA, disc(10, 0, 0.6), None, "PHASE_C"))
    got = contract_exemptions(items, interconnect).get(_pair("path:7/prim:0", "path:8/prim:0"))
    assert got is expected
