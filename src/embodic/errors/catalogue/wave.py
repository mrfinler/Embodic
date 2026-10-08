"""Issue messages of the wave generator (U-M3b, embodic.generators.wave)."""

from collections.abc import Mapping

MESSAGES: Mapping[str, str] = {
    "UNBUILDABLE_WAVE_MIN_POLES": "The interleaved wave winding needs at least 4 poles to place the phase terminals.",
    "UNBUILDABLE_WAVE_SLOT_PITCH": (
        "The radial conductors do not fit at this radius and turn count. Reduce the turns or the trace width, "
        "or increase the inner radius."
    ),
    "UNBUILDABLE_WAVE_OUTER_TIGHT": (
        "The outer end-turns cannot be spaced at the required pitch. Reduce the turns, the outer end-turn width or "
        "the via pad."
    ),
    "UNBUILDABLE_WAVE_INNER_TIGHT": (
        "The inner end-turns cannot be spaced at the required pitch. Reduce the turns, the inner end-turn width or "
        "the via pad, or increase the inner radius."
    ),
    "UNBUILDABLE_WAVE_LINK_ROOM": (
        "There is no room inside the inner via ring for the group links. Increase the inner radius, or reduce the "
        "bus width or the via pad."
    ),
    "UNBUILDABLE_WAVE_LAYER_COUNT": "The wave winding needs an even number of copper layers, at least 2 (T/B pairs).",
    "INVALID_WAVE_COPPER_COUNT": (
        "The wave winding needs an even number of copper layers, from 2 to {limit} (T/B pairs)."
    ),
    "UNBUILDABLE_WAVE_INPUT_OUT_OF_RANGE": "A wave winding input is outside the range the geometry can use.",
    "UNBUILDABLE_WAVE_INTERCONNECT_CROSSING": "The delta links cross, and the ring layers cannot carry crossing links.",
}
