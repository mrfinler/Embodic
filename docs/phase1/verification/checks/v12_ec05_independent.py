# Prepared by: Agent 4 — Independent Verificator — model: claude-opus-5-5
# Independent check of EC-05 (DEF-18 fix): (1) my own digitisation of D09 Fig. 7 (p.4, embedded raster extracted with
# `pdfimages -f 4 -l 4 -png <D09 pdf> d09p4img`, image 002, 905 x 486 px; axes calibrated on the tick marks found in the
# raster: r = 25 mm at x = 61.5, 30/35/40/46 mm at x = 259/456.5/654/891; B = 0.8/0.7/0.6/0.5/0.3 T at y = 9/91.5/174/256/420.5);
# (2) comparison with Agent 2's embedded digitisation; (3) the EQ-05 profile of the same rotor computed by calling the
# read-only Xcoil engine from node; (4) e_edge of the adopted rule k(d) = 1 - 0.47 exp(-d/(0.9 G)) for the default, O1, O2.
# Usage: python3 v12_ec05_independent.py <path to fig7.png>
import sys, json, subprocess, re
import numpy as np
from PIL import Image
im = np.array(Image.open(sys.argv[1]).convert('L')).astype(int)
x2r = lambda x: 25 + (x - 61.5) / 39.5
y2b = lambda y: 0.8 - (y - 9) * (0.5 / (420.5 - 9))
pts = []
for x in range(63, 891):
    ys = np.where(im[:415, x] < 110)[0]
    ys = ys[ys > 5]
    if len(ys): pts.append((x2r(x), y2b(ys.mean())))
pts = np.array(pts)
A2 = json.loads('[' + re.search(r'const FIG = \[(.*?)\];', open('/home/claude/embodic/docs/phase1/engineering/checks/edge_zone_d09.js').read()).group(1) + ']')
A2 = np.array(A2)
mine_at = np.interp(A2[:, 0], pts[:, 0], pts[:, 1])
print(f'own digitisation: {len(pts)} columns; vs Agent 2 points: max |dB| = {np.abs(mine_at - A2[:, 1]).max():.4f} T, mean {np.abs(mine_at - A2[:, 1]).mean():.4f} T')
for r in (25.2, 25.5, 26.0, 27.0, 28.0, 35.5, 44.0, 45.0, 45.8):
    print(f'  r = {r:5.1f} mm: own {np.interp(r, pts[:, 0], pts[:, 1]):.3f} T, Agent 2 {np.interp(r, A2[:, 0], A2[:, 1]):.3f} T')
# EQ-05 profile (pole-centre value, odd n <= 13) of the D09 Table 3 rotor at the mid-plane from the engine
rr = np.linspace(25.05, 45.95, 419)
js = ("const E=require('/home/claude/serpentine/src/engine.js');const F={pp:8,Br:1.33,muR:1.05,lm:2,alphaP:0.8,G:1.5};"
      "const rr=%s;console.log(JSON.stringify(rr.map(r=>{let s=0;for(let n=1;n<=13;n+=2)s+=E.fieldHarmonic(n,r,1.5,F).Bz;return s;})))" % json.dumps(rr.tolist()))
b2 = np.array(json.loads(subprocess.run(['node', '-e', js], capture_output=True, text=True).stdout))
bf = np.interp(rr, pts[:, 0], pts[:, 1])
plate = (rr >= 30) & (rr <= 41); norm = bf[plate].mean() / b2[plate].mean()
print(f'plateau 30-41 mm: own FEA reading {bf[plate].mean():.3f} T, EQ-05 {b2[plate].mean():.3f} T, ratio {norm:.3f}')
ratio = (bf * rr).sum() / (b2 * norm * rr).sum()
print(f'int B r dr over 25-46 mm: FEA/EQ-05 (plateau-normalised) = {ratio:.4f} -> EQ-05 high by {100 * (1 - ratio):.2f} % of the model value')
for d in (0.05, 0.5, 1.0, 1.5, 2.0, 3.0, 4.5):
    kin = np.interp(25 + d, rr, bf) / (np.interp(25 + d, rr, b2) * norm); kout = np.interp(46 - d, rr, bf) / (np.interp(46 - d, rr, b2) * norm)
    print(f'  k(d = {d:4.2f} mm): inner {kin:.3f}, outer {kout:.3f}, fit 1-0.47exp(-d/1.35) = {1 - 0.47 * np.exp(-d / 1.35):.3f}')
# e_edge of the adopted rule, own implementation
js2 = r"""const E=require('/home/claude/serpentine/src/engine.js');
function e(rA,rB,F,G,al,cA,cB){let t=0,s=0;const n=4000,a=Math.max(rA,cA),b=Math.min(rB,cB);for(let i=0;i<n;i++){const r=a+(b-a)*(i+.5)/n,
 w=Math.abs(E.fieldHarmonic(1,r,G,Object.assign({},F,{G:G,alphaP:al(r)})).Bz*r);t+=w;const d=Math.min(r-rA,rB-r);s+=w*0.47*Math.exp(-d/(0.9*G));}return s/t;}
const blk=r=>16*Math.asin(3/r)/Math.PI;
console.log(JSON.stringify({default_12_16:e(18,38,{pp:8,Br:1.315,muR:1.05,lm:2},1.31,blk,18,38),O1_D08:e(15.4,43.4,{pp:5,Br:1.38,muR:1.05,lm:5},1.4,()=>0.72,12.5,44),
 O2_D09_N8:e(25,46,{pp:8,Br:1.33,muR:1.05,lm:2},1.5,()=>0.8,25.2,47.6), O1_D08_G1p7:e(15.4,43.4,{pp:5,Br:1.38,muR:1.05,lm:5},1.7,()=>0.72,12.5,44)}));"""
print('e_edge (own implementation of the adopted rule):', subprocess.run(['node', '-e', js2], capture_output=True, text=True).stdout.strip())
