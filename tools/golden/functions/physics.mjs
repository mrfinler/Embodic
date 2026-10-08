// U-M2e: Xcoil engine functions ported by embodic.physics. Names follow the registry's golden_functions where Xcoil has
// a function of that name; `computeAnalysis` wraps compute() and has no registry name, so its fixtures carry no eq_ids.
const SAMPLES = 181;

// Result fields of compute().analysis that embodic.physics reproduces (EQ-06, EQ-09, EQ-12, EQ-18, EQ-23, EQ-26),
// with the inputs Xcoil's own run used (copper resistivity at the winding temperature, mechanical speed).
function analysisOf(E, params) {
  const r = E.compute(params);
  if (!r.ok || !r.analysis) throw new Error(`Xcoil compute failed: ${JSON.stringify(r.errors)}`);
  const a = r.analysis;
  // Xcoil's own EQ-23 on the winding copper alone: no via barrels, links or interconnect (icR = null).
  const windingOnly = E.applyConnection(
    r.params,
    { ...structuredClone(a), phases: a.phases.map((ph) => ({ ...structuredClone(ph), R: ph.Rtrace })) },
    null,
  );
  const copperT = r.layout.layers.map((layer) => layer.copperT);
  const ic = E.interconnectResistance(r.params, r.layout.interconnect, copperT);
  const icItems = r.layout.interconnect.items.map(icItemOf);
  const phaseWaveform = E.emfWaveform(a, SAMPLES)[0].v;
  const lineWaveform = E.lineWaveform(a, SAMPLES)[0].v;
  return {
    omegaM: a.omegaM,
    rho: E.copperResistivity(r.params.tempC),
    Ke1: a.Ke1,
    phaseKe: a.phases.map((ph) => ph.Ke[0]),
    keLinePk: a.keLinePk,
    keLinePeakWaveform: Math.max(...lineWaveform.map(Math.abs)) / a.omegaM,
    thd: a.thd,
    Rphase: a.Rphase,
    // Rtrace is the winding copper alone; Rphase adds via barrels and links (Rextra), which the mapped circuits omit.
    phaseRtrace: a.phases.map((ph) => ph.Rtrace),
    phaseRextra: a.phases.map((ph) => ph.Rextra),
    phaseR: a.phases.map((ph) => ph.R),
    interconnect: { lineStub: ic.lineStub, link: ic.link, neutralRing: ic.neutralRing },
    icItems,
    rLineLine: a.rLineLine,
    rLineLineWindingOnly: windingOnly.rLineLine,
    pEddy: a.pEddy,
    pCu: a.pCu,
    pCirc: a.pCirc,
    pInterconnect: a.pInterconnect,
    torque: a.torque,
    pOut: a.pOut,
    lossTotal: a.lossTotal,
    efficiency: a.efficiency,
    motorConstant: a.motorConstant,
    phaseWaveform,
    lineWaveform,
  };
}

// What interconnectResistance (engine.js l.1361-1372) reads to sort one interconnect item into lineStub, link or
// neutralRing. `first` is the first primitive, so a reader can find the item among the layout's objects of its layer.
function icItemOf(it) {
  return {
    layer: it.layer,
    net: it.net,
    first: it.prims[0],
    line: it.line ?? null,
    tapOf: it.tapOf ?? null,
    tapPhase: it.tap ? it.tap.phase : null,
    linkNet: it.link ? it.link.net : null,
    ringTapVias: it.link ? it.link.taps.map((t) => t.via) : null,
    neutralPad: !!it.neutralPad,
    primKinds: it.prims.map((q) => q.kind),
    primTapPhase: it.prims.map((q) => (q.tap ? q.tap.phase : null)),
  };
}

// EQ-20 on compute()'s own drive analysis: the star-equivalent inputs torqueSpeed saw and the curve it returned.
function driveOf(E, params) {
  const r = E.compute(params);
  const ts = r.ok && r.analysis ? r.analysis.torqueSpeed : null;
  if (!ts) throw new Error(`Xcoil drive analysis failed: ${JSON.stringify(r.errors)} ${r.analysis && r.analysis.driveError}`);
  return curveOf(ts, {
    phases: r.params.phases,
    connection: r.analysis.connection,
    poles: r.params.poles,
    vDc: r.params.vDc,
    modulation: r.params.modulation,
    resistance: ts.Req,
    inductance: ts.Leq,
    keEqRms: ts.keEq,
    currentLimit: ts.iMax,
  });
}

function curveOf(ts, inputs) {
  return {
    inputs: { ...inputs, points: ts.points.length },
    vPhaseMax: ts.vPhaseMax,
    rpmNoLoad: ts.rpmNoLoad,
    rpmBase: ts.rpmBase,
    torqueMax: ts.torqueMax,
    speedRpm: ts.points.map((q) => q.rpm),
    torque: ts.points.map((q) => q.torque),
    power: ts.points.map((q) => q.pOut),
  };
}

export const FUNCTIONS = {
  copperResistivity: { required: ['tempC'], run: (E, x) => E.copperResistivity(x.tempC) },
  traceResistance: {
    required: ['lengthMm', 'widthMm', 'thickMm', 'tempC'],
    run: (E, x) => E.traceResistance(x.lengthMm, x.widthMm, x.thickMm, x.tempC),
  },
  viaBarrelArea: { required: ['drillMm', 'platingMm'], run: (E, x) => E.viaBarrelArea(x.drillMm, x.platingMm) },
  skinDepthMm: { required: ['freqHz', 'tempC'], run: (E, x) => E.skinDepthMm(x.freqHz, x.tempC) },
  ipc2221Current: {
    required: ['areaMm2', 'dT', 'internal'],
    run: (E, x) => E.ipc2221Current(x.areaMm2, x.dT, x.internal),
  },
  fieldHarmonic: { required: ['n', 'r', 'z', 'F'], run: (E, x) => E.fieldHarmonic(x.n, x.r, x.z, x.F) },
  applyConnection: {
    required: ['p', 'an'],
    run: (E, x) => {
      const an = E.applyConnection(x.p, x.an, null);
      return { keLinePk: an.keLinePk, KtPerArms: an.KtPerArms, KvRpmPerV: an.KvRpmPerV };
    },
  },
  computeAnalysis: { required: ['params'], run: (E, x) => analysisOf(E, x.params) },
  driveAnalysis: { required: ['params'], run: (E, x) => driveOf(E, x.params) },
  torqueSpeed: {
    required: ['p', 'an', 'ind'],
    run: (E, x) => {
      const ts = E.torqueSpeed(x.p, x.an, x.ind);
      return curveOf(ts, {
        phases: x.p.phases,
        connection: x.an.connection,
        poles: x.p.poles,
        vDc: x.p.vDc,
        modulation: x.p.modulation,
        resistance: ts.Req,
        inductance: ts.Leq,
        keEqRms: ts.keEq,
        currentLimit: ts.iMax,
      });
    },
  },
};
