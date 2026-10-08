"""Wave entry point; its Xcoil port arrives with U-M3b."""

from embodic.errors import IssueCategory, Severity, Unbuildable, ValidationIssue, message_for
from embodic.geometry.layout import BoardStack
from embodic.model.design import DesignParameters
from embodic.model.vocabulary import TopologyKind
from embodic.model.winding_specs import WaveWindingSpec
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


def generate_wave(design: DesignParameters, registry: Registry) -> BoardStack | Unbuildable:
    """Stub until the Xcoil buildWave/buildWaveOverlap port (GR-21): always Unbuildable."""
    del registry
    if not isinstance(design.winding, WaveWindingSpec):
        raise TypeError(f"generate_wave needs a wave winding, got {type(design.winding).__name__}")
    return _unsupported(TopologyKind.WAVE)
