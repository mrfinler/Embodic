"""Xcoil wave parameters to an embodic design, driven by ``tools/golden/param_map/wave.json``."""

import dataclasses
import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from tests.unit.model.designs import wave_design

from embodic.model.design import DesignParameters
from embodic.model.stackup import generate_even_stackup
from embodic.model.vocabulary import ConnectionTopology
from embodic.model.winding_specs import CornerStyle, WaveStyle

PARAM_MAP = Path(__file__).resolve().parents[3] / "tools" / "golden" / "param_map" / "wave.json"
OZ_TO_MM = 0.0348  # engine.js l.13


def _even_stackup(xcoil: Mapping[str, Any]) -> Any:
    assert xcoil["copperOzOuter"] == xcoil["copperOzInner"], "the even stack-up has one copper weight"
    return generate_even_stackup(xcoil["waveLayers"], xcoil["copperOzOuter"] * OZ_TO_MM, xcoil["boardThickness"])


_SINGLE: Mapping[str, Callable[[Any], Any]] = {
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
        value = (
            _even_stackup(xcoil)
            if entry["transform"] == "even_stackup"
            else _SINGLE[entry["transform"]](xcoil[entry["xcoil"]])
        )
        design = _set(design, entry["pointer"].strip("/").split("/"), value)
    return design
