"""Serpentine and wave entry points; their Xcoil ports arrive with U-M3a and U-M3b."""

from embodic.errors import IssueCategory, Severity, Unbuildable, ValidationIssue, message_for
from embodic.geometry.layout import BoardStack
from embodic.model.design import DesignParameters
from embodic.model.vocabulary import TopologyKind
from embodic.model.winding_specs import SerpentineWindingSpec, WaveWindingSpec
from embodic.results import Registry


def _unsupported(kind: TopologyKind) -> Unbuildable:
    code = "UNBUILDABLE_UNSUPPORTED_TOPOLOGY"
    issue = ValidationIssue(
        code=code,
        category=IssueCategory.UNBUILDABLE,
        severity=Severity.ERROR,
        message=message_for(code),
        pointers=("/winding/kind",),
        value=kind.value,
    )
    return Unbuildable(issues=(issue,))


def generate_serpentine(design: DesignParameters, registry: Registry) -> BoardStack | Unbuildable:
    """Stub until the Xcoil buildCanonical/buildLayout port (GR-20): always Unbuildable."""
    del registry
    if not isinstance(design.winding, SerpentineWindingSpec):
        raise TypeError(f"generate_serpentine needs a serpentine winding, got {type(design.winding).__name__}")
    return _unsupported(TopologyKind.SERPENTINE)


def generate_wave(design: DesignParameters, registry: Registry) -> BoardStack | Unbuildable:
    """Stub until the Xcoil buildWave/buildWaveOverlap port (GR-21): always Unbuildable."""
    del registry
    if not isinstance(design.winding, WaveWindingSpec):
        raise TypeError(f"generate_wave needs a wave winding, got {type(design.winding).__name__}")
    return _unsupported(TopologyKind.WAVE)
