"""PR-14 on Windows (U-E16): tell a chord-count flip of Ke under rotation from a non-invariance.

Run from the worktree root:
    PYTHONPATH=src:. .venv/bin/python docs/phase3/engineering/checks/pr14_chord_flip_probe.py

For the two failing PR-14 cases (serpentine sharp corners with one turn; wave overlap, turn 1.0) it prints:
1. the Linux Ke of the base and the rotated board and their relative change;
2. every primitive whose ratio L / max_segment_mm lies within FLIP_WINDOW_REL of an integer (a ceil that one rounding
   step can flip), with its distance in ulp;
3. Ke with those chord counts forced down (m chords) and forced up (m + 1 chords), on the base and the rotated board;
   the spread of these values is the most a rotation can move Ke through chord-count flips;
4. Ke after perturbing the rotation angle by a few ulp, which stands in for a different platform's sin and cos.
"""

import math
import sys
from collections.abc import Callable

from tests.unit.generators.serpentine.make_example import example_design
from tests.unit.generators.serpentine.support import with_winding
from tests.unit.generators.wave.designs import wave

import embodic.geometry.discretise as disc
from embodic.generators import build_layout
from embodic.generators.wave.generate import generate_wave_rotated
from embodic.geometry.layout import BoardStack
from embodic.model.design import DesignParameters
from embodic.model.provenance import derive_provenance
from embodic.model.winding_specs import CornerStyle, SerpentineWindingSpec, WaveStyle
from embodic.physics import analyse
from embodic.results import load_registry

REGISTRY = load_registry()
# A designed integer ratio sits a few ulp from the integer; a generic ratio sits about 0.1 to 0.5 away. Anything closer
# than 1e-9 relative is treated as "on the integer" so that no platform's rounding can be missed (the probe prints the
# real distances, which show the separation).
FLIP_WINDOW_REL = 1e-9
WINDOWS = {
    "serpentine": (0.016274993452848437, 0.016274993132285004),
    "wave-overlap": (0.008100672544949162, 0.008100672442611895),
}
_original_piece_count = disc.piece_count


def _near_integer(ratio: float) -> int | None:
    m = round(ratio)
    return m if m >= 1 and abs(ratio - m) <= FLIP_WINDOW_REL * m else None


def _forcing(policy: str, seen: list[tuple[float, float, int]]) -> Callable[..., int]:
    """piece_count that sets every near-integer length ratio to m ('down') or m + 1 ('up'); 'as-is' only records."""

    def piece_count(p, max_segment_mm=disc.DEFAULT_MAX_SEGMENT_MM, *args: float) -> int:  # type: ignore[no-untyped-def]
        n = _original_piece_count(p, max_segment_mm, *args)
        ratio = disc.primitive_length_mm(p) / max_segment_mm
        m = _near_integer(ratio)
        if m is None:
            return n
        seen.append((ratio, (ratio - m) / math.ulp(float(m)), n))
        others = disc.piece_ratios(p, max_segment_mm, *args)[1:]
        floor = max(1, *(math.ceil(r) for r in others)) if others else 1
        if policy == "down":
            return max(floor, m)
        if policy == "up":
            return max(floor, m + 1)
        return n

    return piece_count


def _with_policy(policy: str, run: Callable[[], float]) -> tuple[float, list[tuple[float, float, int]]]:
    seen: list[tuple[float, float, int]] = []
    disc.piece_count = _forcing(policy, seen)
    try:
        return run(), seen
    finally:
        disc.piece_count = _original_piece_count


def _serpentine_ke(design: DesignParameters) -> float:
    stack = build_layout(design, REGISTRY)
    assert isinstance(stack, BoardStack), stack
    analysis = analyse(design, stack, derive_provenance(design, None, ()), REGISTRY)
    assert analysis is not None
    return math.fsum(p.ke_peak_v_s_per_rad.value for p in analysis.phases) / len(analysis.phases)


def _serpentine_case(extra_rad: float) -> Callable[[], float]:
    design = with_winding(example_design(), turns=1, corner_style=CornerStyle.SHARP)
    if extra_rad == 0.0:
        return lambda: _serpentine_ke(design)
    assert isinstance(design.winding, SerpentineWindingSpec)
    delta = 2.0 * math.pi / (design.rotor.poles // 2) + extra_rad
    rotated = with_winding(design, start_angle_rad=design.winding.start_angle_rad + delta)
    return lambda: _serpentine_ke(rotated)


def _wave_case(extra_deg: float) -> Callable[[], float]:
    design = wave(WaveStyle.OVERLAP, poles=8)
    degrees = 0.0 if extra_deg == 0.0 else 360.0 / (design.rotor.poles // 2) + extra_deg

    def run() -> float:
        stack = generate_wave_rotated(design, REGISTRY, degrees)
        assert isinstance(stack, BoardStack)
        result = analyse(design, stack, {}, REGISTRY)
        assert result is not None
        return result.ke_phase_v_s_per_rad.value

    return run


def _rel(a: float, b: float) -> float:
    return (b - a) / a


def _report(name: str, case: Callable[[float], Callable[[], float]], period: float, unit: str) -> None:
    print(f"== {name}")
    base, seen_base = _with_policy("as-is", case(0.0))
    turned, seen_turned = _with_policy("as-is", case(1e-300))  # 1e-300 adds nothing: the exact one-period rotation
    print(f"Linux Ke base {base!r} rotated {turned!r} rel {_rel(base, turned):+.3e}")
    win_base, win_turned = WINDOWS[name]
    print(f"Windows Ke base {win_base!r} rotated {win_turned!r} rel {_rel(win_base, win_turned):+.3e}")
    print(f"Linux base - Windows base rel {_rel(win_base, base):+.3e}")
    for label, seen in (("base", seen_base), ("rotated", seen_turned)):
        ulps = sorted({round(u, 1) for _, u, _ in seen})
        counts = sorted({n for _, _, n in seen})
        print(f"{label}: {len(seen)} near-integer line or arc lengths, distance in ulp {ulps}, chord counts {counts}")
    envelope = {}
    for label, offset in (("base", 0.0), ("rotated", 1e-300)):
        for policy in ("down", "up"):
            envelope[(label, policy)] = _with_policy(policy, case(offset))[0]
            print(f"{label} forced {policy}: Ke {envelope[(label, policy)]!r} rel to Linux base "
                  f"{_rel(base, envelope[(label, policy)]):+.3e}")  # fmt: skip
    values = [*envelope.values(), base, turned]
    spread = (max(values) - min(values)) / base
    print(f"flip envelope (max - min) / Ke = {spread:.3e}")
    inside = all(min(values) - 1e-17 <= v <= max(values) + 1e-17 for v in (win_base, win_turned))
    print(f"Windows values inside the flip envelope: {inside}")
    for k in (1, 2, 4, 8, 64):
        step = k * math.ulp(period)
        ke_plus = case(step)()
        ke_minus = case(-step)()
        plus, minus = _rel(base, ke_plus), _rel(base, ke_minus)
        print(f"rotation {k:>2} ulp off ({step:.1e} {unit}): rel {plus:+.3e} {minus:+.3e}")


if __name__ == "__main__":
    which = sys.argv[1:] or ["serpentine", "wave-overlap"]
    if "serpentine" in which:
        poles = example_design().rotor.poles
        _report("serpentine", _serpentine_case, 2.0 * math.pi / (poles // 2), "rad")
    if "wave-overlap" in which:
        _report("wave-overlap", _wave_case, 360.0 / (wave(WaveStyle.OVERLAP, poles=8).rotor.poles // 2), "deg")
