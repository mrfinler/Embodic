// Third oracle: evaluates Xcoil v3 DRC kernels read-only. Reads one JSON request on stdin, writes one JSON reply.
// Request: {engine, op: "segSegDist", pairs: [[a, b], ...]} | {engine, op: "ptSegDist", cases: [[x, y, s], ...]}
//        | {engine, op: "drcObjects", objects: [{prims, noSelf}], s, wMax}
'use strict';
const fs = require('fs');

const request = JSON.parse(fs.readFileSync(0, 'utf8'));
const E = require(request.engine);
let reply;
if (request.op === 'segSegDist') {
  reply = request.pairs.map(([a, b]) => E.segSegDist(a, b));
} else if (request.op === 'ptSegDist') {
  reply = request.cases.map(([x, y, s]) => E.ptSegDist(x, y, s));
} else if (request.op === 'drcObjects') {
  const r = E.drcObjects(request.objects, request.s, request.wMax);
  reply = { clearance: r.clearance, at: r.at, checked: r.checked, who: r.who };
} else {
  throw new Error('unknown op ' + request.op);
}
process.stdout.write(JSON.stringify(reply));
