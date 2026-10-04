// Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5
// Reference values used in equation_specification_draft.md. Run: node checks/c9_reference_values.js
const E = require('/home/claude/serpentine/src/engine.js');
const s = 1 / E.copperResistivity(20), f = 8 * 1000 / 60, w = 0.5e-3, h = 34.8e-6, L = 20e-3, B = 0.70, om = 2 * Math.PI * f;
const P24 = s * om * om * B * B * w * w * (w * h * L) / 24;
console.log('eddy: fe', f.toFixed(2), 'Hz; one 20 mm x 0.5 mm x 34.8 um trace, peak Bz 0.70 T: P(/24) =', P24.toExponential(4), 'W, P(/12) =', (2 * P24).toExponential(4), 'W; skin depth', E.skinDepthMm(f, 20).toFixed(2), 'mm');
const A = E.viaBarrelArea(0.3, 0.025); console.log('via: A =', A.toFixed(6), 'mm2; R(l = 0.2 mm, 20 C) =', (E.copperResistivity(20) * 0.2e-3 / (A * 1e-6) * 1e3).toFixed(4), 'mOhm');
console.log('D08 Table 9.1: 1.47 V/(454 rpm) =', (1.47 / (454 * 2 * Math.PI / 60)).toFixed(4), 'V s/rad; 9.35 V/(2877 rpm) =', (9.35 / (2877 * 2 * Math.PI / 60)).toFixed(4), '; 1/32.32 =', (1 / 32.32).toFixed(5));
console.log('IPC-2221 (engine form) 0.5 mm x 34.8 um, dT 20 K: external', E.ipc2221Current(0.5 * 0.0348, 20, false).toFixed(3), 'A, internal', E.ipc2221Current(0.5 * 0.0348, 20, true).toFixed(3), 'A');
console.log('R: 1000 mm x 0.5 mm x 34.8 um: R20 =', E.traceResistance(1000, 0.5, 0.0348, 20).toFixed(5), 'ohm, R60 =', E.traceResistance(1000, 0.5, 0.0348, 60).toFixed(5), 'ohm');
// inductance: engine current-sheet model vs magnetising formula (D10 eq.14 form and D15 eq.14 form), 12/16, 8 turns, 2 layers
const b = { topology: 'sector', sectors: 12, poles: 16, phases: 3, turns: 8, coilSides: 'parallel', coilEnds: 'arc', cornerStyle: 'sharp', coilLayers: 2, traceWidth: 0.5, clearance: 0.2, coilGap: 0.2, rIn: 18, rOut: 38,
  copperOzOuter: 1, copperOzInner: 1, boardThickness: 0.62, viaDrill: 0.3, viaPad: 0.5, interconnect: false, connection: 'open', tempC: 20, rpm: 1000, currentRms: 1, Br: 1.3, muR: 1.05, magnetThickness: 2, magnetArcRatio: 0.55, airgap: 1.0, rotorType: 'double' };
const a = E.compute(b).analysis, ind = a.inductance, mu0 = 4e-7 * Math.PI, N = 4 * 8 * 2, dp = (2 * 2 + 2 * 1 + 0.62) * 1e-3;
for (const kw of [a.kw1, 0.866]) { const Lm = 3 * mu0 / (4 * Math.PI) * Math.pow(N * kw, 2) * (0.076 ** 2 - 0.036 ** 2) / (64 * dp);
  console.log('L: engine Ls', (ind.Ls * 1e6).toFixed(2), 'uH (Lself', (ind.Lself * 1e6).toFixed(2), 'M', (ind.M * 1e6).toFixed(2), 'fund. share', ind.fundamentalShare.toFixed(3), ') | magnetising form, N =', N, 'kw =', kw.toFixed(3), ': D10 eq.14', (Lm * 1e6).toFixed(2), 'uH, D15 eq.14', (Lm * Math.PI / 2 * 1e6).toFixed(2), 'uH'); }
