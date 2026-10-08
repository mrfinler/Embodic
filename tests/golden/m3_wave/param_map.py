"""Xcoil wave parameters to an embodic design, driven by ``tools/golden/param_map/wave.json``."""

import dataclasses
import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from tests.unit.model.designs import wave_design

from embodic.model.design import DesignParameters
from embodic.model.operating import Modulation
from embodic.model.rotor import ArcMagnet, RotorType
from embodic.model.stackup import generate_even_stackup
from embodic.model.vocabulary import ConnectionTopology
from embodic.model.winding_specs import CornerStyle, WaveStyle

PARAM_MAP = Path(__file__).resolve().parents[3] / "tools" / "golden" / "param_map" / "wave.json"
OZ_TO_MM = 0.0348  # engine.js l.13


def _even_stackup(xcoil: Mapping[str, Any]) -> Any:
    assert xcoil["copperOzOuter"] == xcoil["copperOzInner"], "the even stack-up has one copper weight"
    return generate_even_stackup(xcoil["waveLayers"], xcoil["copperOzOuter"] * OZ_TO_MM, xcoil["boardThickness"])


def _arc_magnet(xcoil: Mapping[str, Any]) -> ArcMagnet:
    return ArcMagnet(
        pole_arc_ratio=xcoil["magnetArcRatio"], r_inner_mm=xcoil["magnetRIn"], r_outer_mm=xcoil["magnetROut"],
        thickness_mm=xcoil["magnetThickness"],
    )  # fmt: skip


_COMPOSITE: Mapping[str, Callable[[Mapping[str, Any]], Any]] = {
    "even_stackup": _even_stackup,
    "arc_magnet": _arc_magnet,
}
_SINGLE: Mapping[str, Callable[[Any], Any]] = {
    "rotor_type": {
        "double": RotorType.DOUBLE,
        "singleYoke": RotorType.SINGLE_YOKE,
        "singleOpen": RotorType.SINGLE_OPEN,
    }.get,
    "modulation": {"svpwm": Modulation.SVPWM, "sine": Modulation.SPWM, "sixstep": Modulation.SIX_STEP}.get,
    "identity": lambda v: v,
    "zero_is_none": lambda v: v if v > 0 else None,
    "corner_style": CornerStyle,
    "wave_style": WaveStyle,
    "connection_topology": ConnectionTopology,
}


def _set(obj: Any, path: list[str], value: Any) -> Any:
    if not path:
        return value
    return dataclasses.replace(obj, **{path[0]: _set(getattr(obj, path[0]), path[1:], value)})


def design_from_xcoil(xcoil: Mapping[str, Any], base: DesignParameters | None = None) -> DesignParameters:
    """Apply every entry of the parameter map to ``base`` (default: the Xcoil-defaults wave design)."""
    design = base or wave_design()
    for entry in json.loads(PARAM_MAP.read_text())["fields"]:
        if entry["transform"] in _COMPOSITE:
            value = _COMPOSITE[entry["transform"]](xcoil)
        else:
            value = _SINGLE[entry["transform"]](xcoil[entry["xcoil"]])
        design = _set(design, entry["pointer"].strip("/").split("/"), value)
    return design
