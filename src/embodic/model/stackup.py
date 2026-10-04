"""Explicit board stack-up, top to bottom (interfaces.md section 2.1, REQ-F-04)."""

import math
from dataclasses import dataclass
from typing import Literal, TypeAlias


@dataclass(frozen=True, slots=True, kw_only=True)
class CopperLayer:
    """A copper layer; `thickness_mm` is the finished copper (a property input)."""

    kind: Literal["copper"] = "copper"
    name: str
    thickness_mm: float


@dataclass(frozen=True, slots=True, kw_only=True)
class DielectricLayer:
    """A dielectric layer between copper layers."""

    kind: Literal["dielectric"] = "dielectric"
    name: str
    thickness_mm: float
    material: str


StackLayer: TypeAlias = CopperLayer | DielectricLayer


@dataclass(frozen=True, slots=True, kw_only=True)
class Stackup:
    """Ordered layers from the top surface down; copper z positions derive from it."""

    layers: tuple[StackLayer, ...]

    def copper_layers(self) -> tuple[CopperLayer, ...]:
        """Return the copper layers in stack order."""
        return tuple(layer for layer in self.layers if isinstance(layer, CopperLayer))

    def copper_z_mm(self) -> dict[str, float]:
        """Return the centre z of each copper layer from the top surface, as an exact cumulative sum."""
        z_mm: dict[str, float] = {}
        above_mm: list[float] = []
        for layer in self.layers:
            if isinstance(layer, CopperLayer):
                z_mm[layer.name] = math.fsum([*above_mm, layer.thickness_mm / 2.0])
            above_mm.append(layer.thickness_mm)
        return z_mm

    def board_thickness_mm(self) -> float:
        """Return the sum of all layer thicknesses."""
        return math.fsum(layer.thickness_mm for layer in self.layers)


def generate_even_stackup(
    copper_count: int, copper_thickness_mm: float, board_thickness_mm: float, material: str = "FR-4"
) -> Stackup:
    """Build evenly spaced copper layers like Xcoil stackupFor in auto mode (engine.js l.1156-1176).

    Parameters
    ----------
    copper_count : int
        Number of copper layers, at least 1.
    copper_thickness_mm : float
        Finished thickness of every copper layer.
    board_thickness_mm : float
        Total board thickness.
    material : str
        Dielectric material name.

    Returns
    -------
    Stackup
        Copper layers L1..Ln with dielectric layers D1..D(n-1) between them; one copper layer gets one dielectric below.
    """
    if copper_count == 1:
        dielectric_mm = board_thickness_mm - copper_thickness_mm
        return Stackup(
            layers=(
                CopperLayer(name="L1", thickness_mm=copper_thickness_mm),
                DielectricLayer(name="D1", thickness_mm=max(0.0, dielectric_mm), material=material),
            )
        )
    pitch_mm = (board_thickness_mm - copper_thickness_mm) / (copper_count - 1)
    layers: list[StackLayer] = []
    for index in range(copper_count):
        layers.append(CopperLayer(name=f"L{index + 1}", thickness_mm=copper_thickness_mm))
        if index < copper_count - 1:
            dielectric_mm = pitch_mm - copper_thickness_mm
            layers.append(
                DielectricLayer(name=f"D{index + 1}", thickness_mm=max(0.0, dielectric_mm), material=material)
            )
    return Stackup(layers=tuple(layers))
