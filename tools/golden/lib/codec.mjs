// Fixture encoding and board-dump primitive records, shared by the dumper and the area function modules.
// Importing this module has no side effects.

export const NONFINITE_TAG = '$f';

// ---------------------------------------------------------------- non-finite codec and canonical JSON

export function decodeNonFinite(value) {
  if (Array.isArray(value)) return value.map(decodeNonFinite);
  if (value === null || typeof value !== 'object') return value;
  const keys = Object.keys(value);
  if (keys.includes(NONFINITE_TAG)) {
    if (keys.length !== 1) throw new Error(`non-finite tag mixed with other keys: ${JSON.stringify(value)}`);
    const tag = value[NONFINITE_TAG];
    if (tag === 'inf') return Infinity;
    if (tag === '-inf') return -Infinity;
    if (tag === 'nan') return NaN;
    throw new Error(`unknown non-finite tag ${JSON.stringify(tag)}`);
  }
  return Object.fromEntries(keys.map((k) => [k, decodeNonFinite(value[k])]));
}

function scalarText(value) {
  if (typeof value === 'number') {
    if (Number.isNaN(value)) return `{"${NONFINITE_TAG}": "nan"}`;
    if (value === Infinity) return `{"${NONFINITE_TAG}": "inf"}`;
    if (value === -Infinity) return `{"${NONFINITE_TAG}": "-inf"}`;
    // JSON.stringify(-0) is "0"; "-0" would parse to the integer 0 in Python, so the sign needs "-0.0".
    if (Object.is(value, -0)) return '-0.0';
    return String(value);
  }
  if (value === null || typeof value === 'boolean' || typeof value === 'string') return JSON.stringify(value);
  throw new Error(`value of type ${typeof value} has no JSON form`);
}

const isContainer = (value) => value !== null && typeof value === 'object';

// Sorted keys, two-space indent; a container holding only scalars stays on one line so fixtures diff per record.
export function canonicalJson(value, depth = 0) {
  if (!isContainer(value)) return scalarText(value);
  const isArray = Array.isArray(value);
  const entries = isArray ? value.map((v) => [null, v]) : Object.keys(value).sort().map((k) => [k, value[k]]);
  const [open, close] = isArray ? ['[', ']'] : ['{', '}'];
  if (entries.length === 0) return open + close;
  const item = ([key, v], d) => (key === null ? '' : `${JSON.stringify(key)}: `) + canonicalJson(v, d);
  if (entries.every(([, v]) => !isContainer(v))) return open + entries.map((e) => item(e, depth)).join(', ') + close;
  const pad = '  '.repeat(depth + 1);
  return `${open}\n${entries.map((e) => pad + item(e, depth + 1)).join(',\n')}\n${'  '.repeat(depth)}${close}`;
}

// ---------------------------------------------------------------- primitives: board-dump record <-> Xcoil prim

const GEOMETRY_KEYS = { line: ['x1', 'y1', 'x2', 'y2'], arc: ['cx', 'cy', 'r', 'a1', 'a2'] };
const XCOIL_TYPE = { line: 'L', arc: 'A' };
const RECORD_TYPE = { L: 'line', A: 'arc' };

export function requireKeys(obj, allowed, required, what) {
  for (const k of Object.keys(obj)) if (!allowed.includes(k)) throw new Error(`${what}: unexpected key "${k}"`);
  for (const k of required) if (obj[k] === undefined) throw new Error(`${what}: missing key "${k}"`);
}

export function primFromRecord(record) {
  const geometry = GEOMETRY_KEYS[record.type];
  if (!geometry) throw new Error(`primitive record: unknown type ${JSON.stringify(record.type)}`);
  const keys = ['type', ...geometry, 'width', 'kind'];
  requireKeys(record, keys, keys, `${record.type} record`);
  const prim = { t: XCOIL_TYPE[record.type] };
  for (const k of geometry) prim[k] = record[k];
  prim.w = record.width;
  prim.kind = record.kind;
  return prim;
}

export function recordFromPrim(E, prim) {
  const type = RECORD_TYPE[prim.t];
  if (!type) throw new Error(`Xcoil primitive: unknown t ${JSON.stringify(prim.t)}`);
  const geometry = GEOMETRY_KEYS[type];
  requireKeys(prim, ['t', ...geometry, 'w', 'kind'], ['t', ...geometry, 'w', 'kind'], `Xcoil ${type}`);
  const record = { type };
  for (const k of geometry) record[k] = prim[k];
  record.width = prim.w;
  record.kind = prim.kind;
  record.start = E.primStart(prim);
  record.end = E.primEnd(prim);
  return record;
}
