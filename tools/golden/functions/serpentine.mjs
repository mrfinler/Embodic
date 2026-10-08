// GR-20 and GR-23 (U-M3a): Xcoil serpentine raw layouts and the serpentine helper functions, with Xcoil's own keys.
// The Python tests map the layouts to embodic geometry (tests/golden/m3_serpentine/).
const GEOMETRY = { L: ['x1', 'y1', 'x2', 'y2'], A: ['cx', 'cy', 'r', 'a1', 'a2'] };

// mulberry32: integer-only PRNG, identical on every JS engine (same algorithm as dump_xcoil.mjs).
function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const uniform = (rnd, lo, hi) => lo + (hi - lo) * rnd();
const round3 = (x) => Math.round(x * 1000) / 1000;
const pick = (rnd, list) => list[Math.floor(rnd() * list.length)];

// The board-dump primitive record without start and end points (Python computes them), which keeps fixtures small.
function record(E, q) {
  const rec = { type: q.t === 'L' ? 'line' : 'arc', width: q.w, kind: q.kind };
  for (const k of GEOMETRY[q.t]) rec[k] = q[k];
  return rec;
}

function scalars(obj) {
  const out = {};
  for (const [k, v] of Object.entries(obj)) {
    if (v === null || ['number', 'string', 'boolean'].includes(typeof v)) out[k] = v;
  }
  return out;
}

function tapSummary(t) {
  return { phase: t.phase, sign: t.sign, via: t.via, x: t.x, y: t.y };
}

function linkSummary(lk) {
  return { ...scalars(lk), taps: lk.taps.map(tapSummary) };
}

function itemSummary(E, it) {
  const out = { ...scalars(it), touch: it.touch, prims: it.prims.map((q) => record(E, q)) };
  if (it.link) out.link = linkSummary(it.link);
  const stubTaps = it.prims.filter((q) => q.tap).map((q) => tapSummary(q.tap));
  if (stubTaps.length) out.stubTaps = stubTaps;
  return out;
}

function canonSummary(c) {
  const site = (s) => (s ? { ...scalars(s), xy: s.xy } : null);
  return { ...scalars(c), padV: site(c.padV), padT: site(c.padT) };
}

function drcSummary(drc) {
  return {
    ...scalars(drc),
    issues: drc.issues.map((i) => ({ sev: i.sev, code: i.code })),
  };
}

// GR-22 inputs: the phase and total results that embodic's analysis reproduces (engine.js analyze l.880-1017).
function analysisSummary(a) {
  if (!a) return null;
  return {
    ...scalars(a),
    phases: a.phases.map((ph) => ({ name: ph.name, Ke: ph.Ke, R: ph.R, Rtrace: ph.Rtrace, Rextra: ph.Rextra, pCirc: ph.pCirc })),
  };
}

function rawLayout(E, params) {
  const result = E.compute(params);
  const out = {
    params: result.params,
    ok: result.ok,
    errors: result.errors.map((e) => e.code),
    warnings: result.warnings.map((w) => w.code),
  };
  const L = result.layout;
  if (!L) return out;
  return {
    ...out,
    rMinCu: L.rMinCu,
    rMaxCu: L.rMaxCu,
    rMinAll: L.rMinAll,
    rMaxAll: L.rMaxAll,
    nBoards: L.nBoards,
    layersPerBoard: L.layersPerBoard,
    statorThickness: L.statorThickness,
    boardThickness: L.stackup.boardThickness,
    layers: L.layers.map((layer) => {
      const prims = layer.objs.flatMap((o) => o.prims);
      return {
        ...scalars(layer),
        rot: layer.tf.rot,
        mirror: layer.tf.mirror,
        length: E.primsLength(prims),
        objs: layer.objs.map((o) => ({ ...scalars(o), prims: o.prims.map((q) => record(E, q)) })),
      };
    }),
    vias: L.vias.map(scalars),
    pads: L.pads.map(scalars),
    items: L.interconnect ? L.interconnect.items.map((it) => itemSummary(E, it)) : [],
    interconnect: L.interconnect
      ? { ...scalars(L.interconnect), links: L.interconnect.links.map(linkSummary) }
      : null,
    canon: L.canon.map(canonSummary),
    drc: drcSummary(result.drc),
    analysis: analysisSummary(result.analysis),
    derived: result.derived,
  };
}

// ---------------------------------------------------------------- seeded parameter sets

// A partial Xcoil parameter object. Every entry builds or is refused by Xcoil's own checks; none throws.
function randomParams(rnd) {
  const rIn = round3(uniform(rnd, 14, 36));
  const p = {
    poles: pick(rnd, [8, 10, 12, 16]),
    phases: pick(rnd, [1, 2, 3, 3, 3]),
    rIn,
    rOut: round3(rIn + uniform(rnd, 10, 30)),
    turns: 1 + Math.floor(rnd() * 4),
    strands: pick(rnd, [1, 1, 2]),
    traceWidth: round3(uniform(rnd, 0.2, 0.5)),
    clearance: round3(uniform(rnd, 0.15, 0.3)),
    endWidthOuter: pick(rnd, [0, 0, round3(uniform(rnd, 0.2, 0.7))]),
    endWidthInner: pick(rnd, [0, 0, round3(uniform(rnd, 0.2, 0.7))]),
    style: pick(rnd, ['parallel', 'radial']),
    cornerStyle: pick(rnd, ['round', 'round', 'sharp']),
    filletRadius: round3(uniform(rnd, 0, 1.5)),
    filletMax: rnd() < 0.2,
    terminalSide: pick(rnd, ['outer', 'inner']),
    startAngleDeg: round3(uniform(rnd, -180, 180)),
    layersPerPhase: pick(rnd, [1, 2, 2, 4]),
    pairConnection: pick(rnd, ['series', 'parallel']),
    layerOrder: pick(rnd, ['grouped', 'interleaved']),
    stackMode: pick(rnd, ['single', 'single', 'perPhase']),
    boardGap: pick(rnd, [0.1, 0.5]),
    connection: pick(rnd, ['star', 'delta', 'open']),
    interconnect: rnd() < 0.8,
  };
  return p;
}

function seededSets(E, x, build) {
  const rnd = mulberry32(x.seed);
  const items = [];
  for (let i = 0; i < x.count; i++) {
    const given = randomParams(rnd);
    const p = E.normalizeParams(given).params;
    items.push({ params: given, ...build(E, p, rnd) });
  }
  return { items };
}

function randomLine(E, D, rnd) {
  const ju = Math.floor(uniform(rnd, -3, 2 * D.p.poles + 3));
  const i = Math.floor(rnd() * D.N);
  return { ju, i, line: E.sideLine(D, ju, i) };
}

function sideLineCall(E, p, rnd) {
  const D = E.derive(p);
  const { ju, i, line } = randomLine(E, D, rnd);
  return { ju, i, output: line };
}

function makeCornerCall(E, p, rnd) {
  const D = E.derive(p);
  const { ju, i, line } = randomLine(E, D, rnd);
  const R = rnd() < 0.3 ? uniform(rnd, 0.2, 6) : uniform(rnd, 0.5 * p.rIn, 1.2 * p.rOut);
  const u = rnd() < 0.5 ? 1 : -1;
  const type = rnd() < 0.5 ? 'int' : 'ext';
  const rho = rnd() < 0.25 ? 0 : (rnd() < 0.15 ? uniform(rnd, 4, 15) : uniform(rnd, 0.05, 3));
  return { ju, i, R, u, type, rho, output: E.makeCorner(line, R, u, type, rho) };
}

function rhoCall(name) {
  return (E, p, rnd) => {
    const D = E.derive(p);
    const rho0 = rnd() < 0.2 ? 0 : uniform(rnd, 0.05, 2);
    return { rho0, output: E[name](D, rho0) };
  };
}

function fitCall(E, p) {
  const D = E.derive(p);
  return { output: { ...E.fitStatus(D), maxFillet: E.maxFillet(D) } };
}

function tracesCall(E, p) {
  return { output: E.maxTracesFit(p) };
}

function randomChain(E, rnd) {
  const kinds = ['side', 'fillet', 'far', 'near', 'closing'];
  const widths = [0.2, 0.3, 0.4, 0.5, 0.8];
  const count = 2 + Math.floor(rnd() * 8);
  const prims = [];
  for (let k = 0; k < count; k++) {
    const kind = pick(rnd, kinds);
    const w = pick(rnd, widths);
    if (rnd() < 0.5) {
      prims.push({ t: 'L', x1: uniform(rnd, -30, 30), y1: uniform(rnd, -30, 30), x2: uniform(rnd, -30, 30), y2: uniform(rnd, -30, 30), kind, w });
    } else {
      const a1 = uniform(rnd, -3, 3);
      prims.push({ t: 'A', cx: uniform(rnd, -5, 5), cy: uniform(rnd, -5, 5), r: uniform(rnd, 0.3, 40), a1, a2: a1 + uniform(rnd, -3, 3), kind, w });
    }
  }
  return prims;
}

function taperCall(E, p, rnd) {
  const prims = randomChain(E, rnd);
  const through = rnd() < 0.5;
  return {
    prims: prims.map((q) => record(E, q)),
    through,
    output: E.taperJunctions(prims, through).map((q) => record(E, q)),
  };
}

const HELPERS = {
  gr23SideLine: sideLineCall,
  gr23MakeCorner: makeCornerCall,
  gr23TaperJunctions: taperCall,
  gr23MinSweep: rhoCall('minSweep'),
  gr23MinStraight: rhoCall('minStraight'),
  gr23StartRadius: rhoCall('startRadius'),
  gr23FitStatus: fitCall,
  gr23MaxTracesFit: tracesCall,
};

export const FUNCTIONS = {
  xcoilRawLayout: { required: ['params'], run: (E, x) => rawLayout(E, x.params) },
  xcoilRawLayoutSeeded: {
    required: ['seed'],
    run: (E, x) => {
      const params = randomParams(mulberry32(x.seed));
      return { inputs: params, ...rawLayout(E, params) };
    },
  },
  ...Object.fromEntries(
    Object.entries(HELPERS).map(([name, call]) => [
      name,
      { required: ['seed', 'count'], run: (E, x) => seededSets(E, x, call) },
    ]),
  ),
};
