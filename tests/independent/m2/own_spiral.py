"""Own construction of the spiral turn table, turn count and centre via (spiral_generator_spec.md G1, G3, G5).

Written from the spec text, not from embodic or Agent 2's checks/spiral_reference.py. Canonical coil on +x with
half-angle h = pi / Q; parallel sides, arc ends, one layer pair (k = 1).
"""

import math
from dataclasses import dataclass

MAX_TURNS = 100  # D-030 cap (G3 turn-limit refusal)


@dataclass(frozen=True)
class Coil:
    """Coil inputs in mm: Q, copper-edge radii, width, clearance, neighbour gap, via pad, requested turns."""

    q: int
    r_inner: float
    r_outer: float
    w: float
    s: float
    gap: float
    pad: float
    turns: int | None
    min_side: float | None = None

    @property
    def h(self) -> float:
        """Half-angle of the sector in rad."""
        return math.pi / self.q

    @property
    def wd(self) -> float:
        """Turn pitch w + s (G1)."""
        return self.w + self.s

    def d(self, t: int) -> float:
        """Side offset of turn t from the sector edge (G1, gap = max(gap, s))."""
        return max(self.gap, self.s) / 2 + self.w / 2 + t * self.wd

    def r_out(self, t: int) -> float:
        """Outer end radius of turn t (G1)."""
        return self.r_outer - self.w / 2 - t * self.wd

    def r_end(self, t: int) -> float:
        """Inner end radius of turn t: max(R_in,t, apex limit rho_t) (G3 item 3)."""
        half = self.wd / 2
        x_c = (self.d(t) + half * math.cos(self.h)) / math.sin(self.h)
        return max(self.r_inner + self.w / 2 + t * self.wd, math.hypot(x_c, half))

    def right_side(self, t: int, r_low: float) -> float:
        """Length of the right side d_t from the outer end down to radius r_low (G2 parallel line)."""
        d = self.d(t)
        return math.sqrt(self.r_out(t) ** 2 - d**2) - math.sqrt(r_low**2 - d**2)

    def loop_ok(self, t: int) -> bool:
        """G3 loop rule for turn t."""
        min_side = self.min_side if self.min_side is not None else 2 * self.w
        return (
            self.d(t) < self.r_out(t) * math.sin(self.h)
            and self.right_side(t, self.r_end(t)) >= min_side
            and self.r_end(t) < self.r_out(t + 1)
        )

    def n_loop(self) -> int:
        """Return the count of turns passing the loop rule, scanned from turn 0."""
        n = 0
        while n < MAX_TURNS and self.loop_ok(n):
            n += 1
        return n

    def full_via(self, n: int) -> float | None:
        """r_v of the full closing with n turns, or None when the eye does not fit (G5)."""
        t, m, h = n - 1, max(self.pad, self.w) / 2, self.h
        r_lo = max((self.d(t) + self.w / 2 + self.s + m) / math.sin(h), self.r_end(t) + self.w / 2 + self.s + m)
        r_hi = self.r_out(t) - self.w / 2 - self.s - m
        return r_hi if r_hi >= r_lo else None

    def half_via(self, n: int) -> float | None:
        """r_v of the half closing with n turns, or None when a condition 2 to 6 of G5 fails."""
        t, h = n - 1, self.h
        d, r_o = self.d(t), self.r_out(t)
        r_v = d / math.sin(h)
        min_side = self.min_side if self.min_side is not None else 2 * self.w
        below = self.r_end(t - 1) + self.w / 2 + self.s if n > 1 else self.r_inner
        ok = (
            d < r_o * math.sin(h)
            and math.sqrt(r_o**2 - d**2) - d / math.tan(h) >= min_side
            and self.pad <= self.w
            and r_v - self.w / 2 >= below
            and r_v + self.w / 2 + self.s <= r_o - self.w / 2
        )
        return r_v if ok else None

    def plan(self) -> tuple[int, str, float]:
        """Return (turns, closing, r_v): the larger of N_full and N_half, full on a tie (G5 'Choice')."""
        n_loop = self.n_loop()
        cap = self.turns if self.turns is not None else MAX_TURNS
        n_full = next((n for n in range(min(n_loop, cap), 0, -1) if self.full_via(n) is not None), 0)
        n_half = next((n for n in range(min(n_loop + 1, cap), 0, -1) if self.half_via(n) is not None), 0)
        if n_half > n_full:
            return n_half, "half", self.half_via(n_half)
        return n_full, "full", self.full_via(n_full)

    def end_radii(self) -> list[float]:
        """Radii of the end arcs about the origin in path order: outer 0, inner 0, outer 1, ..."""
        n, closing, _ = self.plan()
        radii = []
        for t in range(n):
            radii.append(self.r_out(t))
            if t < n - 1 or closing == "full":
                radii.append(self.r_end(t))
        return radii


def fillet_delta(r: float, d: float, big_r: float, sigma: int) -> float:
    """Length change of one side-to-arc corner filleted at radius r (G9 closed form, sigma -1 inside, +1 outside)."""
    r_c = big_r + sigma * r
    beta_0, beta_c = math.asin(d / big_r), math.asin((d + r) / r_c)
    lam_0, lam_c = math.sqrt(big_r**2 - d**2), math.sqrt(r_c**2 - (d + r) ** 2)
    return r * (math.pi / 2 - sigma * beta_c) - sigma * (lam_c - lam_0) - big_r * (beta_c - beta_0)


def fillet_total(coil: Coil, rho: float) -> float:
    """Sum of G9 corner changes of one coil-layer with full closing: families B, C, D, J, concentric radii."""
    n, closing, _ = coil.plan()
    assert closing == "full"
    trapezoids = [t for t in range(n) if coil.r_end(t) == coil.r_inner + coil.w / 2 + t * coil.wd]
    total = 0.0
    for t in range(n):  # B: outer arc t into right side t
        total += fillet_delta(rho + (n - 1 - t) * coil.wd, coil.d(t), coil.r_out(t), -1)
    for t in range(n - 1):  # J: left side t into outer arc t + 1
        total += fillet_delta(rho + (n - 2 - t) * coil.wd, coil.d(t), coil.r_out(t + 1), -1)
    last = trapezoids[-1]
    for t in trapezoids:  # C and D: both corners of the inner end
        total += 2 * fillet_delta(rho + (last - t) * coil.wd, coil.d(t), coil.r_end(t), +1)
    return total
