"""Ruling b label texts and placement (m4_review.md section 2 b, design_spec.md section 3.3)."""

import functools
import math

import pytest

from embodic.api import ComputeOutcome, compute_project
from embodic.geometry.labels import (
    MINUS,
    Box,
    LabelAnchor,
    Viewport,
    copper_spots,
    label_anchors,
    pad_boxes,
    place_labels,
)
from embodic.geometry.layout import Layout
from embodic.geometry.primitives import PrimitiveRole
from embodic.io.examples import examples_dir
from embodic.model.vocabulary import Phase

pytestmark = pytest.mark.req("REQ-N-23", "REQ-N-14")


@functools.cache
def _board(example_id: str) -> Layout:
    outcome = compute_project(examples_dir() / f"{example_id}.embodic.json")
    assert isinstance(outcome, ComputeOutcome) and outcome.boards is not None
    return outcome.boards.boards[0]


def _size(text: str) -> tuple[float, float]:
    return 6.0 * len(text), 10.0


def test_spiral_labels_name_phase_number_and_polarity_with_the_minus_sign() -> None:
    """Catches the hyphen "A2-" (half the width of "+", F22), a missing coil or numbering across phases."""
    anchors = label_anchors(_board("spiral_12c10p_d08"))
    texts = {a.text for a in anchors}
    assert len(anchors) == 12 and not any("-" in t for t in texts)
    assert {t[:2] for t in texts} == {f"{p.value}{n}" for p in Phase for n in range(1, 5)}
    assert all(t[2] in ("+", MINUS) for t in texts) and any(t.endswith(MINUS) for t in texts)


@pytest.mark.parametrize(
    ("example", "forced"),
    [
        ("spiral_12c10p_d08", {f"{p}{s}" for p in "ABC" for s in ("+", MINUS)}),
        ("wave_16p_example", {f"{p}{s}" for p in "ABC" for s in ("+", MINUS)}),
        ("serpentine_16p_example", {"A", "B", "C"}),
    ],
)
def test_ruling_h_the_forced_labels_are_the_first_of_each_phase_and_sign_and_lead_the_order(example, forced) -> None:
    """U-S4e ruling h. Catches the wave fit view where every label read "+": one forced label per phase hid A−."""
    anchors = label_anchors(_board(example))
    count = len(forced)
    assert all(a.forced for a in anchors[:count]) and not any(a.forced for a in anchors[count:]), example
    shown = {a.text if example.startswith("serpentine") else a.text[0] + a.text[-1] for a in anchors[:count]}
    assert shown == forced, example


def test_wave_labels_once_per_phase_belt_with_polarity() -> None:
    """Catches one label per conductor (the 96 overlapping labels of F5) or a belt without its polarity sign.

    A 16-pole three-phase wave has one belt per phase under each pole: 48 belts, 8 of each sign per phase.
    """
    anchors = label_anchors(_board("wave_16p_example"))
    assert len(anchors) == 16 * 3
    for phase in Phase:
        texts = [a.text for a in anchors if a.phase is phase]
        assert sorted(texts) == sorted([f"{phase.value}+"] * 8 + [f"{phase.value}{MINUS}"] * 8)


def test_serpentine_labels_each_phase_once_per_quadrant_on_its_outermost_end_turn() -> None:
    """Catches the single "A1+" of F6: phases B and C unnamed, or all four letters bunched in one quadrant."""
    board = _board("serpentine_16p_example")
    anchors = label_anchors(board)
    for phase in Phase:
        own = [a for a in anchors if a.phase is phase]
        assert [a.text for a in own] == [phase.value] * 4
        quadrants = sorted(int((math.atan2(a.y_mm, a.x_mm) % math.tau) // (math.pi / 2)) for a in own)
        assert quadrants == [0, 1, 2, 3], phase
        turns = [q for p in board.paths if p.phase is phase for q in p.primitives if q.role is PrimitiveRole.END_TURN]
        outer = max(max(math.hypot(*q.start_point()), math.hypot(*q.end_point())) for q in turns)
        assert all(math.hypot(a.x_mm, a.y_mm) > outer - 1.0 for a in own), phase


VIEW = Viewport(x_min_mm=-50, y_min_mm=-50, x_max_mm=50, y_max_mm=50, px_per_mm=1.0)


def _anchor(x: float, y: float, *, first: bool = False, text: str = "A1+", phase: Phase = Phase.A) -> LabelAnchor:
    return LabelAnchor(phase=phase, text=text, x_mm=x, y_mm=y, forced=first)


def _inside(view: Viewport, x: float, y: float) -> bool:
    return view.x_min_mm <= x <= view.x_max_mm and view.y_min_mm <= y <= view.y_max_mm


def test_a_label_closer_than_2px_to_a_placed_one_is_skipped_and_one_farther_away_places() -> None:
    """Catches overlapping labels (F5) and a gap rule that skips labels with room to spare."""
    first = _anchor(0, 20, first=True)  # box 18 x 10 px around (0, 20)
    near = _anchor(18 + 1.5, 20)  # boxes 1.5 px apart
    far = _anchor(-(18 + 2.5), 20)  # boxes 2.5 px apart
    placed = place_labels([first, near, far], view=VIEW, text_size=_size, obstacles=(), ring_outer_mm=30)
    assert [(p.x_mm, p.y_mm) for p in placed] == [(0, 20), (-20.5, 20)]


def test_a_label_meeting_a_pad_or_the_view_edge_is_skipped() -> None:
    """Catches labels drawn over a terminal pad (F6) or cut by the edge of the view."""
    pad = Box(x_min_mm=-1, y_min_mm=-1, x_max_mm=1, y_max_mm=1)
    anchors = [_anchor(0, 5), _anchor(46, 0)]  # 5 mm box half-height reaches the pad; 46 + 9 px passes the edge
    assert place_labels(anchors, view=VIEW, text_size=_size, obstacles=[pad], ring_outer_mm=30) == ()


def test_the_first_label_of_a_phase_always_places_with_a_leader_outside_the_ring() -> None:
    """Catches a phase left without its letter when its own spot is taken."""
    pad = Box(x_min_mm=9, y_min_mm=-1, x_max_mm=11, y_max_mm=1)
    (placed,) = place_labels(
        [_anchor(10, 0, first=True)], view=VIEW, text_size=_size, obstacles=[pad], ring_outer_mm=10
    )
    assert placed.leader is not None and placed.leader[0] == (10, 0)
    assert math.hypot(placed.x_mm, placed.y_mm) > 10 and abs(placed.y_mm) < 1e-9


def test_every_example_board_places_each_phase_letter_at_page_scale() -> None:
    """Catches a page placement that loses a phase: every phase letter must show in every exported drawing."""
    for example in ("spiral_12c10p_d08", "wave_16p_example", "serpentine_16p_example"):
        board = _board(example)
        r = board.envelope_mm[1]
        view = Viewport(x_min_mm=-r - 5, y_min_mm=-r - 5, x_max_mm=r + 5, y_max_mm=r + 5, px_per_mm=96 / 25.4)
        placed = place_labels(
            label_anchors(board), view=view, text_size=_size, obstacles=pad_boxes(board), ring_outer_mm=r
        )
        assert {p.phase for p in placed} == set(Phase), example


def test_ruling_h_a_forced_label_whose_leader_would_leave_the_view_sits_on_its_phase_copper_in_view() -> None:
    """U-S4e ruling h. Catches a leader drawn to a label beyond the view edge (the ring is wider than the view)."""
    pad = Box(x_min_mm=9, y_min_mm=-1, x_max_mm=11, y_max_mm=1)
    anchor = _anchor(10, 0, first=True)
    copper = {Phase.A: ((60.0, 0.0), (0.0, 30.0), (12.0, 20.0))}
    (placed,) = place_labels([anchor], view=VIEW, text_size=_size, obstacles=[pad], ring_outer_mm=45, copper=copper)
    assert (placed.x_mm, placed.y_mm, placed.leader) == (12.0, 20.0, None)
    (fallback,) = place_labels([anchor], view=VIEW, text_size=_size, obstacles=[pad], ring_outer_mm=45)
    assert _inside(VIEW, fallback.x_mm, fallback.y_mm) and fallback.leader is None


def test_ruling_h_a_forced_label_whose_anchor_is_out_of_view_moves_to_the_nearest_copper_in_view() -> None:
    """U-S4e ruling h. Catches a zoomed view in which a phase's label points at copper the user cannot see."""
    anchor = _anchor(80, 0, first=True)
    copper = {Phase.A: ((70.0, 0.0), (30.0, 5.0), (-30.0, 0.0))}
    (placed,) = place_labels([anchor], view=VIEW, text_size=_size, obstacles=(), ring_outer_mm=45, copper=copper)
    assert (placed.text, placed.x_mm, placed.y_mm, placed.leader) == ("A1+", 30.0, 5.0, None)


def test_ruling_h_every_phase_with_copper_in_view_names_itself_nearest_the_view_centre() -> None:
    """U-S4e ruling h. Catches a phase whose copper shows but whose every label anchor lies outside the view."""
    anchors = [_anchor(0, 20, first=True), _anchor(300, 0, first=True, text="B2" + MINUS, phase=Phase.B)]
    copper = {Phase.A: ((0.0, 20.0),), Phase.B: ((45.0, 45.0), (10.0, -10.0), (500.0, 0.0))}
    placed = place_labels(anchors, view=VIEW, text_size=_size, obstacles=(), ring_outer_mm=45, copper=copper)
    assert [(p.phase, p.text, p.x_mm, p.y_mm, p.leader) for p in placed] == [
        (Phase.A, "A1+", 0.0, 20.0, None),
        (Phase.B, "B2" + MINUS, 10.0, -10.0, None),
    ]


def test_copper_spots_lie_on_each_phase_top_layer_copper() -> None:
    """Catches a moved label that lands on another phase's copper or in empty board."""
    board = _board("wave_16p_example")
    spots = copper_spots(board)
    assert set(spots) == set(Phase)
    for phase, points in spots.items():
        ends = {q.start_point() for p in board.paths if p.phase is phase for q in p.primitives}
        assert points and ends & set(points), phase
