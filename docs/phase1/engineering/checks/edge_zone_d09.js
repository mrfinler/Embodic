// Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5
// DEF-18: basis for the graded EQ-05 radial-edge rule. D09 Fig. 7 (p.4, 3-D FEA, |B| at mid-gap vs radius) was digitised
// from a 300-dpi render of the PDF page (pixel calibration: 25 mm @ x=168, 40 mm @ x=761.5; 0.8 T @ y=41.5, 0.3 T @ y=454);
// the digitised points are embedded below (figure reading -> `inferred`). Compares the FEA radial profile with the 2-D model
// (EQ-05, engine fieldHarmonic, pole-centre value n<=13, D09 Table 3 rotor), derives the edge deficit profile and the
// resulting over-estimate of int B r dr, then applies the proposed graded rule to the default design, O1 (D08) and O2 (D09).
// Run: node checks/edge_zone_d09.js
const E = require('/home/claude/serpentine/src/engine.js');
const FIG = [[25.101, 0.397], [25.303, 0.4406], [25.505, 0.4824], [25.708, 0.5121], [25.91, 0.5388], [26.112, 0.5648], [26.314, 0.5885], [26.516, 0.6097], [26.719, 0.6291], [26.921, 0.6467], [27.123, 0.6618], [27.325, 0.6752], [27.527, 0.6848], [27.73, 0.6909], [27.932, 0.6958], [28.134, 0.7006], [28.336, 0.7055], [28.538, 0.7085], [28.741, 0.7103], [28.943, 0.7127], [29.145, 0.7152], [29.347, 0.717], [29.549, 0.7188], [29.751, 0.72], [29.954, 0.7212], [30.156, 0.723], [30.358, 0.7242], [30.56, 0.7255], [30.762, 0.7273], [30.965, 0.7279], [31.167, 0.7285], [31.369, 0.7291], [31.571, 0.7297], [31.773, 0.7297], [31.976, 0.7303], [32.178, 0.7303], [32.38, 0.7303], [32.582, 0.7309], [32.784, 0.7309], [32.987, 0.7309], [33.189, 0.7321], [33.391, 0.7321], [33.593, 0.7327], [33.795, 0.7333], [33.997, 0.7333], [34.2, 0.7333], [34.402, 0.7333], [34.604, 0.7339], [34.806, 0.7339], [35.008, 0.7339], [35.211, 0.7339], [35.413, 0.7339], [35.615, 0.7345], [35.817, 0.7345], [36.019, 0.7345], [36.222, 0.7345], [36.424, 0.7352], [36.626, 0.7352], [36.828, 0.7352], [37.03, 0.7358], [37.233, 0.7358], [37.435, 0.7364], [37.637, 0.7364], [37.839, 0.737], [38.041, 0.737], [38.243, 0.737], [38.446, 0.737], [38.648, 0.737], [38.85, 0.737], [39.052, 0.737], [39.254, 0.737], [39.457, 0.7364], [39.659, 0.7364], [39.861, 0.7364], [40.063, 0.7364], [40.265, 0.7358], [40.468, 0.7352], [40.67, 0.7345], [40.872, 0.7339], [41.074, 0.7333], [41.276, 0.7321], [41.479, 0.7315], [41.681, 0.7303], [41.883, 0.7291], [42.085, 0.7273], [42.287, 0.7261], [42.489, 0.7236], [42.692, 0.7188], [42.894, 0.7127], [43.096, 0.7067], [43.298, 0.7006], [43.5, 0.6933], [43.703, 0.6861], [43.905, 0.6782], [44.107, 0.6697], [44.309, 0.6503], [44.511, 0.6248], [44.714, 0.597], [44.916, 0.5673], [45.118, 0.5364], [45.32, 0.5018], [45.522, 0.4667], [45.725, 0.4285], [45.927, 0.3879]];   // [r_mm, B_T] digitised from D09 Fig. 7
function fea(r) { for (let i = 1; i < FIG.length; i++) if (r <= FIG[i][0]) { const [r0, b0] = FIG[i - 1], [r1, b1] = FIG[i]; return b0 + (b1 - b0) * (r - r0) / (r1 - r0); } return FIG[FIG.length - 1][1]; }
const F09 = { pp: 8, Br: 1.33, muR: 1.05, lm: 2, alphaP: 0.8, G: 1.5 };
const pk = (r, F, z) => { let s = 0; for (let n = 1; n <= 13; n += 2) s += E.fieldHarmonic(n, r, z, F).Bz; return s; };
// 1) D09: FEA vs 2-D model, plateau normalisation at r = 30...41 mm
let pf = 0, pm = 0, np_ = 0; for (let r = 30; r <= 41; r += 0.25) { pf += fea(r); pm += pk(r, F09, 1.5); np_++; }
const norm = (pf / np_) / (pm / np_);
console.log(`D09 plateau 30-41 mm: FEA ${(pf / np_).toFixed(3)} T, 2-D model ${(pm / np_).toFixed(3)} T (ratio ${norm.toFixed(3)})`);
let I2 = 0, If = 0; const M = 4000;
const prof = [];
for (let i = 0; i < M; i++) { const r = 25 + 21 * (i + 0.5) / M, b2 = pk(r, F09, 1.5) * norm, bf = fea(r); I2 += b2 * r; If += bf * r; }
console.log(`D09: int B r dr, FEA profile / 2-D profile (plateau-normalised) = ${(If / I2).toFixed(4)} -> edge over-estimate of the 2-D model = ${(100 * (I2 / If - 1)).toFixed(2)} % (of the FEA value), ${(100 * (1 - If / I2)).toFixed(2)} % (of the model value)`);
for (const d of [0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.5]) {
  const kin = fea(25 + d) / (pk(25 + d, F09, 1.5) * norm), kout = fea(46 - d) / (pk(46 - d, F09, 1.5) * norm);
  prof.push(`d=${d} mm: k_in ${kin.toFixed(3)}, k_out ${kout.toFixed(3)}`);
}
console.log('D09 edge factor k = B_FEA / B_2D vs distance d from the magnet end (d/G = d/1.5):\n  ' + prof.join('\n  '));
// 2) graded rule: deficit model k(d) = 1 - D*(1 - d/(c*G)) for d < c*G (linear), fitted D and c from D09
function edgeError(rA, rB, F, G, alphaOf, D, c, rCoilA, rCoilB) {
  let tot = 0, err = 0, zone = 0; const n = 4000, a = Math.max(rA, rCoilA), b = Math.min(rB, rCoilB);
  for (let i = 0; i < n; i++) { const r = a + (b - a) * (i + 0.5) / n, w = E.fieldHarmonic(1, r, G, Object.assign({}, F, { alphaP: alphaOf(r) })).Bz * r;
    tot += w; const d = Math.min(r - rA, rB - r); if (d < c * G) { zone += w; err += w * D * (1 - d / (c * G)); } }
  return { share: zone / tot, err: err / tot };
}
const blk = (w, p) => r => 2 * p * Math.asin(w / (2 * r)) / Math.PI;
const cases = [
  ['default 12/16 (blocks 20x6x2, magnets r 18-38, coil copper 18-38)', 18, 38, { pp: 8, Br: 1.315, muR: 1.05, lm: 2 }, 1.31, blk(6, 8), 18, 38],
  ['O1 D08 (magnets r 15.4-43.4, coil 12.5-44, G 1.4 assumed)', 15.4, 43.4, { pp: 5, Br: 1.38, muR: 1.05, lm: 5 }, 1.4, () => 0.72, 12.5, 44],
  ['O2 D09 (magnets r 25-46, coil centre-lines 25.2-47.6, N = 8)', 25, 46, { pp: 8, Br: 1.33, muR: 1.05, lm: 2 }, 1.5, () => 0.8, 25.2, 47.6]];
for (const [D, c] of [[0.5, 2.0], [0.5, 1.5], [0.4, 1.0]]) {
  for (const [name, rA, rB, F, G, al, cA, cB] of cases) {
    const e = edgeError(rA, rB, Object.assign({ G }, F), G, al, D, c, cA, cB);
    console.log(`D=${D}, zone=${c}G | ${name}: edge-zone share ${(100 * e.share).toFixed(1)} %, Ke over-estimate add-on ${(100 * e.err).toFixed(2)} %`);
  }
}

// 3) Adopted edge model (fit to the D09 points above): k(d) = 1 - D_e*exp(-d/(c_e*G)), D_e = 0.47, c_e = 0.9.
//    Graded rule: e_edge = sum_seg w*D_e*exp(-d/(c_e G)) / sum_seg w over EMF-producing radial pieces inside the magnet span,
//    w = |B_z,1(r,z) r dr| (here: uniform radial coverage of the coil annulus within the magnet span).
const De = 0.47, ce = 0.9;
for (const d of [0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.5]) console.log(`fit check d=${d}: model k ${(1 - De * Math.exp(-d / (ce * 1.5))).toFixed(3)}  digitised k_in ${(fea(25 + d) / (pk(25 + d, F09, 1.5) * norm)).toFixed(3)}`);
function edgeExp(rA, rB, F, G, alphaOf, rCoilA, rCoilB) {
  let tot = 0, err = 0; const n = 4000, a = Math.max(rA, rCoilA), b = Math.min(rB, rCoilB);
  for (let i = 0; i < n; i++) { const r = a + (b - a) * (i + 0.5) / n, w = E.fieldHarmonic(1, r, G, Object.assign({}, F, { alphaP: alphaOf(r) })).Bz * r;
    tot += w; const d = Math.min(r - rA, rB - r); err += w * De * Math.exp(-d / (ce * G)); }
  return err / tot;
}
for (const [name, rA, rB, F, G, al, cA, cB] of cases) console.log(`ADOPTED rule | ${name}: e_edge = ${(100 * edgeExp(rA, rB, Object.assign({ G }, F), G, al, cA, cB)).toFixed(2)} %`);
for (const L of [10, 12, 15, 20, 30]) console.log(`magnet radial length ${L} mm, G 1.5 mm (D09 rotor, centred at 35.5 mm): e_edge = ${(100 * edgeExp(35.5 - L / 2, 35.5 + L / 2, Object.assign({ G: 1.5 }, F09), 1.5, () => 0.8, 0, 1e9)).toFixed(2)} %`);
