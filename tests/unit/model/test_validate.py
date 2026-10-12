"""Cross-field rules added in the U-M2a fix round: R12 coil gap hint, UT-GEN-03 serpentine stack mode."""

import dataclasses

import pytest

from embodic.errors import IssueCategory, Severity
from embodic.model.design import DesignParameters
from embodic.model.draft import DesignDraft, DraftIncomplete, draft_from_design, parse_draft
from embodic.model.stackup import generate_even_stackup
from embodic.model.validate import validate_design
from embodic.model.vocabulary import TopologyKind
from embodic.model.winding_specs import SerpentineWindingSpec, SpiralWindingSpec, StackMode

from .designs import COPPER_2OZ_MM, serpentine_design, spiral_design, wave_design


def _with_coil_gap(gap_mm: float) -> DesignParameters:
    design = spiral_design()
    assert isinstance(design.winding, SpiralWindingSpec)
    coil = dataclasses.replace(design.winding.coil, coil_gap_mm=gap_mm)
    return dataclasses.replace(design, winding=dataclasses.replace(design.winding, coil=coil))


def _with_harmonics(harmonics: tuple[int, ...]) -> DesignParameters:
    design = spiral_design()
    return dataclasses.replace(design, analysis=dataclasses.replace(design.analysis, harmonics=harmonics))


@pytest.mark.req("REQ-F-14")
@pytest.mark.parametrize("harmonics", [(), (3, 5), (3, 1)])
def test_a_harmonic_list_that_does_not_start_with_the_fundamental_is_an_error(harmonics):
    """interfaces.md: harmonic 1 is index 0. Defect caught: () and (3, 5) crashed physics, (3, 1) gave Ke of n = 3."""
    found = [(i.code, i.severity, i.pointers) for i in validate_design(_with_harmonics(harmonics))]
    assert found == [("INVALID_HARMONIC_FUNDAMENTAL", Severity.ERROR, ("/analysis/harmonics",))]


@pytest.mark.req("REQ-F-14")
@pytest.mark.parametrize("harmonics", [(1,), (1, 3, 5, 7, 9, 11, 13)])
def test_a_harmonic_list_that_starts_with_the_fundamental_is_accepted(harmonics):
    """Defect caught: the fundamental rule refusing a valid list, such as the fundamental alone."""
    assert validate_design(_with_harmonics(harmonics)) == ()


@pytest.mark.req("REQ-F-14")
def test_coil_gap_below_trace_spacing_is_an_info_hint_proposing_the_spacing():
    """R12. Defect caught: a gap below s rejected as an error, or reported without the spacing as Suggestion."""
    found = [i for i in validate_design(_with_coil_gap(0.1)) if i.code == "RANGE_COIL_GAP_BELOW_CLEARANCE"]
    assert len(found) == 1
    hint = found[0]
    assert hint.severity is Severity.INFO
    assert hint.category is IssueCategory.UNSUPPORTED_RANGE
    assert hint.pointers == ("/winding/coil/coil_gap_mm", "/winding/coil/clearance_mm")
    assert hint.suggestion is not None
    assert (hint.suggestion.pointer, hint.suggestion.proposed_value) == ("/winding/coil/coil_gap_mm", 0.2)
    assert "0.2 mm" in hint.message


@pytest.mark.req("REQ-F-14")
@pytest.mark.parametrize("gap_mm", [0.2, 0.5])
def test_coil_gap_at_or_above_trace_spacing_gives_no_hint(gap_mm):
    """R12. Defect caught: the hint shown when the generator uses the gap as entered."""
    codes = [i.code for i in validate_design(_with_coil_gap(gap_mm))]
    assert "RANGE_COIL_GAP_BELOW_CLEARANCE" not in codes


def _serpentine(mode: StackMode, copper_count: int) -> DesignParameters:
    design = serpentine_design()
    assert isinstance(design.winding, SerpentineWindingSpec)
    winding = dataclasses.replace(design.winding, stack_mode=mode)
    stackup = generate_even_stackup(copper_count, COPPER_2OZ_MM, 1.6)
    return dataclasses.replace(design, winding=winding, stackup=stackup)


@pytest.mark.req("REQ-F-34")
@pytest.mark.parametrize(
    ("mode", "copper_count", "valid"),
    [
        (StackMode.SINGLE, 6, True),
        (StackMode.ONE_BOARD_PER_PHASE, 2, True),
        (StackMode.ONE_BOARD_PER_PHASE, 6, False),
    ],
)
def test_serpentine_copper_count_follows_the_stack_mode(mode, copper_count, valid):
    """UT-GEN-03 (interfaces.md 2.2). Defect caught: a one-board-per-phase stack-up checked as the whole stator.

    3 phases x 2 layers per phase: the single board has 6 copper layers, each board of one per phase has 2.
    """
    found = [i for i in validate_design(_serpentine(mode, copper_count)) if i.code == "INVALID_SERPENTINE_COPPER_COUNT"]
    if valid:
        assert found == []
    else:
        assert len(found) == 1
        assert found[0].category is IssueCategory.INVALID
        assert found[0].pointers == ("/stackup/layers", "/winding/layers_per_phase", "/winding/stack_mode")
        assert found[0].value == copper_count


@pytest.mark.req("REQ-F-34")
@pytest.mark.parametrize(
    ("gap_mm", "code"), [(-0.1, "INVALID_NEGATIVE"), (0.0, None), (10.0, None), (10.5, "RANGE_ABOVE_SUPPORTED")]
)
def test_board_gap_follows_the_xcoil_clamp_range(gap_mm, code):
    """UT-GEN-03. Defect caught: a negative gap accepted, or a gap above Xcoil's 10 mm clamp not flagged."""
    design = _serpentine(StackMode.ONE_BOARD_PER_PHASE, 2)
    assert isinstance(design.winding, SerpentineWindingSpec)
    design = dataclasses.replace(design, winding=dataclasses.replace(design.winding, board_gap_mm=gap_mm))
    codes = [i.code for i in validate_design(design) if i.pointers == ("/winding/board_gap_mm",)]
    assert codes == ([] if code is None else [code])


@pytest.mark.req("REQ-F-34", "REQ-F-37")
def test_one_board_per_phase_design_round_trips_through_the_draft():
    """D-016. Defect caught: stack_mode or board_gap_mm lost or retyped between design and draft."""
    design = _serpentine(StackMode.ONE_BOARD_PER_PHASE, 2)
    assert isinstance(design.winding, SerpentineWindingSpec)
    design = dataclasses.replace(design, winding=dataclasses.replace(design.winding, board_gap_mm=0.25))
    draft = draft_from_design(design)
    assert draft.values["/winding/stack_mode"] == "one_board_per_phase"
    assert draft.values["/winding/board_gap_mm"] == 0.25
    assert parse_draft(draft) == design


@pytest.mark.req("REQ-F-34", "REQ-F-36")
def test_blank_serpentine_draft_starts_on_one_board_with_xcoil_gap():
    """D-016, D-019. Defect caught: new fields required in a blank draft, or defaults that change today's layout."""
    values = dict(draft_from_design(serpentine_design()).values)
    assert (values["/winding/stack_mode"], values["/winding/board_gap_mm"]) == ("single", 0.1)
    del values["/winding/stack_mode"], values["/winding/board_gap_mm"]
    outcome = parse_draft(DesignDraft(topology=TopologyKind.SERPENTINE, values=values))
    assert not isinstance(outcome, DraftIncomplete)
    assert outcome == serpentine_design()


@pytest.mark.req("REQ-F-35")
@pytest.mark.parametrize(
    ("copper_count", "valid"),
    [(2, True), (4, True), (16, True), (1, False), (3, False), (5, False), (18, False)],
)
def test_wave_copper_count_is_even_from_two_to_sixteen(copper_count, valid):
    """UT-GEN-04, D-035 e. Defect caught: a wave stack-up of odd size or beyond Xcoil's 16 layers passing validation.

    The wave winding pairs a T layer with a B layer (Xcoil LAYERS_ODD, num('waveLayers', 2, 16)).
    """
    design = dataclasses.replace(wave_design(), stackup=generate_even_stackup(copper_count, COPPER_2OZ_MM, 1.6))
    found = [i for i in validate_design(design) if i.code == "INVALID_WAVE_COPPER_COUNT"]
    if valid:
        assert found == []
    else:
        assert [(i.category, i.severity, i.pointers, i.value, i.limit) for i in found] == [
            (IssueCategory.INVALID, Severity.ERROR, ("/stackup/layers",), copper_count, 16)
        ]


@pytest.mark.req("REQ-F-35")
def test_wave_copper_count_rule_leaves_the_other_topologies_alone():
    """Defect caught: the wave rule applied to a serpentine or spiral stack-up of an odd size."""
    for design in (serpentine_design(), spiral_design()):
        odd = dataclasses.replace(design, stackup=generate_even_stackup(3, COPPER_2OZ_MM, 1.6))
        assert "INVALID_WAVE_COPPER_COUNT" not in [i.code for i in validate_design(odd)]
