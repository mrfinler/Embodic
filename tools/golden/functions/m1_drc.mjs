// GR-18 band rule (U-M1d fix round 2): Xcoil's drcObjects clearance with Xcoil's own pass/fail for one rule.
// Python compares it with embodic run_drc under D-006 (tests/golden/m1_drc/test_gr18_band_rule.py).
import { primFromRecord, requireKeys } from '../lib/codec.mjs';

// Xcoil exports no function that returns a verdict for an object list. Every compute path compares the clearance with
// `p.clearance - tol` itself (runDrc l.757 and l.774), so the slack is read from runDrc's source and follows the
// engine whose sha256 the fixture records.
function xcoilSlack(E) {
  const source = E.runDrc.toString();
  const tol = /\btol = ([0-9.]+)/.exec(source);
  if (!tol || !source.includes('if (minTrace < p.clearance - tol) issues.push')) {
    throw new Error('engine.js runDrc: clearance verdict not found');
  }
  return Number(tol[1]);
}

function drcObjects(E, x) {
  const objs = x.objs.map((o, i) => {
    requireKeys(o, ['prims'], ['prims'], `objs[${i}]`);
    return { prims: o.prims.map(primFromRecord) };
  });
  const { clearance } = E.drcObjects(objs, x.clearance, x.wMax);
  const slack = xcoilSlack(E);
  // Negated as in Xcoil, which raises the error only when the comparison holds, so a NaN clearance passes there too.
  return { clearance, pass: !(clearance < x.clearance - slack), slack };
}

export const FUNCTIONS = {
  drcObjects: { required: ['objs', 'clearance', 'wMax'], run: drcObjects },
};
