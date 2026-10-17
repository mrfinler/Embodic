"""Issue messages of the generators (U-M2d, embodic.generators)."""

from collections.abc import Mapping

MESSAGES: Mapping[str, str] = {
    "UNBUILDABLE_SPIRAL_OPTION_NOT_IMPLEMENTED": (
        "The spiral generator does not build this option yet; the pointers name the inputs to change."
    ),
    "UNBUILDABLE_SPIRAL_INPUT_OUT_OF_RANGE": "A spiral coil input is outside the range the geometry can use.",
    "UNBUILDABLE_ZERO_TURNS": "No spiral turn with a centre via fits between the inner and outer radius.",
    "UNBUILDABLE_TURNS_EXCEED_LIMIT": (
        "The requested turns, or the turns that fit between the radii, exceed the limit of {limit} per coil layer. "
        "Lower the turn count, or change the trace width or clearance."
    ),
    "UNBUILDABLE_UNSUPPORTED_END_STYLE": "The stadium coil end is not built yet; choose the arc or the straight end.",
    "UNBUILDABLE_PHASE_CHAIN_UNROUTABLE": "The coils of a phase cannot be chained on four bus ring levels.",
    "UNBUILDABLE_INTERCONNECT_CROSSING": "The delta links cross, and one ring layer cannot carry crossing links.",
    "UNBUILDABLE_SCREW_HOLE_EDGE": "A screw hole is closer to the board edge or a cutout than the edge clearance.",
    "UNBUILDABLE_SCREW_HOLE_PITCH": "Two screw holes are closer to each other than the edge clearance.",
    "UNBUILDABLE_PAIRS_ROTATED_APART": (
        "Every layer pair of a winding needs the same rotation. Pairs are joined coil by coil, and a pair rotated by "
        "half a coil pitch has no coil at the same position."
    ),
    "UNBUILDABLE_SERIES_VIA_FAN_DRC": (
        "The series layer pairs need a transfer via fan and one centre via per group; with them the board breaks a "
        "DRC rule."
    ),
}
