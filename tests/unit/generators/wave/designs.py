"""Wave designs for the unit tests: Xcoil's wave defaults (engine.js l.19-97) with the knobs the tests vary."""

import dataclasses

from tests.unit.model.designs import COPPER_2OZ_MM, wave_design

from embodic.model.design import DesignParameters
from embodic.model.stackup import generate_even_stackup
from embodic.model.winding_specs import WaveStyle, WaveWindingSpec


def wave(
    style: WaveStyle = WaveStyle.INVOLUTE,
    phases: int = 3,
    layers: int = 2,
    turns: int = 2,
    poles: int = 16,
    **winding: object,
) -> DesignParameters:
    """Return a wave design; ``winding`` replaces fields of the WaveWindingSpec."""
    base = wave_design()
    assert isinstance(base.winding, WaveWindingSpec)
    spec = dataclasses.replace(base.winding, wave_style=style, turns=turns, **winding)  # type: ignore[arg-type]
    return dataclasses.replace(
        base,
        phases=phases,  # type: ignore[arg-type]
        rotor=dataclasses.replace(base.rotor, poles=poles),
        winding=spec,
        stackup=generate_even_stackup(layers, COPPER_2OZ_MM, 1.6),
    )
