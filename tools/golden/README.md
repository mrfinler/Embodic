Prepared by: Agent 3 (U-M1d) - model: claude-opus-5-5

# Golden regression harness

The harness pins embodic's ports to Xcoil v3. A Node script runs Xcoil's `engine.js` on listed cases and writes JSON
fixtures. Python comparators in `tests/golden/harness/` compare embodic results with those fixtures under the tolerance
classes of `docs/phase2/architecture/test_plan.md` section 3. CI needs no Node, because the fixtures are committed.

## Files

| Path | Content | Owner |
|---|---|---|
| `tools/golden/dump_xcoil.mjs` | the dumper | U-M1d |
| `tools/golden/cases/<area>.json` | case lists, one per owning unit | U-M1d writes `m1.json` |
| `tests/golden/data/<area>/<case_id>.json` | committed fixtures, one per case | written only by the dumper |
| `tests/golden/harness/` | codec, comparators, allow-list reader, self-tests | U-M1d |
| `tests/golden/expected_diffs/<area>.toml` | intentional deviations, one file per owning unit | per unit, via Fable |
| `tests/golden/conftest.py` | makes `harness` importable, provides `golden_report` | U-M1d |

## Regenerate fixtures

```sh
node tools/golden/dump_xcoil.mjs tools/golden/cases/m1.json
node tools/golden/dump_xcoil.mjs tools/golden/cases/m1.json --out /tmp/m1-check   # scratch copy
```

The dumper loads the engine read-only from `$XCOIL_ENGINE`, default `/home/claude/serpentine/src/engine.js`. On
another machine, set `XCOIL_ENGINE` to the local copy, for example `%USERPROFILE%\xcoil\src\engine.js`. Fixtures do
not record the engine path, only its SHA-256.

Two runs give byte-identical fixtures (verified, run 2026-10-04 with Node v22.22.2: 101 files, equal `sha256sum`).
`test_m1_fixtures_equal_a_fresh_dump` repeats that check whenever Node and the engine are present, and is skipped
otherwise.

## Case file

```json
{"format": "embodic.golden-cases", "format_version": 1, "area": "m1", "cases": [
  {"id": "primlength-arc-cw-300", "fn": "primLength", "note": "clockwise 300 degree arc", "tags": ["arc", "cw"],
   "inputs": {"prim": {"type": "arc", "cx": -3, "cy": 4, "r": 2.5, "a1": 5.235987755982989, "a2": 0,
                       "width": 0.2, "kind": "bus"}}},
  {"id": "segsegdist-seeded-crossing", "fn": "segSegDist", "note": "...", "tags": ["seeded", "crossing"],
   "seeded": {"generator": "seg_pair_crossing", "seed": 1003, "count": 1000}}]}
```

- `id` is lower-case kebab and unique. It is also the fixture file name.
- `fn` names an entry of `FUNCTIONS` in the dumper. Each entry lists its input keys. An unknown or missing key stops
  the run, so a typo such as `hmax` cannot fall back to a default silently.
- A case gives either `inputs` (one call) or `seeded` (`count` calls from a generator). Seeded inputs come from
  mulberry32, an integer-only PRNG, and are written into the fixture, so Python needs no PRNG.
- Generators: `seg_pair_random`, `seg_pair_touching`, `seg_pair_crossing`, `seg_pair_collinear`,
  `seg_pair_parallel`, `pt_seg_random`, `pt_seg_near`, `discretize_random`, `tf_prim_random`.
- Inputs may contain `{"$f": "inf"}`, `{"$f": "-inf"}` and `{"$f": "nan"}`.

Tags used in `m1.json`: `line`, `arc`, `ccw`, `cw`, `gt180`, `zero-length`, `degenerate`, `collinear`, `crossing`,
`touching`, `parallel`, `perpendicular`, `mirror`, `rotation`, `threshold`, `default-params`, `pad`, `grid`,
`signed-zero`, `seeded`, `nonfinite-input`, `nonfinite-output`. A `nonfinite-input` case feeds Infinity or NaN to
Xcoil. A port that rejects non-finite input at its boundary skips those cases. A `nonfinite-output` case gets a
non-finite result from finite input, so a port must reproduce it.

## Fixture format

```json
{
  "calls": [{"inputs": {...}, "output": ...}],
  "case_id": "primstart-arc-r-inf",
  "eq_ids": [],
  "fn": "primStart",
  "format": "embodic.golden-case",
  "format_version": 1,
  "note": "...",
  "producer": {"engine_sha256": "3e0659...", "name": "xcoil-v3", "runtime": "node v22.22.2"},
  "seeded": {"count": 1000, "generator": "seg_pair_crossing", "seed": 1003},
  "tags": ["arc", "nonfinite-input"]
}
```

- `eq_ids` come from `golden_functions` in `docs/phase2/engineering/equation_registry.json`. The registry lists no
  EQ-ID for `primStart`, `primEnd`, `reversePrims`, `tfPoint` or `tfPrim`, so their list is empty (verified, read
  from the M1 fixtures 2026-10-04).
- `seeded` is present only for seeded cases.
- Primitive inputs and outputs use the board-dump primitive record (Phase 1 port notes section 7.5, interfaces.md
  section 9.2): `type` `"line"` with `x1, y1, x2, y2`, or `"arc"` with `cx, cy, r, a1, a2` (signed sweep `a2 - a1`);
  `width`; `kind` (Xcoil's name, for example `endturn`). Output primitives also carry `start` and `end`, computed by
  Xcoil's `primStart` and `primEnd`.
- Other outputs are written as Xcoil returns them. A `discretize` segment keeps Xcoil's keys
  `x1, y1, x2, y2, s, len, kind, w, pi`. `makeGrid` gives `{cell, entries: [[key, [indices]]]}` in `Map` insertion
  order. `gridQuery` gives the visited segment indices in visiting order.

Encoding rules (verified by reading the dumper and by `test_codec.py`):

- Keys are sorted. Indent is two spaces. A list or object that holds only scalars stays on one line.
- Finite numbers use JavaScript's shortest round-trip text (`String(x)`), so `5.0` appears as `5`.
- Infinity and NaN become `{"$f": "inf"}`, `{"$f": "-inf"}` and `{"$f": "nan"}`. JSON has no literal for them.
- Negative zero is written `-0.0`. Python reads `-0` as the integer 0 and would lose the sign. The sign matters,
  because `atan2(-0, -5)` is -pi and `atan2(0, -5)` is +pi (see `tfpoint-negative-x-signed-zero`).
- The engine receives a `structuredClone` of the inputs. The recorded inputs are therefore the ones passed, even if a
  function mutated its arguments.

## Python harness

Golden tests import `harness` directly (`from harness import compare_prims, load_area, KERNEL_MM`).
`tests/golden/conftest.py` puts `tests/golden` on `sys.path` for both pytest import modes.

Tolerance classes (a value passes when `|g - a| <= max(rel * max(|g|, |a|), abs)`):

| Name | rel | abs | Source |
|---|---|---|---|
| `EXACT` | 0 | 0 | test_plan.md section 3, discrete outputs |
| `KERNEL` | 1e-12 | 0 | test_plan.md section 3, scalar kernels |
| `KERNEL_MM` | 0 | 1e-12 | GR-17 coordinates, GR-18 distances (mm) |
| `INTEGRATED` | 1e-9 | 0 | test_plan.md section 3, integrated results |
| `DRC_VALUE` | 0 | 1e-6 | test_plan.md section 3, DRC values (mm) |

Every comparator applies these rules:

- Two integers compare exactly under every class.
- An integer and a float compare as numbers.
- A bool never matches a number.
- NaN matches only NaN. An infinity matches only the same infinity.
- `-0.0` equals `0.0`.

Comparators return a `Comparison`. Its verdict is computed from its diffs. It is never stored.

- `compare_scalar(golden, actual, tolerance)` compares one scalar.
- `compare_sequence(golden, actual, tolerance)` compares lists element by element. Elements may be scalars, lists or
  records. Each diff names its path, for example `$[7].y2`.
- `compare_prims(golden, actual, tolerance)` reads board-dump records, or objects with the interfaces.md section 5
  field names (`x1_mm`, `cx_mm`, `start_rad`, `sweep_rad`, `width_mm`). It compares type, endpoints, centre, radius,
  `|sweep|`, sweep direction and width. Endpoints are computed from the angles, so a start angle that differs by a
  whole turn still matches. The direction check exists because a reversed half circle keeps both endpoints and
  `|sweep|`.
- `compare_drc(golden_mm, actual_mm, rule_mm=..., golden_pass=...)` applies D-006. Values must agree within 1e-6 mm.
  embodic passes when `value >= rule - 1e-6`. Pass/fail must agree with Xcoil's flag outside Xcoil's slack band
  `[rule - 0.004, rule)` (Phase 1 port notes section 3.1). Inside the band the result is `indeterminate`. The band is
  half-open, as in D-006 and test_plan.md. A symmetric band `|value - rule| <= 0.004` would hide disagreements above
  the rule, and `test_drc_band_rule_requires_agreement_above_the_rule` guards against it.
- `near_threshold(value, threshold)` is true within 1e-9 relative. A test uses it to report a mismatch in a discrete
  decision, such as a `ceil` count, as indeterminate instead of failed.
- The `golden_report` fixture provides `check(case_id, comparison)`. It raises on a mismatch, and logs expected and
  indeterminate results in a terminal summary section.

A typical golden test (U-M1b's, shown as an example). Every test needs a REQ marker or the trace matrix gate fails
(TR-02); a module-level `pytestmark` covers a file whose tests serve one requirement:

```python
import pytest

from harness import KERNEL_MM, apply_allow_list, compare_scalar, load_allow_list, load_area, EXPECTED_DIFFS_DIR

pytestmark = pytest.mark.req("REQ-…")


def test_primitive_length_matches_xcoil(golden_report):
    allow = load_allow_list(EXPECTED_DIFFS_DIR / "m1.toml")
    for case in load_area("m1").values():
        if case.fn != "primLength" or "nonfinite-input" in case.tags:
            continue
        for call in case.calls:
            result = compare_scalar(call.output, port_primitive_length(call.inputs["prim"]), KERNEL_MM)
            golden_report.check(case.case_id, apply_allow_list(result, case.case_id, allow))
```

## Allow-lists

`tests/golden/expected_diffs/<area>.toml` holds `schema_version = 1` and zero or more `[[diff]]` tables:

| Key | Required | Meaning |
|---|---|---|
| `id` | yes | unique in the file, for example `XD-M1-001` |
| `case` | yes | case id; `*` matches any run of characters |
| `path` | no | diff path pattern, default `*`; only `*` is special, so `$[*].x1` works |
| `eq_id` | yes | owning entry of `equation_registry.json`, form `EQ-nn` |
| `reason` | yes | why the port differs |
| `tolerance` | no | `{ rel = ..., abs = ... }`: admit only numeric value diffs inside this bound |
| `agent2_signoff`, `agent4_signoff` | yes | approval references (test_plan.md section 3) |

The reader rejects unknown keys, missing or empty fields, a malformed `eq_id`, a negative or partial tolerance and
duplicate ids. `apply_allow_list(comparison, case_id, entries)` marks each admitted diff with the entry id. The verdict
is `expected` when every diff is admitted. An entry with a tolerance override never admits a structural diff (length,
type, keys, direction, pass/fail). `m1.toml` has no entries yet.

## Self-checks

```sh
pytest tests/golden/harness -q
```

The self-tests seed a difference and expect it caught. They accept a difference inside the tolerance, and they check
that an allow-listed difference comes back as `expected`. They also check that the committed M1 set agrees with
`m1.json` and covers what the U-M1d brief requires. Each test's docstring names the defect it catches.

## Not covered yet

- No sampled path-distance comparator (test_plan.md "paths by sampled distance 1e-6 mm"). Layout-level cases (GR-20,
  GR-21) need one. `unresolved`.
- No Xcoil board dump of a whole layout. GR-19 needs one per topology. `unresolved`.
- `compare_prims` does not compare `kind` against embodic's `PrimitiveRole`. The name mapping (`endturn` to
  `end_turn`) belongs to U-M1b. `not tested`.
