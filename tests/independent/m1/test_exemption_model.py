"""Self-tests of Agent 4's exemption model against cases worked by hand from interfaces.md section 7, D-022, D-022c."""

import math

import pytest
from drc_universe import Cls, Item, Rule, contract_exemptions, point_to_centreline
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


TRUNK = [Line(0, 0, 5, 0, W), Line(5, 0, 10, 0, W), Line(10, 0, 15, 0, W)]
ARC_TRUNK = [Arc(0, 0, 10, 0.0, math.pi / 2, W), Line(0, 10, -5, 10, W)]
_DIAG = (10 * math.cos(math.pi / 4), 10 * math.sin(math.pi / 4))


@pytest.mark.parametrize(
    ("trunk", "end", "nets", "exempt"),
    [
        (TRUNK, (7.5, 0.0), ("PHASE_A", "PHASE_A"), True),
        (ARC_TRUNK, _DIAG, ("PHASE_A", "PHASE_A"), True),
        (TRUNK, (7.5, 0.0), ("PHASE_A", "PHASE_B"), False),
        (TRUNK, (7.5, -0.01), ("PHASE_A", "PHASE_A"), False),
    ],
    ids=["5a-line", "5b-arc", "5c-other-net", "5d-short"],
)
def test_rule_5_t_junction_exempts_the_end_group_from_the_whole_other_path(
    trunk: list[Line | Arc], end: tuple[float, float], nets: tuple[str, str], exempt: bool
) -> None:
    """D-035b: a same-net end on another path's centreline mid-path; end group against every trunk primitive.

    The stem's first main is not in the end group, so it stays checked against the trunk either way.
    """
    x, y = end
    stem = [Line(x - 3, y - 3, x, y - 3, W), Line(x, y - 3, x, y, W)]
    items = [_trace(7, k, p, nets[0]) for k, p in enumerate(trunk)]
    items += [_trace(8, k, p, nets[1]) for k, p in enumerate(stem)]
    got = contract_exemptions(items)
    expected = Rule.TEE if exempt else None
    assert [got.get(_pair("path:8/prim:1", f"path:7/prim:{k}")) for k in range(len(trunk))] == [expected] * len(trunk)
    assert [got.get(_pair("path:8/prim:0", f"path:7/prim:{k}")) for k in range(len(trunk))] == [None] * len(trunk)


def _u_turn(net: str) -> list[Item]:
    """prim0 east along y = 0, prim1 north 0.5 mm, prim2 back west along y = 0.5."""
    prims = [Line(0, 0, 10, 0, W), Line(10, 0, 10, 0.5, W), Line(10, 0.5, 0, 0.5, W)]
    return [_trace(7, k, p, net) for k, p in enumerate(prims)]


@pytest.mark.parametrize(
    ("centre", "via_net", "expected"),
    [
        ((5.0, 0.0), "PHASE_A", (Rule.VIA_TAP, None, None)),
        ((5.0, 0.29), "PHASE_A", (Rule.VIA_TAP, None, Rule.VIA_TAP)),
        ((5.0, -0.31), "PHASE_A", (None, None, None)),
        ((10.0, 0.0), "PHASE_A", (Rule.VIA_TAP, Rule.VIA_TAP, None)),
        ((5.0, 0.0), "PHASE_B", (None, None, None)),
    ],
    ids=["mid-prim0", "between-prim0-and-prim2", "near-miss", "corner", "other-net"],
)
def test_rule_2b_exempts_a_via_only_from_the_same_net_primitives_it_taps(
    centre: tuple[float, float], via_net: str, expected: tuple[Rule | None, ...]
) -> None:
    """D-036a with D-037a: per primitive whose centreline passes within pad/2 (0.3 mm) of the via centre.

    Catches the whole-path reading (prim2 of the U turn, 0.5 mm away, would be exempt with prim0) and a missing net
    test. The path is no interconnect and the via ends no path, so rules 2 and 4 and D-022c do not apply.
    """
    items = [*_u_turn("PHASE_A"), Item("via:0", Cls.VIA, disc(*centre, 0.6), None, via_net)]
    got = contract_exemptions(items)
    assert tuple(got.get(_pair(f"path:7/prim:{k}", "via:0")) for k in range(3)) == expected


_CW_ARC = Arc(0, 0, 10, math.pi / 2, -math.pi / 2, W)


@pytest.mark.parametrize(
    ("point", "prim", "expected"),
    [
        ((3.0, 4.0), Line(0, 0, 10, 0, W), 4.0),
        ((-3.0, 4.0), Line(0, 0, 10, 0, W), 5.0),
        ((6.0, 8.0), _CW_ARC, 0.0),
        ((3.0, 4.0), _CW_ARC, 5.0),
        ((-6.0, 8.0), _CW_ARC, math.dist((-6.0, 8.0), (0.0, 10.0))),
        ((0.0, 0.0), _CW_ARC, 10.0),
    ],
    ids=["line-foot", "line-end", "cw-arc-on", "cw-arc-inside", "cw-arc-outside-sweep", "arc-centre"],
)
def test_point_to_centreline_closed_forms(point: tuple[float, float], prim: Line | Arc, expected: float) -> None:
    """Catches an unclamped foot, a sweep read as counter-clockwise always, and a radial gap used outside the sweep."""
    assert point_to_centreline(point, prim) == pytest.approx(expected, abs=1e-12)


def test_rule_2b_names_vias_not_pads() -> None:
    """D-036a exempts a via on a same-net centreline; a pad there that no path end lies in stays checked."""
    items = [*_u_turn("PHASE_A"), Item("pad:0", Cls.PAD, disc(5.0, 0.0, 0.6), 0, "PHASE_A")]
    assert contract_exemptions(items).get(_pair("path:7/prim:0", "pad:0")) is None
