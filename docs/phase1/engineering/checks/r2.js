// Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5
// CHECK R2: (a) R of a known track; (b) engine spiral sector-coil path length vs D08 eq. 3.27-3.36 concentric-loop closed form
const E = require('/home/claude/serpentine/src/engine.js');
const Ra = E.traceResistance(1000, 0.5, 0.0348, 20), Rb = E.traceResistance(1000, 0.5, 0.0348, 60);
console.log('(a) 1000 mm x 0.5 mm x 34.8 um: engine R20 =', Ra.toFixed(5), ' hand', (1.724e-8 * 1 / (0.5e-3 * 34.8e-6)).toFixed(5), '| R60 =', Rb.toFixed(5), ' hand', (1.724e-8 * (1 + 0.00393 * 40) / (0.5e-3 * 34.8e-6)).toFixed(5));
for (const cfg of [{ Q: 12, pole: 16 }, { Q: 12, pole: 10 }, { Q: 18, pole: 16 }]) {
  const w = 0.5, s = 0.2, rIn = 18, rOut = 38;
  const base = { topology: 'sector', sectors: cfg.Q, poles: cfg.pole, phases: 3, turns: 1, coilSides: 'parallel', coilEnds: 'arc', cornerStyle: 'sharp', coilLayers: 2,
    traceWidth: w, clearance: s, coilGap: s, rIn, rOut, copperOzOuter: 1, copperOzInner: 1, interconnect: false, connection: 'open', tempC: 20, viaDrill: 0.3, viaPad: 0.5 };
  const N = E.maxSectorTurnsFor(E.normalizeParams(base).params);
  const res = E.compute(Object.assign({}, base, { turns: N }));
  if (res.errors.length) { console.log(cfg, res.errors); continue; }
  const X0 = res.layout.sector.X0.prims, k = {}; X0.forEach(q => { k[q.kind] = (k[q.kind] || 0) + E.primLength(q); });
  const eng = (k.side || 0) + (k.endturn || 0);
  // D08 closed form, centre-line radii r_o' = rOut - w/2, r_i' = rIn + w/2, offsets d_i = (i + 1/2) w_d, theta_cs = 2 pi / Q
  const ro = rOut - w / 2, ri = rIn + w / 2, wd = w + s, th = 2 * Math.PI / cfg.Q; let L = 0, tri = 0;
  for (let i = 0; i < N; i++) { const d = i * wd + wd / 2, po = Math.asin(d / (ro - i * wd)), pi = Math.asin(d / (ri + i * wd)), bo = th / 2 - po, bi = th / 2 - pi;
    if (bi <= 0) tri++; const Lo = 2 * (ro - i * wd) * bo, Li = bi > 0 ? 2 * (ri + i * wd) * bi : 0, Ls = d / Math.tan(po) - d / Math.tan(bi > 0 ? pi : th / 2); L += Lo + Li + 2 * Ls; }
  const Nc = 0.5 * ((ro - ri) / wd + 1);
  console.log(`(b) Q/2p=${cfg.Q}/${cfg.pole}: engine maxTurns=${N}; D08 eq.3.24 bound N_c < ${Nc.toFixed(2)}; engine sides+ends=${eng.toFixed(2)} mm (+lead ${(k.lead || 0).toFixed(2)}, stub ${(k.stub || 0).toFixed(2)}); D08 loops=${L.toFixed(2)} mm (triangular loops: ${tri}); diff=${((eng - L) / L * 100).toFixed(2)} %`);
}
