"""Spiral layer pairs and their series and parallel grouping (interfaces.md section 2.2)."""

from dataclasses import dataclass

from embodic.model.vocabulary import Phase


@dataclass(frozen=True, slots=True, kw_only=True)
class LayerPair:
    """Two copper layers carrying one coil: X spirals in, Y (mirrored) spirals out."""

    index: int
    layer_in: str
    layer_out: str
    rotation_rad: float = 0.0  # option M3
    phases: tuple[Phase, ...] | None = None  # None = all phases (FSCW); one phase = option M4


@dataclass(frozen=True, slots=True, kw_only=True)
class LayerConfig:
    """Layer pairs; pairs inside a group are in parallel, groups are in series (EQ-07)."""

    pairs: tuple[LayerPair, ...]
    series_groups: tuple[tuple[int, ...], ...]
