"""Inspector helpers of the session view-model: layer pairs, rotation mode, screw patterns, phase assignment. Qt-free.

screens.md sections 3 to 5, D-024, D-032b, UI-19.
"""

import dataclasses
import math

import pytest

from embodic.api import compute
from embodic.io.examples import load_example
from embodic.io.project import ProjectFile, project_provenance
from embodic.model.draft import DraftIncomplete, parse_draft
from embodic.model.vocabulary import TopologyKind
from embodic.ui.viewmodels.outcome import ready_state
from embodic.ui.viewmodels.session import (
    SessionComputed,
    assignment_mode,
    feasibility_hints,
    layer_pairs,
    rotation_mode,
    screw_patterns,
)

D08 = "spiral_12c10p_d08"
PAIRS = "/winding/layers/pairs"


def spiral_with_copper(session, copper_count):
    """Open a blank spiral with 12 coils and a generated stack-up of `copper_count` copper layers."""
    session.new_design(TopologyKind.SPIRAL)
    session.edit("/winding/coil/coil_count", 12)
    session.set_stackup_input("copper_oz", 1.0)
    session.set_stackup_input("board_thickness_mm", 1.6)
    session.set_stackup_input("copper_count", copper_count)


def rotations(session):
    """Return the rotation of every listed pair."""
    return [pair.rotation_rad for pair in layer_pairs(session.document.draft.values)]


@pytest.mark.req("REQ-F-23")
def test_a_copper_count_change_names_the_pairs_it_added_or_removed_and_undo_restores_both(session):
    """Catches a silent pair change, a notice naming the wrong pair, or an Undo that keeps the copper count."""
    spiral_with_copper(session, 2)
    assert session.pairs_notice.value == "Layer pairs: 1. Pair 1 added with the default rotation."
    session.set_stackup_input("copper_count", 6)
    assert session.pairs_notice.value == "Layer pairs: 3. Pairs 2 and 3 added with the default rotation."
    session.set_stackup_input("copper_count", 4)
    assert session.pairs_notice.value == "Layer pairs: 2. Pair 3 removed: the stack-up has 4 copper layers."
    session.undo()
    assert session.pairs_notice.value is None
    assert (session.stackup_inputs().copper_count, len(layer_pairs(session.document.draft.values))) == (6, 3)
    session.edit("/winding/coil/coil_count", 9)
    assert session.pairs_notice.value is None


@pytest.mark.req("REQ-F-32")
def test_rotation_mode_writes_every_pair_in_one_edit_and_reads_back_from_the_rotations(session):
    """Catches Alternate on the wrong pairs or step (pi/Q), a mode one undo does not revert, or a stale mode read."""
    spiral_with_copper(session, 6)
    assert rotation_mode(session.document.draft.values) == "none"
    session.set_rotation_mode("alternate")
    assert rotations(session) == [0.0, math.pi / 12, 0.0]
    assert rotation_mode(session.document.draft.values) == "alternate"
    session.edit(f"{PAIRS}/2/rotation_rad", 0.1)
    assert rotation_mode(session.document.draft.values) == "custom"
    session.set_rotation_mode("none")
    assert rotations(session) == [0.0, 0.0, 0.0]
    session.undo()
    assert rotations(session) == [0.0, math.pi / 12, 0.1]


@pytest.mark.req("REQ-F-24")
def test_a_new_screw_pattern_starts_with_its_required_values_missing_and_removal_closes_the_gap(session):
    """Catches a new pattern with invented values (D-031a), or a removal that leaves a gap in the indices."""
    session.load_example(D08)
    session.add_screw_pattern()
    missing = parse_draft(session.document.draft)
    assert isinstance(missing, DraftIncomplete)
    assert missing.missing == tuple(
        f"/outline/screws/0/{leaf}" for leaf in ("size", "fit", "count", "pitch_radius_mm", "hole_diameter_mm")
    )
    for leaf, value in (("size", "M3"), ("fit", "normal"), ("count", 4), ("pitch_radius_mm", 60.0)):
        session.edit(f"/outline/screws/0/{leaf}", value)
    session.edit("/outline/screws/0/hole_diameter_mm", 3.4)
    session.add_screw_pattern()
    session.edit("/outline/screws/1/size", "M2")
    session.remove_screw_pattern(0)
    assert screw_patterns(session.document.draft.values) == [{"angle_offset_rad": 0.0, "size": "M2"}]
    session.remove_screw_pattern(0)
    assert isinstance(session.state.value, SessionComputed)


@pytest.mark.req("REQ-F-28")
def test_manual_assignment_starts_from_the_computed_pattern_and_auto_writes_null(session, outcome_vm):
    """Catches a manual list that does not start from the auto pattern, or an Auto that leaves the list behind."""
    ref, design = load_example(D08)
    session.load_example(D08)
    assert session.phase_assignment() == ()
    outcome = compute(design, project_provenance(ProjectFile(design=design, origin=ref)))
    outcome_vm.state.set(ready_state(outcome))
    auto = session.phase_assignment()
    pattern = "".join(row.phase if row.polarity == 1 else row.phase.lower() for row in auto)
    assert pattern == outcome.boards.boards[0].detail.plan.pattern
    session.set_assignment_mode("manual")
    assert assignment_mode(session.document.draft.values) == "manual"
    assert session.phase_assignment() == auto
    session.set_assignment_mode("auto")
    assert session.document.draft.values["/winding/assignment"] is None


@pytest.mark.req("REQ-F-28")
def test_phase_balance_status_follows_the_engine_and_names_balanced_coil_counts():
    """Catches no status for an unbalanced winding (the build refuses it), or suggested counts the engine rejects."""
    ref, design = load_example(D08)
    provenance = project_provenance(ProjectFile(design=design, origin=ref))
    assert feasibility_hints(compute(design, provenance))["phase-balance-status"] == "Symmetric 3-phase pattern."
    coil = dataclasses.replace(design.winding.coil, coil_count=11)
    unbalanced = dataclasses.replace(design, winding=dataclasses.replace(design.winding, coil=coil))
    hints = feasibility_hints(compute(unbalanced, project_provenance(ProjectFile(design=unbalanced, origin=None))))
    # 10 poles: 3, 6, 9, 12, 15...
    assert hints["phase-balance-status"] == "No symmetric 3-phase pattern: choose 9, 12 or 15 coils."


# Ruling c (m4_review.md): `param-bore` is the shape control; each bore pointer has its own input.
BORE_WIDGETS = {
    "/outline/bore": "param-bore",
    "/outline/bore/shape": "param-bore",
    "/outline/bore/radius_mm#circle": "param-bore-radius",
    "/outline/bore/sides#polygon": "param-bore-sides",
    "/outline/bore/across_flats_mm#polygon": "param-bore-across-flats",
    "/outline/bore/corner_radius_mm#polygon": "param-bore-corner-radius",
    "/outline/bore/rotation_rad#polygon": "param-bore-rotation",
}


@pytest.mark.req("REQ-F-32")
def test_ruling_c_each_bore_pointer_names_its_own_widget_in_the_field_table():
    """Catches every bore pointer sharing `param-bore`, so Go to first missing field focuses the shape, not the gap."""
    from embodic.model.fields import FIELD_BY_KEY

    assert {key: FIELD_BY_KEY[key].widget_id for key in BORE_WIDGETS} == BORE_WIDGETS
