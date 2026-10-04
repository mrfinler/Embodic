"""Electrical element list: phase, series groups, parallel members (interfaces.md section 5)."""

from dataclasses import dataclass

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
class Circuit:
    """Every phase of the winding plus the copper that joins phases (neutral ring, delta links)."""

    phases: tuple[PhaseCircuit, ...]
    topology: ConnectionTopology
    interconnect_path_ids: tuple[int, ...]
