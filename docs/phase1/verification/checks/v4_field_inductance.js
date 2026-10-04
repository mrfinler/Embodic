// Prepared by: Agent 4 — Independent Verificator — model: claude-opus-5-5
// (1) Field model: own implementation of the closed form in EQ-05 (cosh/sinh form) vs engine fieldHarmonic at finite r,
//     and both vs the 1-D magnetic circuit B = Br*lm/(lm + mur*G) (fundamental (4/pi) sin(pi ap/2) B) for r -> infinity.
// (2) Inductance: magnetising inductance forms of D10 eq.14 and D15 eq.14 evaluated for Agent 2's C9 case and an
//     indicative D09 case; ratio check.  Run: node docs/phase1/verification/checks/v4_field_inductance.js
const E = require('/home/claude/serpentine/src/engine.js');
function bzMine(n, r, z, F) {   // EQ-05 as written in equation_specification_draft.md
  const u = n * F.pp / r, K = 4 * F.Br / (n * Math.PI) * Math.sin(n * Math.PI * F.alphaP / 2);
  const coth = x => Math.cosh(x) / Math.sinh(x);
  if (!isFinite(F.G)) return K * Math.exp(-u * z) / (1 + F.muR * coth(u * F.lm));
  const zz = z <= F.G ? z : 2 * F.G - z;
  return K * Math.cosh(u * (F.G - zz)) / (Math.cosh(u * F.G) + F.muR * coth(u * F.lm) * Math.sinh(u * F.G));
}
let maxRel = 0;
for (const F of [{ pp: 8, Br: 1.3, muR: 1.05, lm: 2, alphaP: 0.55, G: 1.31 }, { pp: 5, Br: 1.38, muR: 1.0, lm: 5, alphaP: 0.72, G: 1.4 }, { pp: 8, Br: 1.33, muR: 1.05, lm: 2, alphaP: 0.8, G: Infinity }])
  for (const n of [1, 3, 5, 13]) for (const r of [18, 28, 38]) for (const z of [0, 0.5, 1.0, 1.31]) {
    const a = E.fieldHarmonic(n, r, z, F).Bz, b = bzMine(n, r, z, F); maxRel = Math.max(maxRel, Math.abs(a - b) / Math.abs(b)); }
console.log('engine fieldHarmonic vs own EQ-05 closed form, 144 points (3 rotors x n{1,3,5,13} x r{18,28,38} x z): max rel diff =', maxRel.toExponential(2));
for (const [Br, mur, lm, ap, G] of [[1.30, 1.05, 3.0, 0.85, 2.0], [1.315, 1.05, 2.0, 0.55, 1.31], [1.2, 1.10, 5.0, 0.7, 3.0]]) {
  const oneD = 4 / Math.PI * Math.sin(Math.PI * ap / 2) * Br * lm / (lm + mur * G);
  const r = 1e7, F = { pp: 8, Br, muR: mur, lm, alphaP: ap, G };
  const zs = [0, G / 2, G].map(z => E.fieldHarmonic(1, r, z, F).Bz);
  console.log(`1-D limit Br=${Br} mur=${mur} lm=${lm} ap=${ap} G=${G}: closed 1-D B1=${oneD.toFixed(6)} T; engine r=1e7 mm at z=0,G/2,G: ${zs.map(x => x.toFixed(6)).join(', ')}; max rel ${Math.max(...zs.map(x => Math.abs(x - oneD) / oneD)).toExponential(2)}`);
}
// (2) inductance
const mu0 = 4e-7 * Math.PI;
function Ld10(N, kw, Do, Di, p, dp) { return 3 * mu0 / (Math.PI * dp) * Math.pow(N * kw / (2 * p), 2) * (Do * Do - Di * Di); }   // D10 eq.14 as printed
function Ld15(N, kw, Do, Di, p, dp, m = 3) { return m * mu0 / dp * Math.pow(N * kw, 2) / (8 * p * p) * (Do * Do - Di * Di); } // D15 eq.14 as printed
function Lmine(N, kw, Do, Di, p, dp, m = 3) {           // own derivation: F = (m/2)(4/pi)(N kw/(2p)) I_pk ; B = mu0 F/dp ;
  const Fpk_per_A = (m / 2) * (4 / Math.PI) * (N * kw / (2 * p));            // Phi = B (Ro^2 - Ri^2)/p ; psi = N kw Phi
  const B = mu0 * Fpk_per_A / dp, Phi = B * ((Do / 2) ** 2 - (Di / 2) ** 2) / p; return N * kw * Phi; }
const c9 = { N: 64, Do: 0.076, Di: 0.036, p: 8, dp: 6.62e-3 };
for (const kw of [0.600, 0.866]) console.log(`C9 case (12/16, N=64, D 76/36 mm, delta' 6.62 mm), kw=${kw}: own ${(Lmine(c9.N, kw, c9.Do, c9.Di, c9.p, c9.dp) * 1e6).toFixed(3)} uH, D10 eq.14 ${(Ld10(c9.N, kw, c9.Do, c9.Di, c9.p, c9.dp) * 1e6).toFixed(3)} uH, D15 eq.14 ${(Ld15(c9.N, kw, c9.Do, c9.Di, c9.p, c9.dp) * 1e6).toFixed(3)} uH, ratio D15/D10 = ${(Ld15(1, 1, 1, 0, 1, 1) / Ld10(1, 1, 1, 0, 1, 1)).toFixed(6)} (pi/2 = ${(Math.PI / 2).toFixed(6)})`);
// indicative D09 concentric (12/16, 4 coils/phase, 2 layers, N 6..8 turns/coil/layer -> 48..64 series turns; D 92/50 mm; iron-to-iron 7 mm)
for (const Nt of [6, 7, 8]) { const N = 4 * 2 * Nt; console.log(`D09-like (indicative only): N_series=${N}, kw=0.866, D 92/50 mm, delta' 7 mm -> L_m(D10 form) = ${(Ld10(N, 0.866, 0.092, 0.050, 8, 7e-3) * 1e6).toFixed(2)} uH (D09 measured 14.8 uH, quantity measured not defined in the pages read)`); }
