// U-M2e: Xcoil engine functions ported by embodic.physics. Names follow the registry's golden_functions.
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
};
