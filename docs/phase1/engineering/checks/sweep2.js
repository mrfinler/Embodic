// Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5
// Indicative sweep with the EXISTING engine (sector generator) — default-geometry assumptions (r 18-38 mm, w/s 0.5/0.2, 1 oz, 2 layers,
// double rotor, Br 1.3 T, magnet 2 mm, alpha_p 0.55 const, gap 1.0 mm/side). Not validated; used only to rank candidates.
const E = require('/home/claude/serpentine/src/engine.js');
const base = { topology: 'sector', phases: 3, coilEnds: 'arc', cornerStyle: 'sharp', coilLayers: 2,
  traceWidth: 0.5, clearance: 0.2, coilGap: 0.2, rIn: 18, rOut: 38, copperOzOuter: 1, copperOzInner: 1, boardThickness: 0.62,
  viaDrill: 0.3, viaPad: 0.5, interconnect: false, connection: 'open', tempC: 20, rpm: 1000, currentRms: 1,
  Br: 1.3, muR: 1.05, magnetThickness: 2, magnetArcRatio: 0.55, airgap: 1.0, rotorType: 'double', magnetAuto: true };
console.log('Q/2p   m  sides     Nmax kw1num  Ke1[mV s/rad] R20[ohm] Ke1/sqrt(R) THD');
const cases = [[12,16,3],[15,16,3],[18,16,3],[24,16,3],[9,10,3],[12,10,3],[18,20,3],[24,20,3],[16,16,1]];
for (const [Q, P, m] of cases) for (const sides of ['radial', 'parallel']) {
  const b = Object.assign({}, base, { sectors: Q, poles: P, phases: m, coilSides: sides });
  const N = E.maxSectorTurnsFor(E.normalizeParams(b).params);
  if (N < 1) { console.log(`${Q}/${P}`.padEnd(7), m, sides, 'no turn fits'); continue; }
  const r = E.compute(Object.assign({}, b, { turns: N }));
  if (r.errors.length) { console.log(`${Q}/${P}`, sides, r.errors[0].code); continue; }
  const a = r.analysis;
  console.log(`${Q}/${P}`.padEnd(7), String(m).padEnd(2), sides.padEnd(9), String(N).padEnd(4), a.kw1.toFixed(3).padEnd(7), (a.Ke1 * 1e3).toFixed(2).padEnd(14), a.Rphase.toFixed(3).padEnd(8), (a.Ke1 * 1e3 / Math.sqrt(a.Rphase)).toFixed(2).padEnd(11), a.thd.toFixed(3));
}
