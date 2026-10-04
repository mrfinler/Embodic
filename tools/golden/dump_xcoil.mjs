// Dumps Xcoil v3 engine results to golden fixtures for embodic's Python comparators.
// Usage: node tools/golden/dump_xcoil.mjs tools/golden/cases/<area>.json [--out <dir>]
// Default output: tests/golden/data/<area>/ in this repository.
// The engine is loaded read-only from $XCOIL_ENGINE (default /home/claude/serpentine/src/engine.js).
import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { canonicalJson, decodeNonFinite, primFromRecord, recordFromPrim, requireKeys } from './lib/codec.mjs';

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');
const ENGINE_PATH = process.env.XCOIL_ENGINE || '/home/claude/serpentine/src/engine.js';
const REGISTRY_PATH = join(REPO_ROOT, 'docs', 'phase2', 'engineering', 'equation_registry.json');
const CASES_FORMAT = 'embodic.golden-cases';
const FIXTURE_FORMAT = 'embodic.golden-case';

// ---------------------------------------------------------------- engine functions under test

// Each entry names the case-input keys (required, optional) and runs one Xcoil call on decoded inputs.
const FUNCTIONS = {
  primLength: { required: ['prim'], run: (E, x) => E.primLength(primFromRecord(x.prim)) },
  primsLength: { required: ['prims'], run: (E, x) => E.primsLength(x.prims.map(primFromRecord)) },
  primStart: { required: ['prim'], run: (E, x) => E.primStart(primFromRecord(x.prim)) },
  primEnd: { required: ['prim'], run: (E, x) => E.primEnd(primFromRecord(x.prim)) },
  reversePrims: {
    required: ['prims'],
    run: (E, x) => E.reversePrims(x.prims.map(primFromRecord)).map((q) => recordFromPrim(E, q)),
  },
  tfPoint: { required: ['tf', 'thetaG', 'x', 'y'], run: (E, x) => E.tfPoint(x.tf, x.thetaG, x.x, x.y) },
  tfPrim: {
    required: ['tf', 'thetaG', 'prim'],
    run: (E, x) => recordFromPrim(E, E.tfPrim(x.tf, x.thetaG, primFromRecord(x.prim))),
  },
  discretize: {
    required: ['prims'],
    optional: ['hMax', 'dAngMax', 'sagTol'],
    run: (E, x) => E.discretize(x.prims.map(primFromRecord), x.hMax, x.dAngMax, x.sagTol),
  },
  segSegDist: { required: ['a', 'b'], run: (E, x) => E.segSegDist(x.a, x.b) },
  ptSegDist: { required: ['px', 'py', 'seg'], run: (E, x) => E.ptSegDist(x.px, x.py, x.seg) },
  padSegClearance: { required: ['pad', 'seg'], run: (E, x) => E.padSegClearance(x.pad, x.seg) },
  padsClearance: { required: ['pads', 'vias', 'viaPad'], run: (E, x) => E.padsClearance(x.pads, x.vias, x.viaPad) },
  makeGrid: {
    required: ['segs', 'cell'],
    run: (E, x) => {
      const grid = E.makeGrid(x.segs, x.cell);
      return { cell: grid.cell, entries: [...grid.map.entries()] };
    },
  },
  gridQuery: {
    required: ['segs', 'cell', 'x', 'y', 'radius'],
    run: (E, x) => {
      const visited = [];
      E.gridQuery(E.makeGrid(x.segs, x.cell), x.x, x.y, x.radius, (_seg, index) => visited.push(index));
      return visited;
    },
  },
};

// ---------------------------------------------------------------- seeded input generators

// mulberry32: integer-only PRNG, identical on every JS engine.
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
const randomSeg = (rnd) => ({
  x1: uniform(rnd, -10, 10), y1: uniform(rnd, -10, 10), x2: uniform(rnd, -10, 10), y2: uniform(rnd, -10, 10),
});
const pointOn = (s, t) => [s.x1 + (s.x2 - s.x1) * t, s.y1 + (s.y2 - s.y1) * t];

// Unit vector from two uniforms without libm calls, so regenerated inputs do not depend on the runtime's sin/cos.
function randomDirection(rnd) {
  for (;;) {
    const dx = uniform(rnd, -1, 1), dy = uniform(rnd, -1, 1), n = Math.sqrt(dx * dx + dy * dy);
    if (n > 1e-3 && n <= 1) return [dx / n, dy / n];
  }
}

function segFrom([x, y], [dx, dy], back, ahead) {
  return { x1: x - dx * back, y1: y - dy * back, x2: x + dx * ahead, y2: y + dy * ahead };
}

const KINDS = ['side', 'endturn', 'fillet', 'bus', 'lead'];

function randomPrimRecord(rnd, maxR) {
  const kind = KINDS[Math.floor(rnd() * KINDS.length)], width = uniform(rnd, 0.1, 1);
  if (rnd() < 0.3) {
    const s = randomSeg(rnd);
    return { type: 'line', ...s, width, kind };
  }
  const a1 = uniform(rnd, -7, 7), sweep = uniform(rnd, -2 * Math.PI, 2 * Math.PI);
  return {
    type: 'arc', cx: uniform(rnd, -5, 5), cy: uniform(rnd, -5, 5), r: uniform(rnd, 0.0005, maxR),
    a1, a2: a1 + sweep, width, kind,
  };
}

const GENERATORS = {
  seg_pair_random: (rnd) => ({ a: randomSeg(rnd), b: randomSeg(rnd) }),
  seg_pair_touching: (rnd) => {
    const a = randomSeg(rnd);
    return { a, b: segFrom(pointOn(a, rnd()), randomDirection(rnd), 0, uniform(rnd, 0.1, 10)) };
  },
  seg_pair_crossing: (rnd) => {
    const a = randomSeg(rnd);
    const b = segFrom(pointOn(a, uniform(rnd, 0.05, 0.95)), randomDirection(rnd), uniform(rnd, 0.1, 10), uniform(rnd, 0.1, 10));
    return { a, b };
  },
  seg_pair_collinear: (rnd) => {
    const a = randomSeg(rnd), p = pointOn(a, uniform(rnd, -1.5, 2.5)), q = pointOn(a, uniform(rnd, -1.5, 2.5));
    return { a, b: { x1: p[0], y1: p[1], x2: q[0], y2: q[1] } };
  },
  seg_pair_parallel: (rnd) => {
    const a = randomSeg(rnd), dx = a.x2 - a.x1, dy = a.y2 - a.y1, n = Math.sqrt(dx * dx + dy * dy) || 1;
    const off = uniform(rnd, 0, 1), along = uniform(rnd, -1.2, 1.2);
    const ox = (-dy / n) * off + dx * along, oy = (dx / n) * off + dy * along;
    return { a, b: { x1: a.x1 + ox, y1: a.y1 + oy, x2: a.x2 + ox, y2: a.y2 + oy } };
  },
  pt_seg_random: (rnd) => ({ px: uniform(rnd, -10, 10), py: uniform(rnd, -10, 10), seg: randomSeg(rnd) }),
  pt_seg_near: (rnd) => {
    const seg = randomSeg(rnd), [x, y] = pointOn(seg, uniform(rnd, -0.1, 1.1));
    const dx = seg.x2 - seg.x1, dy = seg.y2 - seg.y1, n = Math.sqrt(dx * dx + dy * dy) || 1;
    const off = rnd() < 0.2 ? 0 : uniform(rnd, -0.01, 0.01);
    return { px: x - (dy / n) * off, py: y + (dx / n) * off, seg };
  },
  discretize_random: (rnd) => ({
    prims: [randomPrimRecord(rnd, 5)],
    hMax: uniform(rnd, 0.1, 2),
    dAngMax: uniform(rnd, 1, 10) * (Math.PI / 180),
    sagTol: uniform(rnd, 1e-4, 1e-2),
  }),
  tf_prim_random: (rnd) => ({
    tf: { rot: uniform(rnd, -Math.PI, Math.PI), mirror: rnd() < 0.5 },
    thetaG: uniform(rnd, -Math.PI, Math.PI),
    prim: randomPrimRecord(rnd, 30),
  }),
};

// ---------------------------------------------------------------- case evaluation

function eqIdsByFunction(registry) {
  const byFn = new Map();
  for (const eq of registry.equations) {
    for (const fn of eq.golden_functions || []) byFn.set(fn, [...(byFn.get(fn) || []), eq.id]);
  }
  return byFn;
}

// The engine gets a clone, so the inputs written to the fixture are the ones passed even if a function mutates them.
function evaluate(E, spec, inputs, where) {
  const allowed = [...spec.required, ...(spec.optional || [])];
  requireKeys(inputs, allowed, spec.required, where);
  return spec.run(E, structuredClone(inputs));
}

function buildFixture(E, engineSha, eqIds, entry) {
  const where = `case ${entry.id}`;
  requireKeys(entry, ['id', 'fn', 'note', 'tags', 'inputs', 'seeded'], ['id', 'fn', 'note', 'tags'], where);
  const spec = FUNCTIONS[entry.fn];
  if (!spec) throw new Error(`${where}: unknown fn ${entry.fn}`);
  if ((entry.inputs === undefined) === (entry.seeded === undefined)) throw new Error(`${where}: give inputs or seeded`);
  let calls;
  const fixture = {};
  if (entry.seeded) {
    const { generator, seed, count } = entry.seeded;
    requireKeys(entry.seeded, ['generator', 'seed', 'count'], ['generator', 'seed', 'count'], `${where} seeded`);
    if (!GENERATORS[generator]) throw new Error(`${where}: unknown generator ${generator}`);
    const rnd = mulberry32(seed);
    calls = Array.from({ length: count }, () => GENERATORS[generator](rnd));
    fixture.seeded = entry.seeded;
  } else {
    calls = [decodeNonFinite(entry.inputs)];
  }
  return Object.assign(fixture, {
    format: FIXTURE_FORMAT,
    format_version: 1,
    case_id: entry.id,
    fn: entry.fn,
    eq_ids: eqIds.get(entry.fn) || [],
    note: entry.note,
    tags: entry.tags,
    producer: { name: 'xcoil-v3', engine_sha256: engineSha, runtime: `node ${process.version}` },
    calls: calls.map((inputs, i) => ({ inputs, output: evaluate(E, spec, inputs, `${where} call ${i}`) })),
  });
}

function main() {
  const [casesPath, outFlag, outArg] = process.argv.slice(2);
  if (!casesPath || (outFlag !== undefined && (outFlag !== '--out' || !outArg))) {
    throw new Error('usage: node tools/golden/dump_xcoil.mjs tools/golden/cases/<area>.json [--out <dir>]');
  }
  const cases = JSON.parse(readFileSync(casesPath, 'utf8'));
  if (cases.format !== CASES_FORMAT || cases.format_version !== 1) throw new Error(`${casesPath}: not ${CASES_FORMAT} v1`);
  if (!/^[a-z0-9_]+$/.test(cases.area)) throw new Error(`${casesPath}: bad area ${JSON.stringify(cases.area)}`);

  const engineSha = createHash('sha256').update(readFileSync(ENGINE_PATH)).digest('hex');
  const E = createRequire(import.meta.url)(ENGINE_PATH);
  const eqIds = eqIdsByFunction(JSON.parse(readFileSync(REGISTRY_PATH, 'utf8')));
  const outDir = outArg ? resolve(outArg) : join(REPO_ROOT, 'tests', 'golden', 'data', cases.area);
  mkdirSync(outDir, { recursive: true });

  const seen = new Set();
  for (const entry of cases.cases) {
    if (!/^[a-z0-9][a-z0-9-]*$/.test(entry.id) || seen.has(entry.id)) throw new Error(`bad or duplicate case id ${entry.id}`);
    seen.add(entry.id);
    writeFileSync(join(outDir, `${entry.id}.json`), `${canonicalJson(buildFixture(E, engineSha, eqIds, entry))}\n`);
  }
  console.log(`wrote ${seen.size} fixtures for area ${cases.area} (engine sha256 ${engineSha})`);
}

main();
