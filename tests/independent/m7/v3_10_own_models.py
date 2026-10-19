"""V3-10: Agent 4's own models against the product on the five packaged examples (verification_plan.md part 3).

Run from the repository root with the dev venv and ``PYTHONPATH=src``:

    python tests/independent/m7/v3_10_own_models.py [--json out.json]

The product side is ``compute_project`` on each packaged example, the path ``embodic-cli compute`` takes, plus the
spiral winding plan the generator uses. The own side imports nothing from embodic for its expected values:

- star of slots and k_w,n: ``m2/own_winding.py`` (exact Fractions, EQ-08 text), against ``plan_spiral_winding``;
- Ke_LL peak: the EQ-05 field written here from equation_specification.md (EQ-04 alpha_p(r) for block magnets, the
  double-rotor G = (t_s + 2 g) / 2), EQ-06 flux linkage and the line peak from ``m2/own_emf.py``, walked over the
  product's copper paths at the product's copper z (the M3 deviation: geometry is the subject's, arithmetic is own);
- DRC: each board through the product's dump writer, M1's reader and M1's certified pair sweep under the section 7
  exemptions (``m3/drc_m3.universe``, ``m1/drc_universe``), with the rule of each pair kind read from the design's
  drc_rules by the interfaces.md section 7 table.
"""

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
for sub in ("m1", "m2", "m3"):
    sys.path.insert(0, str(REPO / "tests" / "independent" / sub))

import own_emf  # noqa: E402
import own_winding  # noqa: E402
from board_dump_reader import parse_board_dump  # noqa: E402
from brute_clearance import Verdict  # noqa: E402
from drc_m3 import universe  # noqa: E402
from drc_universe import contract_exemptions, sweep  # noqa: E402

from embodic.api import compute_project  # noqa: E402
from embodic.io.board_dump import dump_layout, encode_board_dump  # noqa: E402
from embodic.results import load_registry  # noqa: E402
from embodic.winding.plan import plan_spiral_winding  # noqa: E402

EXAMPLES = REPO / "resources" / "examples"
STEP_MM = 0.05
KE_BOUND_REL = 1e-4  # the plan's bound, an assumption this run settles
KW_BOUND_ABS = 1e-12
EQ18_SAMPLES = 181  # EQ-18 names Xcoil emfWaveform; engine.js l.1021-1025 samples 0 to 2 pi on 181 points
# interfaces.md section 7, rule per check kind
RULE_FIELD = {
    "trace_trace": "trace_clearance_mm",
    "pad_trace": "trace_clearance_mm",
    "trace_via": "via_clearance_mm",
    "via_via": "via_clearance_mm",
    "pad_pad": "via_clearance_mm",
    "copper_edge": "edge_clearance_mm",
    "copper_hole": "hole_clearance_mm",
}


@dataclass(frozen=True)
class OwnField:
    """EQ-05 of one double rotor, with alpha_p constant (arc magnets) or EQ-04's alpha_p(r) (block magnets)."""

    poles: int
    remanence_t: float
    mu_r: float
    magnet_mm: float
    g_plane_mm: float
    r_a_mm: float
    r_b_mm: float
    alpha: float | None  # arc magnets
    block_width_mm: float | None  # block magnets
    table_steps: int = 0  # 0: exact at every chord; N: linear interpolation on N + 1 radii of the span (experiment)

    def alpha_p(self, r_mm: np.ndarray) -> np.ndarray:
        """EQ-04: alpha_p(r) = 2 p asin(w / (2 r)) / pi for blocks; the constant ratio for arcs."""
        if self.block_width_mm is None:
            return np.full_like(r_mm, self.alpha)
        return 2 * (self.poles // 2) * np.arcsin(self.block_width_mm / (2 * r_mm)) / math.pi

    def bz(self, n: int, r_mm: np.ndarray, z_mm: float) -> np.ndarray:
        """Peak B_z,n in T at radii r_mm and distance z_mm; with table_steps, interpolated from a radial table."""
        if self.table_steps:
            grid = self.r_a_mm + (self.r_b_mm - self.r_a_mm) * np.arange(self.table_steps + 1) / self.table_steps
            return np.interp(r_mm, grid, self.exact_bz(n, grid, z_mm))
        return self.exact_bz(n, r_mm, z_mm)

    def exact_bz(self, n: int, r_mm: np.ndarray, z_mm: float) -> np.ndarray:
        """Peak B_z,n in T at radii r_mm and distance z_mm from the magnet face (EQ-05 cosh/sinh form)."""
        u = n * (self.poles // 2) / r_mm
        k_n = 4 * self.remanence_t / (n * math.pi) * np.sin(n * math.pi * self.alpha_p(r_mm) / 2)
        g = self.g_plane_mm
        den = np.cosh(u * g) + self.mu_r / np.tanh(u * self.magnet_mm) * np.sinh(u * g)
        return k_n * np.cosh(u * (g - z_mm)) / den


def _v(x: object) -> object:
    """Return an enum's value, or the value itself when the model stores a plain string."""
    return getattr(x, "value", x)


def own_field(design: object, stack: object, table_steps: int = 0) -> OwnField:
    """EQ-05 inputs from the design's rotor and the stack's thickness t_s."""
    rotor = design.rotor
    assert _v(rotor.rotor_type) == "double", rotor.rotor_type
    n = len(stack.boards)
    t_s = n * stack.board_thickness_mm + (n - 1) * stack.board_gap_mm
    magnet = rotor.magnet
    if _v(magnet.kind) == "block":
        span = (magnet.r_center_mm - magnet.length_mm / 2, magnet.r_center_mm + magnet.length_mm / 2)
        alpha, width = None, magnet.width_mm
    else:
        span, alpha, width = (magnet.r_inner_mm, magnet.r_outer_mm), magnet.pole_arc_ratio, None
    return OwnField(
        poles=rotor.poles,
        remanence_t=rotor.remanence_t,
        mu_r=rotor.recoil_permeability,
        magnet_mm=magnet.thickness_mm,
        g_plane_mm=(t_s + 2 * rotor.air_gap_mm) / 2,
        r_a_mm=span[0],
        r_b_mm=span[1],
        alpha=alpha,
        block_width_mm=width,
        table_steps=table_steps,
    )


def own_ke_ll_peak(
    design: object, stack: object, table_steps: int = 0, chord_mm: float = STEP_MM, samples: int = 0
) -> float:
    """Own Ke_LL peak in V s/rad: series groups add, parallel members average (as m3/gr22_own.py).

    ``samples`` 0 takes the peak of the continuous line waveform (own_emf, 7201 points per electrical period).
    ``samples`` N takes the largest |E| on N points from 0 to 2 pi electrical inclusive, the grid EQ-18 names
    (Xcoil emfWaveform, engine.js l.1020-1028, 181 points), with E(theta) = sum_n |E_n| cos(n theta + arg E_n).
    """
    field = own_field(design, stack, table_steps)
    harmonics = design.analysis.harmonics
    lam: dict[str, np.ndarray] = {}
    for layout in stack.boards:
        by_id = {p.id: p for p in layout.paths}
        for phase in layout.circuit.phases:
            total = lam.setdefault(_v(phase.phase), np.zeros(len(harmonics), dtype=np.complex128))
            for group in phase.groups:
                members = [
                    sum(
                        own_emf.path_flux_linkage(
                            by_id[i].primitives,
                            field,
                            design.rotor.air_gap_mm + layout.copper_z_mm[by_id[i].layer],
                            harmonics,
                            chord_mm,
                        )
                        for i in m.path_ids
                    )
                    for m in group.members
                ]
                total += sum(members) / len(members)
    if not samples:
        return own_emf.line_peak_v_s_per_rad(lam["A"], lam["B"], harmonics, field.poles)
    line = lam["A"] - lam["B"]
    theta = 2 * math.pi * np.arange(samples) / (samples - 1)
    wave = sum(abs(line[i]) * np.cos(n * theta + np.angle(line[i])) for i, n in enumerate(harmonics))
    return float(np.max(np.abs(wave))) * 1e-6


def winding_check(design: object) -> dict[str, object]:
    """Own star of slots and k_w,n against the product's spiral winding plan."""
    spec = design.winding
    q, poles = spec.coil.coil_count, design.rotor.poles
    plan = plan_spiral_winding(design, spec, load_registry())
    product = [(_v(c.phase), int(c.polarity)) for c in plan.assignment]
    own = own_winding.star_of_slots(q, poles)
    kw = {n: (own_winding.winding_factor(q, poles, n), plan.winding_factors[n].value) for n in plan.winding_factors}
    worst = max(abs(a - b) for a, b in kw.values())
    return {
        "coils": q,
        "poles": poles,
        "phases_equal": product == own,
        "pattern": plan.pattern,
        "kw_1_own": kw[1][0],
        "kw_1_product": kw[1][1],
        "kw_harmonics": sorted(kw),
        "kw_worst_abs": worst,
        "kw_pass": worst <= KW_BOUND_ABS,
    }


def drc_check(design: object, outcome: object) -> list[dict[str, object]]:
    """Brute violation pairs against the product's reported pair violations, board by board."""
    rules = design.drc_rules
    out = []
    for k, (layout, report) in enumerate(zip(outcome.boards.boards, outcome.drc, strict=True)):
        dump = parse_board_dump(json.loads(encode_board_dump(dump_layout(layout, case_id=f"board{k}"))))
        items = universe(dump)
        exempt = contract_exemptions(items, frozenset(layout.circuit.interconnect_path_ids))
        found = sweep(items, range(len(dump.layers)), lambda kind: getattr(rules, RULE_FIELD[kind]), exempt)
        undecided = [r for r in found if r.verdict is Verdict.UNDECIDED]
        brute = {frozenset((r.a, r.b)): r.kind for r in found if r.verdict is Verdict.VIOLATION}
        engine = {frozenset(v.objects): v.kind.value for v in report.violations if v.kind.value in RULE_FIELD}
        other = sorted({v.kind.value for v in report.violations if v.kind.value not in RULE_FIELD})
        out.append(
            {
                "board": k,
                "engine_total": report.violation_count,
                "engine_listed": len(report.violations),
                "engine_pairs": len(engine),
                "engine_non_pair_kinds": other,
                "brute_pairs": len(brute),
                "undecided": len(undecided),
                "engine_only": sorted(sorted(p) for p in engine.keys() - brute.keys())[:10],
                "brute_only": sorted(sorted(p) for p in brute.keys() - engine.keys())[:10],
                "kinds_differ": sorted(sorted(p) for p in engine.keys() & brute.keys() if engine[p] != brute[p])[:10],
                "sets_equal": engine.keys() == brute.keys() and not undecided,
            }
        )
    return out


def check(example: Path) -> dict[str, object]:
    """Run the three comparisons on one packaged example."""
    outcome = compute_project(example)
    assert not isinstance(outcome, tuple), outcome
    design, stack = outcome.design, outcome.boards
    product_ke = outcome.analysis.ke_line_peak_v_s_per_rad.value
    own_ke = own_ke_ll_peak(design, stack, samples=EQ18_SAMPLES)
    own_continuous = own_ke_ll_peak(design, stack)
    row: dict[str, object] = {
        "example": example.name.removesuffix(".embodic.json"),
        "topology": _v(design.winding.kind) if hasattr(design.winding, "kind") else "spiral",
        "ke_own": own_ke,
        "ke_product": product_ke,
        "ke_rel": product_ke / own_ke - 1,
        "ke_pass": abs(product_ke / own_ke - 1) <= KE_BOUND_REL,
        "ke_own_continuous": own_continuous,
        "ke_rel_continuous": product_ke / own_continuous - 1,
        "drc": drc_check(design, outcome),
    }
    row["winding"] = winding_check(design) if hasattr(design.winding, "coil") else None
    return row


def explain_ke(example: str) -> None:
    """Print own Ke_LL with finer chords and with an own 48-step linear field table, to find what limits the gap."""
    outcome = compute_project(EXAMPLES / f"{example}.embodic.json")
    assert not isinstance(outcome, tuple), outcome
    product = outcome.analysis.ke_line_peak_v_s_per_rad.value
    for label, steps, chord in (("exact, 0.05 mm chords", 0, 0.05), ("exact, 0.02 mm chords", 0, 0.02),
                                ("48-step linear table, 0.05 mm chords", 48, 0.05)):  # fmt: skip
        own = own_ke_ll_peak(outcome.design, outcome.boards, steps, chord)
        print(f"{example} own {label}: {own:.10g}, product {product:.10g}, rel {product / own - 1:+.3e}")


def main(argv: list[str] | None = None) -> int:
    """Print one line per example and comparison; --json writes every row; --explain runs the Ke_LL experiment."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", type=Path)
    parser.add_argument("--explain", nargs="*", default=None, help="example ids for the Ke_LL limiter experiment")
    args = parser.parse_args(argv)
    if args.explain is not None:
        for example in args.explain:
            explain_ke(example)
        return 0
    rows = [check(p) for p in sorted(EXAMPLES.glob("*.embodic.json"))]
    for r in rows:
        print(
            f"{r['example']}: Ke_LL own (181-point peak) {r['ke_own']:.10g} product {r['ke_product']:.10g} "
            f"rel {r['ke_rel']:+.3e}; own continuous peak {r['ke_own_continuous']:.10g} "
            f"rel {r['ke_rel_continuous']:+.3e}"
        )
        if r["winding"]:
            w = r["winding"]
            print(
                f"    star {w['pattern']} phases equal {w['phases_equal']}; k_w1 own {w['kw_1_own']:.15g} "
                f"product {w['kw_1_product']:.15g}; worst |dk_w| {w['kw_worst_abs']:.2e} over n={w['kw_harmonics']}"
            )
        for b in r["drc"]:
            print(
                f"    board {b['board']}: engine {b['engine_total']} ({b['engine_pairs']} pair, other kinds "
                f"{b['engine_non_pair_kinds']}), brute {b['brute_pairs']}, undecided {b['undecided']}, "
                f"pair sets equal {b['sets_equal']}"
            )
            for key in ("engine_only", "brute_only", "kinds_differ"):
                if b[key]:
                    print(f"      {key}: {b[key]}")
    if args.json:
        args.json.write_text(json.dumps(rows, indent=1, default=str) + "\n", encoding="utf-8")
    ok = all(
        all(b["sets_equal"] for b in r["drc"]) and (r["winding"] is None or (r["winding"]["phases_equal"]
        and r["winding"]["kw_pass"])) and r["ke_pass"] for r in rows
    )  # fmt: skip
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
