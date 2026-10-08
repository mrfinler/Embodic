"""Issue messages of embodic.physics (U-M2e-4)."""

from collections.abc import Mapping

MESSAGES: Mapping[str, str] = {
    "RANGE_NON_FINITE_RESULT": (
        "A result is not a finite number at this operating point; it is shown as unresolved. The quantity is named "
        "in the issue value."
    ),
    "INTERNAL_INTERCONNECT_UNCLASSIFIED": (
        "Interconnect copper not classified: the layout records no interconnect roles, so the interconnect loss is "
        "not computed and no interconnect resistance is added to the line resistance."
    ),
}
