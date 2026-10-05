"""Generator plug-in protocol (interfaces.md section 6, ADR-0012)."""

from typing import ClassVar, Protocol

from embodic.errors import Unbuildable
from embodic.geometry.layout import BoardStack
from embodic.model.design import DesignParameters
from embodic.model.vocabulary import TopologyKind
from embodic.results import Registry


class Generator(Protocol):
    """A topology generator. Pure; never raises for user input; deterministic (same design -> same stack_hash)."""

    kind: ClassVar[TopologyKind]

    def generate(self, design: DesignParameters, registry: Registry) -> BoardStack | Unbuildable:
        """Build the boards of ``design`` or say why it cannot be built."""
        ...
