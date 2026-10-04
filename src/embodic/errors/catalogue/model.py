"""Issue messages of the design model: field checks, cross-field rules and draft parsing (U-M2a).

Templates take `{limit}` and `{unit}` where a message names a limit. Sources: Xcoil normalizeParams messages
(engine.js l.107-160), screens.md validation texts, test_plan BV-01 to BV-03 and BV-06 codes.
"""

from collections.abc import Mapping

MESSAGES: Mapping[str, str] = {
    "INVALID_TYPE": "The value is not a finite number of the expected kind.",
    "INVALID_NOT_INTEGER": "The value must be a whole number.",
    "INVALID_CHOICE": "The value is not one of the available options.",
    "INVALID_EMPTY_TEXT": "Enter a name.",
    "INVALID_NON_POSITIVE": "The value must be greater than 0{unit}.",
    "INVALID_NEGATIVE": "The value must be 0{unit} or more.",
    "INVALID_LIST_SHAPE": "The list has missing or extra entries.",
    "RANGE_BELOW_SUPPORTED": "The value is below the supported minimum of {limit}{unit}.",
    "RANGE_ABOVE_SUPPORTED": "The value is above the supported maximum of {limit}{unit}.",
    "INVALID_POLE_COUNT_ODD": "Poles must be an even number of 2 or more.",
    "INVALID_ORDER": "Outer radius must be larger than the inner radius.",
    "INVALID_RADIAL_SPAN": "Outer radius must exceed inner radius by at least {limit} mm.",
    "INVALID_MAGNET_ORDER": "Magnet outer radius must exceed magnet inner radius.",
    "INVALID_LAYERS_PER_PHASE": "Layers per phase must be 1 or an even number (X/Y layer pairs).",
    "INVALID_SERIES_PAIRS_EXCEED_POLE_PAIRS": (
        "Series connection supports at most p layer pairs (p = pole pairs): each pair is rotated by two pole pitches."
    ),
    "RANGE_TOO_MANY_TRACES": "Total traces (turns x strands) exceed {limit}.",
    "INVALID_VIA_RING": "Via pad diameter must exceed the drill by at least {limit} mm (annular ring).",
    "INVALID_TERMINAL_PAD_RING": "Terminal pad must exceed its drill by at least {limit} mm.",
    "INVALID_SPIRAL_PHASES": "Spiral coils need 3 phases.",
    "INVALID_END_WIDTH_BELOW_TRACE": "End-turn width must be at least the trace width ({limit} mm).",
    "INVALID_STACKUP_NO_COPPER": "The stack-up needs at least one copper layer.",
    "INVALID_LAYER_NAME_DUPLICATE": "Each layer needs its own name.",
    "INVALID_PAIR_LAYER_UNKNOWN": "A layer pair refers to a copper layer that is not in the stack-up.",
    "INVALID_PAIR_LAYER_SAME": "A layer pair needs two different copper layers.",
    "INVALID_PAIR_INDEX_DUPLICATE": "Each layer pair needs its own index.",
    "INVALID_SERIES_GROUPS": "Series groups must list every layer pair index exactly once.",
    "INVALID_HARMONIC": "Harmonic orders must be odd and positive.",
}
