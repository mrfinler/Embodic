"""Issue messages of the generators (U-M2d, embodic.generators)."""

from collections.abc import Mapping

MESSAGES: Mapping[str, str] = {
    "UNBUILDABLE_UNSUPPORTED_TOPOLOGY": "This topology has no generator yet; only spiral coils can be built.",
    "UNBUILDABLE_SPIRAL_OPTION_NOT_IMPLEMENTED": (
        "The spiral generator does not build this option yet; the pointers name the inputs to change."
    ),
    "UNBUILDABLE_SPIRAL_INPUT_OUT_OF_RANGE": "A spiral coil input is outside the range the geometry can use.",
    "UNBUILDABLE_ZERO_TURNS": "No spiral turn with a centre via fits between the inner and outer radius.",
    "UNBUILDABLE_TURNS_EXCEED_LIMIT": "The requested turn count exceeds the largest buildable count {limit}.",
    "UNBUILDABLE_PHASE_CHAIN_UNROUTABLE": "The coils of a phase cannot be chained on four bus ring levels.",
}
