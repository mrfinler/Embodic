"""Self-tests of Agent 4's exemption model against cases worked by hand from interfaces.md section 7, D-022, D-022c."""

import math
from itertools import pairwise

import pytest
from brute_clearance import Verdict
from drc_universe import Cls, Item, Rule, contract_exemptions, point_to_centreline, sweep
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
    """Rule 2 tap (D-022c, D-078): a via centred within pad/2 (0.3 mm) of the shared end of two interconnect primitives.

    Both primitives pass within the band, so both are exempt; 0.31 mm off, or on a path that is not an interconnect,
    neither is (UT-DRC-04 2d).
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
def test_rule_5_t_junction_exempts_the_end_group_from_the_landing_primitive_only(
    trunk: list[Line | Arc], end: tuple[float, float], nets: tuple[str, str], exempt: bool
) -> None:
    """D-035b as D-078 narrows it: a same-net end on a trunk primitive mid-path; end group against that primitive.

    Catches the whole-path reading (DEF-UV16-01): the other trunk primitives stay checked. The stem's first main is
    not in the end group, so it stays checked against the trunk either way.
    """
    x, y = end
    stem = [Line(x - 3, y - 3, x, y - 3, W), Line(x, y - 3, x, y, W)]
    items = [_trace(7, k, p, nets[0]) for k, p in enumerate(trunk)]
    items += [_trace(8, k, p, nets[1]) for k, p in enumerate(stem)]
    got = contract_exemptions(items)
    landing = 1 if trunk is TRUNK else 0
    expected = [Rule.TEE if exempt and k == landing else None for k in range(len(trunk))]
    assert [got.get(_pair("path:8/prim:1", f"path:7/prim:{k}")) for k in range(len(trunk))] == expected
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


RULE_MM = 0.2
VIA_MM = 0.6


def _violations(items: list[Item], interconnect: tuple[int, ...] = ()) -> dict[frozenset[str], tuple[str, float]]:
    """Every pair the brute sweep reports at a 0.2 mm rule under the model's exemptions, with its clearance."""
    found = sweep(items, [0], lambda kind: RULE_MM, contract_exemptions(items, interconnect), decide=False, tol=1e-9)
    assert all(r.verdict is not Verdict.UNDECIDED for r in found)
    return {
        frozenset((r.a, r.b)): (r.kind, round((r.clearance.lo + r.clearance.hi) / 2, 6))
        for r in found
        if r.verdict is Verdict.VIOLATION
    }


def _path(pid: int, prims: list[Line | Arc], net: str = "A", corners: tuple[int, ...] = ()) -> list[Item]:
    return [_trace(pid, k, p, net, corner=k in corners) for k, p in enumerate(prims)]


def _via(x: float, y: float, net: str) -> Item:
    return Item("via:0", Cls.VIA, disc(x, y, VIA_MM), None, net)


@pytest.mark.parametrize(
    ("leading", "expected"),
    [(True, {_pair("path:0/prim:0", "path:0/prim:2"): ("trace_trace", 0.1)}),
     (False, {_pair("path:0/prim:0", "path:0/prim:2"): ("trace_trace", 0.1)})],
    ids=["leading-taper", "control-side"],
)  # fmt: skip
def test_rule_1_a_leading_taper_belongs_to_the_first_main_only(leading: bool, expected: dict) -> None:
    """Rule 1 at a path end (DEF-UD25-01, u_d25_rule5.md section 6 Q2): the taper is not exempt from main 1.

    Catches a slot test that gives a leading fillet or taper the slot after main 0. The control has a side in place of
    the taper, so the pair is two mains two indices apart.
    """
    prims = [Line(0, 0, 1, 0, W), Line(1, 0, 1, 0.3, W), Line(1, 0.3, 0, 0.3, W)]
    assert _violations(_path(0, prims, corners=(0,) if leading else ())) == expected


@pytest.mark.parametrize(("h", "expected"), [(0.59, {"path:0/prim:2": 0.19}), (0.61, {})], ids=["2f", "2f-control"])
def test_rule_2_tap_leaves_a_far_primitive_of_the_tapped_interconnect_checked(h: float, expected: dict) -> None:
    """UT-DRC-04 2f (D-078): an N U-turn tapped mid-main0 by a PHASE_A via; main2 returns past the via.

    Catches the whole-path tap of D-022c as first written, which exempts main2 too.
    """
    ring = [Line(-5, 0, 5, 0, W), Line(5, 0, 5, h, W), Line(5, h, -5, h, W)]
    got = _violations([*_path(0, ring, "N"), _via(0, 0, "PHASE_A")], interconnect=(0,))
    assert got == {_pair(label, "via:0"): ("trace_via", c) for label, c in expected.items()}


def test_rule_2_tap_near_a_sharp_corner_exempts_both_primitives_in_the_band() -> None:
    """UT-DRC-04 2e: a PHASE_A via 0.2 mm before the corner of an N interconnect lies within pad/2 of both lines.

    Catches a tap that exempts only the nearest primitive (the second line would be reported at -0.2 mm).
    """
    ring = [Line(-5, 0, 0, 0, W), Line(0, 0, 0, 5, W)]
    items = [*_path(0, ring, "N"), _via(-0.2, 0, "PHASE_A")]
    assert _violations(items, interconnect=(0,)) == {}
    assert [contract_exemptions(items, (0,)).get(_pair(f"path:0/prim:{k}", "via:0")) for k in (0, 1)] == [
        Rule.INTERCONNECT_TAP
    ] * 2


@pytest.mark.parametrize("net", ["N", "PHASE_A"])
def test_rule_2_tap_names_vias_not_pads(net: str) -> None:
    """Q3 of u_d25_rule5.md: a pad centred on an interconnect centreline mid-path, no path end in it, stays checked.

    Section 7 names vias in the tap and in rule 2b; a pad is exempt from an interconnect only where a path end lies
    inside it (rule 2). Catches a tap that runs over every land.
    """
    ring = [Line(-5, 0, 5, 0, W)]
    pad = Item("pad:0", Cls.PAD, disc(0, 0, VIA_MM), 0, net)
    assert _violations([*_path(0, ring, "N"), pad], interconnect=(0,)) == {
        _pair("path:0/prim:0", "pad:0"): ("pad_trace", -0.4)
    }


@pytest.mark.parametrize(("y", "expected"), [(0.39, 0.19), (0.41, None)], ids=["5i", "5j"])
def test_rule_5_a_leg_on_a_coil_end_stays_checked_against_the_coil_turn(y: float, expected: float | None) -> None:
    """UT-DRC-04 5i and 5j, the DEF-UV16-01 shape: a coil turn and stub end on a via, and a leg starts there.

    Rules 2 and 3 exempt the leg from the stub (the coil's end group). Rule 5 adds only the stub's landing group, so
    the leg stays checked against the turn. Catches rule 5 exempting the whole coil.
    """
    coil = _path(0, [Line(-5, 0, 0, 0, W), Line(0, 0, 0, 2, W)])
    leg = _path(1, [Line(0, 2, -5, y, W)])
    want = {} if expected is None else {_pair("path:0/prim:0", "path:1/prim:0"): ("trace_trace", expected)}
    assert _violations([*coil, *leg, _via(0, 2, "A")]) == want


def test_rule_5_a_t_beside_a_fillet_is_exempt_from_the_fillet() -> None:
    """UT-DRC-04 5k: a branch lands on main0 0.1 mm before its fillet, so its copper overlaps the fillet.

    The landing group of main0 holds the fillet. Catches a landing group of the hit primitive alone.
    """
    trunk = _path(0, [Line(-5, 0, 4.5, 0, W), Arc(4.5, 0.5, 0.5, -math.pi / 2, math.pi / 2, W), Line(5, 0.5, 5, 5, W)],
                  corners=(1,))  # fmt: skip
    branch = _path(1, [Line(4.4, -4, 4.4, 0, W)])
    assert _violations([*trunk, *branch]) == {}


@pytest.mark.parametrize(("x", "expected"), [(0.39, 0.19), (0.41, None)], ids=["5l", "5l-control"])
def test_rule_5_a_t_stays_checked_against_the_trunk_return(x: float, expected: float | None) -> None:
    """UT-DRC-04 5l: a branch on the middle of main0; the trunk turns back and main2 ends beside the branch."""
    trunk = _path(0, [Line(-5, 0, 5, 0, W), Line(5, 0, 5, -2, W), Line(5, -2, x, -2, W)])
    branch = _path(1, [Line(0, 0, 0, -4, W)])
    want = {} if expected is None else {_pair("path:0/prim:2", "path:1/prim:0"): ("trace_trace", expected)}
    assert _violations([*trunk, *branch]) == want


def test_rule_5_a_t_before_a_sharp_corner_is_reported_against_the_next_main() -> None:
    """UT-DRC-04 5f inverted (D-078): the branch ends 0.05 mm before the trunk's sharp corner, on main0 only."""
    trunk = _path(0, [Line(-5, 0, 0, 0, W), Line(0, 0, 0, -5, W)])
    branch = _path(1, [Line(-0.05, 4, -0.05, 0, W)])
    assert _violations([*trunk, *branch]) == {_pair("path:0/prim:1", "path:1/prim:0"): ("trace_trace", -0.15)}


_HOOK = [(0.0, 0.0), (0.0, 2.0), (4.0, 2.0), (4.0, 5.0)]


@pytest.mark.parametrize("at_start", [True, False], ids=["trunk-start", "trunk-end"])
def test_rule_5_an_end_on_the_trunk_end_point_is_a_node_only(at_start: bool) -> None:
    """UT-DRC-04 5g inverted (D-078): the branch ends on the trunk's end point; the middle main is reported at 0.

    Rule 3 exempts end group against end group; rule 5's landing group there lies inside the trunk's end group.
    Catches the withdrawn end-point reading, which exempts the whole trunk.
    """
    points = _HOOK if at_start else _HOOK[::-1]
    trunk = _path(0, [Line(*a, *b, W) for a, b in pairwise(points)])
    branch = _path(1, [Line(0.5, 1.8, 0.0, 0.0, W)])
    assert _violations([*trunk, *branch]) == {_pair("path:0/prim:1", "path:1/prim:0"): ("trace_trace", 0.0)}
