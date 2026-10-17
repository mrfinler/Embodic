// F11-1 (U-M7b): Xcoil results the GR-22 analysis fixtures do not carry. EQ-16 and EQ-17 come from massThermal
// (engine.js l.1378-1395), EQ-19 and EQ-22 from applyConnection (l.1398-1438), each on compute()'s own layout. The
// inputs each function read are written next to its output, so a reader can feed embodic's kernels the same numbers.
// U-M8d (fix wave F1 T-A4): outlinePrims and outlineArea (l.1055, l.1094) on one outline, for the rounded polygon.
import { recordFromPrim } from '../lib/codec.mjs';

function computed(E, params) {
  const r = E.compute(params);
  if (!r.ok || !r.analysis) throw new Error(`Xcoil compute failed: ${JSON.stringify(r.errors)}`);
  return r;
}

function layerCopperArea(E, layer) {
  let area = 0;
  layer.objs.forEach((o) => o.prims.forEach((q) => { area += E.primLength(q) * (q.w || 0); }));
  return area;
}

function massThermalOf(E, params) {
  const r = computed(E, params);
  const { layers, vias, mech, stackup } = r.layout;
  const nBoards = r.layout.nBoards || 1;
  const thermal = E.massThermal(r.params, layers, vias, mech, nBoards, r.analysis.lossTotal, stackup);
  return {
    params: r.params,
    nBoards,
    boardArea: mech.area,
    boardThickness: stackup ? stackup.boardThickness : r.params.boardThickness,
    customStackup: !!(stackup && stackup.custom),
    layerCopperT: layers.map((layer) => layer.copperT),
    layerCopperArea: layers.map((layer) => layerCopperArea(E, layer)),
    lossTotal: r.analysis.lossTotal,
    thermal,
    analysisThermal: r.analysis.thermal,
  };
}

function connectionOf(E, params) {
  const r = computed(E, params);
  const a = r.analysis;
  const copperT = r.layout.layers.map((layer) => layer.copperT);
  const ic = r.layout.interconnect ? E.interconnectResistance(r.params, r.layout.interconnect, copperT) : null;
  return {
    params: r.params,
    connection: a.connection,
    omegaM: a.omegaM,
    harmonics: a.harmonics,
    phaseE: a.phases.map((ph) => ph.E),
    phaseR: a.phases.map((ph) => ph.R),
    link: ic ? ic.link : [0, 0, 0],
    iPhaseRms: a.iPhaseRms,
    pDeltaCirc: a.pDeltaCirc,
    iDeltaCircRms: a.iDeltaCircRms,
    currentDensityPerPhaseAmp: a.currentDensityPerPhaseAmp,
    currentDensity: a.currentDensity,
  };
}

function outlineOf(E, x) {
  const prims = E.outlinePrims(x.shape, x.sides, x.apothem, x.rotRad, x.cornerR);
  return { prims: prims.map((q) => recordFromPrim(E, q)), area: E.outlineArea(x.shape, x.sides, x.apothem, x.cornerR) };
}

export const FUNCTIONS = {
  xcoilOutline: { required: ['shape', 'sides', 'apothem', 'rotRad', 'cornerR'], run: outlineOf },
  massThermal: { required: ['params'], run: (E, x) => massThermalOf(E, x.params) },
  applyConnection: { required: ['params'], run: (E, x) => connectionOf(E, x.params) },
};
