"""Electrical element list: phase, series groups, parallel members (interfaces.md section 5)."""

from collections import Counter
from dataclasses import dataclass
from typing import Literal, TypeAlias

from embodic.model.vocabulary import ConnectionTopology, Phase


@dataclass(frozen=True, slots=True, kw_only=True)
class Member:
    """One conductive route between two group nodes, in current direction (electrical element list)."""

    path_ids: tuple[int, ...]
    via_ids: tuple[int, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class ParallelGroup:
    """Members joined at both ends; the group carries the phase current."""

    members: tuple[Member, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class PhaseCircuit:
    """One phase as parallel groups in series, ending at its terminal net."""

    phase: Phase
    groups: tuple[ParallelGroup, ...]  # in series
    terminal_net: str


@dataclass(frozen=True, slots=True, kw_only=True)
class LineLead:
    """Interconnect copper from a phase end to its line pad; carries the line current (Xcoil lineStub)."""

    kind: Literal["line_lead"] = "line_lead"
    path_id: int
    phase: Phase


@dataclass(frozen=True, slots=True, kw_only=True)
class PhaseLink:
    """Interconnect copper in series with one phase branch: a star tap stub or a whole delta link (Xcoil link)."""

    kind: Literal["phase_link"] = "phase_link"
    path_id: int
    phase: Phase


@dataclass(frozen=True, slots=True, kw_only=True)
class NeutralRing:
    """Star-point ring; the copper between two consecutive taps carries one line current (Xcoil neutralRing)."""

    kind: Literal["neutral_ring"] = "neutral_ring"
    path_id: int
    tap_via_ids: tuple[int, ...]  # tap vias in ring order; the first and the last sit at the ring ends


@dataclass(frozen=True, slots=True, kw_only=True)
class NeutralLead:
    """Interconnect copper from the star point to the neutral pad; no current in a balanced star (Xcoil l.1313)."""

    kind: Literal["neutral_lead"] = "neutral_lead"
    path_id: int


InterconnectRole: TypeAlias = LineLead | PhaseLink | NeutralRing | NeutralLead


@dataclass(frozen=True, slots=True, kw_only=True)
class Circuit:
    """Every phase of the winding plus the copper that joins phases (neutral ring, delta links)."""

    phases: tuple[PhaseCircuit, ...]
    topology: ConnectionTopology
    interconnect_path_ids: tuple[int, ...]
    interconnect_roles: tuple[InterconnectRole, ...] = ()  # empty: built by hand, interconnect not classified

    def __post_init__(self) -> None:
        """Raise ValueError when roles are given and their path ids are not interconnect_path_ids, each exactly once."""
        if not self.interconnect_roles:
            return
        roles = Counter(role.path_id for role in self.interconnect_roles)
        if roles != Counter(self.interconnect_path_ids) or max(roles.values()) > 1:
            raise ValueError(
                f"interconnect roles cover paths {sorted(roles.elements())}, "
                f"expected each of {sorted(self.interconnect_path_ids)} exactly once"
            )
