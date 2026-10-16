"""Shared pieces of the D-030 lower-bound property tests (docs/phase3/engineering/d030_property_spec.md).

Each generator's test draws a positive clearance, via pad or terminal pad below the DRC rules, keeps the trace width
valid, and builds. The properties are the same for every topology, so they live here; the topology modules own the
design wiring and their own ``_check_contract``.
"""

import dataclasses
import math
import numbers
import time
from collections.abc import Callable
from dataclasses import dataclass

from hypothesis import settings
from hypothesis import strategies as st

from embodic.errors import Unbuildable
from embodic.geometry.layout import BoardStack
from embodic.model.drc_rules import DrcRules

BUILD_DEADLINE_S = 10.0
HOSTILE_SETTINGS = settings(max_examples=200, deadline=None)  # the build is timed in check_hostile_build, see there
WIDTHS = ("rule_minimum", "example")


@dataclass(frozen=True, slots=True, kw_only=True)
class Sizes:
    """The three sizes the property varies, in mm. A topology without a terminal pad ignores ``terminal_pad_mm``."""

    clearance_mm: float
    pad_mm: float
    terminal_pad_mm: float


@st.composite
def hostile_sizes(draw: st.DrawFn, rules: DrcRules, example: Sizes, *, terminal_pad: bool) -> Sizes:
    """Draw one hostile size, or all three, below the DRC rules; the others keep their example value."""
    pad_limit_mm = rules.min_drill_mm + 2 * rules.min_annular_ring_mm

    def below(limit_mm: float) -> float:
        return draw(st.floats(min_value=0.0, max_value=limit_mm, exclude_min=True, allow_subnormal=True))

    drawn = Sizes(
        clearance_mm=below(rules.trace_clearance_mm), pad_mm=below(pad_limit_mm), terminal_pad_mm=below(pad_limit_mm)
    )
    hostile = draw(
        st.sampled_from(["clearance", "pad", "terminal_pad", "all"] if terminal_pad else ["clearance", "pad", "all"])
    )
    varied = {"clearance", "pad", "terminal_pad"} if hostile == "all" else {hostile}
    if not terminal_pad:
        varied.discard("terminal_pad")
    return Sizes(
        clearance_mm=drawn.clearance_mm if "clearance" in varied else example.clearance_mm,
        pad_mm=drawn.pad_mm if "pad" in varied else example.pad_mm,
        terminal_pad_mm=drawn.terminal_pad_mm if "terminal_pad" in varied else example.terminal_pad_mm,
    )  # fmt: skip


def assert_all_finite(stack: BoardStack) -> None:
    """Every float field of every primitive, and x, y and pad of every via, is finite."""
    for board in stack.boards:
        for path in board.paths:
            for primitive in path.primitives:
                for field in dataclasses.fields(primitive):
                    value = getattr(primitive, field.name)
                    if isinstance(value, numbers.Real):
                        assert math.isfinite(value), (
                            f"path {path.id} {type(primitive).__name__}.{field.name} is {value}"
                        )
        for via in board.vias:
            for name in ("x_mm", "y_mm", "pad_mm"):
                assert math.isfinite(getattr(via, name)), f"via {via.id} {name} is {getattr(via, name)}"


def path_count(stack: BoardStack) -> int:
    """Return the number of copper paths over all boards."""
    return sum(len(board.paths) for board in stack.boards)


def check_hostile_build(
    build_hostile: Callable[[], BoardStack | Unbuildable],
    build_baseline: Callable[[], BoardStack | Unbuildable],
    contract: Callable[[BoardStack | Unbuildable], None],
) -> str:
    """Properties 1 to 5 of the spec for one example; ``build_baseline`` builds the same design at the default sizes.

    Returns how far the example got, for ``hypothesis.event``: "unbuildable", "no baseline" or "compared".

    The 10 s of property 5 applies to the hostile build alone. Hypothesis' own deadline would also count the baseline
    build, so the tests turn it off and this function times the hostile build.

    When the baseline is Unbuildable there is no path count to compare with, and property 4 is not evaluated for the
    example. The spec does not define that case.
    """
    started = time.perf_counter()
    result = build_hostile()
    seconds = time.perf_counter() - started
    assert seconds <= BUILD_DEADLINE_S, f"hostile build took {seconds:.1f} s, deadline {BUILD_DEADLINE_S} s"
    contract(result)
    if isinstance(result, Unbuildable):
        return "unbuildable"
    assert_all_finite(result)
    baseline = build_baseline()
    if isinstance(baseline, Unbuildable):
        return "no baseline"
    assert path_count(result) <= path_count(baseline), (path_count(result), path_count(baseline))
    return "compared"
