"""Hypothesis strategies over spiral designs near the packaged CF-11 example (example values, `assumption`)."""

import dataclasses
import math

from hypothesis import settings
from hypothesis import strategies as st

from embodic.io.examples import load_example
from embodic.model.design import DesignParameters
from embodic.model.draft import DesignDraft, draft_from_design
from embodic.model.schema import JsonValue
from embodic.model.winding_specs import SpiralWindingSpec

# A compute takes about a second, so compute properties draw 1/20 of the profile's examples (5 per commit, 100 nightly).
COMPUTE_EXAMPLES = max(5, settings().max_examples // 20)


def cf11() -> DesignParameters:
    """Return the packaged default example."""
    return load_example("spiral_12c16p_default")[1]


@st.composite
def spiral_designs(draw: st.DrawFn) -> DesignParameters:
    """Draw a balanced-or-not spiral design by changing coil count, poles, copper and operating point of CF-11."""
    base = cf11()
    assert isinstance(base.winding, SpiralWindingSpec)
    coil = dataclasses.replace(
        base.winding.coil,
        coil_count=draw(st.sampled_from([6, 9, 12, 18])),
        trace_width_mm=draw(st.sampled_from([0.3, 0.5, 0.8])),
        turns=draw(st.none() | st.integers(1, 6)),
        first_coil_angle_rad=draw(st.floats(-math.pi, math.pi)),
    )
    rotor = dataclasses.replace(
        base.rotor, poles=draw(st.sampled_from([4, 8, 10, 14, 16])), remanence_t=draw(st.floats(0.8, 1.45))
    )
    operating = dataclasses.replace(
        base.operating,
        speed_rpm=draw(st.floats(100.0, 6000.0)),
        line_current_rms_a=draw(st.floats(0.1, 5.0)),
        winding_temperature_degc=draw(st.floats(20.0, 120.0)),
    )
    return dataclasses.replace(
        base, rotor=rotor, winding=dataclasses.replace(base.winding, coil=coil), operating=operating
    )


ANY_JSON: st.SearchStrategy[JsonValue] = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(-1000, 1000),
    st.floats(allow_nan=True, allow_infinity=True),
    st.floats(-1000.0, 1000.0),
    st.text(max_size=6),
    st.lists(st.integers(-3, 3), max_size=3),
)


def cf11_draft_with(changes: dict[str, JsonValue]) -> DesignDraft:
    """Return the CF-11 draft with some leaves replaced (pinned PR-05 inputs)."""
    draft = draft_from_design(cf11())
    return DesignDraft(topology=draft.topology, values={**draft.values, **changes})


@st.composite
def mutated_drafts(draw: st.DrawFn) -> DesignDraft:
    """Draw the CF-11 draft with one to three leaves set to arbitrary JSON values (PR-05 input)."""
    draft = draft_from_design(cf11())
    values = dict(draft.values)
    for pointer in draw(st.lists(st.sampled_from(sorted(values)), min_size=1, max_size=3, unique=True)):
        values[pointer] = draw(ANY_JSON)
    return DesignDraft(topology=draft.topology, values=values)
