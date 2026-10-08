// Agent 4's own Xcoil dump (U-V3). Reads {"cases": [{"id", "params"}], "angles": [...]} on stdin and writes JSON.
// Xcoil source is read-only: /home/claude/serpentine/src/engine.js.
'use strict';
const E = require(process.env.XCOIL_ENGINE || '/home/claude/serpentine/src/engine.js');

const GEOM = { L: ['x1', 'y1', 'x2', 'y2'], A: ['cx', 'cy', 'r', 'a1', 'a2'] };

function prim(q) {
  const out = { t: q.t, w: q.w, kind: q.kind };
  for (const k of GEOM[q.t]) out[k] = q[k];
  return out;
}

function numbers(obj) {
  const out = {};
  for (const [k, v] of Object.entries(obj || {})) {
    if (typeof v === 'number' || typeof v === 'string' || typeof v === 'boolean') out[k] = v;
  }
  return out;
}

function dumpCase(c) {
  const r = E.compute(c.params);
  const base = { id: c.id, ok: !!r.ok, params: r.params, errors: (r.errors || []).map((e) => e.code), warnings: (r.warnings || []).map((w) => w.code) };
  if (!r.layout) return base;
  const L = r.layout;
  return {
    ...base,
    nBoards: L.nBoards || 1,
    statorThickness: L.statorThickness,
    rMinCu: L.rMinCu, rMaxCu: L.rMaxCu, rMinAll: L.rMinAll, rMaxAll: L.rMaxAll,
    layers: L.layers.map((ly) => ({
      index: ly.index, board: ly.board, name: ly.name, phase: ly.phase, role: ly.role, z: ly.z, copperT: ly.copperT,
      objs: ly.objs.map((o) => ({ kind: o.kind, strand: o.strand === undefined ? null : o.strand, net: o.net || null, prims: o.prims.map(prim) })),
    })),
    vias: L.vias.map(numbers),
    pads: (L.pads || []).map(numbers),
    drcIssues: r.drc ? r.drc.issues.length : null,
    analysis: numbers(r.analysis),
  };
}

let text = '';
process.stdin.on('data', (d) => { text += d; });
process.stdin.on('end', () => {
  const req = JSON.parse(text);
  const out = { cases: (req.cases || []).map(dumpCase) };
  if (req.angles) {
    out.trig = req.angles.map((a, i) => [Math.sin(a), Math.cos(a), Math.atan2(req.pairs[i][0], req.pairs[i][1]), Math.tan(a)]);
  }
  process.stdout.write(JSON.stringify(out));
});
