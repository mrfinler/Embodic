"""Issue messages of the spiral phase plan (U-M2c, embodic.winding)."""

from collections.abc import Mapping

MESSAGES: Mapping[str, str] = {
    "UNBUILDABLE_ASYMMETRIC_WINDING": "No symmetric 3-phase pattern exists for this coil count and pole count.",
    "UNBUILDABLE_PARALLEL_PATHS_NOT_DIVISOR": (
        "The number of parallel paths must divide the machine periodicity t = gcd(Q, p) = {limit}."
    ),
    "UNBUILDABLE_ASSIGNMENT_COVERAGE": "The manual phase assignment must list every coil index from 0 to Q - 1 once.",
    "RANGE_DELTA_TRIPLEN": (
        "Delta connection with a third-harmonic winding factor that is not zero drives a circulating current."
    ),
    "RANGE_MANUAL_ASSIGNMENT_ASYMMETRIC": (
        "The manual phase assignment is not a symmetric 3-phase pattern; the value is the relative spread of the three "
        "phase phasor sums, each coil counted as a unit phasor."
    ),
}
