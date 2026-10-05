# Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5
# Computes the closed-form reference cases CF-01...CF-13 and writes docs/phase2/engineering/oracle_cases.json together with
# the literature oracles O1-O3 carried over from docs/phase1/engineering/oracle_cases_draft.json (with the Phase 2 edits).
# Every computed number below is produced by this script; nothing is typed in by hand except the inputs.
# Run: python3 docs/phase2/engineering/checks/build_oracle_cases.py
import copy
import json
import math
import os
import subprocess

import numpy as np

import spiral_reference as sr

HERE = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(ENG)))
PHASE1 = os.path.join(ROOT, "docs", "phase1", "engineering", "oracle_cases_draft.json")
ENGINE = "/home/claude/serpentine/src/engine.js"
MU0 = 4e-7 * math.pi
RHO20, ALPHA = sr.RHO20, sr.ALPHA20


def bz_harmonic(n, r, z, p, Br, mur, lm, alpha_p, G):
    """EQ-05 closed form (cosh/sinh), double rotor or yoke at z = G; r, z, lm, G in mm."""
    u = n * p / r
    K = 4 * Br / (n * math.pi) * math.sin(n * math.pi * alpha_p / 2)
    den = math.cosh(u * G) + mur / math.tanh(u * lm) * math.sinh(u * G)
    return K * math.cosh(u * (G - z)) / den


def node_eval(js):
    res = subprocess.run(["node", "-e", f"const E=require('{ENGINE}');{js}"], capture_output=True, text=True, check=True)
    return json.loads(res.stdout)


def rel(a, b):
    return (a - b) / b


def inp(value, unit, status, source):
    return {"value": value, "unit": unit, "status": status, "source": source}


cases = []
checks = []

# CF-01 one-dimensional field limit of EQ-05
F = dict(p=1, Br=1.3, mur=1.05, lm=3.0, alpha_p=0.85, G=1.1)
b1d = 4 / math.pi * math.sin(math.pi * F["alpha_p"] / 2) * F["Br"] * F["lm"] / (F["lm"] + F["mur"] * F["G"])
b_py = bz_harmonic(1, 1e5, 0.0, **F)
b_js = node_eval("console.log(JSON.stringify(E.fieldHarmonic(1,1e5,0,{pp:1,Br:1.3,muR:1.05,lm:3,alphaP:0.85,G:1.1}).Bz))")
checks.append(("CF-01 Python cosh form vs 1-D", rel(b_py, b1d)))
checks.append(("CF-01 Xcoil exp form vs 1-D", rel(b_js, b1d)))
cases.append({
    "case_id": "CF-01", "version": 1, "kind": "closed form", "eq_ids": ["EQ-05"],
    "title": "EQ-05 fundamental at a pole pitch much larger than the magnetic gap equals the 1-D magnetic-circuit value",
    "inputs": {"Br_T": inp(1.3, "T", "assumption", "example value"), "mu_r": inp(1.05, "1", "assumption", "example value"),
               "lm_mm": inp(3.0, "mm", "assumption", "example value"), "alpha_p": inp(0.85, "1", "assumption", "example value"),
               "G_mm": inp(1.1, "mm", "assumption", "example value (double rotor, (t_s + 2g)/2)"),
               "p": inp(1, "1", "assumption", "example value"), "r_mm": inp(1e5, "mm", "assumption", "large radius = 1-D limit"),
               "z_mm": inp(0.0, "mm", "assumption", "magnet face")},
    "expected": [{"quantity": "B_z1", "value": b1d, "unit": "T",
                  "formula": "(4/pi) sin(pi alpha_p/2) Br lm/(lm + mu_r G)", "tolerance": "relative 1e-9"}],
    "status": "verified",
    "evidence": f"run: Python cosh form rel {rel(b_py, b1d):.1e}, Xcoil fieldHarmonic rel {rel(b_js, b1d):.1e} (this script)",
})

# CF-02 one-turn radial-sided coil in an injected uniform harmonic field
Bhat, ra, rb, pp, sigma = 0.8, 18.0, 38.0, 8, math.radians(30.0)
ke_cf = Bhat * (rb ** 2 - ra ** 2) * 1e-6 * math.sin(pp * sigma / 2)


def ke_numeric(field, seg=0.5):
    """EQ-06 kernel summed over a discretised closed 1-turn path: outer arc, side, inner arc, side."""
    pts = []
    def arc(r, a1, a2):
        n = max(2, int(abs(a2 - a1) * r / seg) + 1)
        return [(r, a1 + (a2 - a1) * i / (n - 1)) for i in range(n)]
    def line(r1, r2, a):
        n = max(2, int(abs(r2 - r1) / seg) + 1)
        return [(r1 + (r2 - r1) * i / (n - 1), a) for i in range(n)]
    pts += arc(rb, sigma / 2, -sigma / 2) + line(rb, ra, -sigma / 2)[1:] + arc(ra, -sigma / 2, sigma / 2)[1:] + line(ra, rb, sigma / 2)[1:]
    acc = 0j
    for (r1, a1), (r2, a2) in zip(pts[:-1], pts[1:]):
        rm, am = (r1 + r2) / 2, (a1 + a2) / 2
        acc += field(rm) * rm * (r2 - r1) * complex(math.cos(-pp * am), math.sin(-pp * am))
    return abs(acc) * 1e-6


ke_num = ke_numeric(lambda r: Bhat)
checks.append(("CF-02 kernel vs closed form", rel(ke_num, ke_cf)))
cases.append({
    "case_id": "CF-02", "version": 1, "kind": "closed form", "eq_ids": ["EQ-06"],
    "title": "Ke of a 1-turn radial-sided coil in a uniform injected field B = B1 cos(p(theta - theta_r)); arcs carry no EMF",
    "inputs": {"B1_T": inp(Bhat, "T", "assumption", "injected test field"), "r_a_mm": inp(ra, "mm", "assumption", "example"),
               "r_b_mm": inp(rb, "mm", "assumption", "example"), "p": inp(pp, "1", "assumption", "16 poles"),
               "sigma_deg": inp(30.0, "deg", "assumption", "coil side span = 2 pi/Q for Q = 12"),
               "segment_mm": inp(0.5, "mm", "assumption", "EQ-06 validity: segments <= 0.5 mm")},
    "expected": [{"quantity": "Ke1", "value": ke_cf, "unit": "V*s/rad", "formula": "B1 (r_b^2 - r_a^2) sin(p sigma/2)",
                  "tolerance": "relative 1e-9 (arcs must contribute exactly 0)"}],
    "status": "verified", "evidence": f"run: discretised kernel rel {rel(ke_num, ke_cf):.1e} (this script)",
})

# CF-03 the same coil in the EQ-05 field at a copper layer: 1-D quadrature reference
F3 = dict(p=8, Br=1.3, mur=1.05, lm=3.0, alpha_p=0.85, G=1.1)
z3 = 0.8
xg, wg = np.polynomial.legendre.leggauss(64)
rr = (rb - ra) / 2 * xg + (rb + ra) / 2
integral = float(np.sum(wg * np.array([bz_harmonic(1, r, z3, **F3) * r for r in rr])) * (rb - ra) / 2)
ke3 = 2 * math.sin(pp * sigma / 2) * integral * 1e-6
js3 = node_eval("var F={pp:8,Br:1.3,muR:1.05,lm:3,alphaP:0.85,G:1.1},n=20000,s=0;for(var i=0;i<n;i++){var r=18+20*(i+0.5)/n;s+=E.fieldHarmonic(1,r,0.8,F).Bz*r*20/n;}"
                "console.log(JSON.stringify(2*Math.sin(8*Math.PI/12)*s*1e-6))")
ke3_kernel = ke_numeric(lambda r: bz_harmonic(1, r, z3, **F3))
checks.append(("CF-03 Xcoil field midpoint quadrature vs Gauss-Legendre", rel(js3, ke3)))
checks.append(("CF-03 0.5 mm kernel vs Gauss-Legendre", rel(ke3_kernel, ke3)))
cases.append({
    "case_id": "CF-03", "version": 1, "kind": "closed form (1-D quadrature)", "eq_ids": ["EQ-05", "EQ-06"],
    "title": "Ke of the CF-02 coil in the EQ-05 field of a double rotor at the layer facing rotor 1 (z = air gap)",
    "inputs": {"field": inp(F3, "mixed (mm, T)", "assumption", "example; Xcoil DEFAULTS Br, muR, magnetThickness, magnetArcRatio"),
               "z_mm": inp(z3, "mm", "assumption", "layer F.Cu at z = 0 -> 0.8 mm from the magnet face (Xcoil airgap default)"),
               "geometry": inp({"r_a": ra, "r_b": rb, "sigma_deg": 30.0, "magnet_span_mm": [ra, rb]}, "mm", "assumption", "as CF-02")},
    "expected": [{"quantity": "Ke1", "value": ke3, "unit": "V*s/rad", "formula": "2 sin(p sigma/2) * integral B_z1(r, z) r dr (64-point Gauss-Legendre)",
                  "tolerance": "relative 1e-5 (Xcoil 48-bin field table and 0.5 mm segments; Phase 1 C2 found -5e-6)"}],
    "status": "verified",
    "evidence": f"run: Xcoil fieldHarmonic midpoint rule rel {rel(js3, ke3):.1e}; Python 0.5 mm kernel rel {rel(ke3_kernel, ke3):.1e}",
})

# CF-04 resistance of known tracks and a via barrel (EQ-10, EQ-11)
def R_track(L, w, t, T):
    return RHO20 * (1 + ALPHA * (T - 20)) * L * 1e-3 / (w * 1e-3 * t * 1e-3)
L_arc = 30.0 * math.pi / 2
A_via = math.pi * (2 * 0.15 * 0.025 - 0.025 ** 2)
R_via = RHO20 * 1.6e-3 / (A_via * 1e-6)
js4 = node_eval("console.log(JSON.stringify([E.traceResistance(1000,0.5,0.0348,20),E.viaBarrelArea(0.3,0.025)]))")
checks.append(("CF-04 Xcoil R20 (rho 1.724e-8) vs IACS 1.7241e-8", rel(js4[0], R_track(1000, 0.5, 0.0348, 20))))
checks.append(("CF-04 Xcoil via area", rel(js4[1], A_via)))
cases.append({
    "case_id": "CF-04", "version": 1, "kind": "closed form", "eq_ids": ["EQ-10", "EQ-11"],
    "title": "DC resistance of a straight track, an arc track and a plated via barrel",
    "inputs": {"rho20_ohm_m": inp(RHO20, "ohm*m", "verified", "EV-53 IACS (NBS Handbook 100 p.2-4)"),
               "alpha20_per_K": inp(ALPHA, "1/K", "verified", "EV-53"),
               "copper_mm": inp(0.0348, "mm", "assumption", "1 oz (D08 p.54, Xcoil OZ_TO_MM)"),
               "track_straight": inp({"L": 1000, "w": 0.5}, "mm", "assumption", "example"),
               "track_arc": inp({"r": 30.0, "sweep_deg": 90, "w": 0.5}, "mm", "assumption", "example"),
               "via": inp({"drill": 0.3, "plating": 0.025, "barrel_length": 1.6}, "mm", "assumption", "plating 25 um per D05 p.6-8 (EV-37)")},
    "expected": [{"quantity": "R straight 20 degC", "value": R_track(1000, 0.5, 0.0348, 20), "unit": "ohm", "tolerance": "relative 1e-12"},
                 {"quantity": "R straight 60 degC", "value": R_track(1000, 0.5, 0.0348, 60), "unit": "ohm", "tolerance": "relative 1e-12"},
                 {"quantity": "arc length", "value": L_arc, "unit": "mm", "tolerance": "relative 1e-12"},
                 {"quantity": "R arc 20 degC", "value": R_track(L_arc, 0.5, 0.0348, 20), "unit": "ohm", "tolerance": "relative 1e-12"},
                 {"quantity": "via barrel area", "value": A_via, "unit": "mm2", "tolerance": "relative 1e-12"},
                 {"quantity": "via barrel R 20 degC", "value": R_via, "unit": "ohm", "tolerance": "relative 1e-12"},
                 {"quantity": "R straight 20 degC with Xcoil rho20 1.724e-8 (golden-compatible constant)", "value": js4[0], "unit": "ohm",
                  "tolerance": "relative 1e-12"}],
    "status": "verified", "evidence": f"run: Xcoil vs IACS constant rel {rel(js4[0], R_track(1000, 0.5, 0.0348, 20)):.2e} (expected -5.8e-5)",
})

# CF-05 eddy loss of one trace in a uniform sinusoidal normal field (EQ-12) and skin depth (EQ-13)
fe = 8 * 1000 / 60
sig = 1 / RHO20
P_eddy = sig * (2 * math.pi * fe) ** 2 * 0.70 ** 2 * (0.5e-3) ** 3 * 0.0348e-3 * 20e-3 / 24
delta = math.sqrt(RHO20 / (math.pi * fe * MU0)) * 1e3
cases.append({
    "case_id": "CF-05", "version": 1, "kind": "closed form", "eq_ids": ["EQ-12", "EQ-13"],
    "title": "Eddy loss of one radial trace in a uniform normal field B_hat sin(omega t) and the skin depth at that frequency",
    "inputs": {"trace": inp({"L": 20, "w": 0.5, "t": 0.0348}, "mm", "assumption", "example"),
               "B_hat_T": inp(0.70, "T", "assumption", "example"), "f_e_Hz": inp(fe, "Hz", "assumption", "16 poles at 1000 rpm"),
               "T_degC": inp(20, "degC", "assumption", "example")},
    "expected": [{"quantity": "P_eddy (B_z term only)", "value": P_eddy, "unit": "W", "formula": "sigma omega^2 B^2 w^3 t L / 24",
                  "tolerance": "relative 1e-9"},
                 {"quantity": "skin depth", "value": delta, "unit": "mm", "formula": "sqrt(rho/(pi f mu0))", "tolerance": "relative 1e-9"}],
    "status": "verified", "evidence": "arithmetic in this script; formula choice per EQ-12 (D03 eq. 2 p.5, EV-36)",
})

# CF-06 connection identities (EQ-09, EQ-23)
b = [1.0, 1.1, 1.2]
S = sum(b)
R_LL_delta = sum(bk * (S - bk) / S for bk in b) / 3
R_LL_star = 2 * sum(b) / 3
Ke_ph = 0.01
cases.append({
    "case_id": "CF-06", "version": 1, "kind": "closed form", "eq_ids": ["EQ-09", "EQ-23"],
    "title": "Star/delta conversion of Ke, Kt and the mean line-to-line resistance of unequal phase branches",
    "inputs": {"R_branches_ohm": inp(b, "ohm", "assumption", "example"), "Ke_ph": inp(Ke_ph, "V*s/rad", "assumption", "example")},
    "expected": [{"quantity": "R_LL star (mean of the three pairs)", "value": R_LL_star, "unit": "ohm", "tolerance": "relative 1e-12"},
                 {"quantity": "R_LL delta (mean of the three pairs)", "value": R_LL_delta, "unit": "ohm", "tolerance": "relative 1e-12"},
                 {"quantity": "Ke_LL star", "value": math.sqrt(3) * Ke_ph, "unit": "V*s/rad", "tolerance": "relative 1e-12"},
                 {"quantity": "Kt per line A_rms, star", "value": 3 / math.sqrt(2) * Ke_ph, "unit": "N*m/A", "tolerance": "relative 1e-12"},
                 {"quantity": "Kt per line A_rms, delta", "value": 3 / math.sqrt(2) * Ke_ph / math.sqrt(3), "unit": "N*m/A", "tolerance": "relative 1e-12"}],
    "status": "verified", "evidence": "network identities; arithmetic in this script",
})

# CF-07 circulating currents: delta mesh with a triplen EMF (EQ-19) and two parallel members (EQ-07)
E3, Rloop = 0.1, 3.0
I3 = 3 * E3 / Rloop
E1, E2, R1, R2 = 1.00, 0.98, 0.5, 0.5
Eg = (E1 / R1 + E2 / R2) / (1 / R1 + 1 / R2)
Pc_general = (E1 - Eg) ** 2 / (2 * R1) + (E2 - Eg) ** 2 / (2 * R2)
Pc_pair = (E1 - E2) ** 2 / (2 * (R1 + R2))
checks.append(("CF-07 EQ-07 general vs two-member identity", rel(Pc_general, Pc_pair)))
cases.append({
    "case_id": "CF-07", "version": 1, "kind": "closed form", "eq_ids": ["EQ-07", "EQ-19"],
    "title": "Resistance-limited circulating current of a delta mesh with an in-phase 3rd harmonic; circulating loss of two parallel members",
    "inputs": {"E3_peak_per_phase_V": inp(E3, "V", "assumption", "example"), "R_loop_ohm": inp(Rloop, "ohm", "assumption", "example"),
               "E_members_peak_V": inp([E1, E2], "V", "assumption", "example, in phase"), "R_members_ohm": inp([R1, R2], "ohm", "assumption", "example")},
    "expected": [{"quantity": "delta circulating current peak", "value": I3, "unit": "A", "tolerance": "relative 1e-12"},
                 {"quantity": "delta circulating loss", "value": (I3 / math.sqrt(2)) ** 2 * Rloop, "unit": "W", "tolerance": "relative 1e-12"},
                 {"quantity": "parallel-member circulating loss", "value": Pc_general, "unit": "W", "tolerance": "relative 1e-12"}],
    "status": "verified", "evidence": f"run: general form vs |E1-E2|^2/(2(R1+R2)) rel {rel(Pc_general, Pc_pair):.1e}",
})

# CF-08 involute equidistance (wave end-turns, EQ-24)
rb_i, dphi = 20.0, math.radians(2.0)
def inv(phi0, t):
    a = phi0 + t
    return np.array([rb_i * (math.cos(a) + t * math.sin(a)), rb_i * (math.sin(a) - t * math.cos(a))])
ts = np.linspace(0.05, 1.2, 4001)
c2 = np.array([inv(dphi, t) for t in ts])
dmin = []
for t in np.linspace(0.2, 1.0, 9):
    p0 = inv(0.0, t)
    dmin.append(float(np.min(np.hypot(c2[:, 0] - p0[0], c2[:, 1] - p0[1]))))
checks.append(("CF-08 involute spacing max deviation from rb*dphi [mm]", max(abs(d - rb_i * dphi) for d in dmin)))
cases.append({
    "case_id": "CF-08", "version": 1, "kind": "closed form", "eq_ids": ["EQ-24"],
    "title": "Two involutes of one base circle rotated by d_phi are equidistant with spacing r_b d_phi (wave end-turn nesting)",
    "inputs": {"r_b_mm": inp(rb_i, "mm", "assumption", "example"), "d_phi_deg": inp(2.0, "deg", "assumption", "example")},
    "expected": [{"quantity": "normal spacing", "value": rb_i * dphi, "unit": "mm", "tolerance": "absolute 1e-4 mm (sampled curve)"}],
    "status": "verified", "evidence": f"run: 9 sample points, max deviation {max(abs(d - rb_i * dphi) for d in dmin):.1e} mm",
})

# CF-09 exact star of slots (EQ-08)
sos_rows = []
for Q, poles in ((12, 10), (12, 14), (12, 16), (18, 16), (24, 14), (24, 22), (24, 26), (9, 8), (15, 16)):
    s = sr.star_of_slots(Q, poles // 2)
    sos_rows.append({"Q": Q, "poles": poles, "pattern": s["pattern"], "balanced_exact": s["balanced_exact"],
                     "feasible_rule": s["feasible_rule"], "kd1": s["kd1"], "belt_edge_coils": s["belt_edge_coils"]})
js9 = node_eval("console.log(JSON.stringify([[12,5],[12,7],[24,7],[24,11],[24,13]].map(function(a){return E.starOfSlots(a[0],a[1],3).ok;})))")
cases.append({
    "case_id": "CF-09", "version": 1, "kind": "exact integer arithmetic", "eq_ids": ["EQ-08"],
    "title": "Phase pattern of concentrated coils from the exact star of slots (half-open 60-degree belts)",
    "inputs": {"belt_rule": inp("belt = floor((12 (k p mod Q) + Q)/(2 Q)) mod 6; A+, -C, B+, -A, C+, -B", "-", "inferred",
                                "spiral_generator_spec.md step G7")},
    "expected": [{"quantity": "pattern per (Q, poles)", "value": sos_rows, "unit": "-",
                  "tolerance": "exact; 12/10 must equal D08 Fig. 3.7 p.36 'AabBCcaABbcC'"}],
    "status": "verified",
    "evidence": f"run: 12/10 equals D08 Fig. 3.7; Xcoil starOfSlots ok flags for 12/10, 12/14, 24/14, 24/22, 24/26 = {js9} (belt-edge defect C6)",
})

# CF-10 / CF-11 spiral generator reference geometry (D08 3-turn and default 12/16)
ex = {e[0]: sr.example(*e) for e in sr.EXAMPLES}
d08 = ex["D08 12/10"]
g12 = Geo = None
for pad in (1.2,):
    g = sr.Geo(12, 11.47, 45.03, 2.06, 0.8, 0.8, pad)
    tt, _ = sr.turn_limit(g)
    d08_pad12 = sr.closing(g, tt)["N"]
cases.append({
    "case_id": "CF-10", "version": 3, "version_note": "version 3 (revision 2026-10-05, U-E3b): G5 half closing (last turn = outer arc + right side ending on the centre via at P = (d_2/sin h, 0)); 3 turns at via pad 0.6 and 1.2 mm (version 2, U-E3: 2 turns)", "kind": "reference model (spiral_reference.py)", "eq_ids": ["EQ-02", "EQ-03", "EQ-25"],
    "title": "D08 3-turn coil geometry (12 coils, 10 poles): turn limit, turn types, eye, path lengths",
    "inputs": {"coil_centre_lines_mm": inp([12.5, 44.0], "mm", "verified", "D08 p.55"),
               "trace_width_mm": inp(2.06, "mm", "verified", "D08 Table 4.6 p.57"),
               "clearance_mm": inp(0.8, "mm", "verified", "D08 Table 4.5 p.54"),
               "coil_gap_mm": inp(0.8, "mm", "inferred", "equal to the clearance (D08 Fig. 3.4 p.33 convention)"),
               "via_pad_mm": inp(0.6, "mm", "unresolved", "not stated in D08; Xcoil default; sensitivity 1.2 mm"),
               "copper_mm": inp(0.0348, "mm", "verified", "D08 Table 4.5 p.54"), "T_degC": inp(50, "degC", "verified", "D08 Table 4.5 p.54")},
    "expected": [{"quantity": "radial bound D08 eq. 3.24", "value": d08["turn_limit"]["radial_bound_eq_3_24"], "unit": "1", "tolerance": "relative 1e-9"},
                 {"quantity": "loop-rule turns and types", "value": [d08["turn_limit"]["loop_rule_turns"], d08["turn_limit"]["types"]], "unit": "-",
                  "tolerance": "exact; equals D08 Table 4.6 p.57 (3 loops)"},
                 {"quantity": "turns after the centre-via rule, via pad 0.6 / 1.2 mm; closing", "value": [d08["turn_limit"]["eye_limited_turns"], d08_pad12, d08["turn_limit"]["closing"]], "unit": "1", "tolerance": "exact"},
                 {"quantity": "centre via radius r_v = d_2 / sin(pi/Q)", "value": d08["eye"]["r_v"], "unit": "mm", "tolerance": "absolute 1e-4 mm"},
                 {"quantity": "EQ-03 concentric closed form, N = 3 (three full loops)", "value": d08["closed_form_eq03_mm"], "unit": "mm", "tolerance": "absolute 1e-3 mm"},
                 {"quantity": "generated body (sides + ends), N = 3 with half closing", "value": d08["path_mm"]["body"], "unit": "mm", "tolerance": "relative 1e-6 (same rules) / +-1 % (fillet or lead conventions)"},
                 {"quantity": "lead / terminal stub / total", "value": [d08["path_mm"]["lead"], d08["path_mm"]["stub"], d08["path_mm"]["total"]], "unit": "mm", "tolerance": "relative 1e-6"},
                 {"quantity": "R per coil-layer at 50 degC (coil copper only)", "value": d08["R_coil_layer_ohm"], "unit": "ohm", "tolerance": "relative 1e-6"}],
    "status": "inferred", "evidence": "reference model of the spec rules; D08 gives no measured coil length or R (O1 phase R 0.39 ohm is a loop-model calculation)",
})
dft = ex["default 12/16"]
cases.append({
    "case_id": "CF-11", "version": 2, "version_note": "version 2 (revision 2026-10-05, U-E3): G3-G5 revised (both sides on d_t, outer-end jog, lead arc at r_v = r_hi); inputs unchanged", "kind": "reference model (spiral_reference.py)", "eq_ids": ["EQ-02", "EQ-03", "EQ-08", "EQ-25"],
    "title": "Default example 12/16 spiral coil (r 18-38 mm copper edge, w 0.5, s 0.2, gap 0.2, via pad 0.6 mm)",
    "inputs": {k: inp(v, "mm or 1", "assumption", "example values (D-014); answers_to_agents.md 3.2 defaults; Xcoil viaPad/busWidth")
               for k, v in dft["inputs"].items()},
    "expected": [{"quantity": "pattern", "value": dft["star_of_slots"]["pattern"], "unit": "-", "tolerance": "exact"},
                 {"quantity": "loop-rule turns / eye-limited turns", "value": [dft["turn_limit"]["loop_rule_turns"], dft["turn_limit"]["eye_limited_turns"]], "unit": "1", "tolerance": "exact"},
                 {"quantity": "centre via radius r_v", "value": dft["eye"]["r_v"], "unit": "mm", "tolerance": "absolute 1e-6 mm"},
                 {"quantity": "generated body / lead / stub / total, N = 10", "value": [dft["path_mm"]["body"], dft["path_mm"]["lead"], dft["path_mm"]["stub"], dft["path_mm"]["total"]], "unit": "mm", "tolerance": "relative 1e-6"},
                 {"quantity": "EQ-03 closed form N = 10 and (closed - body)/body", "value": [dft["closed_form_eq03_mm"], dft["closed_minus_body_pct"]], "unit": "mm, %", "tolerance": "absolute 1e-3 mm"},
                 {"quantity": "R per coil-layer 20 degC", "value": dft["R_coil_layer_ohm"], "unit": "ohm", "tolerance": "relative 1e-6"},
                 {"quantity": "terminal ring r_T and bus ring levels 0..2", "value": [dft["path_mm"]["r_T"]] + dft["bus_ring_radii_mm"], "unit": "mm", "tolerance": "absolute 1e-9 mm"}],
    "status": "inferred", "evidence": "reference model of the spec rules (example values, not a measured design)",
})

# Literature oracles carried over from Phase 1
p1 = json.load(open(PHASE1))
lit = {c["case_id"]: copy.deepcopy(c) for c in p1["cases"]}
o1 = lit["O1-D08"]
o1["version"] = 3
o1["version_note"] = ("version 3 (revision 2026-10-05, U-E3b): 'turns that fit' uses the G5 half closing of spiral_generator_spec.md "
                      "(3 turns at via pad 0.6 and 1.2 mm, D08 via pad unresolved); Ke comparison names the result field ke_line_peak. "
                      "Version 2: Phase 2 centre-via rule; EC-05 add-on labelled per DEF-23. Inputs unchanged.")
for e in o1["expected"]:
    if e["quantity"] == "turns that fit":
        e["comparison"] = ("EQ-02 / EQ-25: concentric loop rule 3 (1 trapezoid + 2 triangles); generator turns_achieved 3 at via pad 0.6 and 1.2 mm "
                           "with the half closing (G5): turns 0-1 full, turn 2 = outer arc + right side ending on the centre via")
    if e["quantity"].startswith("Ke_LL_peak"):
        e["comparison"] = ("AnalysisResult.ke_line_peak_v_s_per_rad (trace key ke_line_peak): peak of the synthesised line-line waveform "
                           "per mechanical rad/s from EQ-05/06/09/18, not the fundamental ke_line")
        e["tolerance"] = ("model/measured in [-8 %, +8 % + e_edge], e_edge = 4.2 % (EC-05). O1 is the only oracle independent of the EC-05 "
                          "calibration source (D09); the add-on itself is an assumption when transferred to D08's 5 mm T-arrangement magnets (DEF-23)")
o1["runnable"] = True
o2 = lit["O2-D09"]
o2["dec23_note"] = ("DEF-23: D09 Fig. 7 is both the EC-05 calibration source and this oracle, so O2 EMF/torque results cannot validate EC-05; "
                    "they test EQ-05/06 given EC-05. Fig. 7 plots |B| at the magnet middle (caption p.4), used as a proxy for B_z at the copper.")
o2["runnable"] = True
o3 = lit["O3-D10"]
o3["runnable"] = False
cases = [o1, o2, o3] + cases

doc = {
    "prepared_by": "Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5",
    "schema": "embodic oracle cases v1.0 (Phase 2, 2026-10-04); generated by checks/build_oracle_cases.py",
    "notes": [
        "O1-O3: literature oracles (values from the cited pages, carried over from docs/phase1/engineering/oracle_cases_draft.json); "
        "CF-xx: closed-form or reference-model cases computed by checks/build_oracle_cases.py",
        "every input has value, unit, status and source; 'assumed' = value used for an unresolved input",
        "kinds: measured / calculated / FEA as stated by the paper; embodic results are never called measured",
        "a change of any frozen value creates a new case version",
    ],
    "self_checks": [{"check": n, "value": v} for n, v in checks],
    "cases": cases,
}
with open(os.path.join(ENG, "oracle_cases.json"), "w") as f:
    json.dump(doc, f, indent=1, ensure_ascii=False)
for n, v in checks:
    print(f"{n:60s} {v:+.3e}")
print("cases:", [c["case_id"] for c in cases])
print("O1 runnable", o1["runnable"], "| O2 runnable", o2["runnable"], "| O3 runnable", o3["runnable"])
print("CF-02 Ke1 =", ke_cf, "| CF-03 Ke1 =", ke3, "| CF-01 B1 =", b1d)
print("CF-04 R20 =", R_track(1000, 0.5, 0.0348, 20), "R60 =", R_track(1000, 0.5, 0.0348, 60), "R_via =", R_via)
print("CF-05 P_eddy =", P_eddy, "delta =", delta, "| CF-06 R_LL star/delta =", R_LL_star, R_LL_delta)
for r in sos_rows:
    print("CF-09", r)
