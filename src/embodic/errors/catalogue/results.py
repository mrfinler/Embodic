"""Issue messages of the registry loader (U-M2b): gaps between the packaged registries and the contract shape."""

from collections.abc import Mapping

MESSAGES: Mapping[str, str] = {
    "INTERNAL_REGISTRY_EVIDENCE_MISSING": "An equation cites an evidence ID that the evidence register does not list.",
    "INTERNAL_REGISTRY_EQUATION_UNSOURCED": "An equation cites no evidence ID.",
    "INTERNAL_REGISTRY_FIELD_UNTYPED": (
        "A validity-check field is missing or written as prose; the status word that opens the prose, "
        "or else the weakest value, is used."
    ),
    "INTERNAL_REGISTRY_UNIT_UNKNOWN": "A registry constant has a unit outside the unit vocabulary and is not loaded.",
}
