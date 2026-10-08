"""Issue messages of the exporters (U-M4a): why a writer refused to write a file (interfaces.md section 9.3)."""

from collections.abc import Mapping

MESSAGES: Mapping[str, str] = {
    "EXPORT_DRC_ERRORS_NOT_CONFIRMED": (
        "The design rule check did not pass; confirm the export with its failures listed to write the files anyway."
    ),
    "EXPORT_NO_LAYOUT": "There is no board layout to export; the design did not build.",
    "EXPORT_NO_SCREWS": "The board has no screw clearance holes, so there is no screws drawing to export.",
}
