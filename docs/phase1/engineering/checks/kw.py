# Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5
"""Independent star-of-slots / winding-factor check for non-overlapping concentrated (spiral) coils.
Coil k centred at theta_k = k*2pi/Q (mech.), span sigma = 2pi/Q (outermost turn). EMF phasor angle = p*theta_k (elec.).
60-degree phase belts: A+ 0, C- 60, B+ 120, A- 180, C+ 240, B- 300 (elec. deg). k_d = |sum s_k e^{j n p theta_k}| / N_ph ,
k_p = sin(n p sigma / 2), k_w = k_d k_p.  Formulas: standard (EV-26 D04 eq.1 is the integral-slot special case of k_d)."""
import math, cmath
from math import gcd
BELTS = [(0,'A',+1),(60,'C',-1),(120,'B',+1),(180,'A',-1),(240,'C',+1),(300,'B',-1)]
def assign(angles_deg):
    out=[]
    for a in angles_deg:
        a=(a+30+1e-7)%360   # half-open belts [c-30, c+30)
        b=BELTS[int(a//60)]
        out.append((b[1],b[2]))
    return out
def analyse(Q,p2,shift_groups=False,n=1):
    p=p2//2
    pos=[k*360.0/Q for k in range(Q)]
    if shift_groups: pos=pos+[x+180.0/Q for x in pos]
    asg=assign([(p*x)%360 for x in pos])
    res={}
    for ph in 'ABC':
        s=sum(sg*cmath.exp(1j*math.radians(n*p*x)) for x,(pp,sg) in zip(pos,asg) if pp==ph)
        cnt=sum(1 for (pp,sg) in asg if pp==ph)
        res[ph]=(cnt,abs(s)/max(cnt,1),math.degrees(cmath.phase(s)) if cnt else 0)
    kp=abs(math.sin(math.radians(n*p*(360.0/Q)/2)))
    cnts=[res[x][0] for x in 'ABC']; mags=[res[x][1] for x in 'ABC']
    ang=(res['B'][2]-res['A'][2])%360
    balanced = len(set(cnts))==1 and max(mags)-min(mags)<1e-9 and (abs(ang-120)<1e-6 or abs(ang-240)<1e-6)
    pattern=''.join(pp if sg>0 else pp.lower() for (pp,sg) in asg)
    return dict(kd=res['A'][1],kp=kp,kw=res['A'][1]*kp,balanced=balanced,pattern=pattern,counts=cnts)
print('Q  2p  q=Q/(2p m)  t=gcd(Q,p)  Q/(m t)  balanced  kd1    kp1    kw1    kw5    kw7    pattern')
for p2 in (10,14,16,20):
    for Q in (6,9,12,15,18,21,24,27):
        p=p2//2; t=gcd(Q,p); feas = (Q%3==0) and ((Q//t)%3==0)
        r=analyse(Q,p2); r5=analyse(Q,p2,n=5); r7=analyse(Q,p2,n=7)
        q=Q/(p2*3)
        if Q==p2: continue
        print(f"{Q:<3d}{p2:<4d}{q:<12.4f}{t:<12d}{(Q/(3*t)):<9.3f}{str(r['balanced']):<10s}{r['kd']:.4f} {r['kp']:.4f} {r['kw']:.4f} {r5['kw']:.4f} {r7['kw']:.4f} {r['pattern'] if r['balanced'] else '-'}  rule={'ok' if feas else 'no'}")
print()
print('Two layer groups, group 2 rotated by half a coil pitch (pi/Q), 2Q coil positions, each coil span 2pi/Q:')
for Q,p2 in ((12,16),(12,14),(12,10),(18,16),(24,16),(9,8),(15,16)):
    r=analyse(Q,p2,shift_groups=True); r1=analyse(Q,p2)
    print(f"  {Q}/{p2}: single-group kw1={r1['kw']:.4f}; two groups rotated: balanced={r['balanced']} kd1={r['kd']:.4f} kw1={r['kw']:.4f} counts={r['counts']} elec. shift of group 2 = {(p2//2)*180.0/Q:.1f} deg")
print()
print('16 coil positions (8+8 as in the render) with 3 phases:', [ (Q, (Q%3==0)) for Q in (16,)], '-> Q not divisible by m=3: no symmetric balanced 3-phase assignment')
print('D08 Fig.3.7 reference pattern (Bavaria tool), 12/10:  AabBCcaABbcC')
print()
print('Harmonic winding factors, single group vs two groups rotated by pi/Q:')
for Q,p2 in ((12,16),(12,14),(12,10),(18,16),(24,16),(15,16)):
    row=[]
    for n in (1,3,5,7,9,11,13):
        a=analyse(Q,p2,n=n)['kw']; b=analyse(Q,p2,shift_groups=True,n=n)['kw']; row.append(f"n={n}: {a:.3f}/{b:.3f}")
    print(f"  {Q}/{p2}: "+'  '.join(row))
