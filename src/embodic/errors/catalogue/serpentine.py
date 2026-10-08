"""Issue messages of the serpentine generator (U-M3a, embodic.generators.serpentine)."""

from collections.abc import Mapping

MESSAGES: Mapping[str, str] = {
    "UNBUILDABLE_SERPENTINE_R_TOO_SMALL": (
        "The inner radius is too small for the nested end turns. Increase the inner radius, reduce the number of "
        "traces, or move the terminals to the outer rim."
    ),
    "UNBUILDABLE_SERPENTINE_ACUTE_CORNER": (
        "The bundle is wider than half the innermost radius, so the corners between the side lines and the end turns "
        "fall below 60 degrees. Use rounded corners, fewer traces or a larger inner radius."
    ),
    "UNBUILDABLE_SERPENTINE_BUNDLE_TOO_WIDE": (
        "The bundle of traces exceeds the pole pitch at the inner radius. Reduce the turns or strands, the trace "
        "width or the clearance, or increase the inner radius."
    ),
    "UNBUILDABLE_SERPENTINE_GEOMETRY": (
        "The radial span between the inner and outer radius is too short for the start via and the fillets, or a "
        "corner does not close. Increase the span or reduce the fillet radius."
    ),
    "UNBUILDABLE_SERPENTINE_COPPER_COUNT": (
        "The stack-up has {limit} copper layers; the winding needs {value}. The stack-up must match the layers per "
        "phase and the stack mode."
    ),
}
