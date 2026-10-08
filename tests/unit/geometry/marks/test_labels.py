"""Ruling b label texts and placement (m4_review.md section 2 b, design_spec.md section 3.3)."""

import functools
import math

import pytest

from embodic.api import ComputeOutcome, compute_project
from embodic.geometry.labels import MINUS, Box, LabelAnchor, Viewport, label_anchors, pad_boxes, place_labels
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


def test_first_label_of_each_phase_leads_the_priority_order() -> None:
    """Catches a placement order that lets coil A2 crowd out B1 before every phase has its letter."""
    for example in ("spiral_12c10p_d08", "wave_16p_example", "serpentine_16p_example"):
        anchors = label_anchors(_board(example))
        assert {a.phase for a in anchors[:3]} == set(Phase), example
        assert all(a.first_of_phase for a in anchors[:3]) and not any(a.first_of_phase for a in anchors[3:]), example


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


def _anchor(x: float, y: float, *, first: bool = False, text: str = "A1+") -> LabelAnchor:
    return LabelAnchor(phase=Phase.A, text=text, x_mm=x, y_mm=y, first_of_phase=first)


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
        [_anchor(10, 0, first=True)], view=VIEW, text_size=_size, obstacles=[pad], ring_outer_mm=30
    )
    assert placed.leader is not None and placed.leader[0] == (10, 0)
    assert math.hypot(placed.x_mm, placed.y_mm) > 30 and abs(placed.y_mm) < 1e-9


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
