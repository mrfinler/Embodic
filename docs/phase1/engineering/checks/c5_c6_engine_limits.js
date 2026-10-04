// Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5
// C5: sector generator turn limit for D08 geometry; C6: star-of-slots belt-edge bug. Run: node checks/c5_c6_engine_limits.js
const E = require('/home/claude/serpentine/src/engine.js');
const b = { topology: 'sector', sectors: 12, poles: 10, phases: 3, turns: 1, coilSides: 'parallel', coilEnds: 'arc', cornerStyle: 'sharp', coilLayers: 2,
  traceWidth: 2.06, clearance: 0.8, coilGap: 0.8, rIn: 12.5, rOut: 44, copperOzOuter: 1, copperOzInner: 1, boardThickness: 0.6, interconnect: false, connection: 'open', tempC: 50, viaDrill: 0.3, viaPad: 0.6 };
for (const sides of ['parallel', 'radial']) for (const ri of [12.5, 14, 16, 24]) console.log('C5 D08 geometry, sides=' + sides, 'rIn=' + ri, 'maxTurns =', E.maxSectorTurnsFor(E.normalizeParams(Object.assign({}, b, { coilSides: sides, rIn: ri })).params));
for (const [Q, pp] of [[12, 7], [12, 5], [24, 7], [24, 11], [24, 13], [18, 7]]) { const s = E.starOfSlots(Q, pp, 3);
  const pat = s.coils.map(c => { const n = 'ABC'[c.phase]; return c.sign > 0 ? n : n.toLowerCase(); }).join('');
  const cnt = [0, 1, 2].map(i => s.coils.filter(c => c.phase === i).length);
  console.log('C6 starOfSlots ' + Q + '/' + (2 * pp), 'ok=' + s.ok, 'pattern', pat, 'counts', cnt.join(',')); }
console.log('C6 balancedSectorList(14 poles) =', E.balancedSectorList(14, 3).join(', '));
