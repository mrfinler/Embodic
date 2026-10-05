# Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5
# Reference model of the spiral-coil generator rules in spiral_generator_spec.md (steps G1-G9; G3-G5 revision 2026-10-05, U-E3;
# G5 half closing revision 2026-10-05, U-E3b).
# not product code: it prints every intermediate number of the two worked examples (default 12/16 and D08 12/10).
# Geometry: canonical coil centred on the +x axis, half-angle h = pi/Q, left sector edge at +h (y > 0), right edge at -h.
# Run: python3 docs/phase2/engineering/checks/spiral_reference.py [--json]
import json
import math
import sys
from math import gcd

RHO20 = 1.7241e-8      # ohm*m, IACS (EV-53)
ALPHA20 = 0.00393      # 1/K (EV-53)
BELT_NAMES = ["A", "c", "B", "a", "C", "b"]   # 60-degree belts: A+, -C, B+, -A, C+, -B (uppercase = positive coil)


def star_of_slots(Q, p, m=3):
    """Exact integer star of slots (step G7). Angles are integers in units of 360/(12 Q) degrees."""
    if m != 3:
        raise ValueError("reference model covers m = 3 only")
    unit = 12 * Q                      # one electrical revolution
    coils = []
    for k in range(Q):
        a = (12 * k * p) % unit        # electrical angle of coil k
        belt = ((a + Q) // (2 * Q)) % 6   # half-open belts [c - 30 deg, c + 30 deg)
        on_edge = (a + Q) % (2 * Q) == 0
        phase = {0: 0, 3: 0, 2: 1, 5: 1, 4: 2, 1: 2}[belt]
        sign = 1 if belt in (0, 2, 4) else -1
        coils.append({"coil": k, "angle_units": a, "belt": belt, "phase": "ABC"[phase], "sign": sign,
                      "label": BELT_NAMES[belt], "on_belt_edge": on_edge})
    t = gcd(Q, p)
    feasible = Q % 3 == 0 and (Q // t) % 3 == 0 and Q != 2 * p

    def signed_set(ph):
        return sorted((c["angle_units"] + (0 if c["sign"] > 0 else 6 * Q)) % unit for c in coils if c["phase"] == ph)
    sa, sb, sc = signed_set("A"), signed_set("B"), signed_set("C")
    shift = lambda s, d: sorted((x + d) % unit for x in s)
    balanced = len(sa) == len(sb) == len(sc) and sb == shift(sa, 4 * Q) and sc == shift(sa, 8 * Q)
    nA = len(sa)
    kd1 = abs(sum(complex(math.cos(x * 2 * math.pi / unit), math.sin(x * 2 * math.pi / unit)) for x in sa)) / nA
    return {"pattern": "".join(c["label"] for c in coils), "t": t, "feasible_rule": feasible, "balanced_exact": balanced,
            "coils_per_phase": nA, "kd1": kd1, "belt_edge_coils": sum(c["on_belt_edge"] for c in coils), "coils": coils}


class Geo:
    def __init__(self, Q, r_inner, r_outer, w, s, gap, pad, bw=1.0, w_out=None, w_in=None):
        self.Q, self.h = Q, math.pi / Q
        self.w, self.s, self.pad, self.bw = w, s, pad, bw
        self.w_out, self.w_in = w_out or w, w_in or w
        self.gap = max(gap, s)
        self.r_inner, self.r_outer = r_inner, r_outer
        self.Ro0, self.Ri0 = r_outer - self.w_out / 2, r_inner + self.w_in / 2
        self.wd, self.wd_out, self.wd_in = w + s, self.w_out + s, self.w_in + s
        h = self.h
        self.uR, self.nR = (math.cos(h), -math.sin(h)), (math.sin(h), math.cos(h))
        self.uL, self.nL = (math.cos(h), math.sin(h)), (math.sin(h), -math.cos(h))

    def d(self, t):
        return self.gap / 2 + self.w / 2 + t * self.wd

    def R_out(self, t):
        return self.Ro0 - t * self.wd_out

    def R_in(self, t):
        return self.Ri0 + t * self.wd_in

    def on_R(self, d, lam):
        return (lam * self.uR[0] + d * self.nR[0], lam * self.uR[1] + d * self.nR[1])

    def on_L(self, d, lam):
        return (lam * self.uL[0] + d * self.nL[0], lam * self.uL[1] + d * self.nL[1])

    def apex(self, a, b):
        """intersection of the right line at offset a and the left line at offset b"""
        a11, a12, b1 = self.uR[0], -self.uL[0], b * self.nL[0] - a * self.nR[0]
        a21, a22, b2 = self.uR[1], -self.uL[1], b * self.nL[1] - a * self.nR[1]
        det = a11 * a22 - a12 * a21
        return self.on_R(a, (b1 * a22 - a12 * b2) / det)


def ang(p):
    return math.atan2(p[1], p[0])


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def lam(R, d):
    return math.sqrt(R * R - d * d)


def apex_limit_radius(g, d):
    """Radius where the right and left side lines at offset d are w_d apart (|y| = w_d/2): the apex-limited inner end."""
    xc = (d + g.wd / 2 * math.cos(g.h)) / math.sin(g.h)
    return math.hypot(xc, g.wd / 2)


def turn(g, t):
    """Step G3 (revision 2026-10-05, U-E3): turn t with both sides on offset d_t, or None when it does not exist.
    The outer arc of turn t starts at J_t on the left line d_(t-1) (the jog: the pitch advance at constant radius R_out,t)
    and ends at B_t on the right line d_t; the right side runs down to C_t, the inner end joins C_t to D_t on the left
    line d_t, and the left side d_t runs up to J_(t+1) at R_out,t+1 (or to the lead at r_v for the last turn)."""
    dt, Ro, Ri = g.d(t), g.R_out(t), g.R_in(t)
    if not dt < Ro * math.sin(g.h):
        return None
    A, B = g.on_L(dt, lam(Ro, dt)), g.on_R(dt, lam(Ro, dt))
    J = A if t == 0 else g.on_L(g.d(t - 1), lam(Ro, g.d(t - 1)))
    rho = apex_limit_radius(g, dt)
    kind, r_end = ("trapezoid", Ri) if Ri >= rho else ("triangle", rho)
    if not r_end < Ro:
        return None
    C, D = g.on_R(dt, lam(r_end, dt)), g.on_L(dt, lam(r_end, dt))
    return {"t": t, "type": kind, "d_t": dt, "R_out": Ro, "R_in_or_apex": r_end, "A": A, "B": B, "C": C, "D": D, "J": J,
            "outer": Ro * (ang(J) - ang(B)), "jog": Ro * (ang(J) - ang(A)), "right": dist(B, C),
            "inner": r_end * (ang(D) - ang(C)),
            "span_mean_deg": math.degrees(2 * g.h - 2 * math.asin(dt / ((Ro + r_end) / 2)))}


def turn_limit(g, min_side=None):
    """Loop rule: rule 1 inside turn(); rule 2 right side >= min_side; rule 3 the left side reaches R_out,t+1."""
    min_side = 2 * g.w if min_side is None else min_side
    turns = []
    while True:
        tt = turn(g, len(turns))
        if tt is None or tt["right"] < min_side or not tt["R_in_or_apex"] < g.R_out(tt["t"] + 1):
            break
        turns.append(tt)
    radial = 0.5 * ((g.Ro0 - g.Ri0) / g.wd + 1)            # D08 eq. 3.24
    return turns, radial


def eye(g, turns, N, k=1):
    """Step G5 (revision 2026-10-05, U-E3): centre vias on the coil centre line inside turn N-1.
    The last left side d_(N-1) ends at r_v and one lead arc at r_v lands on the via, so the via pad and the lead-arc end
    share the point (r_v, 0): every bound uses m = max(pad, w)/2. No lead runs on d_N any more, so k > 1 uses d_(N-1).
    r_v = r_hi: the last left side is as long as the window allows (the lead arc itself has no radial length)."""
    last = turns[N - 1]
    m = max(g.pad, g.w) / 2
    side_lo = (g.d(N - 1) + g.w / 2 + g.s + m) / math.sin(g.h)
    inner_lo = last["R_in_or_apex"] + g.w_in / 2 + g.s + m
    r_lo, r_hi = max(side_lo, inner_lo), last["R_out"] - g.w_out / 2 - g.s - m
    pitch = max(g.pad, g.w) / 2 + g.pad / 2 + g.s
    return {"r_lo": r_lo, "r_hi": r_hi, "fits": r_hi - r_lo >= (k - 1) * pitch - 1e-9, "r_v": r_hi,
            "binding": "side" if side_lo >= inner_lo else "inner end", "via_pitch": pitch}


def max_turns_with_eye(g, turns, k=1):
    n = 0
    for N in range(1, len(turns) + 1):
        if eye(g, turns, N, k)["fits"]:
            n = N
    return n


def half_turn(g, t):
    """Closing half turn t (revision 2026-10-05, U-E3b): the outer arc J_t -> B_t with its jog, then the right side d_t
    from B_t straight to P_t = (d_t / sin h, 0), where the line d_t meets the coil centre line. The centre via sits at P_t,
    so the side itself lands on it; layer Y's mirrored side ends at the same point."""
    dt, Ro = g.d(t), g.R_out(t)
    if not dt < Ro * math.sin(g.h):
        return None
    A, B = g.on_L(dt, lam(Ro, dt)), g.on_R(dt, lam(Ro, dt))
    J = A if t == 0 else g.on_L(g.d(t - 1), lam(Ro, g.d(t - 1)))
    rv = dt / math.sin(g.h)
    V = (rv, 0.0)
    return {"t": t, "type": "half", "d_t": dt, "R_out": Ro, "r_v": rv, "A": A, "B": B, "J": J, "V": V,
            "outer": Ro * (ang(J) - ang(B)), "jog": Ro * (ang(J) - ang(A)), "right": dist(B, V)}


def half_closing(g, turns, N, min_side=None):
    """Feasibility of N turns whose last turn is the closing half turn N-1 (one centre via, pad <= w).
    Turns 0..N-2 are loop-rule turns. The via pad lies inside the side copper, so m = w/2 bounds the copper at V."""
    min_side = 2 * g.w if min_side is None else min_side
    if N < 1 or N - 1 > len(turns) or g.pad > g.w:
        return None
    ht = half_turn(g, N - 1)
    if ht is None:
        return None
    m, rv = g.w / 2, ht["r_v"]
    inner = turns[N - 2]["R_in_or_apex"] + g.w_in / 2 + g.s if N >= 2 else g.r_inner
    conds = {"side >= min_side": ht["right"] >= min_side,
             "clear of previous inner end": rv - m >= inner - 1e-9,
             "clear of own outer arc": rv + m + g.s <= ht["R_out"] - g.w_out / 2 + 1e-9}
    return {"N": N, "r_v": rv, "fits": all(conds.values()), "conditions": conds, "half_turn": ht,
            "via_to_previous_sides": g.d(N - 1) - (g.d(N - 2) if N >= 2 else 0.0) - g.w / 2 - m}


def closing(g, turns, k=1):
    """G5 choice: the full closing (lead arc in the eye, U-E3) or the half closing (via at P_(N-1), U-E3b), whichever
    builds more turns; at equal N the full closing wins because it keeps the last left side."""
    n_full = max_turns_with_eye(g, turns, k)
    n_half = 0
    if k == 1:
        n_half = max((N for N in range(1, len(turns) + 2) if (hc := half_closing(g, turns, N)) and hc["fits"]), default=0)
    if n_half > n_full:
        return {"kind": "half", "N": n_half, "n_full": n_full, "n_half": n_half}
    return {"kind": "full", "N": n_full, "n_full": n_full, "n_half": n_half}


def coil_path(g, turns, N, kind="full"):
    """Steps G4-G6 (revision 2026-10-05, U-E3; half closing U-E3b): lengths of the canonical layer-X path for N turns.
    'outer' includes the jogs; 'left' runs from each inner end to the next jog start J_(t+1), or to L at r_v for the
    last turn; the lead is the single arc at r_v from L to the centre via. With kind 'half' the last turn is the outer
    arc and the right side to P_(N-1); there is no lead."""
    parts = {"outer": 0.0, "inner": 0.0, "right": 0.0, "left": 0.0}
    jog = 0.0
    if kind == "half":
        ht = half_turn(g, N - 1)
        rv, L = ht["r_v"], ht["V"]
        full = turns[:N - 1]
        tops = [tt["J"] for tt in turns[1:N - 1]] + [ht["J"]]
    else:
        rv = eye(g, turns, N)["r_v"]
        d_last = g.d(N - 1)
        L = g.on_L(d_last, lam(rv, d_last))
        full = turns[:N]
        tops = [tt["J"] for tt in turns[1:N]] + [L]
    for tt, top in zip(full, tops, strict=True):
        parts["outer"] += tt["outer"]
        parts["inner"] += tt["inner"]
        parts["right"] += tt["right"]
        parts["left"] += dist(tt["D"], top)
        jog += tt["jog"]
    if kind == "half":
        parts["outer"] += ht["outer"]
        parts["right"] += ht["right"]
        jog += ht["jog"]
    lead = 0.0 if kind == "half" else rv * ang(L)
    r_T = g.r_outer + g.s + g.pad / 2
    c0 = turns[0]["A"]
    aV = min(ang(c0), g.h - math.asin(min(1.0, (max(g.pad, g.bw) + g.s) / (2 * r_T))) - 1e-6)
    tv = (r_T * math.cos(aV), r_T * math.sin(aV))
    stub = dist(tv, c0)
    body = sum(parts.values())
    return {"parts": parts, "body": body, "jog": jog, "lead": lead, "stub": stub, "total": body + lead + stub, "r_v": rv,
            "r_T": r_T, "terminal_angle_deg": math.degrees(aV), "start_corner_angle_deg": math.degrees(ang(c0)),
            "lead_point_L": L, "terminal_point": tv, "closing": kind}


def closed_form(g, N):
    """EQ-03 concentric-loop length (cross-check only)."""
    th, L = 2 * g.h, 0.0
    for i in range(N):
        d = g.d(i)
        Ro, Ri = g.R_out(i), g.R_in(i)
        po = math.asin(d / Ro)
        bo = th / 2 - po
        if Ri > d and th / 2 - math.asin(d / Ri) > 0:
            pi_ = math.asin(d / Ri)
            L += 2 * Ro * bo + 2 * Ri * (th / 2 - pi_) + 2 * (d / math.tan(po) - d / math.tan(pi_))
        else:
            L += 2 * Ro * bo + 2 * (d / math.tan(po) - d / math.tan(th / 2))
    return L


def via_count(Q, groups, v=1):
    """Step G6 via plan: groups = list of parallel-pair counts per series group (answers_to_agents.md 3.1)."""
    k = len(groups)
    per_coil = 2 * k - 1 + (1 if groups[0] > 1 else 0) + (1 if groups[-1] > 1 else 0)
    return {"centre_vias_per_coil": k, "per_coil": per_coil, "total": Q * v * per_coil}


def bus_ring_radius(g, level):
    """Step G8: Xcoil sector bus levels outside the terminal ring (engine.js buildSector rRing)."""
    r_T = g.r_outer + g.s + g.pad / 2
    return r_T + max(g.pad, g.w) / 2 + g.s + max(g.bw, g.pad) / 2 + level * (max(g.bw, g.pad) + g.s)


def resistance(L_mm, w_mm, t_mm, T=20.0):
    return RHO20 * (1 + ALPHA20 * (T - 20)) * L_mm * 1e-3 / (w_mm * 1e-3 * t_mm * 1e-3)


def example(name, Q, poles, r_inner, r_outer, w, s, gap, pad, t_cu, T, layers, bw=1.0):
    g = Geo(Q, r_inner, r_outer, w, s, gap, pad, bw)
    sos = star_of_slots(Q, poles // 2)
    turns, radial = turn_limit(g)
    n_loop = len(turns)
    cl = closing(g, turns)
    N = n_eye = cl["N"]
    path = coil_path(g, turns, N, cl["kind"])
    cf = closed_form(g, N)
    if cl["kind"] == "half":
        hc = half_closing(g, turns, N)
        ey = {"closing": "half", "r_v": hc["r_v"], "fits": hc["fits"], "conditions": hc["conditions"],
              "via_to_previous_sides": hc["via_to_previous_sides"], "n_full_closing": cl["n_full"]}
    else:
        ey = dict(eye(g, turns, N), closing="full")
    coils_per_phase = sos["coils_per_phase"]
    R_coil_layer = resistance(path["total"], w, t_cu, T)
    out = {
        "name": name, "inputs": {"Q": Q, "poles": poles, "r_inner_mm": r_inner, "r_outer_mm": r_outer, "w_mm": w,
                                 "s_mm": s, "coil_gap_mm": gap, "via_pad_mm": pad, "copper_mm": t_cu, "T_degC": T,
                                 "layers": layers, "bus_width_mm": bw},
        "derived": {"theta_cp_deg": 360 / Q, "w_d_mm": g.wd, "R_o0_mm": g.Ro0, "R_i0_mm": g.Ri0, "d0_mm": g.d(0)},
        "star_of_slots": {k: v for k, v in sos.items() if k != "coils"},
        "turn_limit": {"radial_bound_eq_3_24": radial, "loop_rule_turns": n_loop,
                       "types": [tt["type"] for tt in turns], "eye_limited_turns": n_eye, "closing": cl["kind"],
                       "limiting_reason": "eye" if n_eye < n_loop else "loop"},
        "turn_table": [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in tt.items() if k not in ("A", "B", "C", "D", "J", "V")}
                       for tt in (turns[:N] if cl["kind"] == "full" else turns[:N - 1] + [half_turn(g, N - 1)])],
        "eye": {k: (round(v, 4) if isinstance(v, float) else v) for k, v in ey.items() if k != "conditions"},
        "path_mm": {k: (round(v, 4) if isinstance(v, float) else v) for k, v in path.items() if k not in ("parts", "lead_point_L", "terminal_point")},
        "path_parts_mm": {k: round(v, 4) for k, v in path["parts"].items()},
        "closed_form_eq03_mm": round(cf, 4),
        "closed_minus_body_pct": round(100 * (cf - path["body"]) / path["body"], 3),
        "R_coil_layer_ohm": R_coil_layer,
        "R_phase_series_ohm_coils_only": R_coil_layer * coils_per_phase * layers,
        "via_plan_single_pair": via_count(Q, [1]),
        "via_plan_M1_3_parallel": via_count(Q, [3]),
        "via_plan_M2_3_series": via_count(Q, [1, 1, 1]),
        "M2_3_series_eye_turns": max_turns_with_eye(g, turns, k=3),
        "bus_ring_radii_mm": [round(bus_ring_radius(g, lv), 4) for lv in range(3)],
    }
    return out


EXAMPLES = [
    # default example 12/16 (answers_to_agents.md 3.2 defaults; via pad and bus width = Xcoil DEFAULTS viaPad 0.6, busWidth 1.0)
    ("default 12/16", 12, 16, 18.0, 38.0, 0.5, 0.2, 0.2, 0.6, 0.0348, 20.0, 2),
    # D08 12/10: centre-lines 12.5 / 44.0 mm (D08 p.55) -> copper edges 12.5 - 1.03 and 44.0 + 1.03; w 2.06, s 0.8 (Table 4.5/4.6)
    ("D08 12/10", 12, 10, 12.5 - 1.03, 44.0 + 1.03, 2.06, 0.8, 0.8, 0.6, 0.0348, 50.0, 2),
]

if __name__ == "__main__":
    results = [example(*e) for e in EXAMPLES]
    extra = []
    for pad in (0.5, 1.2):
        for nm, Q, poles, ri, ro, w, s, gap in (("default 12/16", 12, 16, 18.0, 38.0, 0.5, 0.2, 0.2),
                                                ("18/16", 18, 16, 18.0, 38.0, 0.5, 0.2, 0.2),
                                                ("D08 12/10", 12, 10, 11.47, 45.03, 2.06, 0.8, 0.8)):
            g = Geo(Q, ri, ro, w, s, gap, pad)
            turns, _ = turn_limit(g)
            cl = closing(g, turns)
            extra.append((nm, pad, len(turns), cl["N"], cl["kind"]))
    g18 = Geo(18, 18.0, 38.0, 0.5, 0.2, 0.2, 0.6)
    t18, _ = turn_limit(g18)
    cl18 = closing(g18, t18)
    extra.append(("18/16", 0.6, len(t18), cl18["N"], cl18["kind"]))
    if "--json" in sys.argv:
        print(json.dumps({"examples": results, "eye_sensitivity": extra}, indent=1))
        sys.exit(0)
    for r in results:
        print("=" * 100)
        print(r["name"], json.dumps(r["inputs"]))
        print(" derived:", json.dumps({k: round(v, 6) for k, v in r["derived"].items()}))
        print(" star of slots:", json.dumps({k: (round(v, 9) if isinstance(v, float) else v) for k, v in r["star_of_slots"].items()}))
        print(" turn limit:", json.dumps(r["turn_limit"]))
        for row in r["turn_table"]:
            print("   turn", json.dumps(row))
        print(" eye (N = eye-limited turns):", json.dumps(r["eye"]))
        print(" path:", json.dumps(r["path_mm"]), "parts:", json.dumps(r["path_parts_mm"]))
        print(f" EQ-03 closed form {r['closed_form_eq03_mm']} mm; (closed - generated body)/body = {r['closed_minus_body_pct']} %")
        print(f" R per coil-layer {r['R_coil_layer_ohm']:.6f} ohm at {r['inputs']['T_degC']} degC; "
              f"phase (coils only, {r['star_of_slots']['coils_per_phase']} coils x {r['inputs']['layers']} layers in series) "
              f"{r['R_phase_series_ohm_coils_only']:.6f} ohm")
        print(" vias: single pair", r["via_plan_single_pair"], "| M1 3 parallel", r["via_plan_M1_3_parallel"],
              "| M2 3 series", r["via_plan_M2_3_series"], "| M2 eye-limited turns (3 centre vias):", r["M2_3_series_eye_turns"])
        print(" bus ring radii levels 0..2:", r["bus_ring_radii_mm"])
    g = Geo(12, 18.0, 38.0, 0.5, 0.2, 0.2, 0.6)
    N = 10
    gap_y = (g.d(N) - g.d(N - 1)) - g.w / 2 - g.pad / 2
    print("=" * 100)
    print(f"DEF-P2-01: Phase 1 via on the X lead line d_N; copper gap to layer Y's last side d_(N-1) = {gap_y:.4f} mm (rule {g.s} mm)")
    print("eye sensitivity (case, via pad mm, loop-rule turns, turns after the centre-via rule, closing):")
    for e in extra:
        print("  ", e)
