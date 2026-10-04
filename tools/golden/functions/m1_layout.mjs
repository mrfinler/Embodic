// GR-19 (U-M1b): Xcoil's raw layout for one compute() input, with Xcoil's own keys and names.
// Python maps it to embodic geometry and the board dump (tests/golden/m1_layout/xcoil_map.py).
import { recordFromPrim } from '../lib/codec.mjs';

const GEOMETRY = { L: ['x1', 'y1', 'x2', 'y2'], A: ['cx', 'cy', 'r', 'a1', 'a2'] };

// Xcoil primitives carry builder notes (side, turn, tap) that recordFromPrim rejects; the record keeps the geometry.
function record(E, q) {
  const prim = { t: q.t, w: q.w, kind: q.kind };
  for (const k of GEOMETRY[q.t]) prim[k] = q[k];
  return recordFromPrim(E, prim);
}

function scalars(obj) {
  const out = {};
  for (const [k, v] of Object.entries(obj)) {
    if (v === null || ['number', 'string', 'boolean'].includes(typeof v)) out[k] = v;
  }
  return out;
}

function rawLayout(E, params) {
  const result = E.compute(params);
  if (!result.ok || !result.layout) throw new Error(`Xcoil compute failed: ${JSON.stringify(result.errors)}`);
  const L = result.layout;
  return {
    params: result.params,
    rMinCu: L.rMinCu,
    rMaxCu: L.rMaxCu,
    layers: L.layers.map((layer) => {
      const prims = layer.objs.flatMap((o) => o.prims);
      return {
        ...scalars(layer),
        length: E.primsLength(prims),
        objs: layer.objs.map((o) => ({ ...scalars(o), prims: o.prims.map((q) => record(E, q)) })),
      };
    }),
    vias: L.vias.map(scalars),
    pads: L.pads.map(scalars),
    mech: {
      prims: L.mech.prims.map((q) => record(E, q)),
      borePrims: L.mech.borePrims.map((q) => record(E, q)),
      holes: L.mech.holes.map(scalars),
    },
  };
}

export const FUNCTIONS = {
  xcoilRawLayout: { required: ['params'], run: (E, x) => rawLayout(E, x.params) },
};
