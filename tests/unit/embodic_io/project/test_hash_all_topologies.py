"""F15-1 (V3-01 union ruling): design hash and save bytes are exact on serpentine and wave, not only on spiral.

Catches a serpentine or wave field missing from the canonical JSON, so two different designs share a hash.
"""

import copy
import dataclasses
import enum
import functools
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from tests.unit.property.serpentine.strategies import serpentine_designs

from embodic.io.canonical import design_hash
from embodic.io.examples import list_examples, load_example
from embodic.io.project import ProjectFile, load_project, save_project
from embodic.model.design import DesignParameters
from embodic.model.winding_specs import CornerStyle, SerpentineWindingSpec, WaveStyle, WaveWindingSpec

SERPENTINE, WAVE = "serpentine_16p_example", "wave_16p_example"
EXAMPLE_IDS = [info.example_id for info in list_examples()]
STAMP = "2026-10-08T12:00:00Z"


@functools.cache
def _wave_example() -> DesignParameters:
    return load_example(WAVE)[1]


@st.composite
def wave_designs(draw: st.DrawFn) -> DesignParameters:
    """Draw a wave design: the packaged example with its turns, widths, styles and fillet changed."""
    base = _wave_example()
    assert isinstance(base.winding, WaveWindingSpec)
    winding = dataclasses.replace(
        base.winding,
        turns=draw(st.integers(1, 5)),
        trace_width_mm=draw(st.sampled_from([0.2, 0.3, 0.5])),
        clearance_mm=draw(st.sampled_from([0.15, 0.2, 0.3])),
        corner_style=draw(st.sampled_from(CornerStyle)),
        wave_style=draw(st.sampled_from(WaveStyle)),
        fillet_radius_mm=draw(st.sampled_from([0.2, 0.4, 0.8])),
        bus_width_mm=draw(st.sampled_from([0.5, 1.0])),
    )
    return dataclasses.replace(base, winding=winding)


def _hash_matches_equality(a: DesignParameters, b: DesignParameters) -> None:
    assert (design_hash(a) == design_hash(b)) == (a == b)


def _pair(designs: st.SearchStrategy[DesignParameters]) -> st.SearchStrategy[tuple[DesignParameters, DesignParameters]]:
    """Return a strategy of pairs: two independent draws, or a design and an equal copy of it."""
    return st.one_of(
        st.tuples(designs, designs),
        designs.map(lambda design: (design, copy.deepcopy(design))),
    )


def _other(value: object) -> object:
    """Return a value of the same type that differs from ``value``."""
    if isinstance(value, bool):
        return not value
    if isinstance(value, enum.Enum):
        members = list(type(value))
        return members[(members.index(value) + 1) % len(members)]
    if isinstance(value, int):
        return value + 1
    if isinstance(value, float):
        return value * 1.5 + 0.25
    return 0.3  # an optional width that was None


@pytest.mark.req("REQ-F-15")
@settings(max_examples=20)  # each serpentine draw builds a layout, about 0.3 s
@given(pair=_pair(serpentine_designs()))
def test_f15_1_serpentine_hashes_agree_exactly_when_designs_are_equal(pair):
    """Catches a serpentine field that the canonical JSON leaves out or writes twice."""
    _hash_matches_equality(*pair)


@pytest.mark.req("REQ-F-15")
@given(pair=_pair(wave_designs()))
def test_f15_1_wave_hashes_agree_exactly_when_designs_are_equal(pair):
    """Catches a wave field that the canonical JSON leaves out or writes twice."""
    _hash_matches_equality(*pair)


@pytest.mark.req("REQ-F-15")
@pytest.mark.parametrize(
    ("example_id", "winding_type"),
    [(SERPENTINE, SerpentineWindingSpec), (WAVE, WaveWindingSpec)],
    ids=["serpentine", "wave"],
)
def test_f15_1_changing_any_winding_field_changes_the_hash(example_id, winding_type):
    """Catches a winding field missing from the canonical JSON: each field of the spec moves the hash."""
    design = load_example(example_id)[1]
    assert isinstance(design.winding, winding_type)
    unhashed = []
    for field in dataclasses.fields(winding_type):
        if field.name == "kind":
            continue
        changed = dataclasses.replace(design.winding, **{field.name: _other(getattr(design.winding, field.name))})
        if design_hash(dataclasses.replace(design, winding=changed)) == design_hash(design):
            unhashed.append(field.name)
    assert unhashed == []


@pytest.mark.req("REQ-F-15")
@pytest.mark.parametrize("example_id", EXAMPLE_IDS)
def test_f15_1_save_load_save_is_byte_identical_for_every_packaged_example(tmp_path: Path, example_id: str):
    """Catches a lossy serpentine or wave field (angle, list shape, provenance) that changes the second save."""
    ref, design = load_example(example_id)
    first, second = tmp_path / "a.embodic.json", tmp_path / "b.embodic.json"
    save_project(first, ProjectFile(design=design, origin=ref, ui_state={"zoom": 1.5}), saved_utc=STAMP)
    loaded, issues = load_project(first)
    assert loaded is not None, issues
    save_project(second, loaded, saved_utc=STAMP)
    assert first.read_bytes() == second.read_bytes()
