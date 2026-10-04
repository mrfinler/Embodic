"""Analysis options (interfaces.md section 2.1)."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True, kw_only=True)
class AnalysisOptions:
    """Harmonics evaluated, path discretisation and the EC-05 correction switch."""

    harmonics: tuple[int, ...] = (1, 3, 5, 7, 9, 11, 13)  # odd only
    max_segment_mm: float = 0.5
    edge_correction: Literal["off"] = "off"  # EC-05 optional correction stays off in Phase 2
