"""D-024: a blank spiral draft derives its layer pairs from the copper layers of its stack-up."""

import dataclasses
import math

import pytest

from embodic.errors import IssueCategory, Severity
from embodic.model.design import DesignParameters
from embodic.model.draft import DesignDraft, blank_draft, derive_layer_pairs, draft_from_design, parse_draft
from embodic.model.provenance import DefaultValue, UserValue, derive_provenance
from embodic.model.schema import design_values
from embodic.model.stackup import generate_even_stackup
from embodic.model.validate import validate_design
from embodic.model.vocabulary import TopologyKind

from .designs import COPPER_2OZ_MM, serpentine_design, spiral_design

PAIRS = "/winding/layers/pairs"
GROUPS = "/winding/layers/series_groups"


def _stackup_values(copper_count: int) -> dict[str, object]:
    stackup = generate_even_stackup(copper_count, COPPER_2OZ_MM, 1.6)
    design = dataclasses.replace(spiral_design(), stackup=stackup)
    return {p: v for p, v in design_values(design).items() if p.startswith("/stackup/")}


def _with_copper(draft: DesignDraft, copper_count: int) -> DesignDraft:
    """Write a new /stackup/layers as the stack-up generator does (screens.md R3), the rest untouched."""
    kept = {p: v for p, v in draft.values.items() if not p.startswith("/stackup/")}
    return dataclasses.replace(draft, values={**kept, **_stackup_values(copper_count)})


def _pair_values(draft: DesignDraft) -> dict[str, object]:
    return {p: v for p, v in draft.values.items() if p.startswith(PAIRS) or p == GROUPS}


def _blank_spiral(copper_count: int) -> DesignDraft:
    return derive_layer_pairs(_with_copper(blank_draft(TopologyKind.SPIRAL), copper_count))


@pytest.mark.req("REQ-F-03")
def test_layer_pairs_one_pair_per_two_copper_layers_in_stack_order_all_in_series():
    """Defect caught: a blank spiral draft left with an empty pair list (D-024), wrong pair count or layer order."""
    assert _pair_values(_blank_spiral(4)) == {
        f"{PAIRS}/0/index": 0,
        f"{PAIRS}/0/layer_in": "L1",
        f"{PAIRS}/0/layer_out": "L2",
        f"{PAIRS}/0/rotation_rad": 0.0,
        f"{PAIRS}/0/phases": None,
        f"{PAIRS}/1/index": 1,
        f"{PAIRS}/1/layer_in": "L3",
        f"{PAIRS}/1/layer_out": "L4",
        f"{PAIRS}/1/rotation_rad": 0.0,
        f"{PAIRS}/1/phases": None,
        GROUPS: [[0], [1]],
    }
    assert len([p for p in _blank_spiral(8).values if p.endswith("/layer_in")]) == 4


@pytest.mark.req("REQ-F-36")
def test_layer_pairs_derived_rotation_has_default_provenance_until_the_user_changes_it():
    """Defect caught: derived rotation not at its documented default, so the form shows `user` instead of `default`."""
    full = draft_from_design(spiral_design()).values
    rest = {p: v for p, v in full.items() if not p.startswith("/winding/layers/")}
    draft = derive_layer_pairs(_with_copper(DesignDraft(topology=TopologyKind.SPIRAL, values=rest), 4))
    design = parse_draft(draft)
    assert isinstance(design, DesignParameters)
    provenance = derive_provenance(design, None, [])
    assert provenance[f"{PAIRS}/0/rotation_rad"] == DefaultValue()
    assert provenance[f"{PAIRS}/1/rotation_rad"] == DefaultValue()
    edited = parse_draft(dataclasses.replace(draft, values={**draft.values, f"{PAIRS}/1/rotation_rad": math.pi / 12}))
    assert isinstance(edited, DesignParameters)
    assert derive_provenance(edited, None, [])[f"{PAIRS}/1/rotation_rad"] == UserValue()


@pytest.mark.req("REQ-F-03")
def test_layer_pairs_user_edits_survive_a_layer_count_change_while_the_pair_exists():
    """Defect caught: a layer-count change resets the rotation, phase set or series grouping the user chose."""
    draft = _blank_spiral(4)
    edits = {f"{PAIRS}/1/rotation_rad": math.pi / 12, f"{PAIRS}/0/phases": ["A"], GROUPS: [[0, 1]]}
    edited = dataclasses.replace(draft, values={**draft.values, **edits})
    grown = _pair_values(derive_layer_pairs(_with_copper(edited, 6)))
    assert grown[f"{PAIRS}/1/rotation_rad"] == math.pi / 12
    assert grown[f"{PAIRS}/0/phases"] == ["A"]
    assert (grown[f"{PAIRS}/2/layer_in"], grown[f"{PAIRS}/2/layer_out"]) == ("L5", "L6")
    assert grown[f"{PAIRS}/2/rotation_rad"] == 0.0
    assert grown[GROUPS] == [[0, 1], [2]]


@pytest.mark.req("REQ-F-03")
def test_layer_pairs_removed_when_the_copper_count_shrinks():
    """Defect caught: pairs left pointing at copper layers that no longer exist, or their index kept in a group."""
    draft = _blank_spiral(6)
    edited = dataclasses.replace(draft, values={**draft.values, GROUPS: [[0, 2], [1]]})
    shrunk = _pair_values(derive_layer_pairs(_with_copper(edited, 2)))
    assert sorted({p.split("/")[4] for p in shrunk if p.startswith(f"{PAIRS}/")}) == ["0"]
    assert shrunk[GROUPS] == [[0]]
    assert _pair_values(derive_layer_pairs(_with_copper(draft, 1))) == {}


@pytest.mark.req("REQ-F-03")
def test_layer_pairs_odd_copper_count_derives_floor_half_and_warns():
    """Defect caught: an odd count rounded up to a pair with a missing layer, or accepted without telling the user."""
    pairs = _pair_values(_blank_spiral(3))
    assert sorted(p for p in pairs if p.endswith(("/layer_in", "/layer_out"))) == [
        f"{PAIRS}/0/layer_in",
        f"{PAIRS}/0/layer_out",
    ]
    odd = dataclasses.replace(spiral_design(), stackup=generate_even_stackup(3, COPPER_2OZ_MM, 1.6))
    found = [i for i in validate_design(odd) if i.code == "RANGE_SPIRAL_COPPER_COUNT_ODD"]
    assert len(found) == 1
    assert (found[0].category, found[0].severity, found[0].value) == (
        IssueCategory.UNSUPPORTED_RANGE,
        Severity.WARNING,
        3,
    )
    assert found[0].pointers == ("/stackup/layers",)
    assert not [i for i in validate_design(spiral_design()) if i.code == "RANGE_SPIRAL_COPPER_COUNT_ODD"]


@pytest.mark.req("REQ-F-03")
def test_layer_pairs_not_derived_for_other_topologies():
    """Defect caught: spiral pair pointers written into a serpentine draft, where they mean nothing."""
    draft = draft_from_design(serpentine_design())
    assert derive_layer_pairs(_with_copper(draft, 4)) == _with_copper(draft, 4)
