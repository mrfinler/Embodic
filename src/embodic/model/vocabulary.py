"""Closed choices shared by the design model and the geometry (interfaces.md section 2.1)."""

from enum import StrEnum


class TopologyKind(StrEnum):
    """Winding topology: spiral coils, Xcoil serpentine or Xcoil wave."""

    SPIRAL = "spiral"
    SERPENTINE = "serpentine"
    WAVE = "wave"


class Phase(StrEnum):
    """Electrical phase."""

    A = "A"
    B = "B"
    C = "C"


class ViaSpan(StrEnum):
    """Copper layers a via connects."""

    THROUGH = "through"  # Phase 2 builds through vias only (D-015)


class ConnectionTopology(StrEnum):
    """How the phases join: star, delta or left open."""

    STAR = "star"
    DELTA = "delta"
    OPEN = "open"
