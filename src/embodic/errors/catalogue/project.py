"""Issue messages of the project file, the packaged examples and the compute facade (U-M2f)."""

from collections.abc import Mapping

MESSAGES: Mapping[str, str] = {
    "INVALID_PROJECT_FILE": "The file is not an embodic project file or cannot be read.",
    "INVALID_PROJECT_NOT_FOUND": "The project file does not exist.",
    "MISSING_DESIGN_INCOMPLETE": "The project holds an incomplete design; enter the missing values before computing.",
    "INFO_PROVENANCE_EXAMPLE_MISMATCH": (
        "The saved provenance of this field disagrees with the packaged example it names; "
        "provenance is derived again from the example."
    ),
    "INTERNAL_VALIDATE_FAILED": "Validation stopped with an internal error; the traceback is attached.",
    "INTERNAL_GEOMETRY_FAILED": "Layout generation stopped with an internal error; the traceback is attached.",
    "INTERNAL_DRC_FAILED": "The design-rule check stopped with an internal error; the traceback is attached.",
    "INTERNAL_PHYSICS_FAILED": "The analysis stopped with an internal error; the traceback is attached.",
}
