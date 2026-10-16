"""The checks of the D-030 lower-bound property tests can fail: each defect class they name is injected and seen."""

import dataclasses
import math
from types import SimpleNamespace

import pytest
from hypothesis import given, settings
from tests.unit.generators import hostile_sizes as helper
from tests.unit.generators.default_example import default_design
from tests.unit.generators.hostile_sizes import Sizes, assert_all_finite, check_hostile_build, timed_build

from embodic.errors import Unbuildable
from embodic.generators import generate_spiral
from embodic.geometry.layout import BoardStack, Via
from embodic.geometry.primitives import Arc, Line
from embodic.model.winding_specs import SpiralWindingSpec
from embodic.results import load_registry

pytestmark = pytest.mark.req("REQ-F-19")


@pytest.fixture(scope="module")
def stack() -> BoardStack:
    """Return the default spiral stack: lines and arcs, vias, 64 paths."""
    result = generate_spiral(default_design(), load_registry())
    assert isinstance(result, BoardStack)
    return result


def _first(stack: BoardStack, kind: type[Line | Arc]) -> Line | Arc:
    return next(p for path in stack.boards[0].paths for p in path.primitives if isinstance(p, kind))


def _plain_stack(primitives: tuple[Line | Arc, ...], vias: tuple[Via, ...]) -> BoardStack:
    """Plain containers around real primitives and vias: a Layout refuses a NaN when it hashes, so none can be built."""
    path = SimpleNamespace(id=0, primitives=primitives)
    return SimpleNamespace(boards=(SimpleNamespace(paths=(path,), vias=vias),))  # type: ignore[return-value]


def _check(hostile: BoardStack | Unbuildable, baseline: BoardStack | Unbuildable, *, deadline: bool = True) -> str:
    return check_hostile_build(lambda: hostile, lambda: baseline, lambda _: None, deadline=deadline)


@pytest.mark.parametrize(
    ("kind", "change"),
    [(Line, {"x1_mm": math.nan}), (Arc, {"sweep_rad": math.inf}), (Arc, {"width_mm": -math.inf})],
    ids=["line-nan", "arc-inf", "arc-width"],
)
def test_a_non_finite_primitive_field_is_seen(
    stack: BoardStack, kind: type[Line | Arc], change: dict[str, float]
) -> None:
    """Defect caught: a NaN or inf in a primitive, which the DRC and the exporters would then read."""
    via = stack.boards[0].vias[0]
    assert_all_finite(_plain_stack((_first(stack, Line), _first(stack, Arc)), (via,)))
    with pytest.raises(AssertionError, match=r"is (nan|inf|-inf)"):
        assert_all_finite(_plain_stack((dataclasses.replace(_first(stack, kind), **change),), (via,)))


@pytest.mark.parametrize("change", [{"pad_mm": math.nan}, {"x_mm": -math.inf}, {"y_mm": math.inf}])
def test_a_non_finite_via_field_is_seen(stack: BoardStack, change: dict[str, float]) -> None:
    """Defect caught: a via position or pad that is not finite."""
    via = dataclasses.replace(stack.boards[0].vias[0], **change)
    with pytest.raises(AssertionError, match=r"is (nan|inf|-inf)"):
        assert_all_finite(_plain_stack((_first(stack, Line),), (via,)))


def test_more_paths_than_the_default_build_is_seen(stack: BoardStack) -> None:
    """Defect caught: a count derived from 1/clearance or 1/pad that creates paths a default build does not."""
    board = stack.boards[0]
    fewer = dataclasses.replace(stack, boards=(dataclasses.replace(board, paths=board.paths[:-1]),))
    _check(fewer, stack)
    with pytest.raises(AssertionError):
        _check(stack, fewer)


def test_an_unbuildable_baseline_leaves_the_path_count_unchecked(stack: BoardStack) -> None:
    """The spec does not define property 4 without a baseline build; the example is then judged on 1 to 3 and 5."""
    design = default_design()
    assert isinstance(design.winding, SpiralWindingSpec)
    coil = dataclasses.replace(design.winding.coil, trace_width_mm=0.0)
    refused = generate_spiral(
        dataclasses.replace(design, winding=dataclasses.replace(design.winding, coil=coil)), load_registry()
    )
    assert isinstance(refused, Unbuildable)
    assert _check(stack, refused) == "no baseline"
    assert _check(stack, stack) == "compared"
    assert _check(refused, stack) == "unbuildable"


def test_a_build_over_the_deadline_is_seen(monkeypatch: pytest.MonkeyPatch, stack: BoardStack) -> None:
    """Defect caught: a build that grows with 1/size and only fails when the memory cgroup kills it (D-030)."""
    _check(stack, stack)
    monkeypatch.setattr(helper, "BUILD_DEADLINE_S", -1.0)
    with pytest.raises(AssertionError, match="deadline"):
        _check(stack, stack)
    with pytest.raises(AssertionError, match="deadline"):
        timed_build(lambda: stack)
    assert _check(stack, stack, deadline=False) == "compared"


RULES = default_design().drc_rules
EXAMPLE = Sizes(clearance_mm=0.2, pad_mm=0.6, terminal_pad_mm=2.4)


@settings(max_examples=100, deadline=None)
@given(sizes=helper.hostile_sizes(RULES, EXAMPLE, terminal_pad=True))
def test_hostile_sizes_stay_positive_and_below_the_rules_and_the_rest_keep_the_example(sizes: Sizes) -> None:
    """Defect caught: a generator range that draws 0, a value above the rule, or changes an input meant to stay put."""
    pad_limit_mm = RULES.min_drill_mm + 2 * RULES.min_annular_ring_mm
    for value, example, limit in (
        (sizes.clearance_mm, EXAMPLE.clearance_mm, RULES.trace_clearance_mm),
        (sizes.pad_mm, EXAMPLE.pad_mm, pad_limit_mm),
        (sizes.terminal_pad_mm, EXAMPLE.terminal_pad_mm, pad_limit_mm),
    ):
        assert value == example or 0.0 < value <= limit


@settings(max_examples=100, deadline=None)
@given(sizes=helper.hostile_sizes(RULES, EXAMPLE, terminal_pad=False))
def test_a_topology_without_a_terminal_pad_never_varies_it(sizes: Sizes) -> None:
    """Defect caught: the spiral test varying an input its generator does not read, so an example would test nothing."""
    assert sizes.terminal_pad_mm == EXAMPLE.terminal_pad_mm
