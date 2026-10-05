"""Topology generators behind one table (interfaces.md section 6, ADR-0012)."""

from collections.abc import Callable, Mapping
from types import MappingProxyType

from embodic.errors import Unbuildable
from embodic.generators.base import Generator
from embodic.generators.spiral.generate import generate_spiral
from embodic.generators.stubs import generate_serpentine, generate_wave
from embodic.geometry.layout import BoardStack
from embodic.model.design import DesignParameters
from embodic.model.vocabulary import TopologyKind
from embodic.results import Registry

GENERATORS: Mapping[TopologyKind, Callable[[DesignParameters, Registry], BoardStack | Unbuildable]] = MappingProxyType(
    {
        TopologyKind.SPIRAL: generate_spiral,
        TopologyKind.SERPENTINE: generate_serpentine,
        TopologyKind.WAVE: generate_wave,
    }
)


def build_layout(design: DesignParameters, registry: Registry) -> BoardStack | Unbuildable:
    """Dispatch on design.topology through GENERATORS. Adding a topology = one module + one table entry."""
    return GENERATORS[design.topology](design, registry)


__all__ = ["GENERATORS", "Generator", "build_layout", "generate_serpentine", "generate_spiral", "generate_wave"]
