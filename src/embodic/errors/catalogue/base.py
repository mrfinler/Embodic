"""Issue messages of the base modules: the codes interfaces.md names in sections 1, 2.4 and 9.1 (U-M1a)."""

from collections.abc import Mapping

MESSAGES: Mapping[str, str] = {
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
