"""Xcoil parameter objects to the serpentine builders' inputs.

Xcoil's ``normalizeParams`` fills every key, so a fixture's ``params`` (the first call of ``layout-default``) holds all
defaults. ``params_from_xcoil`` reads only the keys the canonical build and the layout use.
"""

import math
from collections.abc import Mapping
from functools import cache
from typing import Any

from harness import load_area

from embodic.generators.serpentine.frame import Params
from embodic.model.winding_specs import CornerStyle, LayerOrder, PairConnection, SideStyle, StackMode, TerminalSide

STACK_MODE = {"single": StackMode.SINGLE, "perPhase": StackMode.ONE_BOARD_PER_PHASE}


@cache
def xcoil_defaults() -> Mapping[str, Any]:
    """Return Xcoil's normalised default parameters as the engine reported them."""
    (call,) = load_area("serpentine")["layout-default"].calls
    return call.output["params"]


def normalised(given: Mapping[str, Any]) -> dict[str, Any]:
    """Return ``given`` over the defaults. The seeded sets stay in range, so Xcoil's clamps change nothing."""
    return {**xcoil_defaults(), **given}


def params_from_xcoil(p: Mapping[str, Any]) -> Params:
    """Return the builders' inputs of a normalised Xcoil parameter object."""
    return Params(
        poles=p["poles"],
        phases=p["phases"],
        r_in=p["rIn"],
        r_out=p["rOut"],
        turns=p["turns"],
        strands=p["strands"],
        trace_width_mm=p["traceWidth"],
        clearance_mm=p["clearance"],
        end_width_outer_mm=p["endWidthOuter"],
        end_width_inner_mm=p["endWidthInner"],
        style=SideStyle(p["style"]),
        corner_style=CornerStyle(p["cornerStyle"]),
        fillet_radius_mm=p["filletRadius"],
        fillet_max=p["filletMax"],
        terminal_side=TerminalSide(p["terminalSide"]),
        start_angle_rad=p["startAngleDeg"] * math.pi / 180,
        layers_per_phase=p["layersPerPhase"],
        pair_connection=PairConnection(p["pairConnection"]),
        layer_order=LayerOrder(p["layerOrder"]),
        stack_mode=STACK_MODE[p["stackMode"]],
        via_pad=p["viaPad"],
    )
