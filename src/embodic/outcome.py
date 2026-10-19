"""What one compute run returns (interfaces.md section 10); `embodic.io` takes an outcome without importing the API."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from embodic.drc import DrcReport
from embodic.errors import Severity, ValidationIssue
from embodic.geometry.layout import BoardStack
from embodic.model.design import DesignParameters
from embodic.model.provenance import ProvenanceMap
from embodic.results import AnalysisResult


class Stage(StrEnum):
    """The pipeline stages in run order; `timings_s` and the INTERNAL_* codes name them."""

    VALIDATE = "validate"
    GEOMETRY = "geometry"  # winding plan and generator
    DRC = "drc"
    PHYSICS = "physics"


@dataclass(frozen=True, slots=True, kw_only=True)
class VersionInfo:
    """Versions that decide a result: the package, the project schema, the equation registry and the runtime."""

    embodic: str
    schema: int
    registry: str
    python: str
    numpy: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ComputeOptions:
    """Switches of one compute run."""

    run_drc: bool = True
    use_symmetry: bool = True


@dataclass(frozen=True, slots=True, kw_only=True)
class ComputeOutcome:
    """Every product of one compute run; a stage that did not run leaves its field None."""

    design: DesignParameters
    design_hash: str  # "" when the design has no file form: validation refused an angle with infinite degrees
    provenance: ProvenanceMap
    issues: tuple[ValidationIssue, ...]
    boards: BoardStack | None
    drc: tuple[DrcReport, ...] | None  # one report per board, in board order
    analysis: AnalysisResult | None
    timings_s: Mapping[str, float]  # Stage value -> seconds, for the stages that ran
    versions: VersionInfo

    @property
    def ok(self) -> bool:
        """No ERROR issue and the DRC of every board passed."""
        no_error = not any(i.severity is Severity.ERROR for i in self.issues)
        return no_error and self.drc is not None and all(report.passed for report in self.drc)
