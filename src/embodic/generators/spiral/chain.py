"""Series chain of the coils of one phase on the bus rings outside r_outer (spiral_generator_spec.md G8).

Port of Xcoil ``chainCoils`` (engine.js l.2330): a depth-first search over coil orders that prefers short links and
few ring levels; a link arc never passes over a ring via of its own level, and never has another link's end strictly
inside it on the same level.
"""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType

from embodic.generators.spiral.turns import CoilFrame

MAX_LEVELS = 4  # Xcoil tries 1 to 4 levels per phase
_EPS_RAD = 1e-9


def norm_angle(a_rad: float) -> float:
    """Angle in [0, 2 pi) (Xcoil ``angNorm``)."""
    a_rad = math.fmod(a_rad, 2 * math.pi)
    return a_rad + 2 * math.pi if a_rad < 0 else a_rad


def _inside(a_rad: float, start_rad: float, sweep_rad: float) -> bool:
    d = norm_angle(a_rad - start_rad)
    return _EPS_RAD < d < sweep_rad - _EPS_RAD


@dataclass(frozen=True, slots=True, kw_only=True)
class CoilEnds:
    """Angles of a coil's entry and exit terminal vias, in [0, 2 pi)."""

    coil: int
    entry_rad: float
    exit_rad: float


class Turning(StrEnum):
    """Which way a link runs from the exit of one coil to the entry of the next."""

    CCW = "ccw"
    CW = "cw"


class End(StrEnum):
    """Which terminal of a coil a ring via serves."""

    ENTRY = "entry"
    EXIT = "exit"


@dataclass(frozen=True, slots=True, kw_only=True)
class Link:
    """Ring arc from ``from_coil``'s exit to ``to_coil``'s entry; ``start_rad`` and ``sweep_rad`` > 0 are CCW."""

    from_coil: int
    to_coil: int
    start_rad: float
    sweep_rad: float
    level: int  # local level l of the phase; the bus level is phase + m l
    turning: Turning

    @property
    def signed_sweep_rad(self) -> float:
        """Sweep in current direction, from the exit angle toward the entry angle."""
        return self.sweep_rad if self.turning is Turning.CCW else -self.sweep_rad


@dataclass(frozen=True, slots=True, kw_only=True)
class PhaseChain:
    """Coil order, links and the local level of every terminal's ring via."""

    order: tuple[int, ...]
    links: tuple[Link, ...]
    levels: Mapping[tuple[int, End], int]
    n_levels: int


def chain_coils(coils: Sequence[CoilEnds]) -> PhaseChain | None:
    """Shortest chain through ``coils`` with the fewest levels up to MAX_LEVELS; None when no level count routes it."""
    for n_levels in range(1, MAX_LEVELS + 1):
        if chain := _Search(coils, n_levels).run():
            return chain
    return None


class _Search:
    """Depth-first search of one level count; local coil indices, keys (index, End) for the ring via levels."""

    def __init__(self, coils: Sequence[CoilEnds], n_levels: int) -> None:
        self.coils, self.n_levels = coils, n_levels
        self.best: tuple[float, PhaseChain] | None = None
        self.order: list[int] = []
        self.used = [False] * len(coils)
        self.links: list[Link] = []
        self.via_level: dict[tuple[int, End], int] = {}

    def run(self) -> PhaseChain | None:
        for start in range(len(self.coils)):
            self.order, self.used[start] = [start], True
            self._dfs(0.0)
            self.used[start] = False
        return None if self.best is None else self.best[1]

    def _angle(self, key: tuple[int, End]) -> float:
        c = self.coils[key[0]]
        return c.entry_rad if key[1] is End.ENTRY else c.exit_rad

    def _covered(self, a_rad: float, level: int) -> bool:
        return any(k.level == level and _inside(a_rad, k.start_rad, k.sweep_rad) for k in self.links)

    def _free_level(self, a_rad: float) -> int | None:
        return next((lv for lv in range(self.n_levels) if not self._covered(a_rad, lv)), None)

    def _level_takes(self, level: int, start_rad: float, sweep_rad: float, exit_rad: float, entry_rad: float) -> bool:
        """No ring via of this level inside the new arc, and neither arc end inside a link of this level."""
        vias_clear = not any(
            v == level and _inside(self._angle(k), start_rad, sweep_rad) for k, v in self.via_level.items()
        )
        return vias_clear and not self._covered(exit_rad, level) and not self._covered(entry_rad, level)

    def _finish(self, total: float) -> None:
        first = self._free_level(self.coils[self.order[0]].entry_rad)
        last = self._free_level(self.coils[self.order[-1]].exit_rad)
        if first is None or last is None:
            return
        levels = {**self.via_level, (self.order[0], End.ENTRY): first, (self.order[-1], End.EXIT): last}
        chain = PhaseChain(
            order=tuple(self.coils[i].coil for i in self.order),
            links=tuple(self.links),
            levels=MappingProxyType({(self.coils[i].coil, end): lv for (i, end), lv in levels.items()}),
            n_levels=self.n_levels,
        )
        self.best = (total, chain)

    def _candidates(self, exit_rad: float) -> list[tuple[int, Turning]]:
        """Nearest unvisited coil counter-clockwise and clockwise from the exit terminal."""
        free = [c for c in range(len(self.coils)) if not self.used[c]]
        ccw = min(free, key=lambda c: norm_angle(self.coils[c].entry_rad - exit_rad))
        cw = min(free, key=lambda c: norm_angle(exit_rad - self.coils[c].entry_rad))
        return [(ccw, Turning.CCW), (cw, Turning.CW)]

    def _dfs(self, total: float) -> None:
        if self.best is not None and total >= self.best[0]:
            return
        if len(self.order) == len(self.coils):
            self._finish(total)
            return
        here = self.order[-1]
        exit_rad = self.coils[here].exit_rad
        for target, turning in self._candidates(exit_rad):
            entry_rad = self.coils[target].entry_rad
            if turning is Turning.CCW:
                start_rad, sweep_rad = exit_rad, norm_angle(entry_rad - exit_rad)
            else:
                start_rad, sweep_rad = entry_rad, norm_angle(exit_rad - entry_rad)
            if sweep_rad < _EPS_RAD:
                continue
            for lv in range(self.n_levels):
                if not self._level_takes(lv, start_rad, sweep_rad, exit_rad, entry_rad):
                    continue
                link = Link(
                    from_coil=self.coils[here].coil,
                    to_coil=self.coils[target].coil,
                    start_rad=start_rad,
                    sweep_rad=sweep_rad,
                    level=lv,
                    turning=turning,
                )
                self._descend(here, target, link, total)

    def _descend(self, here: int, target: int, link: Link, total: float) -> None:
        self.via_level[(here, End.EXIT)] = link.level
        self.via_level[(target, End.ENTRY)] = link.level
        self.used[target] = True
        self.order.append(target)
        self.links.append(link)
        self._dfs(total + link.sweep_rad)
        self.links.pop()
        self.order.pop()
        self.used[target] = False
        del self.via_level[(here, End.EXIT)]
        del self.via_level[(target, End.ENTRY)]


@dataclass(frozen=True, slots=True, kw_only=True)
class BusRings:
    """G8 bus level radii r_ring(l) = r_T + max(pad, w)/2 + s + max(bw, pad)/2 + l (max(bw, pad) + s)."""

    base_mm: float
    pitch_mm: float
    half_width_mm: float  # max(bw, pad)/2: ring vias and bus share each level
    ring_width_mm: float  # bw
    leg_width_mm: float  # min(bw, pad), Xcoil buildSector

    @classmethod
    def of(cls, frame: CoilFrame, bus_width_mm: float) -> "BusRings":
        """Levels outside the terminal ring r_T = r_outer + s + pad/2 of ``frame``."""
        s, pad = frame.clearance_mm, frame.via_pad_mm
        half = max(bus_width_mm, pad) / 2
        r_t = frame.r_outer_mm + s + pad / 2
        return cls(
            base_mm=r_t + max(pad, frame.trace_width_mm) / 2 + s + half,
            pitch_mm=2 * half + s,
            half_width_mm=half,
            ring_width_mm=bus_width_mm,
            leg_width_mm=min(bus_width_mm, pad),
        )

    def radius_mm(self, level: int) -> float:
        """Radius of bus level ``level`` (phase + m l)."""
        return self.base_mm + level * self.pitch_mm
