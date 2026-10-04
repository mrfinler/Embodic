# Prepared by: Agent 4 — Independent Verificator — model: claude-opus-5-5
# Independent re-derivation (polar form, written without reading Agent 2's code paths) of the true-spiral centre-line length
# used for the EQ-03 tolerance basis (DEF-09). Same geometric definition as Agent 2's eq03_spiral_vs_loops.py header:
# sides parallel to the sector edges at offsets d_t = (t+1/2) w_d; turn t = outer arc at R_out,t (offset d_t both sides),
# right side d_t inward, inner arc at R_in,t from right d_t to left d_{t+1} if it exists, else the intersection of right d_t
# and left d_{t+1}; left side d_{t+1} outward to R_out,t+1; last turn: lead on left d_N up to r_v = (r_end + R_out,N-1)/2.
# Side length between radii r1<r2 on a line at offset d: sqrt(r2^2-d^2)-sqrt(r1^2-d^2). Angular half-position of a side
# line at radius r: h - asin(d/r), h = pi/Q.  Run: python3 docs/phase1/verification/checks/v10_true_spiral_length.py
import math
def s(r, d): return math.sqrt(r * r - d * d)
def spiral(Ro, Ri, wd, Q, N):
    h = math.pi / Q; L = 0.0; kinds = []
    for t in range(N):
        dt, dn = (t + .5) * wd, (t + 1.5) * wd
        Rot, Rin = Ro - t * wd, Ri + t * wd
        L += 2 * Rot * (h - math.asin(dt / Rot))                                   # outer arc
        if Rin > dn and math.asin(dt / Rin) + math.asin(dn / Rin) < 2 * h:        # inner arc exists
            L += s(Rot, dt) - s(Rin, dt)                                           # right side
            L += Rin * ((h - math.asin(dt / Rin)) + (h - math.asin(dn / Rin)))     # inner arc
            rend = Rin; kinds.append('trap')
        else:                                                                     # sides meet: bisection on r
            lo, hi = dn * 1.0000001, Rot
            f = lambda r: math.asin(dt / r) + math.asin(min(1, dn / r)) - 2 * h
            for _ in range(200):
                mid = (lo + hi) / 2
                if f(mid) > 0: lo = mid
                else: hi = mid
            rend = (lo + hi) / 2; L += s(Rot, dt) - s(rend, dt); kinds.append('tri')
        top = (Ro - (t + 1) * wd) if t < N - 1 else (rend + Rot) / 2              # next outer arc, or lead end r_v
        L += s(top, dn) - s(rend, dn)                                             # left side d_{t+1}
    return L, kinds
for name, Ro, Ri, wd, Q, N, a2 in [('D08 N=3', 44.0, 12.5, 2.86, 12, 3, 143.941), ('D08 N=2', 44.0, 12.5, 2.86, 12, 2, 123.637),
                                   ('12/16 N=8', 37.75, 18.25, 0.7, 12, 8, 364.353), ('12/16 N=11', 37.75, 18.25, 0.7, 12, 11, 402.979),
                                   ('18/16 N=4', 37.75, 18.25, 0.7, 18, 4, 182.711), ('18/16 N=8', 37.75, 18.25, 0.7, 18, 8, 261.613)]:
    L, k = spiral(Ro, Ri, wd, Q, N)
    print(f"{name:11s} own spiral {L:9.3f} mm   Agent 2 {a2:9.3f} mm   diff {L - a2:+.3f} mm   turns {''.join('T' if x == 'trap' else 't' for x in k)}")
