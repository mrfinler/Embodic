"""Traceable results, the equation and evidence registries, the D-007 badge rule and number formatting."""

from embodic.results.analysis_result import AnalysisResult, LayerResult, PhaseResult, TorqueSpeedEstimate
from embodic.results.formatting import format_quantity, format_value
from embodic.results.labels import QUANTITY_LABELS
from embodic.results.registry import (
    Assumption,
    EquationEntry,
    EvidenceEntry,
    Registry,
    RegistryConstant,
    RegistryFormatError,
    Tolerance,
    ValidityCheckSpec,
    load_registry,
)
from embodic.results.status import (
    STATUS_ORDER_WEAKEST_FIRST,
    GateVerdict,
    MetricBound,
    Status,
    ValidityEffect,
    ValidityFlag,
    combine_status,
)
from embodic.results.traceable import AssumedInput, InputRef, Traceable, evaluate_validity, traced

__all__ = [
    "QUANTITY_LABELS",
    "STATUS_ORDER_WEAKEST_FIRST",
    "AnalysisResult",
    "AssumedInput",
    "Assumption",
    "EquationEntry",
    "EvidenceEntry",
    "GateVerdict",
    "InputRef",
    "LayerResult",
    "MetricBound",
    "PhaseResult",
    "Registry",
    "RegistryConstant",
    "RegistryFormatError",
    "Status",
    "Tolerance",
    "TorqueSpeedEstimate",
    "Traceable",
    "ValidityCheckSpec",
    "ValidityEffect",
    "ValidityFlag",
    "combine_status",
    "evaluate_validity",
    "format_quantity",
    "format_value",
    "load_registry",
    "traced",
]
