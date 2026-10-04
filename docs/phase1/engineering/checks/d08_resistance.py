# Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5
# D08 eq. 3.27-3.38 track length / phase resistance variants (D08 geometry: Table 4.5 p.54, Table 4.6 p.57)
import math
ri,ro,wtr,ws,N,t=12.5,44.0,2.06,0.8,3,34.8e-3
wd=wtr+ws
def coil(theta_cs, double_straight):
    L=0;S=0
    for i in range(N):
        d=i*wd+wd/2
        po=math.asin(d/(ro-i*wd)); bo=theta_cs/2-po
        pi_=math.asin(d/(ri+i*wd)); bi=theta_cs/2-pi_
        Lo=2*(ro-i*wd)*bo
        if bi>0:
            Li=2*(ri+i*wd)*bi; Ls=(d/math.tan(po)-d/math.tan(pi_))
        else:
            Li=0; Ls=(d/math.tan(po)-d/math.tan(theta_cs/2))
        Ls_tot = (4 if double_straight else 2)*Ls
        L+=Lo+Li+Ls_tot
    return L
for th,lab in [(2*math.pi/12,'30deg=2pi/Q'),(math.pi/5,'36deg=pi/p')]:
    for dbl in (False,True):
        Lc=coil(th,dbl)
        for coils in (8,4):
            Ltot=Lc*coils
            for rho in (1.724e-8, 1.724e-8*(1+0.00393*30)):
                R=rho*Ltot*1e-3/(wtr*1e-3*t*1e-3)
                print(f"{lab:12s} straight x{'4' if dbl else '2'} coils/phase={coils} Lcoil={Lc:7.1f} mm Lphase={Ltot:7.1f} mm rho={rho:.4e} R={R:.3f} ohm")
