"""Issue vocabulary shared by every package: severities, categories, issues, suggestions and the message catalogue.

A failure the user can cause is returned as a value (`ValidationIssue`, `Unbuildable`); exceptions mean programming
errors (interfaces.md section 0).
"""

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType


class Severity(StrEnum):
    """How strongly an issue blocks the user."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class IssueCategory(StrEnum):
    """What kind of problem an issue reports."""

    INVALID = "invalid"
    MISSING = "missing"  # new-design flow: a required field has no value yet (D-014)
    UNSUPPORTED_RANGE = "unsupported_range"
    UNBUILDABLE = "unbuildable"
    DRC = "drc"
    INTERNAL = "internal"


@dataclass(frozen=True, slots=True, kw_only=True)
class Suggestion:
    """The engine proposes, never applies (REQ-F-23)."""

    pointer: str
    proposed_value: float | int | str
    reason: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidationIssue:
    """One problem found in a design, located by JSON pointers."""

    code: str  # stable UPPER_SNAKE code with category prefix, e.g. "RANGE_SKIN_DEPTH"
    category: IssueCategory
    severity: Severity
    message: str  # English sentence from the message catalogue
    pointers: tuple[str, ...]  # JSON pointers into the design
    value: float | int | str | None = None
    limit: float | int | str | None = None
    hint: str = ""
    eq_ids: tuple[str, ...] = ()
    suggestion: Suggestion | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class Unbuildable:
    """Returned instead of a Layout when valid input cannot produce copper."""

    issues: tuple[ValidationIssue, ...]

    def __post_init__(self) -> None:
        """Refuse construction without the ERROR issue that explains why no copper was produced."""
        if not any(i.severity is Severity.ERROR and i.category is IssueCategory.UNBUILDABLE for i in self.issues):
            raise ValueError("Unbuildable needs at least one ERROR issue with category UNBUILDABLE")


CODE_PREFIXES = ("INVALID_", "MISSING_", "RANGE_", "UNBUILDABLE_", "DRC_", "INTERNAL_", "INFO_")

MESSAGES = MappingProxyType(
    {
        "RANGE_SKIN_DEPTH": (
            "The trace is wider than one third of the skin depth at the operating frequency, "
            "so resistance and eddy-loss results lose accuracy."
        ),
        "INVALID_MEASURED_SOURCE_EMPTY": "A measured value needs a named source, such as a datasheet or a test record.",
        "INVALID_MEASURED_DESIGN_FIELD": "Only material and property fields can be marked as measured.",
        "INVALID_PROVENANCE": "A measured entry needs a source and must belong to a property field.",
        "INVALID_SCHEMA_VERSION_NEWER": "This project file was written by a newer version of embodic.",
        "INFO_EXAMPLE_NOT_PACKAGED": (
            "The example this project started from is not packaged with this version, so provenance is kept as saved."
        ),
        "INFO_MIGRATED": "The project file was upgraded to the current file format.",
    }
)


def message_for(code: str) -> str:
    """English message template for an issue code; raises KeyError for an unknown code (programming error)."""
    return MESSAGES[code]
