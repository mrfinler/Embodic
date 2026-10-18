// Fix wave F8 (U-E22): the parts of Xcoil's kw1 (EQ-27) for the three GR-22 layouts, as one JSON line on stdout.
// Read-only use of the engine: node docs/phase3/engineering/checks/f8_eq27_xcoil.mjs [/path/to/engine.js]
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';

const ENGINE = process.argv[2] || process.env.XCOIL_ENGINE || '/home/claude/serpentine/src/engine.js';
const E = createRequire(import.meta.url)(ENGINE);
const M = 200; // midpoint steps of every Xcoil `ideal` integral (engine.js l.979, l.1885, l.2068)

function idealAt(p, F, z) {
  const rA = p.magnetRIn, rB = p.magnetROut;
  let sum = 0;
  for (let i = 0; i < M; i++) {
    const r = rA + ((rB - rA) * (i + 0.5)) / M;
    sum += (E.fieldHarmonic(1, r, z + p.airgap, F).Bz * r * (rB - rA)) / M;
  }
  return sum;
}

const mean = (xs) => xs.reduce((a, b) => a + b, 0) / xs.length;

function kindCounts(prims) {
  const out = {};
  for (const q of prims) out[q.kind] = (out[q.kind] || 0) + 1;
  return out;
}

function sector() {
  const r = E.compute({ topology: 'sector' });
  const p = r.params, a = r.analysis, S = r.layout.S, G = r.layout.sector;
  const F = E.fieldSetup({ pp: p.poles / 2, p }, { statorThickness: r.layout.statorThickness });
  const zs = r.layout.layers.map((L) => L.z);
  const ideal = mean(zs.map((z) => idealAt(p, F, z)));
  const coilsPerPhase = S.sos.coilsPerPhase;
  const condXcoil = coilsPerPhase * 4 * S.N; // engine.js l.2478
  // X0: the canonical coil of one layer; the Y coil is its mirror (engine.js l.2380), so it has the same kinds.
  const x0Kinds = kindCounts(G.X0.prims);
  const lead = G.X0.prims.filter((q) => q.kind === 'lead' && q.t === 'L').map((q) => [Math.hypot(q.x1, q.y1), Math.hypot(q.x2, q.y2)]);
  const sideRadii = G.X0.prims.filter((q) => q.kind === 'side').map((q) => [Math.hypot(q.x1, q.y1), Math.hypot(q.x2, q.y2)]);
  return {
    kw1: a.kw1,
    Ke1: a.Ke1,
    phaseKe: a.phases.map((ph) => ph.Ke[0]),
    nElements: a.phases.map((ph) => ph.nElements),
    turnsPerSpiral: S.N,
    coilsPerPhase,
    coilLayers: S.L,
    conductorsPerPhaseXcoil: condXcoil,
    x0Kinds,
    x0LeadRadii: lead,
    x0SideRadii: sideRadii,
    magnetSpan: [p.magnetRIn, p.magnetROut],
    copperZ: zs,
    idealMeanZ: ideal,
    recomputed: (a.Ke1 * 1e6) / (ideal * condXcoil),
  };
}

function serpentine() {
  const r = E.compute({ topology: 'serpentine' });
  const p = r.params, a = r.analysis, layout = r.layout;
  const D = E.derive(p);
  const F = E.fieldSetup(D, layout);
  const perConductorScale = D.series ? 1 : D.nPairs;
  const phase0 = layout.layers.filter((L) => L.phase === 0);
  const idealLam = phase0.reduce((acc, L) => acc + (idealAt(p, F, L.z) * p.poles * D.Nt) / perConductorScale, 0); // engine.js l.977-982
  const condNominal = phase0.reduce((acc) => acc + (p.poles * D.Nt) / perConductorScale, 0);
  const idealAllZ = mean(layout.layers.map((L) => idealAt(p, F, L.z)));
  const idealPhase0Z = mean(phase0.map((L) => idealAt(p, F, L.z)));
  const ke0 = a.phases[0].Ke[0];
  // analyze's own ratio (l.977-983) evaluated for each phase on that phase's layers; Xcoil reports phase 0 only
  const perPhaseKu = a.phases.map((ph, k) => {
    const lam = layout.layers.filter((L) => L.phase === k).reduce((acc, L) => acc + (idealAt(p, F, L.z) * p.poles * D.Nt) / perConductorScale, 0);
    return (ph.Ke[0] * 1e6) / lam;
  });
  return {
    perPhaseKu,
    kw1: a.kw1,
    Ke1: a.Ke1,
    phaseKe: a.phases.map((ph) => ph.Ke[0]),
    keImbalance: a.keImbalance,
    poles: p.poles,
    turns: D.Nt,
    strands: D.J,
    series: D.series,
    nPairs: D.nPairs,
    layers: layout.layers.map((L) => ({ index: L.index, phase: L.phase, z: L.z, role: L.role })),
    conductorsPerPhaseNominal: condNominal,
    idealLam,
    idealPhase0Z,
    idealAllZ,
    variants: {
      xcoil_phaseA_over_phaseAz: (ke0 * 1e6) / idealLam,
      mean_over_phaseAz: (a.Ke1 * 1e6) / idealLam,
      phaseA_over_allz: (ke0 * 1e6) / (idealAllZ * condNominal),
      mean_over_allz: (a.Ke1 * 1e6) / (idealAllZ * condNominal),
    },
  };
}

function wave() {
  const r = E.compute({ topology: 'wave', turns: 2 });
  const a = r.analysis;
  return { kw1: a.kw1, Ke1: a.Ke1, phaseKe: a.phases.map((ph) => ph.Ke[0]), nElements: a.phases.map((ph) => ph.nElements), conductorsPerPhase: a.conductorsPerPhase };
}

const engineSha256 = createHash('sha256').update(readFileSync(ENGINE)).digest('hex');
console.log(JSON.stringify({ engineSha256, node: process.version, sector: sector(), serpentine: serpentine(), wave: wave() }));
