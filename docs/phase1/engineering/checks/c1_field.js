// Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5
// C1 field checks against the Xcoil v3 engine (read-only). Run: node checks/c1_field.js
const E = require('/home/claude/serpentine/src/engine.js');
// C1a: large pole pitch vs 1-D magnetic circuit  B1 = (4/pi) sin(pi*ap/2) * Br*lm/(lm+mur*G)
const F = { pp: 8, Br: 1.30, muR: 1.05, lm: 3.0, alphaP: 0.85, G: 2.0 };
for (const zz of [0, 1, 2]) { const b = E.fieldHarmonic(1, 1e7, zz, F).Bz; const ref = 4 / Math.PI * Math.sin(Math.PI * 0.85 / 2) * 1.30 * 3.0 / (3.0 + 1.05 * 2.0);
  console.log('C1a z=' + zz, 'engine', b.toFixed(6), '1-D', ref.toFixed(6), 'rel', ((b - ref) / ref).toExponential(2)); }
// C1b: D08 eq.3.1 (implemented independently, odd n) vs engine; identity expected for muPM = 1
function d08(n, r, p, Brem, mu, hPM, z2, z, ap) { const u = n * p / r; return 4 * Brem / (n * Math.PI * mu) * Math.sin(n * Math.PI * ap / 2) * Math.sinh(u * hPM) / Math.sinh(u * z2) * Math.cosh(u * (z2 - z)); }
const p = 5, r2 = 40, hPM = 5, ap = 2 * Math.asin(9 / 40) / (Math.PI / 5);   // D08 Table 3.1: 18 mm wide magnet, r = 40 mm, D08 eq. 3.3
for (const mu of [1.0, 1.05]) for (const g of [1.4, 2.8]) { const z2 = hPM + g; let pkE = 0, pkD = 0;
  for (let n = 1; n <= 13; n += 2) { pkE += E.fieldHarmonic(n, r2, g, { pp: p, Br: 1.38, muR: mu, lm: hPM, alphaP: ap, G: g }).Bz; pkD += d08(n, r2, p, 1.38, mu, hPM, z2, z2, ap); }
  const b1E = E.fieldHarmonic(1, r2, g, { pp: p, Br: 1.38, muR: mu, lm: hPM, alphaP: ap, G: g }).Bz, b1D = d08(1, r2, p, 1.38, mu, hPM, z2, z2, ap);
  console.log('C1b muPM=' + mu, 'gap/side=' + g, 'ap(r=40)=' + ap.toFixed(4), 'B1 engine', b1E.toFixed(4), 'B1 D08', b1D.toFixed(4), 'ratio', (b1D / b1E).toFixed(4), '| pole-centre B (n<=13) engine', pkE.toFixed(4), 'D08', pkD.toFixed(4)); }
// C1c: D09 Table 3 rotor (16 poles, Br 1.33 T, hm 2 mm, rotor cores 7 mm apart -> G = 1.5 mm, ap 0.8), mid-plane
for (const mu of [1.0, 1.05]) for (const r of [30, 35.5, 40]) { const Fd = { pp: 8, Br: 1.33, muR: mu, lm: 2, alphaP: 0.8, G: 1.5 }; let pk = 0;
  for (let n = 1; n <= 13; n += 2) pk += E.fieldHarmonic(n, r, 1.5, Fd).Bz;
  console.log('C1c mur=' + mu, 'r=' + r, 'B1=' + E.fieldHarmonic(1, r, 1.5, Fd).Bz.toFixed(3), 'pole-centre B (n<=13)=' + pk.toFixed(3)); }
// C1d: per-layer spread, 6 x 1 oz in 0.62 mm, gap 1.0 mm, p = 8, r = 28 mm, double rotor
const stk = E.stackupFor(E.normalizeParams({ copperOzOuter: 1, copperOzInner: 1, boardThickness: 0.62 }).params, 6);
const b = stk.z.map(z => E.fieldHarmonic(1, 28, z + 1.0, { pp: 8, Br: 1.3, muR: 1.05, lm: 2, alphaP: 0.55, G: (0.62 + 2) / 2 }).Bz);
console.log('C1d B1 per layer', b.map(x => x.toFixed(4)).join(' '), 'spread', ((Math.max(...b) / Math.min(...b) - 1) * 100).toFixed(3) + ' %');
// C1e: rectangular 20x6 blocks (D08 eq.3.3 alpha_p(r)) vs constant alpha_p 0.55, r = 18..38 mm, mid-plane
let I1 = 0, I2 = 0; const M = 400, base = { pp: 8, Br: 1.3, muR: 1.05, lm: 2, G: 1.31 };
for (let i = 0; i < M; i++) { const r = 18 + 20 * (i + 0.5) / M, a = 2 * Math.asin(3 / r) / (Math.PI / 8);
  I1 += E.fieldHarmonic(1, r, 1.31, Object.assign({ alphaP: a }, base)).Bz * r * 20 / M; I2 += E.fieldHarmonic(1, r, 1.31, Object.assign({ alphaP: 0.55 }, base)).Bz * r * 20 / M; }
console.log('C1e alpha_p(18/28/38 mm) =', [18, 28, 38].map(r => (2 * Math.asin(3 / r) / (Math.PI / 8)).toFixed(3)).join('/'), ' int B1 r dr: blocks', I1.toFixed(2), 'const 0.55', I2.toFixed(2), 'ratio', (I1 / I2).toFixed(4));
