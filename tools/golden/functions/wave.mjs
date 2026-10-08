// GR-21, GR-22 and GR-23 (U-M3b): Xcoil's wave builders. waveRawLayout dumps a whole layout (the GR-19 raw layout, without the
// derived start/end points, plus the envelope and the wave frame); the wave* helpers dump one Xcoil helper over seeded
// inputs (200 per case), written into the fixture so Python needs no PRNG. waveAnalysis is the physics area's
// computeAnalysis on the same input.
import { FUNCTIONS as M1_LAYOUT } from './m1_layout.mjs';
import { FUNCTIONS as PHYSICS } from './physics.mjs';
import { recordFromPrim } from '../lib/codec.mjs';

// mulberry32: integer-only PRNG, as in dump_xcoil.mjs.
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
const pick = (rnd, list) => list[Math.floor(rnd() * list.length)];
const unitVec = (rnd) => {
  for (;;) {
    const x = uniform(rnd, -1, 1), y = uniform(rnd, -1, 1), l = Math.sqrt(x * x + y * y);
    if (l > 0.2 && l <= 1) return [x / l, y / l];
  }
};
const record = (E, q) => recordFromPrim(E, { t: q.t, ...(q.t === 'L' ? { x1: q.x1, y1: q.y1, x2: q.x2, y2: q.y2 } : { cx: q.cx, cy: q.cy, r: q.r, a1: q.a1, a2: q.a2 }), w: q.w, kind: q.kind });
const records = (E, prims) => prims.map((q) => record(E, q));
const noEnds = (r) => { const { start, end, ...rest } = r; return rest; };
const noEndsAll = (rs) => rs.map(noEnds);
const seeded = (x, one) => { const rnd = mulberry32(x.seed); return Array.from({ length: x.count }, () => one(rnd)); };

function waveParams(rnd) {
  const rIn = uniform(rnd, 14, 30), style = pick(rnd, ['involute', 'jog', 'chord', 'overlap']);
  return {
    topology: 'wave', poles: pick(rnd, [8, 12, 16, 20]), phases: pick(rnd, [1, 2, 3]), turns: pick(rnd, [1, 2, 3, 4]),
    rIn, rOut: rIn + uniform(rnd, 8, 24), traceWidth: uniform(rnd, 0.2, 0.5), clearance: uniform(rnd, 0.15, 0.3),
    endWidthOuter: pick(rnd, [0, 0, uniform(rnd, 0.25, 0.5)]), endWidthInner: pick(rnd, [0, 0, uniform(rnd, 0.25, 0.5)]),
    viaDrill: 0.3, viaPad: uniform(rnd, 0.5, 0.8), waveStyle: style, cornerStyle: pick(rnd, ['round', 'round', 'sharp']),
    filletRadius: uniform(rnd, 0.1, 0.8), busWidth: uniform(rnd, 0.4, 1.2), startAngleDeg: pick(rnd, [0, 0, 17]),
  };
}
const endSummary = (e) => ({ rv: e.rv, spacing: e.spacing, need: e.need, wEnd: e.wEnd, ...(e.rb === undefined ? {} : { rb: e.rb }) });
function frameSummary(W) {
  return { rVo: W.rVo, rVi: W.rVi, outer: endSummary(W.outer), inner: endSummary(W.inner),
    ...(W.rTrackMin === undefined ? {} : { rTrackMin: W.rTrackMin }),
    ...(W.pitchOut === undefined ? {} : { pitchOut: W.pitchOut, pitchIn: W.pitchIn, rhoOut0: W.rhoOut(0), rhoIn0: W.rhoIn(0), rhoOutTop: W.rhoOut(W.mq - 1), rhoInTop: W.rhoIn(W.mq - 1) }) };
}

function rawLayout(E, params) {
  const raw = M1_LAYOUT.xcoilRawLayout.run(E, { params });
  const L = E.compute(params).layout;
  const strip = (obj) => ({ ...obj, prims: obj.prims.map(noEnds) });
  return {
    ...raw,
    layers: raw.layers.map((layer) => ({ ...layer, objs: layer.objs.map(strip) })),
    mech: { ...raw.mech, prims: noEndsAll(raw.mech.prims), borePrims: noEndsAll(raw.mech.borePrims) },
    rMinAll: L.rMinAll, rMaxAll: L.rMaxAll,
    frame: frameSummary(L.W),
  };
}

// The physics area's computeAnalysis needs interconnect copper; a layout without it (phases other than 3, open
// connection) gets the same fields minus the interconnect ones.
function analysisOf(E, params) {
  const r = E.compute(params);
  if (!r.ok || !r.analysis) throw new Error(`Xcoil compute failed: ${JSON.stringify(r.errors)}`);
  if (r.layout.interconnect) return PHYSICS.computeAnalysis.run(E, { params });
  const a = r.analysis;
  return {
    omegaM: a.omegaM, rho: E.copperResistivity(r.params.tempC), Ke1: a.Ke1, phaseKe: a.phases.map((ph) => ph.Ke[0]),
    keLinePk: a.keLinePk, keLinePeakWaveform: Math.max(...E.lineWaveform(a, 181)[0].v.map(Math.abs)) / a.omegaM,
    thd: a.thd, Rphase: a.Rphase, phaseRtrace: a.phases.map((ph) => ph.Rtrace), phaseRextra: a.phases.map((ph) => ph.Rextra),
    phaseR: a.phases.map((ph) => ph.R), pEddy: a.pEddy, pCu: a.pCu, pCirc: a.pCirc, torque: a.torque, pOut: a.pOut,
    lossTotal: a.lossTotal, efficiency: a.efficiency, motorConstant: a.motorConstant,
  };
}

export const FUNCTIONS = {
  waveRawLayout: { required: ['params'], run: (E, x) => rawLayout(E, x.params) },
  waveAnalysis: { required: ['params'], run: (E, x) => analysisOf(E, x.params) },
  waveRefusal: {
    required: ['params'],
    run: (E, x) => { const r = E.compute(x.params); return { ok: r.ok === true, errors: r.errors.map((e) => ({ code: e.code, field: e.field })) }; },
  },
  waveInvol: { required: ['seed', 'count'], run: (E, x) => seeded(x, (rnd) => { const alpha = uniform(rnd, 0, 1.45); return { alpha, value: E.invol(alpha) }; }) },
  waveInvolutePoint: {
    required: ['seed', 'count'],
    run: (E, x) => seeded(x, (rnd) => { const rb = uniform(rnd, 1, 30), phi0 = uniform(rnd, -3, 3), t = uniform(rnd, 0, 3); return { rb, phi0, t, point: E.involutePoint(rb, phi0, t) }; }),
  },
  waveBiarc: {
    required: ['seed', 'count'],
    run: (E, x) => seeded(x, (rnd) => {
      for (;;) {
        const P0 = [uniform(rnd, -30, 30), uniform(rnd, -30, 30)], P1 = [uniform(rnd, -30, 30), uniform(rnd, -30, 30)], T0 = unitVec(rnd), T1 = unitVec(rnd);
        if (1 - (T0[0] * T1[0] + T0[1] * T1[1]) < 0.01) continue;
        const vt = (P1[0] - P0[0]) * (T0[0] + T1[0]) + (P1[1] - P0[1]) * (T0[1] + T1[1]);
        if (Math.abs(vt) < 0.05) continue;
        return { P0, T0, P1, T1, w: 0.4, kind: 'endturn', prims: records(E, E.biarc(P0, T0, P1, T1, 0.4, 'endturn')) };
      }
    }),
  },
  waveInvolutePrims: {
    required: ['seed', 'count'],
    run: (E, x) => seeded(x, (rnd) => {
      const rb = uniform(rnd, 5, 15), phi0 = uniform(rnd, -1, 1), t1 = uniform(rnd, 0.1, 1), t2 = t1 + uniform(rnd, 0.3, 1.5);
      return { rb, phi0, t1, t2, w: 0.4, kind: 'endturn', prims: records(E, E.involutePrims(rb, phi0, t1, t2, 0.4, 'endturn')) };
    }),
  },
  waveFilletPath: {
    required: ['seed', 'count'],
    run: (E, x) => seeded(x, (rnd) => {
      const rho = uniform(rnd, 0.1, 0.9), w = uniform(rnd, 0.2, 0.5);
      let prims;
      if (rnd() < 0.5) {
        const pts = Array.from({ length: 4 }, () => [uniform(rnd, 0, 12), uniform(rnd, -6, 6)]);
        prims = [0, 1, 2].map((i) => ({ t: 'L', x1: pts[i][0], y1: pts[i][1], x2: pts[i + 1][0], y2: pts[i + 1][1], kind: 'side', w }));
      } else {
        const rA = uniform(rnd, 2, 8), rB = rA + uniform(rnd, 4, 12), sweep = uniform(rnd, 0.3, 1.2) * (rnd() < 0.5 ? 1 : -1), a2 = sweep, e = [rB * Math.cos(a2), rB * Math.sin(a2)], d = uniform(rnd, 2, 6);
        prims = [{ t: 'L', x1: rA, y1: 0, x2: rB, y2: 0, kind: 'side', w }, { t: 'A', cx: 0, cy: 0, r: rB, a1: 0, a2, kind: 'endturn', w },
          { t: 'L', x1: e[0], y1: e[1], x2: e[0] * (1 + d / rB), y2: e[1] * (1 + d / rB), kind: 'endturn', w }];
      }
      return { rho, prims: records(E, prims), out: records(E, E.filletPath(prims, rho, null)) };
    }),
  },
  waveTaperJunctions: {
    required: ['seed', 'count'],
    run: (E, x) => seeded(x, (rnd) => {
      const n = 3 + Math.floor(rnd() * 3), prims = [];
      let px = uniform(rnd, 1, 5), py = uniform(rnd, -3, 3);
      for (let i = 0; i < n; i++) {
        const nx = px + uniform(rnd, 2, 9), ny = py + uniform(rnd, -4, 4);
        prims.push({ t: 'L', x1: px, y1: py, x2: nx, y2: ny, kind: pick(rnd, ['side', 'endturn']), w: pick(rnd, [0.3, 0.4, 0.5, 0.6]) });
        px = nx; py = ny;
      }
      return { prims: records(E, prims), out: records(E, E.taperJunctions(prims)) };
    }),
  },
  waveDerive: {
    required: ['seed', 'count'],
    run: (E, x) => seeded(x, (rnd) => {
      const raw = waveParams(rnd), p = E.normalizeParams(raw).params, dw = E.deriveWave(p);
      return { params: raw, errors: dw.errors.map((e) => ({ code: e.code, field: e.field })), frame: dw.W ? frameSummary(dw.W) : null, maxTurns: dw.errors.length ? E.maxWaveTurns(p) : null };
    }),
  },
  waveTrack: {
    required: ['seed', 'count'],
    run: (E, x) => {
      const rnd = mulberry32(x.seed), out = [];
      while (out.length < x.count) {
        const raw = waveParams(rnd);
        if (raw.waveStyle === 'overlap') continue;
        const p = E.normalizeParams(raw).params, dw = E.deriveWave(p);
        if (dw.errors.length) continue;
        const W = dw.W, shifted = W.q > 1 ? E.waveTrack(W, W.tau / 2 - W.dTheta) : null;
        out.push({ params: raw, t0: records(E, E.waveTrack(W, null)), shift: shifted ? records(E, shifted) : null });
      }
      return out;
    },
  },
  waveBelts: {
    required: ['seed', 'count'],
    run: (E, x) => seeded(x, (rnd) => {
      const raw = waveParams(rnd), p = E.normalizeParams(raw).params, dw = E.deriveWave(p);
      if (dw.errors.length) return { params: raw, belts: null };
      const W = dw.W, ks = Array.from({ length: 12 }, () => Math.floor(rnd() * W.Q)), betas = Array.from({ length: 12 }, () => Math.floor(rnd() * 40) - 10);
      return { params: raw, ks, betas, angles: ks.map((k) => E.slotAngle(W, k)), phases: betas.map((b) => E.beltPhase(W, b)), signs: betas.map((b) => E.beltSign(W, b)) };
    }),
  },
};
