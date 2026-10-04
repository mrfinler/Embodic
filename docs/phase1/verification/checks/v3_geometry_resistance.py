# Prepared by: Agent 4 — Independent Verificator — model: claude-opus-5-5
# Independent re-computation of D08 eq. 3.24-3.26 (turn limits), a constructive concentric-loop turn count,
# D08 eq. 3.27-3.38 track length / phase resistance, and two resistance hand calculations.
# Written from the D08 page text (PDF p.43-45, printed 38-40) read by Agent 4; does not import Agent 2's scripts.
# Run: python3 docs/phase1/verification/checks/v3_geometry_resistance.py
import math
RHO20_IACS = 1 / 58e6          # ohm*m (IACS: 58 MS/m at 20 C)  -> 1.72414e-8
ALPHA = 0.00393                # 1/K (IACS at 20 C)
def rho(T, rho20=RHO20_IACS): return rho20 * (1 + ALPHA * (T - 20))

def turn_limits(ro, ri, wd, th):
    s = math.sin(th / 2); csc = 1 / s
    Nc = 0.5 * ((ro - ri) / wd + 1)                       # (3.24)
    Nc1 = ri * s / (wd * (1 - s)) + 1                     # (3.25)
    n1 = math.ceil(Nc1) - 1                               # largest integer strictly below
    Nc2 = ((ro - ri) / wd - csc - 2 * n1 + 2) / (1 + csc) # (3.26)
    n2 = max(0, math.ceil(Nc2) - 1)
    return Nc, Nc1, n1, Nc2, n2

def loops(ro, ri, wd, th):
    """Constructive count: loop i has side offset d_i=(i+1/2)wd from each sector edge, end-turn radii ro-i*wd, ri+i*wd.
    Trapezoid if both inner corners exist (d_i < (ri+i wd) sin(th/2)); otherwise triangle if the two sides meet
    (apex radius d_i/sin(th/2)) inside the outer end-turn radius; stop otherwise."""
    s = math.sin(th / 2); out = []
    i = 0
    while True:
        d = (i + 0.5) * wd; Ro = ro - i * wd; Ri = ri + i * wd
        if Ri < Ro and d < Ri * s: out.append('trap')
        elif d / s < Ro: out.append('tri')
        else: break
        i += 1
    return out

def loop_length(ro, ri, wd, th, i, sides_per_loop=2):
    d = (i + 0.5) * wd; Ro = ro - i * wd; Ri = ri + i * wd
    po = math.asin(d / Ro); Lo = 2 * Ro * (th / 2 - po)
    if d < Ri * math.sin(th / 2):
        pi_ = math.asin(d / Ri); Li = 2 * Ri * (th / 2 - pi_); side = Ro * math.cos(po) - Ri * math.cos(pi_)
    else:
        Li = 0.0; side = Ro * math.cos(po) - d / math.tan(th / 2)    # side from outer corner to apex
    return Lo + Li + sides_per_loop * side

print('== D08 geometry (Table 4.5 p.54, Table 4.6 p.57): r_o 44, r_i 12.5, w_tr 2.06, w_s 0.8 -> w_d 2.86 mm')
for lab, th in (('theta = 2pi/Q = 30 deg', 2 * math.pi / 12), ('theta = pi/p = 36 deg (as printed, eq. 3.27)', math.pi / 5)):
    Nc, Nc1, n1, Nc2, n2 = turn_limits(44.0, 12.5, 2.86, th)
    L = loops(44.0, 12.5, 2.86, th)
    print(f"  {lab}: (3.24) N_c < {Nc:.4f}; (3.25) N_c1 < {Nc1:.4f} -> {n1}; (3.26) N_c2 < {Nc2:.4f} -> {n2}; printed total {n1+n2};"
          f" constructive loops {len(L)} ({L.count('trap')} trap + {L.count('tri')} tri)")
th = 2 * math.pi / 12
Lc = sum(loop_length(44.0, 12.5, 2.86, th, i) for i in range(3))
Lc4 = sum(loop_length(44.0, 12.5, 2.86, th, i, 4) for i in range(3))
print(f"  track length per coil-layer (3 loops, 2 sides/loop, 30 deg) = {Lc:.3f} mm; with eq.3.34x3.36 double count (4 sides) = {Lc4:.3f} mm")
for coils in (8,):
    for T in (20, 50):
        R = rho(T) * Lc * coils * 1e-3 / (2.06e-3 * 34.8e-6)
        print(f"  phase R: {coils} coil-layers in series, T = {T} C, rho = {rho(T):.4e} ohm m -> R = {R:.4f} ohm (D08 Table 4.6: 0.39 ohm)")
th36 = math.pi / 5
Lc36 = sum(loop_length(44.0, 12.5, 2.86, th36, i) for i in range(3))
print(f"  variant 36 deg: L = {Lc36:.3f} mm/coil-layer, R(20 C) = {rho(20)*Lc36*8e-3/(2.06e-3*34.8e-6):.4f} ohm, R(50 C) = {rho(50)*Lc36*8e-3/(2.06e-3*34.8e-6):.4f} ohm")
print()
print('== embodic default annulus (copper edges 18/38 mm, w 0.5, s 0.2 -> centre-lines 18.25/37.75, w_d 0.7)')
for Q in (12, 18):
    th = 2 * math.pi / Q
    Nc, Nc1, n1, Nc2, n2 = turn_limits(37.75, 18.25, 0.7, th); L = loops(37.75, 18.25, 0.7, th)
    print(f"  Q={Q}: (3.24) {Nc:.4f}; printed 3.25/3.26 -> {n1}+{n2}={n1+n2}; constructive {L.count('trap')}+{L.count('tri')}={len(L)}")
    N = 8 if Q == 12 else 4
    print(f"     closed-form length of the first {N} loops = {sum(loop_length(37.75, 18.25, 0.7, th, i) for i in range(N)):.3f} mm per coil-layer")
print()
print('== Resistance hand calculations')
print(f"  1000 mm x 0.5 mm x 34.8 um: R20 = {rho(20)*1/(0.5e-3*34.8e-6):.5f} ohm (IACS 1.72414e-8); with engine rho 1.724e-8: {1.724e-8/(0.5e-3*34.8e-6):.5f}; R60 = {rho(60)*1/(0.5e-3*34.8e-6):.5f} ohm")
R09 = rho(20) * 3.244 / (0.8e-3 * 70e-6)
print(f"  D09 concentric (Table 1 p.3: 3244 mm, Table 2: w 0.8 mm, 70 um): R20 = {R09:.4f} ohm; D09 calc 1.04 ohm -> implied T = {20+(1.04/R09-1)/ALPHA:.1f} C;"
      f" D09 measured 1.07 ohm -> implied T = {20+(1.07/R09-1)/ALPHA:.1f} C (temperature of either not stated in the pages read)")
