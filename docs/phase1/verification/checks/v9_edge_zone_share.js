// Prepared by: Agent 4 — Independent Verificator — model: claude-opus-5-5
// Re-verification: how much of the EMF integral int B1(r) r dr (2-D model, EQ-05) comes from conductors within one
// magnetic gap G of the magnet's radial ends, for the default design and the oracle designs O1 (D08) and O2 (D09)?
// Indicative bound on the resulting Ke over-estimate if the true field drops linearly to (1 - drop) at the magnet edge.
// Run: node docs/phase1/verification/checks/v9_edge_zone_share.js
const E = require('/home/claude/serpentine/src/engine.js');
function share(name, F, rA, rB, G, alphaOf, drop) {
  const n = 4000; let tot = 0, edge = 0, err = 0;
  for (let i = 0; i < n; i++) {
    const r = rA + (rB - rA) * (i + 0.5) / n, b = E.fieldHarmonic(1, r, G, Object.assign({}, F, { alphaP: alphaOf(r) })).Bz * r;
    tot += b; const dEdge = Math.min(r - rA, rB - r);
    if (dEdge < G) { edge += b; err += b * drop * (1 - dEdge / G); }
  }
  console.log(`${name}: magnet span ${rA}-${rB} mm, G = ${G} mm: edge-zone share of int B1 r dr = ${(100 * edge / tot).toFixed(1)} %; ` +
              `Ke over-estimate if the field falls linearly to ${100 - 100 * drop} % at the edge = ${(100 * err / tot).toFixed(1)} %`);
}
const blk = (w, p) => r => 2 * p * Math.asin(w / (2 * r)) / Math.PI;
for (const drop of [0.2, 0.4]) {
  share('default 12/16 (blocks 20x6x2, r 18-38)', { pp: 8, Br: 1.315, muR: 1.05, lm: 2, G: 1.31 }, 18, 38, 1.31, blk(6, 8), drop);
  share('O1 D08 (r_PM 15.4-43.4, alpha_p 0.72 const)', { pp: 5, Br: 1.38, muR: 1.05, lm: 5, G: 1.7 }, 15.4, 43.4, 1.7, () => 0.72, drop);
  share('O2 D09 (r_PM 25-46, alpha_p 0.8)', { pp: 8, Br: 1.33, muR: 1.05, lm: 2, G: 1.5 }, 25, 46, 1.5, () => 0.8, drop);
}
