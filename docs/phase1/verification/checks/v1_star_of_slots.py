# Prepared by: Agent 4 — Independent Verificator — model: claude-opus-5-5
# Independent star-of-slots / winding-factor check (written from scratch; does not import Agent 2's kw.py).
# Exact rational electrical angles (fractions.Fraction, degrees) -> no floating-point ties at belt edges.
# Coil k centred at theta_k = 360*k/Q (mech). EMF phasor angle alpha_k = p*theta_k (elec, mod 360).
# Belts (60 deg wide, centred on): A+ 0, C- 60, B+ 120, A- 180, C+ 240, B- 300.
# Tie rule T1: half-open [c-30, c+30); tie rule T2: half-open (c-30, c+30]. A combination is reported balanced
# only if equal coil counts, equal |phasor sum| (1e-12) and 120 deg spacing hold.
# Pitch factor of the OUTERMOST turn (span 2*pi/Q mech): kp_n = |sin(n*p*pi/Q)|.
# Run: python3 docs/phase1/verification/checks/v1_star_of_slots.py
from fractions import Fraction as Fr
import cmath, math
BELT = [('A', +1), ('C', -1), ('B', +1), ('A', -1), ('C', +1), ('B', -1)]
def belt_index(a, rule):
    x = (a + 30) % 360                      # Fraction arithmetic, exact
    i = int(x // 60)
    if rule == 'T2' and x % 60 == 0:        # exactly on an edge -> belong to the lower belt
        i = (i - 1) % 6
    return i
def analyse(Q, poles, rule='T1', n=1, groups=1):
    p = poles // 2
    pos = [Fr(360 * k, Q) for k in range(Q)]
    if groups == 2:
        pos += [x + Fr(180, Q) for x in pos]          # second layer group rotated by half a coil pitch
    alpha = [(p * x) % 360 for x in pos]
    asg = [BELT[belt_index(a, rule)] for a in alpha]
    ph = {}
    for P in 'ABC':
        idx = [i for i, (q, s) in enumerate(asg) if q == P]
        ssum = sum(asg[i][1] * cmath.exp(1j * math.radians(float(n * alpha[i]))) for i in idx)
        ph[P] = (len(idx), abs(ssum) / max(1, len(idx)), cmath.phase(ssum) if idx else None)
    cnt = [ph[P][0] for P in 'ABC']; mag = [ph[P][1] for P in 'ABC']
    ok = len(set(cnt)) == 1 and cnt[0] > 0 and max(mag) - min(mag) < 1e-12
    if ok and n == 1:
        d = math.degrees(ph['B'][2] - ph['A'][2]) % 360
        ok = abs(d - 120) < 1e-9 or abs(d - 240) < 1e-9
    kp = abs(math.sin(n * p * math.pi / Q))
    pattern = ''.join(q if s > 0 else q.lower() for q, s in asg)
    on_edge = sum(1 for a in alpha if (a + 30) % 60 == 0)
    return dict(ok=ok, counts=cnt, kd=ph['A'][1], kp=kp, kw=ph['A'][1] * kp, pattern=pattern, edge=on_edge,
                angA=None if ph['A'][2] is None else math.degrees(ph['A'][2]))
cases = [(12, 10), (12, 14), (12, 16), (18, 16), (16, 16), (15, 16), (24, 16), (24, 14), (24, 22), (24, 26), (9, 10), (18, 20)]
print('Q/2p   t=gcd(Q,p) Q/(3t)  T1-bal T2-bal  on-edge  kd1     kp1     kw1     kw3     kw5     kw7    pattern(T1)')
for Q, P in cases:
    p = P // 2; t = math.gcd(Q, p)
    r1 = analyse(Q, P, 'T1'); r2 = analyse(Q, P, 'T2')
    k3, k5, k7 = (analyse(Q, P, 'T1', n)['kw'] if r1['ok'] else float('nan') for n in (3, 5, 7))
    print(f"{Q}/{P}".ljust(7), str(t).ljust(10), f"{Q/(3*t):.3f}".ljust(7), str(r1['ok']).ljust(6), str(r2['ok']).ljust(6),
          str(r1['edge']).ljust(8), f"{r1['kd']:.4f}  {r1['kp']:.4f}  {r1['kw']:.4f}  {k3:.4f}  {k5:.4f}  {k7:.4f}  {r1['pattern'] if r1['ok'] else '-'} (counts {r1['counts']})")
print()
print('Phase-A phasor angle 12/16 =', analyse(12, 16)['angA'], 'deg; 12/14 =', round(analyse(12, 14)['angA'], 6), 'deg')
print('Two groups rotated by pi/Q (M3):')
for Q, P in [(12, 10), (12, 14), (12, 16)]:
    a = [analyse(Q, P, 'T1', n, 1)['kw'] for n in (1, 11, 13)]; b = [analyse(Q, P, 'T1', n, 2)['kw'] for n in (1, 11, 13)]
    print(f"  {Q}/{P}: single kw1/kw11/kw13 = {a[0]:.4f}/{a[1]:.4f}/{a[2]:.4f}; rotated pair = {b[0]:.4f}/{b[1]:.4f}/{b[2]:.4f}; balanced={analyse(Q, P, 'T1', 1, 2)['ok']}")
