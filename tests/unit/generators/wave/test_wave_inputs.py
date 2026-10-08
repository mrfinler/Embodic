"""D-030 input bounds of the wave generator and its degenerate end-turn (DEF-M3b-03, REQ-F-35)."""

import dataclasses
import math

import pytest

from embodic.errors import Unbuildable
from embodic.generators.wave import generate as wave_generate
from embodic.generators.wave import generate_wave
from embodic.generators.wave.involute import DegenerateBiarcError, biarc
from embodic.geometry.layout import BoardStack
from embodic.model.design import DesignParameters
from embodic.model.winding_specs import WaveStyle
from embodic.results import Registry, load_registry

from .designs import wave

pytestmark = pytest.mark.req("REQ-F-35")
OUT_OF_RANGE = "UNBUILDABLE_WAVE_INPUT_OUT_OF_RANGE"
NAN, INF = math.nan, math.inf


@pytest.fixture(scope="module")
def registry() -> Registry:
    """Return the packaged registry, loaded once."""
    return load_registry()


@pytest.fixture
def no_geometry(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail the test if the generator derives the frame or builds any track: a refusal must come first."""

    def built(*_: object, **__: object) -> None:
        raise AssertionError("geometry was built for a refused input")

    for name in ("derive_wave", "build_wave", "build_overlap"):
        monkeypatch.setattr(wave_generate, name, built)


def _refused(design: DesignParameters, registry: Registry) -> Unbuildable:
    result = generate_wave(design, registry)
    assert isinstance(result, Unbuildable), type(result)
    return result


def _spec(**changes: float) -> DesignParameters:
    design = wave()
    return dataclasses.replace(design, winding=dataclasses.replace(design.winding, **changes))  # type: ignore[type-var]


def _with_pad(pad_mm: float) -> DesignParameters:
    design = wave()
    return dataclasses.replace(design, vias=dataclasses.replace(design.vias, pad_mm=pad_mm))


def _span(span_mm: float) -> DesignParameters:
    return _spec(r_outer_mm=22.0 + span_mm)


@pytest.mark.parametrize(
    ("design", "pointer"),
    [
        pytest.param(_spec(trace_width_mm=NAN), "/winding/trace_width_mm", id="trace-width-nan"),
        pytest.param(_spec(trace_width_mm=0.0), "/winding/trace_width_mm", id="trace-width-zero"),
        pytest.param(_spec(trace_width_mm=-0.4), "/winding/trace_width_mm", id="trace-width-negative"),
        pytest.param(_spec(trace_width_mm=1.175494351e-38), "/winding/trace_width_mm", id="trace-width-denormal"),
        pytest.param(_spec(trace_width_mm=0.149), "/winding/trace_width_mm", id="trace-width-below-drc-minimum"),
        pytest.param(_spec(clearance_mm=NAN), "/winding/clearance_mm", id="clearance-nan"),
        pytest.param(_spec(clearance_mm=0.0), "/winding/clearance_mm", id="clearance-zero"),
        pytest.param(_spec(clearance_mm=-0.2), "/winding/clearance_mm", id="clearance-negative"),
        pytest.param(_with_pad(NAN), "/vias/pad_mm", id="pad-nan"),
        pytest.param(_with_pad(0.0), "/vias/pad_mm", id="pad-zero"),
        pytest.param(_spec(r_inner_mm=NAN), "/winding/r_inner_mm", id="r-inner-nan"),
        pytest.param(_spec(r_inner_mm=INF), "/winding/r_inner_mm", id="r-inner-infinite"),
        pytest.param(_spec(r_inner_mm=0.0), "/winding/r_inner_mm", id="r-inner-zero"),
        pytest.param(_span(0.0), "/winding/r_outer_mm", id="span-zero"),
        pytest.param(_span(-5.0), "/winding/r_outer_mm", id="span-negative"),
        pytest.param(_spec(r_outer_mm=NAN), "/winding/r_outer_mm", id="r-outer-nan"),
        pytest.param(_spec(r_outer_mm=INF), "/winding/r_outer_mm", id="r-outer-infinite"),
        pytest.param(_spec(fillet_radius_mm=NAN), "/winding/fillet_radius_mm", id="fillet-radius-nan"),
        pytest.param(_spec(fillet_radius_mm=-0.4), "/winding/fillet_radius_mm", id="fillet-radius-negative"),
    ],
)
def test_unusable_size_is_refused_before_any_geometry(
    design: DesignParameters, pointer: str, registry: Registry, no_geometry: None
) -> None:
    """Catches D-030 missing for wave: a size that is not finite and positive, or a width the DRC refuses, built."""
    result = _refused(design, registry)
    assert [i.code for i in result.issues] == [OUT_OF_RANGE]
    assert pointer in result.issues[0].pointers


@pytest.mark.parametrize(
    ("design", "pointer"),
    [
        pytest.param(wave(turns=0), "/winding/turns", id="turns-zero"),
        pytest.param(wave(turns=-1), "/winding/turns", id="turns-negative"),
        pytest.param(wave(turns=201), "/winding/turns", id="turns-above-maximum"),
        pytest.param(wave(turns=5, poles=200), "/winding/turns", id="slots-above-maximum"),
        pytest.param(wave(poles=0), "/rotor/poles", id="poles-zero"),
        pytest.param(wave(poles=202), "/rotor/poles", id="poles-above-maximum"),
    ],
)
def test_count_beyond_the_maximum_is_refused_before_any_geometry(
    design: DesignParameters, pointer: str, registry: Registry, no_geometry: None
) -> None:
    """Catches an unbounded build: turns or slot counts past Xcoil's ranges and MAX_SLOTS must not reach the builder."""
    result = _refused(design, registry)
    assert [i.code for i in result.issues] == [OUT_OF_RANGE]
    assert pointer in result.issues[0].pointers


def test_a_width_exactly_at_the_drc_minimum_is_not_refused(registry: Registry) -> None:
    """Catches an off-by-one in the DRC width bound: D-006 flags a width below the rule, not one equal to it."""
    design = wave()
    at_minimum = _spec(trace_width_mm=design.drc_rules.min_trace_width_mm)
    assert isinstance(generate_wave(at_minimum, registry), BoardStack)


def test_biarc_of_coincident_points_is_degenerate_not_a_zero_division() -> None:
    """Catches DEF-M3b-03: p0 == p1 divided by zero in the joint formula."""
    point, tangent = (0.5, -0.25), (math.cos(2.0), math.sin(2.0))
    with pytest.raises(DegenerateBiarcError):
        biarc(point, tangent, point, tangent, 0.4, "endturn")


def test_biarc_of_equal_tangents_and_a_perpendicular_chord_is_degenerate() -> None:
    """Catches the second zero division of the joint formula: c == 0 and the chord normal to the shared tangent."""
    with pytest.raises(DegenerateBiarcError):
        biarc((0.0, 0.0), (1.0, 0.0), (0.0, 3.0), (1.0, 0.0), 0.4, "endturn")


def test_a_regular_biarc_still_joins_its_end_points() -> None:
    """Catches a degenerate test that is too wide: a quarter turn from (1, 0) to (0, 1) must give two arcs."""
    first, second = biarc((1.0, 0.0), (0.0, 1.0), (0.0, 1.0), (-1.0, 0.0), 0.4, "endturn")
    assert (first.kind, second.kind) == ("endturn", "endturn")


def test_collapsed_end_turns_are_unbuildable_not_an_exception(registry: Registry) -> None:
    """Catches DEF-M3b-03 at the generator: tiny clearance, pad and inner end width put both biarc points together."""
    design = wave(
        WaveStyle.INVOLUTE, turns=1, poles=4, r_inner_mm=0.5, r_outer_mm=18.5, trace_width_mm=0.15, clearance_mm=1e-9,
        end_width_inner_mm=1e-9, bus_width_mm=0.4, fillet_radius_mm=0.4,
    )  # fmt: skip
    design = dataclasses.replace(design, vias=dataclasses.replace(design.vias, pad_mm=1e-9))
    assert [i.code for i in _refused(design, registry).issues] == ["UNBUILDABLE_WAVE_END_TURN_DEGENERATE"]
