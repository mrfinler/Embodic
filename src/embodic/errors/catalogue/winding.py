"""Issue messages of the spiral phase plan (U-M2c, embodic.winding)."""

from collections.abc import Mapping

MESSAGES: Mapping[str, str] = {
    "UNBUILDABLE_UNBALANCED_WINDING": (
        "The star of slots gives no balanced 3-phase winding for this coil count and pole count."
    ),
    "UNBUILDABLE_PARALLEL_PATHS_EXCEED_T": (
        "The number of parallel paths exceeds the machine periodicity t = gcd(Q, p) = {limit}."
    ),
    "UNBUILDABLE_ASSIGNMENT_COVERAGE": "The manual phase assignment must list every coil index from 0 to Q - 1 once.",
    "RANGE_DELTA_TRIPLEN": (
        "Delta connection with a third-harmonic winding factor that is not zero drives a circulating current."
    ),
    "RANGE_MANUAL_ASSIGNMENT_UNBALANCED": (
        "The manual phase assignment is not balanced; the value is the spread of the phase EMF phasor magnitudes."
    ),
}
