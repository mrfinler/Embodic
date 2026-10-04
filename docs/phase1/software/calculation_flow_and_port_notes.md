Prepared by: Agent 3 — Senior Software Engineer — model: claude-opus-5-5

# Calculation flow and JS → Python port notes (Phase 1 draft, 2026-10-04)

Scope: how to port the Xcoil v3 engine (`/home/claude/serpentine/src/engine.js`) to Python without losing its numerics,
how to structure the geometry primitives so that every exporter and the KiCad adapter share them, and a design (not an
implementation) for a JS↔Python cross-check harness. The call graph from `compute()` is in `feature_inventory.md` §4.
All measurements below were made in this container (Node v22.22.2, CPython 3.11.15 on Linux/glibc, NumPy 2.4.4, Intel Xeon
2.1 GHz, 2 cores); they are not measurements on the user's Windows machine. Scripts are in my scratchpad and are described
inline so they can be re-created in Phase 2.

## 1. What must be reproduced

| Item | Where | What it pins down | Status |
|---|---|---|---|
| Golden v1 numbers | `/home/claude/serpentine/golden-configs.json` (23 configurations), `golden-v1.json` (captured from the frozen v1 engine by `golden-capture.js`), checked by `golden-check.js` | per config: DRC issue codes and clearances, envelope, layer count/z, Ke harmonics per phase, R per phase, Ke1, R_phase, torque, P_Cu, P_eddy, P_circ, efficiency, kw1, kd, THD, EMF L–L, Kv, Kt, J, IPC limit, skin depth, B1, imbalance, max traces, ρ0, ρ0max, r_V | verified (code) |
| Tolerances used by Xcoil | `golden-check.js` l.26 | rel 1e-9 for every number; P_eddy 3e-2; efficiency 5e-4 (comment l.24–25: v1 counted end-turn arcs on the magnet edge "depending on the last bit of sin/cos, so its value differed between JavaScript engines by up to 3 %") | verified (code) |
| Result today | runs in `feature_inventory.md` §0 | defaults: FAIL (c5 efficiency, rel 6.02e-4, interconnect loss); with `{"interconnect":false}`: OK, 1417 numbers | verified (run) |
| In-suite regression | `tests.js` REG-01…03 (l.377–400), table from `gen-reg.js` → `reg-table.json` (8 configs × 19 quantities) | same idea inside the 131-test suite | verified (code+run) |
| Agent 2's engineering checks | `docs/phase1/engineering/checks/` C1–C9 | engineering validity (field 1-D limit, EMF closed form, R hand calc …) | verified by Agent 2 (reproduced) |

Two different questions must stay separate in Phase 2 (`assumption`, design choice):
1. **Port equivalence** — does the Python port compute what Xcoil v3 computes (for every function that is ported
   "as-is")? Oracle: the JS engine itself, tolerances from §3.
2. **Engineering validity** — is the equation right for spiral coils? Oracle: Agent 2's EQ references and Agent 5's
   measured cases (O1–O3). A function can pass (1) and still be blocked by (2).

The new spiral generator (N-01) and every `replace` item have no JS counterpart; for them only (2) and Agent 2's closed
forms (EQ-02, EQ-03) apply.

## 2. Where JavaScript and Python floating-point behaviour differ

### 2.1 Measured differences

| Topic | Experiment | Result | Consequence for the port | Status |
|---|---|---|---|---|
| libm functions (sin, cos, tan, asin, acos, atan2, exp, pow) | 200,000 deterministic inputs generated in Node, same inputs evaluated with Python `math`, compared bit-for-bit | not bit-identical in sin 3.2 %, cos 3.3 %, tan 3.2 %, asin 6.4 %, acos 7.8 %, exp 9.7 %, pow 11.4 %, atan2 17.8 % of cases; maximum difference **1 ulp** everywhere | Bit-exact reproduction with the standard library is impossible; compare with tolerances. Windows CRT (user's machine) may differ again — `not tested` | verified (run) |
| `hypot` | engine uses its own `hypot(x,y) = Math.sqrt(x*x + y*y)` (`engine.js` l.77; `Math.hypot` is not used in the engine, 0 occurrences) | literal Python `math.sqrt(x*x + y*y)`: 0 of 200,000 differ; Python `math.hypot`: 8.8 % differ (1 ulp) | Port the helper literally; do **not** use `math.hypot` in the reference port. (Python doc: hypot accuracy algorithm changed in 3.10, "maximum error is under 1 ulp" — https://docs.python.org/3/library/math.html, `math.hypot`) | verified (run + doc) |
| A real kernel | literal Python port of `fieldHarmonic` (`engine.js` l.856–867) vs JS on 3,969 (n, r, z, G) samples incl. open rotor | 773 of 7,938 values not bit-identical; max relative difference **1.6e-15** | Unit-level kernels: tolerance 1e-12 relative is safe; integrated quantities: 1e-9 (Xcoil's own choice) | verified (run) |
| Rounding `Math.round` | values 2.5, −2.5, 0.5, −0.5, 1.5, 3.5 | JS 3, −2, 1, 0, 2, 4; Python `round` 2, −2, 0, 0, 2, 4 (banker's); `math.floor(x + 0.5)` 3, −2, 1, 0, 2, 4 | Use `math.floor(x + 0.5)` wherever the engine uses `Math.round`: `fmt()` for **every exported coordinate** (l.2762), angle quantisation in `windingInductance` (l.2629), DXF layer names (l.2866), validation (l.115) | verified (run) |
| Number → text | JS `fmt()` vs naive `repr(round(v*1e5)/1e5)` on 18 values | differences: `1` vs `1.0`, `0.00001` vs `1e-05`, `0.000005` → JS `0.00001` vs Python `0`, `1.000005` → JS `1.00001` vs Python `1.0`, `99999.999995` → `100000` vs `100000.0` | Exporters need a dedicated `fmt()` that reproduces JS `Number.prototype.toString` for the rounded value (no exponent between 1e-6 and 1e21, no trailing `.0`) if text-identical files are wanted; otherwise compare exported files by parsed numbers | verified (run) |
| `toFixed(6)` (used as dictionary keys for layer z, l.1852, l.2619) | 4 values | identical to `format(v, '.6f')` for those values | Ties can still differ (JS picks the larger n on an exact tie, Python rounds half-even on the exact binary value) → replace string keys by tolerance-based grouping of z values in the port | verified (run) for the sample; tie behaviour `inferred` from the language rules |
| Integer arithmetic | an LCG `(s*1103515245+12345) % 2^31` gave different sequences in JS and Python | JS numbers are doubles (exact only to 2^53); Python ints are exact | No such large products in the engine (Q, p ≤ 200, `normalizeParams` l.119, l.129); `crc32` (l.2932–2938) uses `>>> 0` and `^` → use `zlib.crc32` or mask with `& 0xFFFFFFFF` | verified (run) |

### 2.2 Language semantics to translate deliberately (`verified` = documented behaviour or code reading)

| Topic | JS (engine) | Python | Port rule |
|---|---|---|---|
| Summation order | left-to-right `reduce`/loops | `sum()` of floats uses **Neumaier summation since 3.12** ("sum() now uses Neumaier summation to improve accuracy and commutativity", What's New 3.12, gh-100425 — https://docs.python.org/3/whatsnew/3.12.html); NumPy `np.sum` uses pairwise summation | In the reference port write explicit loops (or always `math.fsum`, accepting a known difference); never mix. User runs 3.11+, KiCad's bundled version is unknown → the same code could give different last bits on 3.11 and 3.12 if `sum()` is used (`inferred`) |
| Division by zero, empty min/max | `x/0` → ±Infinity/NaN; `Math.min.apply(null, [])` → Infinity | `ZeroDivisionError`; `min([])` → `ValueError` | The engine relies on Infinity as a value in many places (e.g. `KvRpmPerV` l.1008, `tempRiseEst` l.1391, clearance initialisers `Infinity` l.757–823, `drc.linkClearance = Infinity` l.1973); use `math.inf` explicitly and guard every division that can be zero |
| `%` | remainder has the sign of the dividend (`fmod`) | float `%` is floored | `angNorm` (l.1221) and `((a % Q) + Q) % Q` (l.1652) give the same values if written with `math.fmod` (float) and Python `%` (int) respectively |
| Sorting | `Array.prototype.sort` stable since ES2019 (V8 "supported since … Node.js 12", https://v8.dev/features/stable-sort); comparators `a - b` (l.1231, l.1243, l.1298, l.1717, l.2161, l.2399, l.2666) | `sorted` is guaranteed stable (https://docs.python.org/3/howto/sorting.html) | Translate comparators to `key=` functions; equal keys keep input order in both |
| Map/object iteration | `Map` insertion order (`makeGrid` l.580–596) | `dict` insertion order (3.7+) | equivalent |
| JSON | `JSON.stringify(Infinity)` → `null` | `json.dumps(math.inf)` → `Infinity` (non-standard) unless `allow_nan=False` | Harness encodes non-finite values explicitly (§6.2); results contain 1–6 non-finite numbers per config (verified run) |
| Typed arrays | `Float64Array` zero-initialised (`windingInductance` l.2622, l.2642–2643) | lists or `numpy.zeros` | same doubles |
| Closures with state | e.g. `W.rhoOut = function (L)…` stored in the result (l.1563) | — | Results must be plain data in Python (functions are dropped by JSON in JS anyway) |

### 2.3 Threshold branches that can amplify 1-ulp differences

Each of these is a discrete decision on a continuous value; a 1-ulp difference near the threshold changes counts or flags.
The cross-check must treat them as "near-threshold → indeterminate", not as failures (§7.2). All `verified (code)`
except where a run is cited:

| Location | Decision |
|---|---|
| `discretize` l.543, l.551 | `n = ceil(L / hMax)` and angle/sagitta counts → number and position of DRC/EMF segments |
| `analyze` l.913–919, `analyzeWave` l.2024–2026, `analyzeElements` l.1861–1862 | segment inside/outside the magnet span with a 1e-9 mm tolerance (added after the v1 3 % eddy discrepancy) |
| `involutePrims` l.1481–1488 | biarc piece count doubles until deviation ≤ 0.5 µm (cap 128) → primitive count may differ |
| `fitStatus` l.389, `maxFillet` l.332–340 (60 bisections), `maxTracesFit` l.394–404 | fits / does not fit; maximum fillet radius |
| `sectorFeasible` l.2274–2277, `deriveWave` gap checks l.1534–1557 (`- 1e-9`) | turn limits |
| `chainCoils` l.2331–2366 (EPS 1e-9) | coil chain order and ring levels |
| `starOfSlots` l.1904 (belt index `floor(((a + π/(2m)) mod 2π) / (π/m))`) and its balance check l.1915–1916 (`1e-6`) | phase and sign of every coil; "balanced" flag. Phasors that lie exactly on a 60° belt edge are float ties: Agent 2's C6 shows 12/14, 24/14, 24/22, 24/26 wrongly rejected; **12/10 (the O1 configuration, D08) has 6 of its 12 phasors within 1e-9 rad of a belt edge (30°, 90°, 150°, 210°, 270°, 330°) and passes in Xcoil only because the rounding happens to be consistent** — `verified (run)`: `node -e` on `E.starOfSlots(12, 5, 3)` → `ok true`, 6 ties. A port that mimics the float expression could flip 12/10 on another platform/libm (`inferred`, §2.1) |
| DRC tolerance 0.004 mm (`runDrc` l.757, l.774, l.1929, l.1988, l.2147, l.2429) and path-distance exemptions (`drcLayer` l.611–633, `drcObjects` l.1700–1708) | Xcoil pass/fail and which pair is reported. **Not ported**: embodic uses the D-006 rule (§3.1) |

**Phase assignment in the Python port (DEF-14):** `starOfSlots`/`balancedSectorList` are replaced (EQ-08) by exact
integer/rational arithmetic for **all** Q/2p: the electrical position of coil k is the integer `r = (k·p) mod Q` in units
of 2π/Q, and the belt index is the exact integer `b = ((4·m·r + Q) // (2·Q)) mod 2m` (the float expression
`floor(2m·r/Q + 1/2)` evaluated without rounding; an edge phasor goes deterministically to the upper belt, i.e. half-open
belts `[edge, edge + 60°)` for m = 3). Phase and sign then follow Xcoil's belt order (m = 3: phase `[A, C, B][b mod 3]`,
positive for even b). No floating-point comparison decides a phase or the balance flag (balance: equal integer counts per
phase plus Agent 2's phasor-sum check in exact or tolerance-free form). Floats are used only afterwards for k_d/k_w
magnitudes. Check of this formula (`verified (run)`, `node -e` against `E.starOfSlots`): 12/10 → "AabBCcaABbcC" (12/12
coils identical to Xcoil, = D08 Fig. 3.7), 12/16 → "ACBACBACBACB", 18/16 identical; for 12/14, 24/14, 24/22, 24/26 it
gives equal counts per phase (4/4/4 resp. 8/8/8) where Xcoil reports "unbalanced". Final tie convention to be confirmed by
Agent 2 (EQ-08). 12/10 must be a regression case. `assumption` (design rule), consistent with Agent 2's EQ-08 verdict.
| `spreadPadAngles` l.1716–1721 (80 iterations, `- 1e-9`) | pad positions |
| `windingInductance` l.2628–2629 | radial bin index `floor`, angle quantised to 1/2e4 rad with `Math.round` |
| `filletPath` l.1755–1758 | corner skipped when gap > 1e-6 mm or turn < 0.03 rad |

## 3. Tolerances proposed for port equivalence (`assumption`, to be confirmed by Agent 4)

| Quantity class | Tolerance | Reasoning |
|---|---|---|
| Integers, enums, error/issue codes, topology structure (layer count, via count, element count) | exact | Discrete outputs; mismatch = bug, unless flagged near-threshold (§2.3) |
| Scalar kernels (field, resistance, via area, skin depth, corner construction) | rel 1e-12 | measured max 1.6e-15 for `fieldHarmonic` (§2.1) |
| Integrated scalar results (Ke per harmonic, R, torque, losses, kw1, THD, L_s) | rel 1e-9 | Xcoil's own golden tolerance (`golden-check.js` l.26) |
| P_eddy when conductors lie on the magnet edge | rel 3e-2 (as Xcoil) or construct the case so that no edge coincidence exists | documented edge case (golden-check l.24–25) |
| Geometry | sampled distance between Python and JS copper paths ≤ 1e-6 mm (sample every 0.05 mm, both directions); primitive counts compared only where no adaptive threshold applies | biarc/fillet counts can differ legitimately |
| DRC clearances (values: `traceClearance`, `padClearance`, `linkClearance`, `padPadClearance`, `interconnectClearance`, `viaGap`) | abs 1e-6 mm between Python and JS values (same discretisation); with exact line/arc distances in embodic, Python ≥ JS − 1e-6 mm (discretised chords can only over- or under-estimate by the bounded sagitta, which must be documented) | values are what is compared (D-006) |
| DRC pass/fail | **derived in Python from the value with the D-006 rule** (§3.1); agreement with Xcoil's flag required only outside Xcoil's slack band | D-006, DEF-01 |
| Exported text | parsed-number comparison at the 1e-5 mm grid of `fmt()`; byte-identity optional | §2.1 formatting |

### 3.1 DRC acceptance rule (decision D-006, `docs/decision_log.md`)

- embodic reports a violation whenever `measured clearance < rule − ε`, with **ε ≤ 1e-6 mm** (proposed ε = 1e-6 mm).
  There is **no 0.004 mm slack**. Xcoil accepts down to `clearance − 0.004 mm` (`engine.js` l.757 `tol = 0.004`, l.774
  `minTrace < p.clearance - tol`, l.1988) — `verified (code)`; a literal port would under-report intrusions up to 4 µm.
- The measured clearance must be exact or provably conservative (Agent 4 IT-12: analytic line/arc distances); if the
  discretised Xcoil method is kept for speed, its worst-case error (chord sagitta ≤ `sagTol`, `discretize` l.537, l.550)
  must be subtracted from the measured value, not hidden in a slack (`assumption`, implementation detail for Phase 2).
- Cross-check classification per DRC quantity with set clearance s, Xcoil value v_JS, Python value v_PY:
  - values: |v_PY − v_JS| ≤ 1e-6 mm (or the documented exact-vs-discretised bound);
  - pass/fail agreement is **required** when v_JS ≥ s (both pass) or v_JS < s − 0.004 mm (both fail);
  - when **s − 0.004 ≤ v_JS < s** (Xcoil's slack band: Xcoil passes, embodic fails by design) the case is marked
    **"indeterminate for pass/fail agreement"** and listed in the report with its value; it is not a failure.
- Example from the baseline: Xcoil's default design has `traceClearance = 0.19901 mm` for s = 0.20 mm (`golden-v1.json`
  c0; the v3 engine gives the same value with `ok: true` — `verified (run)`) — inside the slack band, so embodic would report a violation there (consequence `inferred`); the
  spiral generator must therefore place copper with margin ≥ ε, not rely on a tolerance.

## 4. Performance measurements and consequences

| Measurement (this container) | Result | Status |
|---|---|---|
| Node `compute()` default serpentine (6 layers, 1,532 primitives, 140,172 DRC pairs) | 156 ms | verified (run) |
| Node `compute()` 16-pole wave preset (2 layers, 2,810 primitives, 458,853 DRC pairs) | 94 ms | verified (run) |
| Node `compute()` 12/10 sector preset (857 primitives, 573,747 DRC pairs) | 81 ms | verified (run) |
| Node `compute()` SPARK-style preset (12 layers, 52,224 primitives, 5,344,555 DRC pairs, 240 inductance orders) | 5,516 ms | verified (run) |
| Kernel `segSegDist` × 1,000,000 (the DRC inner loop, `engine.js` l.563–578) | Node 40 ms; CPython literal port 1,813 ms (≈45×); NumPy vectorised over all pairs 543 ms | verified (run) |

Consequences (`inferred` from the measurements): a literal pure-Python port would need seconds for the default case and
minutes for large boards — acceptable for a batch run or a one-shot KiCad action, not for the live recompute that Xcoil
offers (F-08). Proposed strategy (`assumption`):
1. **Reference implementation** in plain Python + `math`, a line-by-line port used only for cross-checking and as readable
   specification (fast enough for small test cases).
2. **Production kernels** vectorised with NumPy for the four hot spots: discretisation, DRC pair distances (grid broad
   phase + vectorised narrow phase), EMF/eddy integration over segments × harmonics, inductance harmonic sums. Each kernel
   is tested against (1) with the §3 tolerances.
3. **Staged recompute**: cache geometry + DRC by a hash of geometry parameters; operating-point parameters (rpm, current,
   temperature, drive) re-run only the cheap analysis stage.
4. Numba/Cython are not proposed: they add compilers or large native wheels to the KiCad per-plugin venv (`assumption`;
   see the dependency draft).

## 5. Library choice for the engine

| Candidate | Licence (PyPI, read 2026-10-04) | Use | Proposal | Status |
|---|---|---|---|---|
| Python stdlib (`math`, `cmath`, `dataclasses`, `enum`, `json`, `zipfile`, `zlib`, `hashlib`, `struct`) | PSF | everything in the reference implementation; ZIP, CRC-32, hashing | **yes** | verified (stdlib) |
| NumPy | 2.4.4: `BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0`, requires Python ≥ 3.11; 2.5.3 requires ≥ 3.12; cp311 win_amd64 wheels exist for 2.2.6, 2.3.5, 2.4.4 | vectorised kernels (§4) | **yes, the only native dependency of the core**; version range set after KiCad's bundled Python is known (T2) | verified (PyPI JSON API) |
| Shapely 2.1.2 | BSD 3-Clause (bundles the GEOS C++ library, whose licence was not checked here) | polygon buffering/booleans | **no**: converts arcs to segments (KiCad needs true arc tracks), adds a native dependency; our DRC is centre-line distance minus half widths, which needs no polygon engine | verified (licence field) / inferred (suitability) |
| ezdxf 1.4.4 | MIT (classifier) | DXF read/write | not needed for writing (Xcoil's R12 writer is ≈ 50 lines, l.2826–2874); keep as an option if DXF *import* is wanted | verified (licence) |
| SciPy, sympy, numba | not checked | — | not needed | — |

## 6. Geometry primitive set shared by all exporters

Design proposal (`assumption`); mirrors Xcoil's `prims` (F-16) so the port stays traceable.

```
core.geometry (pure Python + optional NumPy, no UI/KiCad imports)
  Line(x1, y1, x2, y2, w, kind)            # mm; w = copper width
  Arc(cx, cy, r, a1, a2, w, kind)          # rad; signed sweep a2 - a1 gives the traversal direction (as Xcoil)
  Prim = Line | Arc                         # frozen dataclasses with slots
  Path = tuple[Prim, ...]                   # invariant: end(p[i]) == start(p[i+1]) within 1e-9 mm (test GEO-01)
  CopperObject(kind, path, net, phase, touch_vias: tuple[int, ...], flags)
  Via(x, y, drill, pad, layer_from, layer_to, net, role)      # role: centre, transfer, terminal, ring …
  Pad(x, y, shape, w, h, drill, rot, net, label, layer)
  Layer(index, name, kicad_name, z, copper_t, role, phase, pair, objects)
  Board(layers, vias, pads, outline: Path, cutouts: tuple[Path, ...], holes, stackup, meta)
  ops: length, start, end, reverse, rotate, mirror, transform, discretize, fillet, taper, width_runs,
       sample_points, distance(prim, prim)   # exact line/arc distances optional, discretised as in Xcoil first
```

Rules:
- Internal units mm and radians (as `engine.js` l.2); conversion to KiCad nanometres (kipy, Agent 5 §5 item 5) and the
  `.kicad_pcb` y-flip and origin offset (`exportKicad` l.2878–2880: X = 150 + x, Y = 100 − y) happen **only** in the
  KiCad adapters.
- Arcs are exported as start/mid/end (KiCad track `arc` and `gr_arc`, as Xcoil l.2900); a full circle is only allowed for
  outline/holes (`gr_circle`) — a copper arc of ≥ 2π must be split (`inferred`).
- Exporters (`io.export.svg`, `.dxf`, `.kicad_pcb`, PDF figure, 2-D canvas, 3-D view, `kicad.ipc` adapter) consume a
  `Board` and never call generators. Generators return `Board` plus an electrical element list
  (`phase → series elements → parallel members (layer, path)`, the shape `analyzeElements` already uses, l.1844–1846).
- Deterministic: no randomness, stable ordering, a geometry hash (SHA-256 of the canonical JSON) for caching and
  traceability (N-05).

### 6.1 Keeping the engine free of UI and KiCad imports

- Package split (names are placeholders for Agent 6): `embodic_core` (params, geometry, topology, analysis, DRC, mech,
  equations registry; depends on stdlib + NumPy), `embodic_io` (project files, exporters; depends on core), `embodic_app`
  (UI), `embodic_kicad` (kipy adapter + plugin entry point).
- Enforced by a test that parses every module of `embodic_core` with `ast` and fails on imports of UI toolkits, `kipy`,
  `pcbnew`, `wx` or `embodic_app`/`embodic_kicad` (no extra dependency; an import-linter tool is an alternative).
- Core API is pure: `compute(project: Params) -> Result`; `Result` is plain data, JSON-serialisable, with units, EQ-IDs
  and status on every quantity (N-04/N-05). No global state; logging through `logging`.

## 7. JS ↔ Python cross-check harness (Phase 2 task — design only)

### 7.1 Components

| Component | Runs on | Function |
|---|---|---|
| `tools/xcheck/cases/*.json` | — | case lists: golden configs (23, with `{"interconnect": false}`), the 15 presets, seeded fuzz sets (ranges as VAL-12 / WAV-13 / SEC-06, e.g. 200 configs), unit vectors for kernels (`fieldHarmonic`, `makeCorner`, `segSegDist`, `discretize`, `stackupFor`, `starOfSlots` …) |
| `tools/xcheck/dump_xcoil.js` | Node (dev machine only) | `require('/home/claude/serpentine/src/engine.js')` read-only; for each case call `E.compute` or the named kernel (all exported, l.2968–2985); write canonical JSON: non-finite numbers as `{"$f": "inf"}` (or `"-inf"`, `"nan"`), `-0` preserved, plus `{node_version, engine_sha256, case_id}`; geometry in the **board dump format** of §7.5 (the Python side writes the same format) |
| `tests/data/xcoil_v3/*.json` | — | committed snapshots, so CI and the user's machine need no Node; regenerated only when the case list changes |
| `tests/xcheck/test_equivalence.py` | pytest | runs the Python reference port and the production kernels on the same inputs; compares with the §3 tolerance map |
| `tests/xcheck/expected_diffs.toml` | — | allow-list of intentional deviations, each with EQ-ID and reason (e.g. EQ-08 integer star of slots: 12/14 now balanced; EQ-04 α_p(r)) |
| report | pytest plugin / script | Markdown table: per quantity max relative difference, worst case, number of near-threshold indeterminates |

### 7.2 Comparison rules

1. Structure first: errors/issue codes, layer count, via count, element count exact.
2. Scalars with the class tolerance (§3); paths by sampled distance; DRC **values** (`traceClearance`, `padClearance`,
   `linkClearance`, `padPadClearance`, `interconnectClearance`, `viaGap`) abs 1e-6 mm.
3. DRC pass/fail is not copied from Xcoil's `ok`/issue list: the harness derives it from each value with the D-006 rule
   (`value < s − ε`, ε ≤ 1e-6 mm) for both sides, and requires agreement with Xcoil's own flag only outside Xcoil's slack
   band; cases with `s − 0.004 ≤ v_JS < s` are reported as **"indeterminate for pass/fail agreement"** (§3.1).
4. Near-threshold detection: the Python side reports the margin of each decision listed in §2.3 (e.g. distance of a
   segment end from the magnet edge, distance of a star-of-slots phasor from a belt edge, DRC clearance minus limit); a
   mismatch with margin < 1e-9 (relative) is "indeterminate", logged, not failed. Phase assignment itself is exact in
   the port (§2.3), so a phase mismatch on a tie is listed in `expected_diffs` (EQ-08), not as indeterminate.
5. Output files: parse `.kicad_pcb`/DXF/SVG back to numbers and compare on the `fmt()` grid; byte-identity is optional.

### 7.3 Order of porting with the harness (proposal)

primitives + discretise → DRC kernels → field (EQ-05) → EMF path integral (EQ-06) → resistance (EQ-10/11) → assembly
(EQ-07) → losses (EQ-12) → connection (EQ-09) → waveforms (EQ-18) → mechanics (outline, screws) → exporters → (blocked
items EQ-14/15/20 only after approval). The spiral generator (N-01) is new and is checked against EQ-02/EQ-03 and
Agent 2's C2 closed form instead of Xcoil.

### 7.4 Licence note

Xcoil v3 is the team's own prior work (brief §2); running it read-only under Node for snapshots raises no licence issue
(`inferred`). No GPL reference code (magnetless_motor, kimotor) enters the harness.

### 7.5 Board dump format (JSON) for independent checks and the cross-check

One documented format, written by the JS dumper (from an Xcoil result) and by embodic (from its `Board`), serves the
JS↔Python cross-check and Agent 4's independent checks IT-06, IT-07 (resistance by own summation), IT-12 (brute-force DRC)
and IT-21 (continuity) (`independent_test_strategy.md` l.149). Draft v1 (`assumption`, to be frozen in Phase 2):

| Key | Content |
|---|---|
| `format`, `format_version` | `"embodic.board-dump"`, `1` |
| `producer` | `{name: "xcoil-v3" \| "embodic", version, engine_sha256, runtime}` (runtime e.g. Node or CPython version) |
| `case_id`, `params`, `params_sha256` | the input parameters as used and the SHA-256 of their canonical JSON |
| `units`, `frame` | `{length: "mm", angle: "rad"}`; engine frame (x right, y up, origin on the rotor axis; no KiCad y-flip/offset) |
| `layers[]` | `{index, name, kicad_name, z, copper_t, role, pair, phase}` (`phase` null when a layer carries all phases) |
| `primitives[]` | one record per copper primitive: `id`; `type` `"line"` or `"arc"`; `layer` (index); `start` `[x, y]`, `end` `[x, y]` (always present, in current direction); line: `x1, y1, x2, y2`; arc: `cx, cy, r, a1, a2` (signed sweep `a2 − a1`, start at angle `a1`, as Xcoil); `width`; `kind` (side, endturn, fillet, taper, lead, stub, ring, leg, bus, link …); `object` (id); `seq` (position along the object path); `net`; `phase` (0/1/2 or null); `coil` (coil/track/strand id or null) |
| `objects[]` | `{id, kind (coil, strand, track, ring, leg, ic, link, vbus, tbus), layer, net, phase, coil, primitive_ids[], touch_vias[]}` |
| `vias[]` | `{id, x, y, drill, pad, layer_from, layer_to, role (centre, transfer, terminal, ring, stitch), net, phase, terminal, label}` |
| `pads[]` | `{id, x, y, shape, w, h, rot, drill, smd, layer, net, label}` |
| `outline` | `{board: [primitives with width 0], cutouts: [[…]], holes: [{x, y, dia}]}` |
| `circuits[]` | per phase: ordered series `elements[]`, each `{members: [{object, layer, direction ±1}], vias: [via ids in the current path]}`; terminals `{plus, minus}` (pad/via ids) |
| `drc` | `{rule: {clearance, epsilon}, values: {traceClearance, padClearance, …}, pass_d006, producer_flag}` (`producer_flag` = Xcoil's `ok`, informational only) |

Rules: numbers are JSON doubles written in shortest round-trip form (both `JSON.stringify` and Python `repr` do this);
non-finite values encoded as above; ids are stable within one dump; every primitive belongs to exactly one object.
For Xcoil dumps, `net` follows `exportKicad` (l.2886–2892), `phase` = `o.phase` or the layer phase (`objColor` logic
l.2793), and `circuits` must be reconstructed by the dumper, because Xcoil keeps its element lists local (`computeSector`
`phases` l.2471, `computeWaveOverlap` l.2210) and does not return them (`verified (code)`); embodic emits `circuits`
natively.

## Revision 2026-10-04 (defect fixes)

- DEF-01 / D-006: §2.3 DRC row, new §3 rows and §3.1 (acceptance rule `value < rule − ε`, ε ≤ 1e-6 mm, no 0.004 mm slack;
  values compared; Xcoil slack band = "indeterminate for pass/fail agreement"); §7.2 rules 2–3 updated.
- DEF-14: `starOfSlots` belt-edge ties added to §2.3 (12/10 has 6 ties, verified run); exact integer phase-assignment rule
  for all Q/2p with a run check against Xcoil.
- Agent 4 request: board dump JSON format §7.5; §7.1 dumper row references it.
- Fixed a stale cross-reference in §2.3 (§6.3 → §7.2).
