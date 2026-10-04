"""Issue messages of the DRC (U-M1c): one DRC_ code per DrcCheckKind and the DrcRules validation codes."""

from collections.abc import Mapping

MESSAGES: Mapping[str, str] = {
    "DRC_TRACE_TRACE": "Two traces are closer than the trace clearance rule.",
    "DRC_TRACE_VIA": "A trace is closer to a via than the via clearance rule.",
    "DRC_VIA_VIA": "Two vias are closer than the via clearance rule.",
    "DRC_PAD_TRACE": "A trace is closer to a pad than the trace clearance rule.",
    "DRC_PAD_PAD": "A pad is closer to another pad or a via than the via clearance rule.",
    "DRC_COPPER_EDGE": "Copper is closer to the board edge or a cutout than the edge clearance rule.",
    "DRC_COPPER_HOLE": "Copper is closer to a screw hole than the hole clearance rule.",
    "DRC_MIN_WIDTH": "A trace is narrower than the minimum trace width.",
    "DRC_MIN_DRILL": "A drill is smaller than the minimum drill diameter.",
    "DRC_ANNULAR_RING": "A via or pad ring is narrower than the minimum annular ring.",
    "INVALID_DRC_RULE_NOT_FINITE": "A DRC rule must be a finite number.",
    "INVALID_DRC_RULE_NEGATIVE": "A DRC rule cannot be negative.",
}
