# Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5
# DEF-09: tolerance basis for EQ-03. Builds a TRUE spiral centre-line path (sharp corners, sides parallel to the sector edges,
# trapezoidal AND triangular turns) and compares its length with the concentric-loop closed form (EQ-03).
# Spiral turn t: outer arc at R_out,t between the left/right sides at offset d_t; right side d_t down to the inner end;
# inner end = arc at R_in,t from right side d_t to left side d_{t+1} if that arc exists, otherwise the intersection point of
# right line d_t and left line d_{t+1} (triangular turn); left side d_{t+1} up to the outer arc of turn t+1. Last turn: lead
# along left line d_N from the inner end to the eye-centre radius r_v = (r_inner_end + R_out,N-1)/2 (Xcoil convention).
# Run: python3 checks/eq03_spiral_vs_loops.py
import math
def closed_form(Ro, Ri, wd, Q, N):
    th = 2 * math.pi / Q; L = 0
    for i in range(N):
        d = (i + .5) * wd; Rout = Ro - i * wd; Rin = Ri + i * wd
        po = math.asin(d / Rout); bo = th / 2 - po
        if Rin > d and th / 2 - math.asin(d / Rin) > 0:
            pi_ = math.asin(d / Rin); L += 2 * Rout * bo + 2 * Rin * (th / 2 - pi_) + 2 * (d / math.tan(po) - d / math.tan(pi_))
        else:
            L += 2 * Rout * bo + 2 * (d / math.tan(po) - d / math.tan(th / 2))
    return L
def spiral(Ro, Ri, wd, Q, N):
    h = math.pi / Q
    uR = (math.cos(h), -math.sin(h)); nR = (math.sin(h), math.cos(h))     # right edge direction / inward normal
    uL = (math.cos(h), math.sin(h)); nL = (math.sin(h), -math.cos(h))     # left edge direction / inward normal
    def onR(d, lam): return (lam * uR[0] + d * nR[0], lam * uR[1] + d * nR[1])
    def onL(d, lam): return (lam * uL[0] + d * nL[0], lam * uL[1] + d * nL[1])
    lamc = lambda R, d: math.sqrt(R * R - d * d)
    def ang(p): return math.atan2(p[1], p[0])
    def dist(a, b): return math.hypot(a[0] - b[0], a[1] - b[1])
    total = 0; parts = []
    for t in range(N):
        dt = (t + .5) * wd; dn = (t + 1.5) * wd; Rout = Ro - t * wd; Rin = Ri + t * wd
        A = onL(dt, lamc(Rout, dt)); B = onR(dt, lamc(Rout, dt))            # outer arc A (left) -> B (right)
        outer = Rout * (ang(A) - ang(B))
        # inner end: arc at Rin from right line d_t to left line d_{t+1} if it exists
        tri = True
        if Rin > dn:
            C = onR(dt, lamc(Rin, dt)); D = onL(dn, lamc(Rin, dn))
            if ang(D) - ang(C) > 0: tri = False
        if not tri:
            right = dist(B, C); inner = Rin * (ang(D) - ang(C)); E = D
        else:  # intersection of right line d_t and left line d_{t+1}: solve lam1*uR + dt*nR = lam2*uL + dn*nL
            a11, a12, b1 = uR[0], -uL[0], dn * nL[0] - dt * nR[0]
            a21, a22, b2 = uR[1], -uL[1], dn * nL[1] - dt * nR[1]
            det = a11 * a22 - a12 * a21; l1 = (b1 * a22 - a12 * b2) / det
            X = onR(dt, l1); right = dist(B, X); inner = 0.0; E = X
        if t < N - 1:
            Rn = Ro - (t + 1) * wd; F = onL(dn, lamc(Rn, dn)); left = dist(E, F)
        else:
            rE = math.hypot(*E); rv = (rE + Rout) / 2; F = onL(dn, lamc(rv, dn)) if rv > dn else E; left = dist(E, F)
        total += outer + right + inner + left
        parts.append('tri' if tri else 'trap')
    return total, parts
cases = [("G1 D08 (2 triangular loops)", 44.0, 12.5, 2.86, 12, 3), ("G2 12/16 N=8", 37.75, 18.25, 0.7, 12, 8),
         ("G2 12/16 N=11 (2 tri)", 37.75, 18.25, 0.7, 12, 11), ("G3 18/16 N=4", 37.75, 18.25, 0.7, 18, 4),
         ("G3 18/16 N=8 (3 tri)", 37.75, 18.25, 0.7, 18, 8), ("D08 N=2", 44.0, 12.5, 2.86, 12, 2), ("G2 N=4", 37.75, 18.25, 0.7, 12, 4)]
print(f"{'case':30s} {'closed form':>11s} {'spiral':>9s} {'(cf-sp)/sp':>10s}  turn types (spiral)")
for name, Ro, Ri, wd, Q, N in cases:
    cf = closed_form(Ro, Ri, wd, Q, N); sp, parts = spiral(Ro, Ri, wd, Q, N)
    print(f"{name:30s} {cf:11.3f} {sp:9.3f} {100*(cf-sp)/sp:9.2f} %  {','.join(parts)}")

# Spiral-mode turn count (no eye) and eye clearance of the centre via (DEF-09 turn criterion)
def spiral_turns_and_eye(Ro, Ri, w, s, Q, pad, clr):
    wd = w + s; h = math.pi / Q
    nR = (math.sin(h), math.cos(h)); uL = (math.cos(h), math.sin(h)); nL = (math.sin(h), -math.cos(h)); uR = (math.cos(h), -math.sin(h))
    def apex_r(a, b):  # intersection radius of right line offset a and left line offset b
        a11, a12, b1 = uR[0], -uL[0], b * nL[0] - a * nR[0]; a21, a22, b2 = uR[1], -uL[1], b * nL[1] - a * nR[1]
        det = a11 * a22 - a12 * a21; l1 = (b1 * a22 - a12 * b2) / det
        return math.hypot(l1 * uR[0] + a * nR[0], l1 * uR[1] + a * nR[1])
    N = 0
    while True:
        t = N; dt = (t + .5) * wd; dn = (t + 1.5) * wd; Rout = Ro - t * wd
        if apex_r(dt, dn) < Rout - 1e-9: N += 1
        else: break
    res = []
    for n in range(1, N + 1):
        t = n - 1; dt = (t + .5) * wd; dn = (t + 1.5) * wd; Rout = Ro - t * wd; Rin = Ri + t * wd
        rE = max(Rin, apex_r(dt, dn)); rv = (rE + Rout) / 2
        lam = math.sqrt(rv * rv - dn * dn); V = (lam * uL[0] + dn * nL[0], lam * uL[1] + dn * nL[1])
        side_clear = (V[0] * nR[0] + V[1] * nR[1]) - dt - w / 2 - pad / 2       # copper-to-pad distance to the right side
        rim_clear = Rout - w / 2 - rv - pad / 2                                  # copper-to-pad distance to the outer arc
        res.append((n, round(side_clear, 3), round(rim_clear, 3), side_clear >= clr and rim_clear >= clr))
    return N, res
for name, Ro, Ri, w, s, Q, pad in [("D08", 44.0, 12.5, 2.06, 0.8, 12, 0.6), ("D08", 44.0, 12.5, 2.06, 0.8, 12, 1.2),
                                   ("G2 12/16", 37.75, 18.25, 0.5, 0.2, 12, 0.5), ("G3 18/16", 37.75, 18.25, 0.5, 0.2, 18, 0.5)]:
    N, res = spiral_turns_and_eye(Ro, Ri, w, s, Q, pad, s)
    ok = [r[0] for r in res if r[3]]
    print(f"{name}: spiral-mode turns without eye = {N}; via pad {pad} mm, clearance {s} mm -> largest N with a fitting centre via = {max(ok) if ok else 0}; (N, side clearance, rim clearance) for last 3: {res[-3:]}")
