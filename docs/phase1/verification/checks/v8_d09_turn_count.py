# Prepared by: Agent 4 — Independent Verificator — model: claude-opus-5-5
# Indicative inversion for D09's concentric board (Agent 2 task T-D): which turn count N and coil radii reproduce
# both published numbers of D09 Table 1 p.3 — phase trace length 3244 mm (=> 3244/8 = 405.5 mm per coil-layer for
# 4 coils/phase x 2 layers) and "covered area" 171 mm^2 of the middle loop — with the D08 concentric-loop model?
# Inputs: Q = 12, w = 0.8 mm, s = 0.2 mm (D09 Table 2), w_d = 1.0 mm, d_i = (i+1/2) w_d, sides parallel to sector edges.
# Coil radii are NOT published; they are scanned. Leads, vias and the terminal tracks are ignored -> indicative only.
# Run: python3 docs/phase1/verification/checks/v8_d09_turn_count.py
import math
Q, wd = 12, 1.0; h = math.pi / Q
def loop(Ro, Ri, i):
    d = (i + 0.5) * wd; Ro_i = Ro - i * wd; Ri_i = Ri + i * wd
    if not (d < Ri_i * math.sin(h) and Ri_i < Ro_i): return None
    po, pi_ = math.asin(d / Ro_i), math.asin(d / Ri_i)
    L = 2 * Ro_i * (h - po) + 2 * Ri_i * (h - pi_) + 2 * (Ro_i * math.cos(po) - Ri_i * math.cos(pi_))
    n = 400; A = 0.0
    for k in range(n):                     # exact polar area of the loop (centre-line), midpoint rule
        r = Ri_i + (Ro_i - Ri_i) * (k + 0.5) / n
        A += 2 * (h - math.asin(d / r)) * r * (Ro_i - Ri_i) / n
    return L, A
best = []
for N in range(4, 11):
    for Ri10 in range(200, 300, 2):          # inner centre-line radius 20.0 ... 29.8 mm
        for Ro10 in range(420, 480, 2):      # outer centre-line radius 42.0 ... 47.8 mm
            Ri, Ro = Ri10 / 10, Ro10 / 10; Ls = []; As = []
            ok = True
            for i in range(N):
                r = loop(Ro, Ri, i)
                if r is None: ok = False; break
                Ls.append(r[0]); As.append(r[1])
            if not ok: continue
            Ltot = sum(Ls); Amid = As[N // 2] if N % 2 else 0.5 * (As[N // 2 - 1] + As[N // 2])
            err = abs(Ltot - 405.5) / 405.5 + abs(Amid - 171) / 171
            best.append((err, N, Ri, Ro, round(Ltot, 1), round(Amid, 1)))
best.sort()
print('best fits (relative error sum, N, R_i0, R_o0 centre-line mm, L per coil-layer mm, mid-loop area mm^2):')
for b in best[:8]: print('  ', b)
for N in range(5, 10):
    c = [b for b in best if b[1] == N][:1]
    print(f'  best for N={N}:', c[0] if c else None)
