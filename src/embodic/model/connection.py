"""Phase connection and on-board interconnect inputs (interfaces.md section 2.1)."""

from dataclasses import dataclass

from embodic.model.vocabulary import ConnectionTopology


@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionSpec:
    """Star, delta or open phases, the interconnect ring and the terminal pads."""

    topology: ConnectionTopology = ConnectionTopology.STAR  # D-015 default
    draw_interconnect: bool = True
    ring_width_mm: float
    terminal_pad_mm: float
    terminal_drill_mm: float  # 0 = SMD pad
    neutral_pad: bool = False
