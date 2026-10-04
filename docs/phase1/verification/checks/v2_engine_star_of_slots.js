// Prepared by: Agent 4 — Independent Verificator — model: claude-opus-5-5
// Calls the read-only Xcoil v3 engine starOfSlots / balancedSectorList and exposes the belt-index arithmetic.
// Run: node docs/phase1/verification/checks/v2_engine_star_of_slots.js
const E = require('/home/claude/serpentine/src/engine.js');
const cases = [[12, 10], [12, 14], [12, 16], [18, 16], [16, 16], [24, 14], [24, 22], [24, 26], [15, 16], [9, 10]];
for (const [Q, P] of cases) {
  const s = E.starOfSlots(Q, P / 2, 3);
  const pat = s.coils.map(c => { const n = 'ABC'[c.phase]; return c.sign > 0 ? n : n.toLowerCase(); }).join('');
  const cnt = [0, 1, 2].map(i => s.coils.filter(c => c.phase === i).length);
  console.log(`engine starOfSlots ${Q}/${P}: ok=${s.ok} kw1(kd)=${s.kw1.toFixed(4)} counts=${cnt} pattern=${pat}`);
}
// replicate the engine's belt index expression for 12/14 and 12/10 to show where ties break
function angNorm(a) { const t = 2 * Math.PI; a = a % t; return a < 0 ? a + t : a; }
for (const [Q, pp] of [[12, 7], [12, 5]]) {
  const alpha = 2 * Math.PI * pp / Q, rows = [];
  for (let k = 0; k < Q; k++) { const a = angNorm(k * alpha); const x = ((a + Math.PI / 6) % (2 * Math.PI)) / (Math.PI / 3); rows.push(`${k}:${(a * 180 / Math.PI).toFixed(1)}deg->${x.toPrecision(17)}`); }
  console.log(`belt-index raw value (engine expression) ${Q}/${2 * pp}:`, rows.join(' '));
}
console.log('engine balancedSectorList(14) =', E.balancedSectorList(14, 3).join(','), '| (16) =', E.balancedSectorList(16, 3).join(','), '| (10) =', E.balancedSectorList(10, 3).join(','));
