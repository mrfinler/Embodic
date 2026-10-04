# Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5
# Closed-form reference values for the spiral generator checks (EQ-02 turn limits, EQ-03 loop geometry/track length).
# Convention: R_o0, R_i0 = centre-line radii of loop 0 (outermost loop) at the outer and inner end-turn; w_d = w + s;
# loop i: d_i = (i + 1/2) w_d (perpendicular offset of both sides from the sector edge, sides parallel to the edge),
# R_out,i = R_o0 - i w_d, R_in,i = R_i0 + i w_d, theta_cp = 2 pi / Q. Strict inequalities -> largest integer below the bound.
# Run: python3 checks/eq02_eq03_reference.py
import math
def ref(name, Ro, Ri, w, s, Q, N=None):
    wd = w + s; th = 2 * math.pi / Q; sh = math.sin(th / 2); csc = 1 / sh
    Nc = 0.5 * ((Ro - Ri) / wd + 1)
    Nc1b = Ri * sh / (wd * (1 - sh)) + 1; n1 = math.ceil(Nc1b) - 1
    Nc2b = ((Ro - Ri) / wd - csc - 2 * n1 + 2) / (1 + csc); n2 = max(0, math.ceil(Nc2b) - 1)
    nmax_c = math.ceil(Nc) - 1
    print(f"== {name}: R_o0={Ro} R_i0={Ri} w={w} s={s} w_d={wd:.3f} Q={Q} theta_cp={math.degrees(th):.3f} deg sin(theta/2)={sh:.6f}")
    print(f"EQ-02: N_c < 0.5*(({Ro}-{Ri})/{wd:.3f}+1) = {Nc:.4f} -> N <= {nmax_c}")
    print(f"       N_c1 < {Ri}*{sh:.6f}/({wd:.3f}*(1-{sh:.6f}))+1 = {Nc1b:.4f} -> {n1} trapezoidal")
    print(f"       N_c2 < (({Ro}-{Ri})/{wd:.3f} - {csc:.4f} - 2*{n1} + 2)/(1+{csc:.4f}) = {Nc2b:.4f} -> {n2} triangular ; total {n1+n2} (min with radial bound: {min(n1+n2, nmax_c)})")
    # constructive loop criterion (exact for this loop model): trapezoidal iff d_i < R_in,i sin(theta/2);
    # triangular iff not trapezoidal and apex radius d_i/sin(theta/2) < R_out,i; also R_in,i < R_out,i for trapezoids
    trap = tri = 0; i = 0
    while True:
        d = (i + 0.5) * wd; Rout = Ro - i * wd; Rin = Ri + i * wd
        if d < Rin * sh and Rin < Rout: trap += 1
        elif d / sh < Rout: tri += 1
        else: break
        i += 1
    print(f"       loop criterion: trapezoidal loops = {trap}, triangular loops = {tri}, total = {trap+tri} "
          f"(derived bound for trapezoidal: i < (R_i0 sin - w_d/2)/(w_d(1-sin)) = {(Ri*sh - wd/2)/(wd*(1-sh)):.4f})")
    if N is None: N = trap + tri
    tot = 0
    print(" i   d_i     R_out,i  R_in,i   phi_out  phi_in   beta_out beta_in  L_out    L_in     L_side   L_loop   type")
    for i in range(N):
        d = (i + 0.5) * wd; Rout = Ro - i * wd; Rin = Ri + i * wd
        po = math.asin(d / Rout); pi_ = math.asin(d / Rin) if d < Rin else math.pi / 2
        bo = th / 2 - po; bi = th / 2 - pi_
        Lo = 2 * Rout * bo
        if bi > 0: Li = 2 * Rin * bi; Ls = d / math.tan(po) - d / math.tan(pi_); typ = 'trap'
        else: Li = 0.0; Ls = d / math.tan(po) - d / math.tan(th / 2); typ = 'tri'
        L = Lo + Li + 2 * Ls; tot += L
        print(f"{i:2d} {d:7.3f} {Rout:8.3f} {Rin:8.3f} {math.degrees(po):8.4f} {math.degrees(pi_):8.4f} {math.degrees(bo):8.4f} {math.degrees(bi):8.4f} {Lo:8.3f} {Li:8.3f} {Ls:8.3f} {L:8.3f} {typ}")
    print(f"EQ-03: track length per coil-layer (N={N}) = {tot:.3f} mm")
    return tot
ref('G1 D08 thesis (Table 4.5/4.6)', 44.0, 12.5, 2.06, 0.8, 12)
ref('G2 embodic default 12/16', 37.75, 18.25, 0.5, 0.2, 12, 8)
ref('G3 embodic 18/16', 37.75, 18.25, 0.5, 0.2, 18, 4)
