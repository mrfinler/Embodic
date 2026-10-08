"""BV-01 to BV-03 and BV-06, plus the ported Xcoil normalizeParams rules; issues, never exceptions (REQ-F-14)."""

import dataclasses
import importlib.util
import math
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from embodic.errors import IssueCategory
from embodic.model.draft import DesignDraft, DraftIncomplete, draft_from_design, parse_draft
from embodic.model.layers import LayerPair
from embodic.model.stackup import generate_even_stackup
from embodic.model.validate import validate_design
from embodic.model.vocabulary import TopologyKind
from embodic.model.winding_specs import SerpentineWindingSpec, StackMode

# tests/unit is not a package, so the shared example designs are loaded by path.
_SPEC = importlib.util.spec_from_file_location("model_designs", Path(__file__).parents[1] / "model" / "designs.py")
assert _SPEC is not None and _SPEC.loader is not None
designs = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(designs)
spiral_design, serpentine_design, wave_design = designs.spiral_design, designs.serpentine_design, designs.wave_design


def _codes(design):
    return [(i.code, i.pointers) for i in validate_design(design)]


def _replace(design, path, value):
    head, *rest = path.split(".")
    inner = getattr(design, head)
    return dataclasses.replace(design, **{head: _replace(inner, ".".join(rest), value) if rest else value})


def _parse_with(design, pointer, value):
    values = {**draft_from_design(design).values, pointer: value}
    return parse_draft(DesignDraft(topology=design.topology, values=values))


@pytest.mark.req("REQ-F-14")
@pytest.mark.parametrize(
    ("value", "code"),
    [(0.0, "INVALID_NON_POSITIVE"), (-0.2, "INVALID_NON_POSITIVE"), (math.nan, "INVALID_TYPE"),
     (math.inf, "INVALID_TYPE"), ("0.5", "INVALID_TYPE"), (True, "INVALID_TYPE")],
)  # fmt: skip
def test_bv01_trace_width(value, code):
    """BV-01. Defect caught: a zero, negative, NaN or infinite trace width reaching the generator."""
    outcome = _parse_with(spiral_design(), "/winding/coil/trace_width_mm", value)
    assert isinstance(outcome, DraftIncomplete)
    assert [(i.code, i.pointers) for i in outcome.issues] == [(code, ("/winding/coil/trace_width_mm",))]


@pytest.mark.req("REQ-F-14")
@pytest.mark.parametrize("r_outer_mm", [18.0, 10.0])
def test_bv02_spiral_radius_order(r_outer_mm):
    """BV-02. Defect caught: r_outer equal to or below r_inner accepted."""
    design = _replace(spiral_design(), "winding.coil.r_outer_mm", r_outer_mm)
    assert _codes(design) == [("INVALID_ORDER", ("/winding/coil/r_inner_mm", "/winding/coil/r_outer_mm"))]


@pytest.mark.req("REQ-F-14")
@pytest.mark.parametrize(
    ("r_outer_mm", "codes"),
    [(22.0, ["INVALID_ORDER"]), (22.5, ["INVALID_RADIAL_SPAN"]), (22.500001, [])],
)
def test_bv02_xcoil_radial_span(r_outer_mm, codes):
    """Xcoil R_ORDER: rOut must exceed rIn + 0.5 mm; equality is refused like Xcoil's `!(rOut > rIn + 0.5)`."""
    for design in (serpentine_design(), wave_design()):
        changed = _replace(design, "winding.r_outer_mm", r_outer_mm)
        assert [code for code, _ in _codes(changed)] == codes


@pytest.mark.req("REQ-F-14")
def test_bv03_odd_pole_count_suggests_the_next_even_count():
    """BV-03. Defect caught: an odd pole count accepted, or the fix applied silently instead of proposed."""
    issues = validate_design(_replace(spiral_design(), "rotor.poles", 15))
    assert [(i.code, i.suggestion.proposed_value if i.suggestion else None) for i in issues] == [
        ("INVALID_POLE_COUNT_ODD", 16)
    ]


@pytest.mark.req("REQ-F-14")
def test_bv06_pair_references_unknown_copper_layer():
    """BV-06. Defect caught: a layer pair naming a layer that is not copper in the stack-up."""
    design = spiral_design()
    pairs = (LayerPair(index=0, layer_in="L1", layer_out="D1"),)
    changed = _replace(design, "winding.layers.pairs", pairs)
    assert _codes(changed) == [("INVALID_PAIR_LAYER_UNKNOWN", ("/winding/layers/pairs/0/layer_out",))]


@pytest.mark.req("REQ-F-14")
def test_xcoil_via_and_terminal_rings():
    """Xcoil VIA_RING (pad >= drill + 0.1) and PAD_RING (pad >= drill + 0.3 when drilled)."""
    design = _replace(spiral_design(), "vias.pad_mm", 0.39)
    assert [code for code, _ in _codes(design)] == ["INVALID_VIA_RING"]
    assert _codes(_replace(spiral_design(), "vias.pad_mm", 0.4)) == []
    design = _replace(spiral_design(), "connection.terminal_pad_mm", 1.4)
    assert [code for code, _ in _codes(design)] == ["INVALID_TERMINAL_PAD_RING"]
    smd = _replace(_replace(spiral_design(), "connection.terminal_drill_mm", 0.0), "connection.terminal_pad_mm", 1.4)
    assert _codes(smd) == []


def _serpentine_with_layers(layers_per_phase):
    """Return the serpentine example on a stack-up of phases x layers per phase, so only the layer rules apply."""
    design = _replace(serpentine_design(), "winding.layers_per_phase", layers_per_phase)
    stackup = generate_even_stackup(design.phases * layers_per_phase, designs.COPPER_2OZ_MM, 1.6)
    return dataclasses.replace(design, stackup=stackup)


@pytest.mark.req("REQ-F-14")
def test_xcoil_serpentine_layer_rules():
    """Xcoil LAYERS_ODD, PAIRS_GT_P and TOO_MANY for serpentine."""
    odd = _serpentine_with_layers(3)
    assert [i.code for i in validate_design(odd)] == ["INVALID_LAYERS_PER_PHASE"]
    many_pairs = _replace(_serpentine_with_layers(4), "rotor.poles", 2)
    assert [i.code for i in validate_design(many_pairs)] == ["INVALID_SERIES_PAIRS_EXCEED_POLE_PAIRS"]
    traces = _replace(_replace(serpentine_design(), "winding.turns", 200), "winding.strands", 3)
    assert [i.code for i in validate_design(traces)] == ["RANGE_TOO_MANY_TRACES"]


@pytest.mark.req("REQ-F-14", "REQ-F-34")
@pytest.mark.parametrize(
    ("phases", "layers_per_phase", "copper_count", "valid"),
    [
        (3, 2, 6, True),
        (3, 1, 3, True),
        (3, 1, 6, False),
        (3, 2, 2, False),
        (3, 2, 4, False),
        (3, 2, 12, False),
        (2, 2, 4, True),
        (2, 2, 6, False),
    ],
)
def test_single_stack_copper_count_is_phases_times_layers_per_phase(phases, layers_per_phase, copper_count, valid):
    """UT-GEN-03, D-031e, DEF-U-D4-02. Defect caught: a single-board stack-up of any size accepted.

    The single board carries every phase, so 3 phases x 1 layer per phase need 3 copper layers, not 6.
    """
    design = serpentine_design()
    assert isinstance(design.winding, SerpentineWindingSpec)
    winding = dataclasses.replace(design.winding, stack_mode=StackMode.SINGLE, layers_per_phase=layers_per_phase)
    stackup = generate_even_stackup(copper_count, designs.COPPER_2OZ_MM, 1.6)
    changed = dataclasses.replace(design, phases=phases, winding=winding, stackup=stackup)
    found = [i for i in validate_design(changed) if i.code == "INVALID_SERPENTINE_COPPER_COUNT"]
    if valid:
        assert found == []
    else:
        assert [(i.category, i.pointers, i.value, i.limit) for i in found] == [
            (
                IssueCategory.INVALID,
                ("/stackup/layers", "/winding/layers_per_phase", "/winding/stack_mode"),
                copper_count,
                phases * layers_per_phase,
            )
        ]


@pytest.mark.req("REQ-F-14")
def test_xcoil_range_is_unsupported_not_invalid_and_proposes_the_clamp():
    """Defect caught: an out-of-range value treated as invalid, or clamped silently instead of proposed."""
    issues = validate_design(_replace(wave_design(), "winding.turns", 201))
    assert [(i.code, i.category, i.suggestion.proposed_value if i.suggestion else None) for i in issues] == [
        ("RANGE_ABOVE_SUPPORTED", IssueCategory.UNSUPPORTED_RANGE, 200)
    ]
    assert issues[0].message == "The value is above the supported maximum of 200."


@pytest.mark.req("REQ-F-14")
def test_spiral_needs_three_phases_and_end_widths_at_least_the_trace():
    """spiral_generator_spec.md Inputs: 3 phases only; end-turn widths >= w."""
    two_phase = dataclasses.replace(spiral_design(), phases=2)
    assert [i.code for i in validate_design(two_phase)] == ["INVALID_SPIRAL_PHASES"]
    narrow = _replace(spiral_design(), "winding.coil.end_width_outer_mm", 0.4)
    assert [i.code for i in validate_design(narrow)] == ["INVALID_END_WIDTH_BELOW_TRACE"]


@pytest.mark.req("REQ-F-14")
def test_examples_validate_clean():
    """Defect caught: a rule that rejects the documented example designs."""
    for design in (spiral_design(), serpentine_design(), wave_design()):
        assert validate_design(design) == ()


JSON_LEAVES = st.recursive(
    st.none() | st.booleans() | st.integers() | st.floats() | st.text(max_size=5),
    lambda inner: st.lists(inner, max_size=3) | st.dictionaries(st.text(max_size=3), inner, max_size=3),
    max_leaves=6,
)


@pytest.mark.req("REQ-F-14")
@given(
    topology=st.sampled_from(list(TopologyKind)),
    edits=st.dictionaries(st.sampled_from(sorted(draft_from_design(spiral_design()).values)), JSON_LEAVES, max_size=6),
    junk=st.dictionaries(st.text(alphabet="/abc019*", max_size=12), JSON_LEAVES, max_size=3),
)
def test_parse_draft_never_raises(topology, edits, junk):
    """PR-05 style fuzz. Defect caught: user input that raises instead of returning issues."""
    base = {TopologyKind.SPIRAL: spiral_design, TopologyKind.SERPENTINE: serpentine_design}.get(topology, wave_design)
    values = {**draft_from_design(base()).values, **edits, **junk}
    outcome = parse_draft(DesignDraft(topology=topology, values=values))
    if not isinstance(outcome, DraftIncomplete):
        validate_design(outcome)
