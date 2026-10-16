"""D-030 input bounds of the serpentine generator; UT-GEN-01: hostile numbers never raise (DEF-M3b-03)."""

import dataclasses
import math
from functools import cache

import pytest
from hypothesis import event, example, given, settings
from hypothesis import strategies as st

from embodic.errors import Unbuildable
from embodic.generators import generate_serpentine
from embodic.generators.serpentine import generate as serpentine_generate
from embodic.geometry.layout import BoardStack
from embodic.model.design import DesignParameters
from embodic.model.winding_specs import SerpentineWindingSpec
from embodic.results import Registry, load_registry

from ..hostile_sizes import HOSTILE_SETTINGS, WIDTHS, Sizes, check_hostile_build, hostile_sizes, timed_build
from .make_example import example_design
from .support import with_copper_count, with_winding

pytestmark = pytest.mark.req("REQ-F-34")
REGISTRY = load_registry()
OUT_OF_RANGE = "UNBUILDABLE_SERPENTINE_INPUT_OUT_OF_RANGE"
NAN, INF = math.nan, math.inf


def _check_contract(result: BoardStack | Unbuildable) -> None:
    """Every winding path is in the circuit exactly once or is interconnect; every referenced via exists."""
    if isinstance(result, Unbuildable):
        return
    for board in result.boards:
        members = [m for pc in board.circuit.phases for g in pc.groups for m in g.members]
        listed = [i for m in members for i in m.path_ids] + list(board.circuit.interconnect_path_ids)
        assert sorted(listed) == sorted(p.id for p in board.paths)
        assert all(v in {via.id for via in board.vias} for m in members for v in m.via_ids)


@cache
def _base() -> DesignParameters:
    return example_design()


def _fuzzed(
    r_inner: float, span: float, w: float, s: float, pad: float, turns: int, strands: int, poles: int, layers: int
) -> DesignParameters:  # fmt: skip
    design = _base()
    assert isinstance(design.winding, SerpentineWindingSpec)
    if layers in (1, 2, 4):  # the stack-up matches, so the build itself is reached; other counts test the refusal
        design = with_copper_count(design, design.phases * layers)
    design = with_winding(
        design, r_inner_mm=r_inner, r_outer_mm=r_inner + span, trace_width_mm=w, clearance_mm=s, turns=turns,
        strands=strands, layers_per_phase=layers,
    )  # fmt: skip
    return dataclasses.replace(
        design,
        rotor=dataclasses.replace(design.rotor, poles=poles),
        vias=dataclasses.replace(design.vias, pad_mm=pad),
    )


@pytest.fixture(scope="module")
def registry() -> Registry:
    """Return the packaged registry, loaded once."""
    return REGISTRY


@settings(max_examples=40, deadline=None)
@example(r_inner=22.0, span=18.0, w=0.4, s=0.2, pad=0.6, turns=2, strands=1, poles=0, layers=2)
@example(r_inner=float("nan"), span=18.0, w=0.4, s=0.2, pad=0.6, turns=2, strands=1, poles=16, layers=2)
@example(r_inner=22.0, span=18.0, w=0.4, s=0.0, pad=0.6, turns=200, strands=3, poles=200, layers=2)
@example(r_inner=22.0, span=18.0, w=1e-9, s=0.2, pad=0.6, turns=2, strands=1, poles=16, layers=4)
@example(  # DEF-M3b-03 shape: denormal width, clearance and pad on a small span
    r_inner=1.0, span=1.0, w=1.175494351e-38, s=1.401298464324817e-45, pad=1.401298464324817e-45,
    turns=1, strands=1, poles=4, layers=2,
)  # fmt: skip
@given(
    r_inner=st.floats(-5.0, 60.0) | st.just(float("nan")) | st.just(float("inf")),
    span=st.floats(-5.0, 40.0),
    w=st.floats(-0.1, 3.0),
    s=st.floats(-0.1, 1.0),
    pad=st.floats(0.0, 2.0),
    turns=st.integers(-1, 250),
    strands=st.integers(-1, 5),
    poles=st.sampled_from([0, 1, 2, 4, 8, 16, 20, 200, 202]),
    layers=st.sampled_from([0, 1, 2, 3, 4]),
)
def test_fuzzed_inputs_give_a_stack_or_unbuildable_never_an_exception(
    r_inner: float, span: float, w: float, s: float, pad: float, turns: int, strands: int, poles: int, layers: int
) -> None:  # fmt: skip
    """UT-GEN-01. Catches an exception, an unbounded build or an incomplete circuit on hostile numbers."""
    _check_contract(generate_serpentine(_fuzzed(r_inner, span, w, s, pad, turns, strands, poles, layers), REGISTRY))


def _example_sizes() -> Sizes:
    design = _base()
    assert isinstance(design.winding, SerpentineWindingSpec)
    return Sizes(
        clearance_mm=design.winding.clearance_mm,
        pad_mm=design.vias.pad_mm,
        terminal_pad_mm=design.connection.terminal_pad_mm,
    )


_TINIEST = Sizes(clearance_mm=5e-324, pad_mm=5e-324, terminal_pad_mm=5e-324)
_SMALLEST_NORMAL_MM = 2.2250738585072014e-308


_D030_INPUTS = {
    "r_inner": st.floats(1.0, 60.0),
    "span": st.floats(1.0, 40.0),
    "width": st.sampled_from(WIDTHS),
    "turns": st.integers(1, 30),
    "sizes": st.deferred(lambda: hostile_sizes(_base().drc_rules, _example_sizes(), terminal_pad=True)),
}


def _hostile_build(r_inner: float, span: float, width: str, turns: int, at: Sizes) -> BoardStack | Unbuildable:
    base = _base()
    assert isinstance(base.winding, SerpentineWindingSpec)
    width_mm = base.drc_rules.min_trace_width_mm if width == WIDTHS[0] else base.winding.trace_width_mm
    design = with_winding(
        base, r_inner_mm=r_inner, r_outer_mm=r_inner + span, trace_width_mm=width_mm,
        clearance_mm=at.clearance_mm, turns=turns,
    )  # fmt: skip
    design = dataclasses.replace(
        design,
        vias=dataclasses.replace(design.vias, pad_mm=at.pad_mm),
        connection=dataclasses.replace(design.connection, terminal_pad_mm=at.terminal_pad_mm),
    )
    return generate_serpentine(design, REGISTRY)


@pytest.mark.slow
@pytest.mark.req("REQ-F-19")
@HOSTILE_SETTINGS
@example(r_inner=1.0, span=1.0, width="example", turns=1, sizes=_TINIEST)  # DEF-M3b-03 shape
@example(
    r_inner=22.0,
    span=18.0,
    width="example",
    turns=4,
    sizes=Sizes(clearance_mm=0.2, pad_mm=_SMALLEST_NORMAL_MM, terminal_pad_mm=2.4),
)
@given(**_D030_INPUTS)
def test_d030_hostile_clearance_and_pads_are_built_or_refused_without_error(
    r_inner: float, span: float, width: str, turns: int, sizes: Sizes
) -> None:
    """D-030 lower bounds (d030_property_spec.md), properties 1 to 4; the build time is the next test.

    Defect caught: a division by one of these sizes (DEF-M3b-03 for the width), a count derived from 1/size without the
    width floor, a non-finite coordinate, or an exception instead of Unbuildable. The width is valid by construction,
    so the width refusal never stops the build.

    Property 4 is not evaluated when the design is Unbuildable at the default sizes (the spec does not define it). One
    nightly run of 200 examples: 54.0% Unbuildable, 40.0% compared with the baseline, 6.0% without a baseline.
    """
    reached = check_hostile_build(
        lambda: _hostile_build(r_inner, span, width, turns, sizes),
        lambda: _hostile_build(r_inner, span, width, turns, _example_sizes()),
        _check_contract,
        deadline=False,
    )
    event(f"example reached: {reached}")


@pytest.mark.xfail(
    strict=True, raises=AssertionError, reason="DEF-M6b-01: serpentine build time at near-zero clearance, Phase 5"
)
@pytest.mark.slow
@pytest.mark.req("REQ-F-19")
@HOSTILE_SETTINGS
@example(
    r_inner=60.0, span=40.0, width="rule_minimum", turns=30, sizes=_TINIEST
)  # DEF-M6b-01: 16 s, 3 s at the default
@given(**_D030_INPUTS)
def test_d030_hostile_clearance_and_pads_are_built_within_the_deadline(
    r_inner: float, span: float, width: str, turns: int, sizes: Sizes
) -> None:
    """D-030 lower bounds, property 5: the hostile build takes at most 10 s (the bound stays as the spec has it).

    A strict xfail until Phase 5 (D-050): near-zero clearance multiplies the build time by about 5 with identical
    output (fit.py min_straight iterates more). The test turns XPASS, and so fails, once the time drops under 10 s.
    """
    timed_build(lambda: _hostile_build(r_inner, span, width, turns, sizes))


@pytest.fixture
def no_geometry(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail the test if the generator derives the frame or plans any copper: a refusal must come first."""

    def built(*_: object, **__: object) -> None:
        raise AssertionError("geometry was built for a refused input")

    for name in ("derive", "plan_stack"):
        monkeypatch.setattr(serpentine_generate, name, built)


def _spec(**changes: float) -> DesignParameters:
    return with_winding(_base(), **changes)


def _with(**changes: float) -> DesignParameters:
    """Return the example with ``changes`` applied to its via spec."""
    design = _base()
    return dataclasses.replace(design, vias=dataclasses.replace(design.vias, **changes))


def _with_poles(poles: int) -> DesignParameters:
    design = _base()
    return dataclasses.replace(design, rotor=dataclasses.replace(design.rotor, poles=poles))


@pytest.mark.parametrize(
    ("design", "pointers"),
    [
        pytest.param(_spec(trace_width_mm=NAN), ["/winding/trace_width_mm"], id="trace-width-nan"),
        pytest.param(_spec(trace_width_mm=0.0), ["/winding/trace_width_mm"], id="trace-width-zero"),
        pytest.param(_spec(trace_width_mm=-0.4), ["/winding/trace_width_mm"], id="trace-width-negative"),
        pytest.param(_spec(trace_width_mm=1.175494351e-38), ["/winding/trace_width_mm"], id="trace-width-denormal"),
        pytest.param(_spec(trace_width_mm=0.149), ["/winding/trace_width_mm"], id="trace-width-below-drc-minimum"),
        pytest.param(_spec(clearance_mm=NAN), ["/winding/clearance_mm"], id="clearance-nan"),
        pytest.param(_spec(clearance_mm=0.0), ["/winding/clearance_mm"], id="clearance-zero"),
        pytest.param(_spec(clearance_mm=-0.2), ["/winding/clearance_mm"], id="clearance-negative"),
        pytest.param(_with(pad_mm=NAN), ["/vias/pad_mm"], id="pad-nan"),
        pytest.param(_with(pad_mm=0.0), ["/vias/pad_mm"], id="pad-zero"),
        pytest.param(_spec(r_inner_mm=NAN), ["/winding/r_inner_mm"], id="r-inner-nan"),
        pytest.param(_spec(r_inner_mm=INF), ["/winding/r_inner_mm"], id="r-inner-infinite"),
        pytest.param(_spec(r_inner_mm=0.0), ["/winding/r_inner_mm"], id="r-inner-zero"),
        pytest.param(_spec(r_outer_mm=22.0), ["/winding/r_outer_mm"], id="span-zero"),
        pytest.param(_spec(r_outer_mm=17.0), ["/winding/r_outer_mm"], id="span-negative"),
        pytest.param(_spec(r_outer_mm=NAN), ["/winding/r_outer_mm"], id="r-outer-nan"),
        pytest.param(_spec(r_outer_mm=INF), ["/winding/r_outer_mm"], id="r-outer-infinite"),
        pytest.param(_spec(fillet_radius_mm=NAN), ["/winding/fillet_radius_mm"], id="fillet-radius-nan"),
        pytest.param(_spec(fillet_radius_mm=-0.4), ["/winding/fillet_radius_mm"], id="fillet-radius-negative"),
        pytest.param(_spec(start_angle_rad=INF), ["/winding/start_angle_rad"], id="start-angle-infinite"),
        pytest.param(_spec(end_width_outer_mm=NAN), ["/winding/end_width_outer_mm"], id="end-width-outer-nan"),
        pytest.param(_spec(end_width_inner_mm=-0.4), ["/winding/end_width_inner_mm"], id="end-width-inner-negative"),
    ],
)
def test_unusable_size_is_refused_before_any_geometry(
    design: DesignParameters, pointers: list[str], registry: Registry, no_geometry: None
) -> None:
    """Catches D-030 missing for serpentine: a size that is not finite and positive, or a DRC-refused width, built."""
    result = generate_serpentine(design, registry)
    assert isinstance(result, Unbuildable)
    assert [i.code for i in result.issues] == [OUT_OF_RANGE]
    assert set(pointers) <= set(result.issues[0].pointers)


@pytest.mark.parametrize(
    ("design", "pointers"),
    [
        pytest.param(_spec(turns=0), ["/winding/turns"], id="turns-zero"),
        pytest.param(_spec(turns=-1), ["/winding/turns"], id="turns-negative"),
        pytest.param(_spec(strands=0), ["/winding/strands"], id="strands-zero"),
        pytest.param(_spec(turns=401, strands=1), ["/winding/turns", "/winding/strands"], id="traces-above-maximum"),
        pytest.param(
            _spec(turns=201, strands=2), ["/winding/turns", "/winding/strands"], id="strands-push-over-maximum"
        ),
        pytest.param(_with_poles(0), ["/rotor/poles"], id="poles-zero"),
        pytest.param(_with_poles(1), ["/rotor/poles"], id="poles-one"),
        pytest.param(_spec(layers_per_phase=0), ["/winding/layers_per_phase"], id="layers-per-phase-zero"),
    ],
)
def test_count_beyond_the_range_is_refused_before_any_geometry(
    design: DesignParameters, pointers: list[str], registry: Registry, no_geometry: None
) -> None:
    """Catches an unbounded or zero-divided build: turns x strands past Xcoil's 400, and counts below one."""
    result = generate_serpentine(design, registry)
    assert isinstance(result, Unbuildable)
    assert [i.code for i in result.issues] == [OUT_OF_RANGE]
    assert set(pointers) <= set(result.issues[0].pointers)


def test_exactly_the_maximum_trace_count_reaches_the_builder(
    monkeypatch: pytest.MonkeyPatch, registry: Registry
) -> None:
    """Catches an off-by-one in the trace bound: Xcoil allows turns x strands == 400, so the build must start."""

    class ReachedError(Exception):
        pass

    def reached(*_: object, **__: object) -> None:
        raise ReachedError

    monkeypatch.setattr(serpentine_generate, "derive", reached)
    with pytest.raises(ReachedError):
        generate_serpentine(_spec(turns=200, strands=2), registry)


def test_a_width_exactly_at_the_drc_minimum_is_not_refused(registry: Registry) -> None:
    """Catches an off-by-one in the DRC width bound: D-006 flags a width below the rule, not one equal to it."""
    at_minimum = _spec(trace_width_mm=_base().drc_rules.min_trace_width_mm)
    assert isinstance(generate_serpentine(at_minimum, registry), BoardStack)
