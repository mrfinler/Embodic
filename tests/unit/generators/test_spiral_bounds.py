"""D-030: the spiral generator bounds its work and refuses hostile inputs before building any geometry.

Each rejection test also checks that no turn or artwork was built. The defect is DEF-M2d2-01: trace width 0.001 mm with
clearance 0 made the generator build thousands of turns per coil, so the UT-GEN-01 fuzz test was killed by the memory
cgroup.
"""

import dataclasses
import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

import pytest
from tests.unit.generators.default_example import default_design

from embodic.errors import Unbuildable
from embodic.generators import generate_spiral
from embodic.generators.spiral import generate as generate_module
from embodic.generators.spiral.artwork import CoilArtwork
from embodic.generators.spiral.turns import MAX_TURNS_PER_LAYER, CoilFrame, LoopStop, LoopTurn, loop_turns
from embodic.geometry.details import SpiralDetail
from embodic.geometry.layout import BoardStack
from embodic.model.design import DesignParameters
from embodic.results import Registry, load_registry

OUT_OF_RANGE = "UNBUILDABLE_SPIRAL_INPUT_OUT_OF_RANGE"
TURNS_EXCEED = "UNBUILDABLE_TURNS_EXCEED_LIMIT"
WIDTH = "/winding/coil/trace_width_mm"
TURNS = "/winding/coil/turns"


@pytest.fixture(scope="module")
def registry() -> Registry:
    """Return the shipped equation registry."""
    return load_registry()


@dataclass
class GeometrySpy:
    """What the generator built: calls of the turn and artwork steps, and the size of each turn scan."""

    calls: Counter[str] = field(default_factory=Counter)
    loops_returned: list[int] = field(default_factory=list)


@pytest.fixture
def geometry_spy(monkeypatch: pytest.MonkeyPatch) -> GeometrySpy:
    """Record the two steps that build turns and artwork; the real functions still run."""
    spy = GeometrySpy()
    real_loop_turns, real_artwork = generate_module.loop_turns, generate_module.coil_artwork

    def loop_turns(frame: CoilFrame) -> tuple[tuple[LoopTurn, ...], LoopStop]:
        spy.calls["loop_turns"] += 1
        loops, stop = real_loop_turns(frame)
        spy.loops_returned.append(len(loops))
        return loops, stop

    def coil_artwork(*args: Any) -> CoilArtwork:
        spy.calls["coil_artwork"] += 1
        return real_artwork(*args)

    monkeypatch.setattr(generate_module, "loop_turns", loop_turns)
    monkeypatch.setattr(generate_module, "coil_artwork", coil_artwork)
    return spy


def _design(min_trace_width_mm: float | None = None, **coil_changes: float | int | None) -> DesignParameters:
    design = default_design()
    coil = dataclasses.replace(design.winding.coil, **coil_changes)  # type: ignore[union-attr]
    rules = design.drc_rules
    if min_trace_width_mm is not None:
        rules = dataclasses.replace(rules, min_trace_width_mm=min_trace_width_mm)
    return dataclasses.replace(design, winding=dataclasses.replace(design.winding, coil=coil), drc_rules=rules)


def _refused(result: object, code: str, pointer: str) -> Unbuildable:
    assert isinstance(result, Unbuildable)
    assert [i.code for i in result.issues] == [code]
    pointers = result.issues[0].pointers
    assert pointer in pointers and len(set(pointers)) == len(pointers)
    return result


CASES = [
    pytest.param("trace_width_mm", math.nan, WIDTH, id="width-nan"),
    pytest.param("trace_width_mm", math.inf, WIDTH, id="width-inf"),
    pytest.param("trace_width_mm", 0.0, WIDTH, id="width-zero"),
    pytest.param("trace_width_mm", -0.5, WIDTH, id="width-negative"),
    pytest.param("clearance_mm", math.nan, "/winding/coil/clearance_mm", id="clearance-nan"),
    pytest.param("clearance_mm", math.inf, "/winding/coil/clearance_mm", id="clearance-inf"),
    pytest.param("clearance_mm", 0.0, "/winding/coil/clearance_mm", id="clearance-zero"),
    pytest.param("clearance_mm", -0.2, "/winding/coil/clearance_mm", id="clearance-negative"),
    pytest.param("coil_gap_mm", math.nan, "/winding/coil/coil_gap_mm", id="gap-nan"),
    pytest.param("coil_gap_mm", math.inf, "/winding/coil/coil_gap_mm", id="gap-inf"),
    pytest.param("coil_gap_mm", -0.1, "/winding/coil/coil_gap_mm", id="gap-negative"),
    pytest.param("r_inner_mm", math.nan, "/winding/coil/r_inner_mm", id="r-inner-nan"),
    pytest.param("r_inner_mm", math.inf, "/winding/coil/r_inner_mm", id="r-inner-inf"),
    pytest.param("r_inner_mm", 0.0, "/winding/coil/r_inner_mm", id="r-inner-zero"),
    pytest.param("r_inner_mm", -1.0, "/winding/coil/r_inner_mm", id="r-inner-negative"),
    pytest.param("r_outer_mm", math.nan, "/winding/coil/r_outer_mm", id="r-outer-nan"),
    pytest.param("r_outer_mm", math.inf, "/winding/coil/r_outer_mm", id="r-outer-inf"),
    pytest.param("r_outer_mm", 18.0, "/winding/coil/r_outer_mm", id="r-outer-equals-r-inner"),
]


@pytest.mark.req("REQ-F-19")
@pytest.mark.parametrize(("field", "value", "pointer"), CASES)
def test_non_finite_or_non_positive_input_is_refused_before_any_geometry(
    field: str, value: float, pointer: str, registry: Registry, geometry_spy: GeometrySpy
) -> None:
    """A width, clearance, gap or radius that is not finite or not positive gives Unbuildable and builds nothing.

    Catches the generator walking the turn loop with a zero or NaN pitch (clearance 0 was accepted).
    """
    result = generate_spiral(_design(**{field: value}), registry)
    _refused(result, OUT_OF_RANGE, pointer)
    assert not geometry_spy.calls


@pytest.mark.req("REQ-F-19")
def test_zero_coil_gap_is_allowed_because_the_used_gap_is_max_of_gap_and_clearance(registry: Registry) -> None:
    """A zero coil gap is valid input (fields.py: non-negative); it builds the same copper as gap = clearance."""
    zero, equal = (generate_spiral(_design(coil_gap_mm=gap), registry) for gap in (0.0, 0.2))
    assert isinstance(zero, BoardStack) and isinstance(equal, BoardStack)
    assert zero.stack_hash == equal.stack_hash


@pytest.mark.req("REQ-F-05")
@pytest.mark.parametrize(
    ("trace_width_mm", "clearance_mm"),
    [pytest.param(0.14, 0.2, id="just-below-min"), pytest.param(0.001, 0.0, id="def-m2d2-01")],
)
def test_trace_width_below_the_drc_minimum_is_refused_before_any_geometry(
    trace_width_mm: float, clearance_mm: float, registry: Registry, geometry_spy: GeometrySpy
) -> None:
    """Width below DrcRules.min_trace_width_mm (0.15 in the default example) is refused, whatever the clearance.

    Catches building a coil whose own traces the DRC would flag, and the unbounded turn count of DEF-M2d2-01.
    """
    design = _design(trace_width_mm=trace_width_mm, clearance_mm=clearance_mm)
    assert design.drc_rules.min_trace_width_mm == 0.15
    _refused(generate_spiral(design, registry), OUT_OF_RANGE, WIDTH)
    assert not geometry_spy.calls


@pytest.mark.req("REQ-F-05")
def test_trace_width_equal_to_the_drc_minimum_is_built(registry: Registry) -> None:
    """D-006 has no slack band and no extra margin: a width equal to the rule builds.

    Catches a guard written with <= instead of the DRC's own comparison.
    """
    result = generate_spiral(_design(trace_width_mm=0.15), registry)
    assert isinstance(result, BoardStack)


@pytest.mark.req("REQ-F-19")
def test_requested_turns_above_the_cap_are_refused_before_the_turn_loop(
    registry: Registry, geometry_spy: GeometrySpy
) -> None:
    """A request of cap + 1 turns gives TURNS_EXCEED_LIMIT with limit = cap and does not even scan the loop rule."""
    result = generate_spiral(_design(turns=MAX_TURNS_PER_LAYER + 1), registry)
    refused = _refused(result, TURNS_EXCEED, TURNS)
    assert refused.issues[0].limit == MAX_TURNS_PER_LAYER == 100
    assert refused.issues[0].value == "user_cap"
    assert not geometry_spy.calls


@pytest.mark.req("REQ-F-19")
@pytest.mark.parametrize("requested", [None, 5])
def test_a_coil_whose_loop_rule_admits_more_than_the_cap_is_refused_before_artwork(
    requested: int | None, registry: Registry, geometry_spy: GeometrySpy
) -> None:
    """Width 0.02 mm and clearance 0.02 mm on the 20 mm span admit about 190 turns; the generator stops at the cap.

    Catches an unbounded scan: the turn loop returns exactly the cap and no artwork is built. A user request below the
    cap does not lift the refusal, because the limit shown on the feasibility rail would be a lie.
    """
    design = _design(min_trace_width_mm=0.01, trace_width_mm=0.02, clearance_mm=0.02, turns=requested)
    refused = _refused(generate_spiral(design, registry), TURNS_EXCEED, TURNS)
    assert refused.issues[0].limit == MAX_TURNS_PER_LAYER
    assert refused.issues[0].value == "loop_rule"
    assert geometry_spy.calls == {"loop_turns": 1}
    assert geometry_spy.loops_returned == [MAX_TURNS_PER_LAYER]


@pytest.mark.req("REQ-F-19", "REQ-F-14")
def test_requested_turns_above_the_turns_that_fit_are_refused_as_the_users_request(registry: Registry) -> None:
    """The default coil fits N turns (loop rule below the cap); N + 1 is refused with limit N and the cause user_cap.

    Catches a cause that follows the limit's size instead of who exceeded it: the loop rule is not what the user fixes.
    """
    built = generate_spiral(_design(), registry)
    assert isinstance(built, BoardStack)
    detail = built.boards[0].detail
    assert isinstance(detail, SpiralDetail)
    fits = detail.turns_achieved
    assert fits < MAX_TURNS_PER_LAYER
    refused = _refused(generate_spiral(_design(turns=fits + 1), registry), TURNS_EXCEED, TURNS)
    assert (refused.issues[0].limit, refused.issues[0].value) == (fits, "user_cap")


@pytest.mark.req("REQ-F-19")
def test_a_coil_with_many_turns_below_the_cap_still_builds(registry: Registry) -> None:
    """Width 0.04 mm and clearance 0.04 mm on the default radii give more than 50 turns, below the cap, and build.

    Catches a cap set too low or an off-by-one that refuses fine-pitch coils the loop rule admits.
    """
    result = generate_spiral(_design(min_trace_width_mm=0.01, trace_width_mm=0.04, clearance_mm=0.04), registry)
    assert isinstance(result, BoardStack)
    detail = result.boards[0].detail
    assert isinstance(detail, SpiralDetail)
    assert 50 < detail.turns_achieved <= MAX_TURNS_PER_LAYER


@pytest.mark.req("REQ-F-19")
def test_loop_turns_returns_at_most_the_cap_and_says_the_cap_stopped_it() -> None:
    """The loop rule alone would admit about 190 turns here; loop_turns returns the cap and LoopStop.CAP."""
    coil = dataclasses.replace(
        default_design().winding.coil,  # type: ignore[union-attr]
        trace_width_mm=0.02,
        clearance_mm=0.02,
    )
    loops, stop = loop_turns(CoilFrame.of(coil, 0.6))
    assert len(loops) == MAX_TURNS_PER_LAYER and stop is LoopStop.CAP
