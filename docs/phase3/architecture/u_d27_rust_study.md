# U-D27: would a Rust code base be faster than embodic 0.0.4?

Agent 6 (Software Architecture Specialist), 2026-10-20, model `claude-opus-5-5`, branch `unit/U-D27` from `fcd050b`.
A study for the user and Fable, not a decision. Nothing under `src/`, `tests/` or `tools/` changed. Statuses follow
standing order 12. `verified` means measured in this unit with the method and load given here. `inferred` gives its
basis. `assumption` and `not tested` mean what they say. Earlier figures from D-050a, D-074, D-076, D-077, D-080 and
U-M8x are not quoted as this unit's runs.

## The short answer

Yes for the compute kernels, no for the GUI, and the biggest waits are not where a language change helps most.

- The compute stages are CPU-bound on one core (median CPU time within 10 % of median wall time for every operation,
  `verified`). Physics
  spends 54 to 68 % of its time in NumPy, but that time is mostly NumPy's per-call dispatch and allocation on
  7-element arrays, one call after another for every 0.5 mm chord. A compiled loop removes exactly that cost.
- One kernel was ported, `embodic.physics.emf.integrate_path`. Its output is bit-identical to 0.0.4 on all 410 calls
  the five examples make, and the outcome JSON of every example is identical (`verified`, Linux only). The Rust loop is
  27 to 69 times faster than the Python kernel. Because `discretise_path` still runs in Python, physics is 3.3 to
  6.7 times faster and the whole compute 1.17 to 3.08 times faster (`verified`, medians of same-round ratios).
- The GUI operations are 55 to 91 % Qt C++ already (`verified`). A Rust GUI that keeps Qt (cxx-qt) can gain at most
  the Python share, 1.08 to 1.28 times per operation (`inferred`, Amdahl's law on the measured share).
- The two longest waits a user sees are pure interpreter time. The serpentine build of DEF-M6b-01 takes 16.8 s (98 %
  interpreter). SVG and PDF export of a 12-coil spiral take 1.7 to 2.2 s (85 to 89 % our Python, in the coil-eye
  search of `geometry/marks.py`). A compiled port would cut them about 18 to 29 times and 6 to 8 times (`inferred`).
- 0.0.4 is not bit-identical across CPUs today. On this machine the analysis results of all five examples change in
  the last bits when NumPy's AVX-512 kernels are switched off (`verified`). Every option inherits that.

The recommendation is option B (Rust kernels behind the Python API) for three kernels, measured one at a time, and option C's
separate compute process for DEF-W-12. Option B alone does not fix DEF-W-12 (`verified` on a Linux proxy). Do not
start option A.

## How the numbers were taken

Machine and software (`verified`): 2 vCPU "Intel(R) Xeon(R) Processor @ 2.80GHz" with AVX-512, Ubuntu 24.04.5, Python
3.11.17, NumPy 2.4.6 (dispatch targets `X86_V3` and `X86_V4` active), PySide6 6.11.2, `QT_QPA_PLATFORM=offscreen`,
`PYTHONPATH=/home/claude/wt/U-D27/src` (the import resolved there, `embodic.__version__` 0.0.4).

Timing. `checks/u_d27/ops.py time <group>` sets up every operation of a group, runs each once untimed, then runs five
rounds of all operations in turn, so the other units' load falls on every operation alike. Each run records wall time
(`time.perf_counter`) and the process CPU time. Each round records the CPU time the rest of the machine used per second
of the round, from `/proc/stat` minus this process. Tables give the median of 5 and the range.

Two other units ran tests beside this one. Their load during each group, in cores per round (or the 1-minute load
average where a round is shorter than the 10 ms jiffy):

| Group | Other processes, cores per round | Load average |
|---|---|---|
| compute | 0.83, 0.03, 0.06, 0.06, 0.10 | 1.38 to 1.60 |
| export | 0.71, 0.05, 0.07, 0.07, 0.07 | 1.00 to 1.19 |
| project | rounds too short | 1.15 |
| hostile (DEF-M6b-01) | 1.03, 1.02, 1.02, 1.00, 0.44 | 1.73 to 1.94 |
| gui | 0.02 to 0.04 | 0.71 to 0.77 |
| cold start | 1.02 to 1.04 | 1.00 to 1.15 |

Every operation here is single-threaded apart from the GUI worker, so one busy neighbour still leaves a core free. Wall
time equals CPU time in the compute, export and render groups, so no run waited for a core. The run-to-run range is
still 20 to 40 % in places. Ratios below therefore come from runs of both sides in the same round.

Profiler. The split uses py-spy 0.4.2 (`py-spy record --native --idle -r 250 -f raw`), MIT licence (read from the
wheel's `licenses/LICENSE`), installed from PyPI into a scratch virtual environment, not the project's. cProfile was
not used for the split. It does not see NumPy ufunc calls or array operators as calls, so their C time lands in the
calling Python function's own time and would read as "our Python". py-spy samples the native stack from outside the
process, so each sample has a leaf frame in a known library. `ops.py split` assigns each sample under the timed call
to one owner:

| Owner | Leaf of the sample |
|---|---|
| our Python, other Python | a Python frame of `embodic/`, or of the standard library, NumPy's Python code or a dataclass `__init__` |
| NumPy | `numpy/_core/_multiarray_umath...so` |
| other C | a CPython C module (`json`, `hashlib`), or libm or zlib called from Python code |
| Qt and PySide6 | `libQt6*`, `libshiboken6`, `libpyside6`, the PySide6 modules, and the font and image libraries Qt loads |
| I/O | libc `read`, `write`, `open`, `stat` and the like |
| wait | libc `poll`, `futex` and condition waits: the event loop idle, or a thread waiting for the GIL |

libc allocator and libm frames belong to their caller. Profiled runs were never timed; py-spy stretches a run while it
unwinds native stacks. `checks/u_d27/splits.txt` holds every split with its sample count and top frames.

## 1. Where the time goes in 0.0.4

### Compute of the five packaged examples

Medians of 5, wall time in ms (range). Median CPU time was within 10 % of median wall time in every cell (`verified`,
`checks/u_d27/time_compute.json`). "Results" is the CLI's `json.dumps(outcome_to_json(outcome), indent=2, ...)`.

| Example | generate | DRC | physics | results | compute end to end |
|---|---|---|---|---|---|
| serpentine_16p_example | 368 (257 to 418) | 310 (242 to 341) | 876 (638 to 909) | 89 (52 to 98) | 1325 (1175 to 1502) |
| spiral_12c10p_d08 | 20 (12 to 22) | 242 (153 to 303) | 491 (302 to 631) | 61 (35 to 77) | 692 (492 to 883) |
| spiral_12c14p | 41 (25 to 47) | 419 (344 to 535) | 1232 (926 to 1402) | 48 (39 to 87) | 1849 (1490 to 2097) |
| spiral_12c16p_default | 30 (23 to 36) | 447 (376 to 491) | 1091 (1020 to 1255) | 47 (39 to 70) | 1615 (1470 to 1948) |
| wave_16p_example | 48 (46 to 58) | 717 (621 to 987) | 339 (288 to 381) | 58 (49 to 86) | 1173 (916 to 1319) |

Split of samples (`verified`):

| Operation | NumPy | our Python | other Python | other C | Hot frame |
|---|---|---|---|---|---|
| physics, spiral_12c14p | 68 % | 24 % | 6 % | 1 % | `emf.integrate_path` and `FieldTable.at` |
| physics, serpentine | 61 % | 29 % | 8 % | 2 % | the same |
| physics, wave | 54 % | 32 % | 12 % | 1 % | the same, plus `AnalysisResult.to_json` |
| DRC, wave | 85 % | 8 % | 7 % | 0 % | `drc/kernels.py`, `engine.candidate_pairs` |
| DRC, default spiral | 88 % | 7 % | 5 % | 0 % | `engine.candidate_pairs` 44 % |
| generate, serpentine | 0 % | 63 % | 31 % | 6 % | `serpentine/corners.make_corner`, dataclass `__init__` |
| results, D08 | 0 % | 30 % | 67 % | 3 % | the pure-Python JSON encoder (`indent` turns off the C encoder) |

Why physics is NumPy-bound but still a good Rust target. `integrate_path` loops over every 0.5 mm chord of a path
(160,971 chords over the five examples) and makes about fifteen NumPy calls per chord on arrays of 7 harmonics. The
innermost NumPy symbols on spiral_12c14p are `ufunc_generic_fastcall` 14 %, `PyArray_NewFromDescr_int` 5 %, the
allocator, and float-status checks; glibc `cexp` is 1.4 %. The time is call overhead, not arithmetic. DRC is different.
Its NumPy time goes to array kernels and copies on long arrays (`_contig_to_contig`, fancy indexing, `DOUBLE_add`), so
a port gains little there.

### The serpentine build of DEF-M6b-01

The input is the `@example` of `test_d030_hostile_clearance_and_pads_are_built_within_the_deadline`: r_inner 60 mm,
span 40 mm, rule-minimum width, 30 turns, clearance and pads 5e-324 mm (`ops.py hostile_design`).

| Build | Wall, median of 5 (range) | CPU |
|---|---|---|
| near-zero sizes | 16 765 ms (15 703 to 18 323) | 16 347 ms |
| the example's own sizes | 3 291 ms (3 032 to 4 463) | 3 216 ms |

`verified`, one other core busy (table above). The split is 70 % our Python and 28 % dataclass `__init__` (the frozen
`Corner` and `SideLine` objects), 2 % libm. `make_corner` holds 59 % of samples, `side_line` 18 %, `fit.min_straight`
11 %. `fit.max_fillet` bisects the fillet radius in 60 steps, and each step rebuilds every turn's corners in
`min_straight`.

### Export and project files

Medians of 5 in ms (`verified`, `checks/u_d27/time_export.json`, `time_project.json`). Wave exports pass
`allow_drc_errors=True` because its 186 DRC violations make `write_svg` refuse otherwise.

| Example | SVG | DXF | PDF | load | save |
|---|---|---|---|---|---|
| serpentine | 10.6 | 17.2 | 150 | 3.3 | 7.8 |
| D08 | 475 | 4.7 | 598 | 3.2 | 6.5 |
| spiral_12c14p | 1708 (1452 to 1877) | 9.7 | 1998 (1821 to 2164) | 3.0 | 6.7 |
| default spiral | 1858 (1674 to 2394) | 12.2 | 2177 (1964 to 2569) | 3.3 | 7.5 |
| wave | 19.9 | 26.0 | 181 | 2.8 | 7.7 |

The spiral SVG is 89 % our Python and 11 % other C, mostly libm `atan2` called from `math`. The spiral PDF is 85 %
and 15 %. Both are the coil-eye search
`marks._eye`: a 23 x 23 grid per coil and layer, where `_encloses` takes `atan2` of every sample point of the coil
(69 % of samples) in every cell. The serpentine PDF is 78 % zlib `deflate` (other C). DXF of the wave example is 82 %
our Python. Load and save take under 8 ms and do not matter to a user.

Three identical-output Python fixes of `_eye` were tried (`checks/u_d27/eye_hoist.py`). Hoisting its four
loop-invariant `min` and `max` calls, stopping `_encloses` at the eighth sector, and a NumPy `_encloses` per cell all
gave the same marks as 0.0.4, and none was measurably faster. Medians moved both ways inside a 30 % run-to-run range,
and the NumPy variant was slower because it builds an array per cell (`verified`, load average 1.65 to 2.02).

### The offscreen GUI

Medians of 5 (`verified`, `checks/u_d27/time_gui.json`, `time_cold.json`). Open and result use the real shell
(`create_shell`) with the real compute in its worker thread. CPU is the GUI thread's own time (`time.thread_time`)
inside `DesignSession.load_example` and `OutcomeViewModel.on_finished`. Redraw, zoom and pan use a 1280 x 800
`GeometryView` that shows the serpentine example, as `tests/ui/qt_shell/layer_cue_time.py` does. Redraw switches the
render mode and grabs the viewport. Zoom is one step of 1.25 or 0.8 right after a redraw. Pan is 100 px at 4x zoom.

| Operation | Wall | GUI-thread CPU | Qt and PySide6 | our Python | wait |
|---|---|---|---|---|---|
| cold start to a shown, grabbed window | 1835 ms (1634 to 1871) | 1779 ms (process) | about 80 % (indicative) | 4 % | 1 % |
| D08 open, `load_example` | 89 ms (59 to 115) | 39 ms | 55 % | 6 % | 35 % |
| D08 result arrival, `on_finished` | 48 ms (46 to 67) | 48 ms | 91 % | 6 % | 1 % |
| default spiral open | 72 ms (69 to 95) | 34 ms | not split | | |
| default spiral result arrival | 84 ms (77 to 96) | 83 ms | not split | | |
| serpentine redraw | 254 ms (230 to 288) | 254 ms | 90 % | 9 % | 0 % |
| serpentine zoom step after a redraw | 150 ms (130 to 178) | 150 ms | 78 % | 21 % | 0 % |
| serpentine pan step at 4x | 33 ms (28 to 48) | 33 ms | 78 % | 20 % | 0 % |

The cold-start split is indicative only, because py-spy reported 333 sampling errors beside its 598 samples. Of those,
`libshiboken6` and `libpyside6` (the binding layer) hold 29 %, and `coil_panel.py` widget construction is the largest
Python frame. This zoom step is not U-M8x's zoom step. That one repeats zooms on a warm view; this one follows a scene
rebuild.

The D08 open shows the mechanism of DEF-W-12 on Linux too. The GUI thread spends 35 % of the open waiting, and its
wall time is twice its CPU time, because the worker thread starts computing at once and holds the GIL. The worker sees
the same contention from its side. It waits in 44 % of its `api.compute` samples and 58 % of its `ready_state`
samples. `ready_state` builds the result in the worker (`ui/viewmodels/outcome.py` l.173), and 87 % of its samples
sit in the same `marks._eye` search the exports run (l.250 calls `coil_marks`).

### The top five time sinks

1. DEF-M6b-01 serpentine build, 16.8 s. Interpreter 98 % (our code 70 %, dataclass construction 28 %).
2. SVG and PDF export of a 12-coil spiral, 1.7 to 2.2 s each. Our Python 85 to 89 %, libm 11 to 15 %. The same search
   runs a third time in the GUI worker for every spiral result.
3. Physics, 0.34 to 1.23 s. NumPy 54 to 68 % (mostly per-call overhead), our Python 24 to 32 %, other Python 6 to 12 %.
4. Cold start, 1.8 s. Qt and PySide6 about 80 % (indicative), the binding layer 29 % of that.
5. DRC, 0.24 to 0.72 s. NumPy 85 to 88 %, Python 12 to 15 %.

The serpentine redraw (254 ms, Qt 90 %) is next.

## 2. The Rust port of `integrate_path`

### What was built

`checks/u_d27/rust/lib.rs` is a `cdylib` with one C-ABI function, `u_d27_integrate_path`, and no crates. It mirrors the
0.0.4 arithmetic operation for operation:

- `math.hypot` is CPython 3.11's own `vector_norm`, not libm `hypot`. The port copies it from `Modules/mathmodule.c`
  of v3.11.9, whose function text is identical in v3.11.14 (fetched from raw.githubusercontent.com, compared by
  `diff`).
- Python's `min` and `max` keep their tie order. `math.atan2` keeps CPython's zero cases.
- NumPy's products run left to right as the expression parses. `w**3` is C `pow(w, 3.0)`, not `powi`.
- The complex exponential is glibc `cexp`, which NumPy 2.4.6 calls here (`nc_exp` then `cexpf64` in the samples), or
  Rust's `sin` and `cos` (`use_cexp` 0).

The library imports `atan2@GLIBC_2.2.5`, `exp@GLIBC_2.29` and `pow@GLIBC_2.29`, the same symbols CPython binds, and
`cexp@GLIBC_2.2.5` as NumPy does (`nm -D`, `verified`). Python calls it through `ctypes` (standard library). The
wrapper in `checks/u_d27/emf_bench.py` keeps the signature of `integrate_path`. It runs `discretise_path` in Python,
packs the chords into an `(n, 6)` array, and calls the loop.

Toolchain (`verified`): Ubuntu `rustc-1.91` and `cargo-1.91` 1.91.1+dfsg~24.04-0ubuntu0.24.04.3 from noble-updates,
licence MIT OR Apache-2.0 (`/usr/share/doc/rustc-1.91/copyright`). Release profile, `opt-level = 3`,
`codegen-units = 1`, no `target-cpu`, so the code is portable x86-64. The container already had rustup 1.28.2 with
rustc 1.97.0 in `/root/.cargo`, whose manifest names static.rust-lang.org, but the proxy refuses static.rust-lang.org
(HTTP 403), so its checksum could not be checked and it was not used. crates.io was reachable but not needed.

### Identity

`emf_bench.py` records every `integrate_path` call that `analyse` makes on the five examples (410 paths, 160,971
chords) and compares Python against Rust bit for bit on every output (flux linkage, both eddy sums, both edge sums).
`gil_probe.py` then compares the full outcome JSON of `compute_project` with each kernel.

| Check | Result |
|---|---|
| calls with any differing bit, glibc `cexp` | 0 of 410 (`verified`) |
| calls with any differing bit, Rust `sin` and `cos` | 0 of 410 (`verified`) |
| `analyse(...).to_json()` identical, five examples | yes (`verified`) |
| `outcome_to_json` identical, five examples | yes (`verified`) |
| identity on Windows | `not tested` |

No tolerance was used or needed (order 11).

### Speed

Same-round ratios, medians of 7 rounds (kernel and physics) or 5 rounds (compute), with the range. Load average 0.74
to 1.02 during `emf_bench.py` and 0.46 to 0.88 during `gil_probe.py`, this process included (`verified`,
`checks/u_d27/emf_bench.json`, `gil_probe.json`).

| Example | Rust loop alone | Rust wrapper | `analyse` | `compute_project` |
|---|---|---|---|---|
| serpentine | 64 (43 to 82) | 3.8 (2.8 to 4.7) | 3.3 (2.3 to 4.8) | 1.67 (1.08 to 2.01) |
| D08 | 43 (35 to 74) | 5.4 (3.8 to 8.9) | 4.5 (2.7 to 6.3) | 2.21 (2.02 to 3.04) |
| spiral_12c14p | 69 (40 to 77) | 8.1 (5.2 to 9.9) | 6.0 (4.4 to 7.8) | 2.40 (2.11 to 2.59) |
| default spiral | 54 (50 to 78) | 6.8 (4.7 to 10.1) | 6.7 (6.0 to 7.8) | 3.08 (2.54 to 3.12) |
| wave | 27 (23 to 38) | 4.0 (3.3 to 5.7) | 3.4 (2.4 to 4.0) | 1.17 (0.93 to 1.24) |

In absolute terms, physics of the default spiral fell from 1280 ms to 191 ms, and its compute from 1533 ms to 519 ms.
The checks of benchmark-checklist were applied as follows:

- The limiter of the wrapper is the Python half it keeps. `discretise_path` and packing cost 62 to 174 ms per example,
  against a 9 to 26 ms Rust loop.
- The limiter of `compute_project` is the stages not ported. The wave example is 61 % DRC, so its gain is 1.17.
- The Rust loop takes about 390 ns per chord on spiral_12c14p (16.7 ms for 43,132 chords, each with two `hypot`, two
  `atan2` and seven `cexp`) against about 26 us in Python. Both are plausible and break no limit.
- Every timed call returned a result that was kept. The first run of the bench patched the wrong name and timed Python
  twice; it recorded no calls, it was discarded, and `record` now asserts that calls were seen.
- Both sides ran as shipped. NumPy used its AVX-512 kernels, the Rust code no CPU-specific flags.

### Effect on the GIL (a Linux proxy for DEF-W-12)

`gil_probe.py` runs `analyse` in a worker thread while the main thread sleeps 1 ms in a loop, as an event loop waits
for its next event. Each wake needs the GIL, so the gap between wakes is the main thread's wait. CPython asks the
holder to release every 5 ms (`sys.getswitchinterval()`). `ctypes` releases the GIL while the Rust loop runs.

| Example | Python kernel: median gap, gaps over 4 ms, max | Rust kernel: median gap, gaps over 4 ms, max |
|---|---|---|
| serpentine | 6.35 ms, 99.8 %, 25.5 ms | 6.34 ms, 74.8 %, 24.6 ms |
| D08 | 6.34 ms, 98.0 %, 13.2 ms | 1.82 ms, 11.8 %, 12.4 ms |
| spiral_12c14p | 6.37 ms, 99.4 %, 25.8 ms | 4.68 ms, 75.0 %, 16.2 ms |
| default spiral | 6.33 ms, 99.3 %, 70.5 ms | 4.80 ms, 79.6 %, 16.4 ms |
| wave | 6.33 ms, 97.8 %, 13.0 ms | 1.31 ms, 13.2 %, 20.6 ms |

`verified` on Linux, 5 runs per side. The Rust kernel frees the GIL for most of the physics time only where the
kernel is most of it. The largest gaps stay at 12 to 25 ms, because `discretise_path` and the rest of `analyse` still
hold the GIL in 5 ms slices. Windows schedules threads differently (D-076c), so these gaps say nothing about the
laptop's 100 ms bound (`not tested` there).

## 3. Three options

### Speed per operation

Factors against 0.0.4. `verified` cells come from section 2. `inferred` cells use Amdahl's law on the measured share
that a compiled port replaces, with the measured 27 to 69 times of the Rust loop as the speed of that share. That loop
is scalar floating-point code like the serpentine and marks loops, but those loops were not ported.

| Operation (0.0.4 median) | A: full rewrite | B: Rust kernels behind Python | C: no Rust |
|---|---|---|---|
| physics (339 to 1232 ms) | at least B's figure; up to the loop's 27 to 69 on the ported part (`inferred`) | 3.3 to 6.7 with `integrate_path` alone (`verified`); more with `discretise_path` ported (`inferred`) | vectorise the chord loop: large but changes bits (`inferred`, see identity) |
| compute end to end (692 to 1849 ms) | more than B (`inferred`) | 1.17 to 3.08 with one kernel (`verified`) | depends on the physics change (`inferred`) |
| DRC (242 to 717 ms) | at least 1.14 to 1.17; more only if a fused loop beats NumPy's array kernels, not measured (`inferred`) | the same, if DRC is ported | about 1 (`inferred`) |
| DEF-M6b-01 build (16.8 s) | 18 to 29, to about 0.6 to 0.9 s (`inferred`) | the same, if `serpentine/fit.py` and `corners.py` are ported | at most 1.39 from removing dataclass construction, to about 12 s, still over 10 s (`inferred`); the 60-step bisection needs an algorithm change |
| generate serpentine (368 ms) | 10.6 to 13.6 (`inferred`) | the same, if ported | small (`inferred`) |
| spiral SVG and PDF (1.7 to 2.2 s) | 5.6 to 8.1 (`inferred`) | the same, if `marks._eye` is ported | three identical-output fixes gave no measurable gain (`verified`); build the marks once per layout and share them between GUI, SVG and PDF (`inferred`) |
| results JSON (47 to 89 ms) | 14.5 to 20.8 (`inferred`) | no change | no change |
| project load and save (3 to 8 ms) | not worth it | not worth it | not worth it |
| GUI open, result, redraw, zoom, pan | with cxx-qt at most 1.08 to 1.28 (`inferred`); with egui, iced or Slint unknown, another renderer (`not tested`) | no change | no change |
| cold start (1.8 s) | with cxx-qt at most 1.7, the Python and binding share (`inferred`, from an indicative split) | slightly slower by loading one more library (`assumption`) | a second process to start (`not tested`) |

### DEF-W-12 and DEF-M6b-01

- A removes the GIL, so the worker and the GUI no longer share an interpreter lock (`inferred`). Whether Windows then
  schedules the GUI thread on time is `not tested`.
- B frees the GIL only inside each Rust call. One kernel lowered the median wait but not the largest gaps (`verified`
  above). B would need every hot loop of the worker ported, `ready_state`'s eye search included, before the worker
  stops holding the GIL for long (`inferred`). B fixes DEF-M6b-01 if the serpentine fit is ported (`inferred` 18 to 29
  times).
- C's separate compute process removes the shared GIL by construction (`inferred`). The measured contention is the
  35 % wait in the open, and the 44 % and 58 % waits in the worker. Its cost, serialising each `ComputeOutcome` to the
  GUI process, is `not tested`. C does not fix DEF-M6b-01 without a change to the bisection, which may change output
  (a spec question, not settled here).

### Cross-platform identity

PK-04 compares a Windows outcome with the Linux reference at 1e-9 relative, per value, or per array peak for arrays
(`docs/phase3/verification/checks/pk04_compare.py` l.6-8). Measured here:

- 0.0.4 already changes bits with the CPU. `npy_dispatch.py` computed the five examples three times, with NumPy's
  dispatch at `X86_V4` (AVX-512), at `X86_V3` (`NPY_DISABLE_CPU_FEATURES="X86_V4"`) and at the `X86_V2` baseline. Design
  hashes and DRC results were identical in all three. The analysis JSON differed between V4 and V3 for every example,
  and V3 equalled V2. The largest differences were 7.7e-13 relative (serpentine EMF phasor angle) and 3.1e-16 of the
  peak for the default spiral's EMF waveform (`verified`, `npy_dispatch_diff.py`). Measured per value, that waveform
  reaches 1.4e-3 relative on a sample of -2.4e-15 V next to a zero crossing, which is why PK-04 compares arrays
  against their peak. Both pass the PK-04 rule as
  `pk04_compare.py` states it; the script itself was not run. Which NumPy function changes under V4 was not traced.
- `np.arctan2` differs from `math.atan2` in the last bit for 8 % of values here (4,183 of 52,371 on D08, 15,363 of
  199,962 on spiral_12c14p, `verified`). NumPy vectorising (option C) therefore changes results relative to 0.0.4,
  unless each replaced function is checked bit for bit.
- The Rust port matches 0.0.4 bit for bit on Linux because it calls the same glibc functions in the same order.
  Windows Rust (the `x86_64-pc-windows-msvc` target) calls the Microsoft C runtime's maths functions, so last-bit
  differences against Linux are likely (`inferred`, `not tested`). The `libm` crate (0.2.16, MIT, crates.io) is a
  pure-Rust maths library. With it the Rust code gives the same bits on both systems (`inferred`), at the price of new
  bits against today's glibc results, and so one regeneration of the golden values.
- Golden tests compare at `rel=0.0` or `abs=0.0` in 22 places and at `rel=1e-12` in 9 (a count of the literals in
  `tests/golden`, `verified`). Any option that changes bits needs a review of which of those compare embodic's own
  output, against order 11, before it lands.

### Cost and risk

**A, a full rewrite in Rust with the GUI.** Toolkit candidates and licences, read from crates.io (`verified`):
cxx-qt 0.10.0 MIT OR Apache-2.0 (keeps Qt, so Qt's licence terms stay), Slint 1.18.1 GPL-3.0-only OR Slint
Royalty-free 2.0 OR Slint Software 3.0, egui and eframe 0.37.0 MIT OR Apache-2.0, iced 0.14.0 MIT. What is lost or
redone (`verified` counts at `fcd050b`):

- 30,437 lines of source (19,724 outside `ui/`, 10,713 in `ui/`).
- 4,368 collected tests in 58,739 lines (the brief says 4,353; `pytest --collect-only` here gives 4,368). Python tests
  cannot drive a Rust GUI, and they reach Rust core code only through bindings, which is option B.
- 275 golden data files (26 MB). They stay as data, but every value becomes a claim to verify again.
- The evidence and trust record of Phases 1 to 3: Windows gates, PK-04, Xcoil parity such as the bit-for-bit claims in
  `drc/kernels.py`.

The measured gain for the GUI is at most 1.28 times with Qt kept. Risk high. No person-time estimate is given, because
none was measured.

**B, Rust kernels behind the Python API.** The Python API and tests stay; the Python kernel stays as the oracle until
each port matches it. New costs:

- A Rust build in CI and a binary wheel per platform. Today hatchling builds one pure-Python wheel, and PyInstaller
  makes the Windows bundle (`packaging/pyinstaller/embodic.spec`), which must then carry the library.
- A Windows build, either the MSVC target with Visual Studio Build Tools, whose licence was not checked
  (`unresolved`), or the GNU target with MinGW-w64 (licence not checked here).
- A binding. Bare `ctypes`, as here, needs no crates. PyO3 0.30.1 (MIT OR Apache-2.0), rust-numpy 0.30.0
  (BSD-2-Clause) and maturin 1.15.0 (MIT OR Apache-2.0) give typed bindings and wheel builds (`verified` licences).

Risk medium. Each kernel is one unit with a bit-for-bit gate like `emf_bench.py`.

**C, no Rust.** A compute process separate from the GUI, plus NumPy vectorising. New costs are the inter-process
transfer of each outcome and process start-up (`not tested`), and a bit-identity review of every vectorised function
(np.arctan2 already fails it, `verified`). Risk medium. The measured hot spots of export and DEF-M6b-01 are
interpreter-bound loops that NumPy does not fit well (`inferred`; three tries on `_eye`, `verified`).

## 4. Recommendation

Measure and prototype next, in this order:

1. Port `discretise_path` behind the same gate (`emf_bench.py`). It is now the limiter of the physics wrapper, 62 to
   174 ms per example (`verified`). The target is the loop's 27 to 69 times on all of `integrate_path`.
2. Port `marks._eye` and `serpentine/fit.py` with `corners.py`, one unit each. Gate each on identical marks and an
   identical `stack_hash`. Measure the spiral export, the GUI worker's `ready_state`, and the DEF-M6b-01 build against
   its 10 s bound. These are the two longest waits (`verified`), and the gain is `inferred` until measured.
3. On the Windows laptop, build the same library for Windows and run `emf_bench.py` there. That measures the bit
   difference against NumPy on Windows, so the `libm` question is settled by data.
4. Prototype C's separate compute process. Measure the outcome transfer cost, then UI-05 and N02-10 on the laptop.
   B alone did not remove the large GIL gaps (`verified`), so DEF-W-12 needs C or a fully ported worker.
5. Do not start A. The GUI is 55 to 91 % Qt C++ (`verified`), and A would reset the trust record for at most 1.28
   times there (`inferred`).

## Reproduce

All scripts live in `docs/phase3/architecture/checks/u_d27/` and run with the project's interpreter, one process at a
time, from a directory outside the tree. Build outputs go to a scratch directory, not the repository.

	export PYTHONPATH=/home/claude/wt/U-D27/src QT_QPA_PLATFORM=offscreen
	PY=/home/claude/embodic/.venv/bin/python; C=docs/phase3/architecture/checks/u_d27
	$PY $C/ops.py time compute --rounds 5        # also: export project hostile gui cold
	py-spy record --native --idle -r 250 -f raw -o raw.txt -- $PY $C/ops.py sample compute physics/c14 --seconds 4
	$PY $C/ops.py split raw.txt                  # --frame REGEX for the GUI hooks
	CARGO_TARGET_DIR=/tmp/t RUSTC=rustc-1.91 cargo-1.91 build --release --offline --manifest-path $C/rust/Cargo.toml
	$PY $C/emf_bench.py /tmp/t/release/libu_d27_emf.so --rounds 7
	PYTHONPATH=$PYTHONPATH:$C $PY $C/gil_probe.py /tmp/t/release/libu_d27_emf.so --rounds 5
	$PY $C/eye_hoist.py --rounds 5
	$PY $C/npy_dispatch.py v4.json; NPY_DISABLE_CPU_FEATURES=X86_V4 $PY $C/npy_dispatch.py v3.json
	python3 $C/npy_dispatch_diff.py v4.json v3.json

## References

- Brief U-D27; standing orders 2, 3, 5, 11, 12 and 13; decision log D-050 (b), D-075, D-076 (c, d).
- `tests/unit/generators/serpentine/test_serpentine_inputs.py` l.168-186 (DEF-M6b-01 input and bound).
- `tests/ui/qt_shell/layer_cue_time.py` and `stall_profile.py` (the GUI operations this unit's harness follows).
- `src/embodic/physics/emf.py` l.91-100 and l.149-202; `src/embodic/geometry/marks.py` l.47-82;
  `src/embodic/generators/serpentine/fit.py` l.87-143; `src/embodic/ui/viewmodels/outcome.py` l.250.
- CPython `Modules/mathmodule.c`, `vector_norm`, tags v3.11.9 and v3.11.14 (raw.githubusercontent.com/python/cpython).
- py-spy 0.4.2, MIT, github.com/benfred/py-spy. crates.io API records of pyo3, numpy, maturin, cxx-qt, slint, egui,
  eframe, iced and libm, read 2026-10-20.
- `docs/phase3/verification/checks/pk04_compare.py` l.1-25 (the PK-04 rule).
