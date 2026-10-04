// Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5
// CHECK E1: 1-turn radial-sided sector coil, 12 coils / 10 poles, 2 layers (X,Y), double rotor.
// Closed form: Ke_phase = Ncoil_ph * kd * sum_layers[ sin(p*b0)*I(Ri',Ro';z) + sin(p*b1)*I(Ri',xv;z) ]
// where I(a,b;z) = int_a^b B1(r,z) r dr (B1 from engine.fieldHarmonic), b0,b1 = angles of side and lead.
const E = require('/home/claude/serpentine/src/engine.js');
const w = 0.4, s = 0.2, rIn = 20, rOut = 40;
const P = { topology: 'sector', sectors: 12, poles: 10, phases: 3, turns: 1, coilSides: 'radial', coilEnds: 'arc', cornerStyle: 'sharp',
  coilLayers: 2, traceWidth: w, clearance: s, coilGap: s, rIn, rOut, magnetAuto: false, magnetRIn: rIn + w / 2, magnetROut: rOut - w / 2,
  interconnect: false, connection: 'open', rpm: 1000, currentRms: 1, tempC: 20, Br: 1.3, muR: 1.05, magnetThickness: 3, magnetArcRatio: 0.8, airgap: 1.0, rotorType: 'double' };
const res = E.compute(P);
if (res.errors.length) { console.log(res.errors); process.exit(1); }
const an = res.analysis, S = res.layout.S, L = res.layout.layers;
const p = 5, h = Math.PI / 12, d0 = S.gap / 2 + S.w / 2, d1 = d0 + S.pitch;
const b0 = h - Math.asin(d0 / rIn), b1 = h - Math.asin(d1 / rIn);
const Ri = rIn + w / 2, Ro = rOut - w / 2, xv = (rIn + rOut) / 2;
const F = an.field;
function I(a, b, z) { const M = 20000; let s2 = 0; for (let i = 0; i < M; i++) { const r = a + (b - a) * (i + 0.5) / M; s2 += E.fieldHarmonic(1, r, z, F).Bz * r * (b - a) / M; } return s2; }
let kc = 0; for (const Ly of L) { const z = Ly.z + P.airgap; kc += Math.sin(p * b0) * I(Ri, Ro, z) + Math.sin(p * b1) * I(Ri, xv, z); }
const sos = E.starOfSlots(12, 5, 3);
const KeClosed = sos.coilsPerPhase * sos.kw1 * kc * 1e-6;
console.log('layers z [mm]:', L.map(x => x.z.toFixed(4)).join(', '), ' G =', F.G);
console.log('b0 [deg] =', (b0 * 180 / Math.PI).toFixed(4), ' b1 [deg] =', (b1 * 180 / Math.PI).toFixed(4), ' kd(12/10) =', sos.kw1.toFixed(5), ' coils/phase =', sos.coilsPerPhase);
console.log('Ke1 engine  [V s/rad] =', an.Ke1.toExponential(6));
console.log('Ke1 closed  [V s/rad] =', KeClosed.toExponential(6));
console.log('relative difference   =', ((an.Ke1 - KeClosed) / KeClosed).toExponential(3));
console.log('phase Ke spread (imbalance) =', an.keImbalance.toExponential(2), ' engine kw1 =', an.kw1.toFixed(4));
