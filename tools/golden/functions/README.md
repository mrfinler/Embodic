Prepared by: Agent 3 (U-M1d fix round) - model: claude-opus-5-5

# Area function modules

The M1 kernels live in `tools/golden/dump_xcoil.mjs`. Every other golden area keeps its Xcoil engine functions in
`tools/golden/functions/<area>.mjs`, one file per owning unit (`docs/phase2/architecture/work_breakdown.md` section 4).
No unit edits the dumper to add a function.

## How the dumper loads a module

1. The case file's `area` picks the module. `tools/golden/cases/m1_layout.json` with `"area": "m1_layout"` loads
   `tools/golden/functions/m1_layout.mjs`. Area `m1` loads no module.
2. The function table for the run is the M1 kernels plus the module's `FUNCTIONS`. A case may call either.
3. The run stops before it writes any fixture when the module is missing, when it exports no `FUNCTIONS` object, when
   an entry has an unknown key or lacks `required` or `run`, or when a name is already an M1 kernel.

`$GOLDEN_FUNCTIONS_DIR` replaces the folder. Only the self-test `tests/golden/harness/test_dumper_loader.py` uses it.

## Writing a module

Export `FUNCTIONS`, an object from function name to entry:

| Key | Required | Meaning |
|---|---|---|
| `required` | yes | case-input keys every call must give |
| `optional` | no | case-input keys a call may give |
| `run` | yes | `(E, x) => output`; `E` is the Xcoil engine module, `x` the decoded inputs of one call |

The dumper checks the input keys of every call against `required` and `optional`, decodes `{"$f": ...}` tags, and
passes `run` a `structuredClone` of the inputs. `run` returns plain JSON data: numbers (non-finite allowed), strings,
booleans, `null`, arrays and plain objects. Convert a `Map` or a typed array before returning it.

Import helpers from `../lib/codec.mjs`. Importing it has no side effects. Never import `dump_xcoil.mjs`, because
importing it starts a dump.

- `primFromRecord(record)` turns a board-dump primitive record into an Xcoil primitive.
- `recordFromPrim(E, prim)` turns an Xcoil primitive into a board-dump record with `start` and `end`.
- `decodeNonFinite(value)`, `requireKeys(obj, allowed, required, what)` and `canonicalJson(value)` are the dumper's own
  codec and key check.

Example (the module the loader self-test writes, verified by `pytest tests/golden/harness -q`):

```js
import { primFromRecord } from '../lib/codec.mjs';

export const FUNCTIONS = {
  scratchHalfLength: { required: ['prim'], run: (E, x) => E.primLength(primFromRecord(x.prim)) / 2 },
};
```

## Rules

- Load the engine only through `E`. Write no files. Leave `/home/claude/serpentine` untouched.
- Emit Xcoil's own keys and names. Python maps them to embodic names (`docs/phase2/architecture/test_plan.md`
  section 3, layout dumps).
- A fixture's `eq_ids` come from `golden_functions` in `docs/phase2/engineering/equation_registry.json`, matched by
  function name. Use the registry's name when the function computes a registered equation.
- The dumper compares names with the M1 kernels only. It never loads two area modules in one run. Pick names that no
  other area module uses, so one name means one computation in every fixture.
- Regenerate with `node tools/golden/dump_xcoil.mjs tools/golden/cases/<area>.json`. Fixtures go to
  `tests/golden/data/<area>/`.
