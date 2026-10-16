// GR-07: Xcoil stackupFor (engine.js l.1156-1178), the layer centres and thicknesses that embodic's even stack-up helper
// reproduces. The input `p` carries only the keys stackupFor reads; the output is the engine's own result.
export const FUNCTIONS = {
  stackupFor: { required: ['p', 'nCu'], run: (E, x) => E.stackupFor(x.p, x.nCu) },
};
