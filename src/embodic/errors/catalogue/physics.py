"""Issue messages of embodic.physics (U-M2e-4)."""

from collections.abc import Mapping

MESSAGES: Mapping[str, str] = {
    "INTERNAL_INTERCONNECT_UNCLASSIFIED": (
        "Interconnect copper not classified: the layout records no interconnect roles, so the interconnect loss is "
        "not computed and no interconnect resistance is added to the line resistance."
    ),
}
