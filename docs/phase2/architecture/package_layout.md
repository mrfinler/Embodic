Prepared by: Agent 6 - Software Architecture Specialist - model: claude-opus-5-5

# embodic Phase 2 package layout, import rules and dependencies (build contract v1, 2026-10-04)

This file fixes where code, tests and resources live, which module may import which, and which third-party packages are
allowed. It replaces `docs/phase1/architecture/architecture_draft.md` §4 and §15.1 (KiCad parts removed, generators and
Qt-free view-models added). Unit ownership of each path is in `work_breakdown.md`.

Revision 2026-10-04 (U-D1, corrections from the W0 pilot):

- §1. `errors.py` becomes the package `errors/` with one message-catalogue module per owning unit. The golden dumper
  gains one function module per area under `tools/golden/functions/`.
- §3. Contract C2 is restated in the implemented form (`-> PySide6`, `-> shiboken6`), DEF-M1a-01. MT-06 names the
  new quantiser.
- §4. Ruff excludes `docs/` (U-M1a deviation, ratified).
- §5. The numpy pin is 2.4.6 (DEF-M1a-03). hatchling joins the `dev` extra. The extras `desktop` and `desktop-dev` are
  ratified (U-M1a deviation).

Revision 2026-10-05 (U-D2, corrections from the W1 and W2 reports):

- §1. `geometry/` and `drc/` list the merged modules. The Xcoil distance and grid ports (`geometry/distance.py`,
  `geometry/grid.py`) live in `geometry`, not in `drc` (U-M1b report). `model/schema.py` is added (U-M2a report).
- §1. Test folders follow a naming rule that keeps every top-level test package name unique and untaken (U-M1y, MT-08).
  The planned golden and Qt test folders are renamed to fit it, and `tests/unit/io` became `tests/unit/embodic_io`.

Revision 2026-10-09 (U-D9, D-038e; `src/embodic/results/labels.py` on main 3acb044, `verified` by reading). §1 lists
`results/labels.py`.

Revision 2026-10-09 (U-D10, claude-sonnet-5-5, D-039 a and c, D-040; the tree of main fd190c1 was read for every item).

- §1. The tree lists `geometry/marks.py` and `geometry/labels.py` (the drawing data the canvas and the exporters share),
  `ui/fonts.py` and `resources/fonts/`. `results/labels.py` now also holds `QUANTITY_SYMBOLS` and `quantity_title`
  (interfaces.md §3).
- §5. The table gains the `fonttools` row (dev, test side only). A new subsection 5.1 lists the licence files that the
  wheel and the PyInstaller folder must carry at M5, as Agent 5 recorded them in
  `docs/phase2/evidence/dependency_licences.md`.

Revision 2026-10-09 (U-D11, claude-sonnet-5-5, D-039 a, D-040 and U-S4e ruling e2; the tree of main 9776555 was read
for every item).

- §1. `resources/fonts/` holds the two static Inter faces, `Inter/Inter-Regular.ttf` and `Inter/Inter-SemiBold.ttf`, and
  no variable file (U-M4e-1 deleted it). The tree also lists `ui/app.py`'s `qt_application`, the
  one place that starts Qt with the fonts registered, `tests/ui/conftest.py` and `tools/design/`.
- §4. The pytest row names the hang guard `timeout = 900`.
- §5. The table gains the `pytest-timeout` row, which U-D10 left open (D-034). §5.1 is unchanged: the wheel and the
  folder still carry the same licence files, because both Inter files are under the one `Inter/LICENSE.txt`.

Revision 2026-10-11 (U-D12, claude-sonnet-5-5, U-M4e-2; the tree of main 4fda98d was read for every item).

- §1. The tree lists `.claude/skills/verify/`, the project verification skill. It is developer tooling in the repository.
  The wheel does not carry it: `pyproject.toml` builds the wheel from `src/embodic` and force-includes `resources` only
  (`[tool.hatch.build.targets.wheel]`, `verified` by reading), and `.claude/` is in neither. Whether a source
  distribution carries it is `unresolved`, because `pyproject.toml` has no sdist section. The tree also lists the files of
  `tests/ui/qt_e2e/` and `tests/ui/qt_shell/capture_acceptance.py`, the lever that the skill runs.

Revision 2026-10-12 (U-D13, claude-opus-5-5, D-034, D-042a; the tree and `pyproject.toml` of main 7b9b4c9 were read for
every item, and a wheel and an sdist were built from a scratch copy of it).

- §1. The tree adds `embodic/selftest/`, the Tests dialog modules, `tools/record_passed_tests.py`,
  `packaging/pyinstaller/`, the git-ignored evidence file `resources/evidence/passed_tests.v1.json`,
  `tests/packaging/evidence/` and `tests/performance/baseline.json`, and reserves the place of embodic's `LICENSE`.
- §3. Contract C1 gains the layer `(embodic.selftest)` between the adapters and `embodic.api`.
- §5. The lock tool is uv (row added). The new §5.2 fixes the wheel, sdist, lock files, README and install guide
  sections, the `THIRD_PARTY_LICENSES.md` structure, the PyInstaller one-folder layout and the PF baseline file.

Revision 2026-10-13 (U-D14, claude-sonnet-5-5, D-045c, U-S5c; `pyproject.toml`, `src/embodic/ui` and the tree of main 6243163
were read for every item).

- §1. `ui/workers.py` is the place of `SelfTestWorker` (interfaces.md §14; the first version of this note called it a
  target, and the continuation below closes that).
- §5.1. The bundle does not rely on LGPL route 1 (a): it complies with route 0 (U-S5c, `dependency_licences.md` R8). The
  table gains the rows for embodic's source and the spec file with the build script (Agent 5's open point 6). The
  PyInstaller result rows first read "U-M5c records"; the continuation below fills them.
- §5.2. The folder tree names the spec file and the build script inside the sdist.

Revision 2026-10-13, continuation (U-D14, claude-sonnet-5-5; D-046g, D-046h; main 76f054b).

- §1. `SelfTestWorker` is in `src/embodic/ui/workers.py` l.87. `create_shell` builds it and passes it to `MainWindow` as
  `selftests=` (`ui/app.py` l.122 and l.133, `verified` by reading). The "target" marking is gone (interfaces.md §14).
- §5.1. The PyInstaller rows carry the result of U-M5c's Linux build, read from its build log and its folder (read-only,
  `verified`). The wheel rows carry a wheel that this unit built into a scratch folder with
  `tests.packaging.support.build_wheel` (265 members). The old "absent" for `THIRD_PARTY_LICENSES.md` in the wheel was
  stale and is corrected. The sdist moves from the top of the folder to a separate `source/` row (Fable's ruling of
  2026-10-13), because U-M5c ships `source/embodic-0.0.1.tar.gz`, the sdist, inside the folder. The sdist carries the
  spec, the build script and the lock files. Three open items follow the table.
- §5.2. The wheel table is read again on main 76f054b. The sdist paragraph and the folder tree describe what U-M5c
  built. `resource_root()` in a frozen build is no longer `unresolved`, with the limit stated there.

Revision 2026-10-19 (U-D24, claude-sonnet-5-5, D-068; main 4fa3198, `tools/ci.py`, `tests/bundle/bundle_gate.py` and
`tests/bundle/test_bundle_smoke.py` read for every item).

- §5.1 and §5.2. Since U-M8q the release profile builds the PyInstaller folder with `tools/build_bundle.py` and runs
  `tests/bundle` with `EMBODIC_REQUIRE_BUNDLE=1`, so a missing folder fails the run instead of skipping. The sentence in
  §5.2 that the 6 tests skip now names the profiles for which that holds. Open item 3 at the end of §5.1 keeps only the
  Windows gap. This unit ran no test suite and did not build the folder.

## 1. Repository tree

```
embodic/
  pyproject.toml                 PEP 621 metadata, extras, tool config (ruff, mypy, pytest, import-linter)
  README.md                      English; install, run, test, package (U-M5b)
  THIRD_PARTY_LICENSES.md        licence list, one section per runtime dependency and bundled asset (U-M5b, §5.2)
  LICENSE                        embodic's own licence: not written. Pending the user's choice (§5.2)
  CHANGELOG.md
  .gitignore                     adds resources/evidence/passed_tests.v1.json (U-M5b): a build product, never committed
  .github/workflows/ci.yml       calls tools/ci.py (U-M1a)
  .claude/skills/verify/         project verification skill (U-M4e-2). Developer tooling, not shipped in the wheel
    SKILL.md                     how to drive the app offscreen: launch, doctor, drive, evidence, cleanup
    verify.py                    --doctor, --rows, --acceptance. Runs tests/ui/qt_e2e, the 41 checklist rows and the
                                 UI-09 grabs, then writes build/verify/<UTC timestamp>/ (build/ is git-ignored)
    features/                    README.md (the feature map) and design_walkthrough.md, results_and_checks.md,
                                 export_and_save.md, accessibility.md, canvas_and_shell.md
  requirements/                  lock files with hashes from uv: py311.txt, py312.txt, py313.txt and the -dev files
                                 (U-M5b, §5.2); README.md holds the regeneration command
  src/embodic/
    __init__.py                  __version__ only
    units.py                     Unit vocabulary, conversions, js_round and quantise (JS Math.round semantics)
    errors/
      __init__.py                Severity, IssueCategory, ValidationIssue, Suggestion, Unbuildable, MESSAGES,
                                 message_for; merges every catalogue module, rejects duplicate codes
      catalogue/                 one module per owning unit, each exporting MESSAGES: base.py (U-M1a) geometry.py
                                 drc.py model.py results.py winding.py generators.py physics.py project.py
                                 serpentine.py wave.py exporters.py cli.py (work_breakdown.md §4)
    paths.py                     resource_root() via importlib.resources
    model/                       vocabulary.py (TopologyKind, Phase, ViaSpan, ConnectionTopology; U-M1b) design.py rotor.py stackup.py layers.py vias.py connection.py outline.py
                                 operating.py materials.py analysis_options.py drc_rules.py (DrcRules, validate_drc_rules)
                                 winding_specs.py schema.py (type-hint walk: leaves, JSON conversion, pointers)
                                 fields.py draft.py provenance.py validate.py
    results/                     status.py traceable.py registry.py analysis_result.py formatting.py labels.py
                                 (QUANTITY_LABELS, D-038e; QUANTITY_SYMBOLS and quantity_title, D-039 e)
    winding/                     feasibility.py star_of_slots.py winding_factors.py plan.py
    geometry/                    merged (U-M1b): primitives.py transforms.py discretise.py paths.py (CopperPath,
                                 COINCIDENCE_MM) circuit.py layout.py arrays.py hashing.py distance.py grid.py
                                 (Xcoil ptSegDist, segSegDist, makeGrid, gridQuery ports)
                                 planned (U-M2d): outline.py fasteners.py details.py (TopologyDetail records)
                                 marks.py labels.py (U-M4f, D-039 c and d): coil numbering, the eye disc and the
                                 collision-free label placement that the canvas and the exporters share; Qt-free
    generators/                  __init__.py (GENERATORS, build_layout)  base.py (Generator protocol, details)
      spiral/                    artwork.py turns.py placement.py vias.py interconnect.py generate.py
      serpentine/                port of Xcoil serpentine (module split mirrors engine.js sections)
      wave/                      port of Xcoil wave: involute.py jog.py chord.py overlap.py generate.py
    drc/                         merged (U-M1c): report.py (vocabulary, REQUIRED_MM, CancelToken) items.py (item table,
                                 exemptions) kernels.py (exact line and arc kernels, pad kernels) engine.py (run_drc,
                                 grid broad phase) symmetry.py
    physics/                     magnets.py field.py edge.py emf.py circuit_solution.py constants.py
                                 resistance.py losses.py inductance.py thermal.py mass.py drive.py analyse.py
    outcome.py                   ComputeOutcome, VersionInfo (shared by api, io, ui, cli)
    io/                          board_dump.py project.py canonical.py migrations.py examples.py
                                 schema/project.v1.schema.json
                                 svg_writer.py dxf_writer.py pdf_writer.py report.py readme_writer.py bundle.py
    api.py                       compute, compute_project, outcome_to_json, StageCache
    cli/                         __main__.py commands.py; `selftest` subcommand (U-M5d, interfaces.md §12)
    selftest/                    __init__.py (public names) checks.py (SELFTESTS, the 45 checks) runner.py
                                 (run_selftests, agrees, selftest_to_json); no Qt, no pytest (U-M5d, interfaces.md §14)
    ui/
      strings/                   __init__.py (merges, rejects duplicate keys) shell.py design.py results.py export.py
      fonts.py                   register_fonts, FONT_FILES, family stacks (Qt-free; app.py passes Qt's loader in)
      theme.py                   ThemeTokens, load_theme, resolve_theme (Qt-free)
      toolstrip.py               TOOLSTRIP action table (Qt-free)
      viewmodels/                observable.py session.py outcome.py results.py export.py appearance.py
                                 selftest.py (U-M5d) (Qt-free)
      views/                     Qt widgets: main_window.py toolstrip_bar.py geometry_view.py style.py
                                 new_design_dialog.py coil_panel.py phase_panel.py layer_panel.py board_rotor_panel.py
                                 results_view.py results_rail.py charts.py status_badge.py checks_view.py
                                 export_view.py dialogs.py equation_view.py examples_gallery.py
                                 tests_dialog.py (`dlg-tests`, U-M5d)
      workers.py                 QThreadPool compute worker, debounce, latest-wins cancellation; SelfTestWorker
                                 (composed by create_shell and passed to MainWindow, D-046g)
      app.py                     QApplication (`qt_application` registers the fonts), theme, canvas share store, logging,
                                 crash handler, autosave, entry point `embodic`
  resources/                     shipped in the wheel as embodic/_resources (hatchling force-include)
    icons/                       monochrome SVG drawn with currentColor; file stem = ToolstripAction.icon (Agent 1)
    themes/                      light.json, dark.json derived from Agent 1 tokens.json (Agent 1)
    fonts/                       Inter/Inter-Regular.ttf, Inter/Inter-SemiBold.ttf and Inter/LICENSE.txt (static
                                 faces of Inter v4.1, no variable file, U-S4e ruling e2);
                                 JetBrainsMono/JetBrainsMono-Regular.ttf, JetBrainsMono-Medium.ttf and OFL.txt (SIL
                                 OFL 1.1, D-039 a); FONTS.md names the release, source URL and SHA-256 of every file.
                                 Read through resource_root(); no font is fetched at run time
    examples/                    <example_id>.embodic.json, one file per example with its own title block;
                                 no shared index file, list_examples() scans the folder (U-M2f, U-M3a, U-M3b)
    evidence/                    equations.v1.json, evidence.v1.json, manifest.v1.json, synced copies
                                 (tools/sync_registry.py); passed_tests.v1.json, written by the release gate only and
                                 git-ignored (interfaces.md §3.1)
  tests/
    conftest.py                  markers: req, eq, slow, manual; offscreen Qt for tests/ui
    ui/conftest.py               offscreen platform and the autouse session fixture `qapp`, which returns `qt_application()`
                                 so every UI test runs with the bundled fonts registered
    unit/<package>/              Agent 3 units; embodic_io/ for embodic.io (io is a stdlib name)
    unit/ui/<area>/              view-model tests; unit/ui/ holds an __init__.py (U-M4b)
    golden/harness/              comparators, tolerance map, non-finite decoding
    golden/data/<area>/          committed Xcoil dumps (no __init__.py)
    golden/<milestone>_<area>/   comparison tests (m1_geometry, m1_drc, m1_layout, m2_physics, m3_serpentine, m3_wave)
    golden/expected_diffs/<area>.toml   one allow-list per owning unit
    ui/qt_<area>/                pytest-qt tests (qt_shell, qt_design, qt_results, qt_e2e)
    ui/qt_e2e/                   U-M4e-2: conftest.py (fixtures `window`, `wait_drawn`), support.py (user actions by
                                 objectName), test_walkthroughs.py, test_ax02_keyboard_only.py, test_ax04_target_size.py,
                                 test_ui09_scaling.py, test_review_2_fixes.py (test_plan.md §5.3.1)
    ui/qt_shell/capture_acceptance.py   the lever that grabs the 41 checklist rows and the UI-09 scales; verify.py runs it
    static/                      AST lints: MT-04 to MT-08, LG-01 to LG-08
    independent/                 Agent 4 only
    performance/                 PF tests and baseline.json (§5.2)
    packaging/                   PK tests; packaging/evidence/ holds PK-10, which runs after the record step (§5.2)
  tools/
    ci.py                        one entry for every gate profile (commit, nightly, release)
    trace_matrix.py              REQ markers -> matrix, TR-01/TR-02
    sync_registry.py             docs/phase2/engineering + evidence JSON -> resources/evidence, with SHA-256 check
    record_passed_tests.py       REQ report -> resources/evidence/passed_tests.v1.json (U-M5b, interfaces.md §3.1)
    golden/dump_xcoil.mjs        Node dumper, reads /home/claude/serpentine read-only; M1 kernel functions built in
    golden/functions/<area>.mjs  engine functions for one area (m1_layout, physics, serpentine, wave), one owner each
    golden/cases/<area>.json     case lists, one file per owning unit
    golden/param_map/<topology>.json  embodic field -> Xcoil parameter names (serpentine, wave)
    contrast_check.py            AX-01, AX-08, AX-09 from resources/themes and resources/icons
    design/                      Agent 1's rerunnable scripts (D-021): build_themes.py, build_icons.py, check_*.py,
                                 layout_probe.py (widths of the panes and tables), qss_smoke.py, render_sheet.py
    build_bundle.py              PyInstaller one-folder attempt (stretch, U-M5c); runs the spec below
  packaging/pyinstaller/         embodic.spec and the bundle's licence texts (U-M5c, §5.2)
  docs/                          role folders; docs/install/INSTALL.md (English) and INSTALL_TH.md (Fable)
```

Test package names (revision 2026-10-05, U-M1y). pytest registers a test folder that holds an `__init__.py`, and
whose parent holds none, in `sys.modules` under the folder's bare name. W1's `tests/unit/io` replaced the stdlib `io`
that way and broke numpy (decision log, U-M1y). The rule:

1. A folder directly under `tests/unit/`, `tests/golden/` or `tests/ui/` is a top-level package. Its name is unique
   across `tests/` and `src/` and is not a standard-library or installed module name. MT-08 enforces both on the real
   tree, and `checks/check_contract.py` enforces them on the write paths in `work_breakdown.md`.
2. A deeper test folder is a subpackage: its parent holds an `__init__.py`, written by the unit that owns the parent
   (for example U-M2d for `tests/unit/generators/`, U-M2f for `tests/unit/property/`, U-M4b for `tests/unit/ui/`).
3. Names that satisfy rule 1: `tests/unit/<package>` uses the embodic package name, prefixed `embodic_` when the name is
   taken (`embodic_io`); golden comparison folders are `<milestone>_<area>`; Qt test folders are `qt_<area>`. Data
   folders (`golden/data`, `golden/expected_diffs`) and the level folders (`tests/static`, `tests/packaging`,
   `tests/performance`, `tests/bundle`, `tests/independent`) hold no `__init__.py`.

Resource packaging risk (`unresolved`): hatchling `force-include` maps `resources/` into the wheel; whether an editable
install (`pip install -e .`) exposes the same path is not tested. U-M1a's verify step checks
`python -c "import embodic.paths as p; print(p.resource_root())"` in both install modes. If the editable mode fails, the
fallback is moving `resources/` to `src/embodic/_resources/` (one move, no code change beyond `paths.py`).

## 2. Naming conventions

Phase 1 §15.2 stays in force: snake_case noun modules, verb functions, PascalCase noun dataclasses, `StrEnum` with
UPPER members and lower-case values, unit suffixes on every dimensional name, `is_` / `has_` / `allow_` booleans,
`UPPER_SNAKE` issue codes with category prefix, tests named `test_<unit>_<behaviour>` with `@pytest.mark.req(...)`.
Phase 2 additions:

| Element | Rule | Example |
|---|---|---|
| Generator package | `embodic.generators.<topology>` with one public `generate_<topology>` | `generate_wave` |
| Faithful-port helpers | private, named after the Xcoil function they port, docstring cites `engine.js` line | `_make_corner` (engine.js l.208) |
| Example files | `<topology>_<coils>c<poles>p_<purpose>.embodic.json` | `spiral_12c16p_default.embodic.json` |
| Icons | kebab-case file stem equal to `ToolstripAction.icon` | `export-dxf.svg` |
| Theme tokens | Agent 1 token names unchanged | `phase-a`, `phase-a-grey` |
| String keys | `<area>.<element-id>.<role>` | `results.ke_phase.label` |
| Golden data | `tests/golden/data/<area>/<case_id>.json` | `serpentine/s16p-3ph-grouped.json` |

## 3. Import rules (enforced by import-linter 2.15)

Arrows mean "may import". A module may import any module in a lower layer. Modules separated by `|` in one layer are
independent of each other. A layer name in parentheses is optional: the contract does not fail while that package does
not exist yet, so U-M1a writes the final contracts once and no later unit edits them. The `|` delimiter, the optional
`( )` form, `ignore_imports` wildcards and `unmatched_ignore_imports_alerting` were read in the import-linter 2.15 wheel
source on 2026-10-04 (`importlinter/contracts/layers.py` l.20-21 and l.49-55, `importlinter/domain/fields.py`
l.202-215, `importlinter/contracts/forbidden.py` l.58-76; `verified` by reading, not yet run).

```
embodic.ui | embodic.cli
embodic.selftest
embodic.api
embodic.generators
embodic.io
embodic.outcome
embodic.physics | embodic.drc
embodic.geometry
embodic.winding
embodic.results
embodic.model
embodic.units | embodic.errors | embodic.paths
```

Revision 2026-10-12 (U-D13). `embodic.selftest` sits below both adapters, because `embodic.cli` and
`embodic.ui.viewmodels` import it, and siblings joined by `|` may not import each other. It sits above `embodic.api`,
because its checks call `compute`, the exporters and the project file. U-M5d adds `"(embodic.selftest)"` as the second
entry of the C1 `layers` list in `pyproject.toml`; the parentheses keep the contract green until the package exists.

Why this order. `generators` sits above `io`, `outcome`, `physics` and `drc`, so no consumer of a Layout can import a
generator (ADR-0012); only `api` (and the UI above it) reaches them. `outcome` sits below `io` because exporters take a
`ComputeOutcome` while `api` imports `io` for `compute_project`. `geometry` sits above `winding` because
`embodic.geometry.details.SpiralDetail` carries the spiral winding plan.

Contract text for `pyproject.toml` (U-M1a):

```toml
[tool.importlinter]
root_packages = ["embodic"]
include_external_packages = true

[[tool.importlinter.contracts]]
id = "C1"
name = "Core layers"
type = "layers"
layers = [
    "(embodic.ui) | (embodic.cli)",
    "(embodic.selftest)",
    "(embodic.api)",
    "(embodic.generators)",
    "(embodic.io)",
    "(embodic.outcome)",
    "(embodic.physics) | (embodic.drc)",
    "(embodic.geometry)",
    "(embodic.winding)",
    "(embodic.results)",
    "(embodic.model)",
    "embodic.units | embodic.errors | embodic.paths",
]

[[tool.importlinter.contracts]]
id = "C2"
name = "Qt only in the Qt adapter modules"
type = "forbidden"
source_modules = ["embodic"]
forbidden_modules = ["PySide6", "shiboken6"]
ignore_imports = [
    "embodic.ui.views -> PySide6",
    "embodic.ui.views.** -> PySide6",
    "embodic.ui.views.** -> shiboken6",
    "embodic.ui.workers -> PySide6",
    "embodic.ui.app -> PySide6",
]
unmatched_ignore_imports_alerting = "none"

[[tool.importlinter.contracts]]
id = "C3"
name = "UI layers: view-models know no widgets"
type = "layers"
layers = [
    "(embodic.ui.app)",
    "(embodic.ui.views) | (embodic.ui.workers)",
    "(embodic.ui.viewmodels)",
    "(embodic.ui.theme) | (embodic.ui.toolstrip) | (embodic.ui.strings)",
]

[[tool.importlinter.contracts]]
id = "C4"
name = "No KiCad and no other GUI toolkits"
type = "forbidden"
source_modules = ["embodic"]
forbidden_modules = ["kipy", "pcbnew", "wx", "tkinter"]
```

With `include_external_packages = true`, import-linter puts an external package into the graph under its top-level
name only. An `ignore_imports` target therefore names `PySide6` or `shiboken6`, never `PySide6.**` or `shiboken6.**`:
a wildcard below an external package matches nothing (DEF-M1a-01, found by U-M1a and recorded in the comment above C2
in `pyproject.toml`; `verified` by reading that file on 2026-10-04, not re-run by Agent 6).

U-M1a's verify step runs `lint-imports` on the skeleton and on a scratch module that breaks each contract once (the
scratch module is deleted before commit). If C2 or C4 cannot name an external package that is never imported, that
contract moves into the MT-07 AST scan and this section is amended through Fable.

Two rules are AST scans because they concern the standard library or call sites: no network modules (`socket`, `http`,
`urllib.request`) anywhere in `src` (PK-07, REQ-N-17) and no built-in `sum()` over floats or `round()` on coordinates in
physics, DRC and geometry (MT-06). Code that needs rounding calls `embodic.units.js_round` or `embodic.units.quantise`
(interfaces.md §1).

## 4. Configuration that other gates read

| Tool | Setting | Value |
|---|---|---|
| ruff | `target-version`, `line-length`, rule sets, scope | `py311`, 120, `E,F,W,I,N,UP,B,C90,D,RUF`; `mccabe.max-complexity = 10`; pydocstyle convention `numpy`; `extend-exclude = ["docs"]`, because the role folders hold other agents' check scripts in their own style and no gate reads them as product code |
| mypy | strict on | `src/embodic` except `embodic.ui.views`, `embodic.ui.app`, `embodic.ui.workers` (Qt stubs vary across PySide6 versions; checked non-strict) |
| pytest | markers, default options | `req`, `eq`, `slow`, `manual`; `-p no:cacheprovider` on CI; `QT_QPA_PLATFORM=offscreen` set in `tests/ui/conftest.py`; `timeout = 900` s per test (pytest-timeout, `pyproject.toml` l.91) |
| coverage | scope, thresholds | `src/embodic` minus Qt views; 90 % lines, 80 % branches (REQ-N-10, `assumption`) |

## 5. Dependencies

Versions, licences and Python ranges were read from the PyPI JSON API on 2026-10-04 by Agent 6 (`verified (PyPI
metadata)`); nothing was installed on the user's machine. "Pin" is the version the lock files start from (U-M5b).
"Range" is what `pyproject.toml` declares. The two are different on purpose: the range keeps installs flexible, the pin
makes the lock files reproducible.

Extras, as implemented by U-M1a and ratified on 2026-10-04:

| Extra | Contents | Used by |
|---|---|---|
| `desktop` | PySide6-Essentials | end users who run the app |
| `dev` | every dev and test-only row below except pytest-qt; no Qt | core CI, every non-UI unit (`pip install -e .[dev]`) |
| `desktop-dev` | `embodic[desktop,dev]` plus pytest-qt | UI units and the UI test profile (`pip install -e .[desktop-dev]`) |

`dev` stays Qt-free so that the core gates run where PySide6 is not installed. hatchling is in `dev` so that the wheel
test (U-M1a resource-root check, PK tests) runs offline with `pip wheel --no-build-isolation --no-deps .`.

| Package | Pin | Range | Licence (PyPI) | Python | Scope | Reason |
|---|---|---|---|---|---|---|
| numpy | 2.4.6 | `>=2.2,<2.5` | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | >= 3.11 | core | vectorised DRC and EMF kernels; 2.4.x is the last line installable on Python 3.11, and 2.4.6 is the newest release with a `cp311-win_amd64` wheel (Phase 1 ADR-0008 l.15, `docs/phase2/evidence/dependency_licences.snapshot.json`; `verified` by reading both on 2026-10-04). Revision 2026-10-04: the pin was 2.4.4 here and 2.4.6 in the evidence file (DEF-M1a-03); 2.4.6 is the documented pin |
| PySide6-Essentials | 6.11.2 | `>=6.11,<6.12` | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only | >= 3.10, < 3.15 | extra `desktop` | the approved UI toolkit (D-010); Essentials only: no Addons, no QtWebEngine |
| pytest | 9.1.1 | `>=9,<10` | MIT | >= 3.10 | dev | test runner |
| pytest-qt | 4.5.0 | `>=4.5,<5` | MIT | >= 3.9 | extra `desktop-dev` | UI tests on the offscreen platform |
| ruff | 0.16.10 | `==0.16.10` | MIT | >= 3.7 | dev | lint and format; exact pin because rule sets change between minors |
| import-linter | 2.15 | `>=2.15,<3` | BSD 2-Clause | >= 3.10 | dev | contracts C1 to C4 |
| mypy | 2.4.0 | `>=2.4,<3` | MIT | >= 3.10 | dev | REQ-N-08 strict typing of the core |
| hypothesis | 6.168.3 | `>=6.168,<7` | MPL-2.0 | >= 3.10 | dev | property tests PR-01 to PR-14 (brief: "DRC never under-reports", rotation symmetry) |
| pytest-cov | 7.1.0 | `>=7,<8` | MIT | >= 3.9 | dev | REQ-N-10 coverage gate |
| pytest-timeout | 2.4.0 | `>=2.4,<3` | MIT | >= 3.7 | dev | hang guard: a test that hangs fails with its stack after `timeout = 900` s (`pyproject.toml` l.91 and its comment) instead of stalling the gate. Pin read from the installed 2.4.0 metadata (`verified` by `importlib.metadata`, 2026-10-09). Licence MIT in the installed PyPI metadata and in Agent 5's row (`dependency_licences.md` l.44). The line entered `pyproject.toml` (l.26) in commit 073d081 (`git log -S`); this row is added by U-D11 |
| ezdxf | 1.4.4 | `>=1.4,<2` | MIT (classifier) | >= 3.10 | dev (test-only) | independent DXF parser and audit for UT-EXP-02; never imported by `src` |
| pypdf | 6.19.0 | `>=6,<7` | BSD-3-Clause | >= 3.9 | dev (test-only) | independent PDF parser for UT-EXP-03 |
| fonttools | 4.66.1 | `>=4.60,<5` | MIT | >= 3.11 | dev (test-only) | independent reader of the bundled TrueType files: the oracle for the stdlib parser of `io/pdf_writer.py` and for the glyph coverage test of `resources/fonts`; never imported by `src`. Licence read from PyPI metadata by Agent 5 (EV-108, `dependency_licences.md`); the Python range read from the installed 4.66.1 metadata (`verified` by running `importlib.metadata`, 2026-10-09). Added by U-M4f, row added by U-D10 |
| jsonschema | 4.26.0 | `>=4.23,<5` | MIT | >= 3.10 | dev (test-only) | keeps the published project schema and the hand-written loader in step (UT-IO-03) |
| hatchling | 1.32.4 | `>=1.27,<2` | MIT | >= 3.10 | dev (build backend) | already the `[build-system]` backend; in `dev` as well so that the wheel test needs no network. Read from https://pypi.org/pypi/hatchling/json on 2026-10-04 (`verified (PyPI metadata)`); Agent 5's licence register does not list it yet |
| PyInstaller | 6.22.3 | `>=6.22,<7` | GPLv2-or-later with the bootloader exception (Agent 3, PyPI text) | >= 3.8, < 3.16 | build (stretch) | one-folder Windows bundle attempt (D-015); build tool only, nothing of it enters `src` |
| uv | the version U-M5b runs, written into the header of each lock file | not in `pyproject.toml` | MIT OR Apache-2.0 (https://pypi.org/pypi/uv/json, `license_expression`, read 2026-10-12; latest 0.13.0, and this container has 0.8.17 at `/root/.local/bin/uv`) | >= 3.8 | build (lock files only) | writes the hashed lock file of each Python version from one interpreter (`uv pip compile --python-version 3.1x --generate-hashes`). pip-tools 7.6.2 (BSD-3-Clause, same source and date) needs an interpreter of each target version per run. Chosen 2026-10-12 (U-D13); the user's pip never needs uv, because the lock files are plain `pip install --require-hashes -r` input |

Not used, with the reason: reportlab (the PDF writer is a port of Xcoil's own dependency-free `report.js`), platformdirs
(Qt's `QStandardPaths` gives the per-user log and recovery folders inside the UI adapter), pyqtgraph and matplotlib
(charts draw with Qt's own painter; one plotting stack fewer), Shapely and SciPy (Phase 1 port notes §4 to §5), kicad-python
(D-009). Adding any other package needs a reason recorded here and Fable's approval.

The Python standard library covers JSON, hashing, ZIP, XML parsing in tests, logging and `importlib.resources`.

### 5.1 Licence files the packages carry (M5)

Agent 5 recorded this list in `docs/phase2/evidence/dependency_licences.md` (§What the M5 packages must carry, U-S5a).
This table repeats the file names so that U-M5b and U-M5c find them next to the dependency table. The reasons and the
quoted licence text stay in that file. "Today" for the wheel rows is a wheel that this unit (U-D14, 2026-10-13) built
from main 76f054b with `tests.packaging.support.build_wheel` into a scratch folder and listed: 265 members, 179 `.py`
(`verified`). "Today" for the PyInstaller rows is the Linux folder that U-M5c built with `python tools/build_bundle.py`
(D-046h). This unit read the checklist in U-M5c's `build/logs/build.log` and listed that folder, read-only (`verified`
for what is written below), and did not build it again or run the smoke tests against it. The Windows folder is
`not tested` (PK-05).

| Package | File | Today |
|---|---|---|
| wheel | `embodic/_resources/fonts/Inter/LICENSE.txt` and `embodic/_resources/fonts/JetBrainsMono/OFL.txt` (OFL condition 2, beside the fonts) | present |
| wheel | `embodic/_resources/fonts/FONTS.md` | present |
| wheel | `THIRD_PARTY_LICENSES.md` (REQ-N-19, U-M5b): licence, copyright line and pin of NumPy, PySide6-Essentials, shiboken6, Inter and JetBrains Mono, and the notice that Qt is used under LGPL-3.0 | present as `embodic-0.0.1.dist-info/licenses/THIRD_PARTY_LICENSES.md` (`verified` by listing; `test_pk03_the_wheel_holds_the_package_resources_and_licences_and_nothing_else` pins it) |
| wheel | embodic's own licence file | absent. The user decides which licence (dependency_licences.md, open point 2) |
| PyInstaller folder | the four font files with `LICENSE.txt` and `OFL.txt` beside them; the spec `datas` entry takes the text files as well as `*.ttf` | present in `_internal/embodic/_resources/fonts/`: `Inter-Regular.ttf`, `Inter-SemiBold.ttf` and `LICENSE.txt`; `JetBrainsMono-Medium.ttf`, `JetBrainsMono-Regular.ttf` and `OFL.txt`; `FONTS.md` |
| PyInstaller folder | `licenses/LGPL-3.0.txt` and `licenses/GPL-3.0.txt` (LGPL-3.0 section 4 b) | present, 7,651 and 35,147 bytes. Their SHA-256 values equal Agent 5's (`da7eabb7…4768` and `8ceb4b9e…b903`, `dependency_licences.md` l.484), `verified` by `sha256sum` on the folder. The PySide6-Essentials wheel carries only `LicenseRef-Qt-Commercial.txt`, so the texts come from `packaging/pyinstaller/licenses/` |
| PyInstaller folder | `THIRD_PARTY_LICENSES.md` with a prominent notice that the application uses Qt under LGPL-3.0 | present, 58,509 bytes. It opens with the section "Notice: embodic uses Qt and PySide6 under LGPL-3.0". The notice wording is `assumption` until the coordinator and a lawyer review it (the file says so) |
| PyInstaller folder | the Qt libraries as separate files (LGPL-3.0 section 4 d, route 0) | present as separate files: `_internal/PySide6/Qt/lib/libQt6Core.so.6` (7,524,648 bytes), `libQt6Gui.so.6` (11,412,488), `libQt6Widgets.so.6` (8,155,496) and `libQt6Svg.so.6` (691,176), the check of `tools/build_bundle.py` and of `test_qt_libraries_are_separate_files`. M5 complies with route 0 for the bundle and does not rely on route 1 (U-S5c; `dependency_licences.md` R8). Route 1 (a) against a bundled Qt copy stays `unresolved` as a reading, and nothing here depends on it. Route 1 is met only in the pip install, where Qt comes from PyPI |
| PyInstaller folder | `source/embodic-<version>.tar.gz`, embodic's source as the sdist, inside the folder (§5.2). U-M5c chose the sdist because it carries the spec, the build script and the lock files. Route 0 needs the source (`dependency_licences.md` R5 to R7) | present as `source/embodic-0.0.1.tar.gz`, 18.8 MB. It holds `packaging/pyinstaller/embodic.spec`, `tools/build_bundle.py` and `src/embodic/__init__.py` (the three checks of `source_ok`, `verified`), and `requirements/` with the lock files (`verified` by listing the top-level names). This row replaces the earlier placement of the sdist at the top of the folder. The size is an open item below |
| PyInstaller folder | the spec file `packaging/pyinstaller/embodic.spec` and the build script `tools/build_bundle.py`. R7 asks that both be published, because LGPL-3.0 counts "utility programs needed for reproducing the Combined Work" as Application code | both exist on main 76f054b (`verified` by `ls`) and ride inside the sdist above |
| PyInstaller folder | a written offer, or the files, for the Qt 6.11.2 and PySide6 6.11.2 source | absent. Who makes the offer is a user decision (`dependency_licences.md` R5, R6), so the folder has no `SOURCE.md` |
| PyInstaller folder | `licenses/numpy/` | present, 17 files, 92,518 bytes: the files of the `licenses/` folder in NumPy's dist-info (`LICENSE.txt` and a `numpy/` folder) |
| PyInstaller folder | `licenses/PYTHON-LICENSE.txt` (PSF License Agreement section 2) | present, 13,936 bytes, SHA-256 `3b2f81fe…da3bf` |
| PyInstaller folder | Qt's third-party component notices for the bundled modules | absent. The proxy refused `doc.qt.io`, so the list of bundled modules is `unresolved` |
| PyInstaller folder | embodic's own licence file | absent. The user decides which licence (D-015) |

Open items from the folder build (D-046h, `verified` for the facts; the decisions are not taken here).

1. The sdist is 18.8 MB (18,805,798 bytes in the checklist of `build.log`, 18,807,803 bytes for the file in the latest
   folder). Listing it shows 1,059 files and 46.7 MB uncompressed, of which `tests/` is 27.3 MB and `docs/` 15.4 MB. Route
   0 needs the spec, the build script, the lock files and the source, which are far smaller. Whether the folder should
   carry a trimmed sdist is a design and licensing question for Fable and the user.
2. PyInstaller warned on Linux that `libxcb-cursor.so.0` cannot be resolved for four Qt files: the xcb platform plugin
   `libqxcb.so`, `libQt6XcbQpa.so.6` and the two `xcbglintegrations` plugins (`build.log` l.104 to l.107). The folder
   does not carry that library, so a Linux desktop needs the system package that provides it (`inferred`). The smoke tests
   run with `QT_QPA_PLATFORM=offscreen` (`tests/bundle/test_bundle_smoke.py`), which does not load the xcb plugin, so a
   start of the frozen GUI on an xcb desktop is `not tested`.
3. PK-05 on Windows is `not tested`. The Linux folder is a smoke of the spec only (D-046h), and D-046h records
   `6 passed` for U-M5c's folder. The skip half of this item is closed (revision 2026-10-19, U-D24; D-068, U-M8q).
   `python tools/ci.py --profile release` builds the folder with `tools/build_bundle.py` before pytest and sets
   `EMBODIC_REQUIRE_BUNDLE=1`, so `tests/bundle` fails instead of skipping when the folder is missing (`tools/ci.py`
   l.85-86 and l.104-105, `tests/bundle/bundle_gate.py`, `verified` by reading). The commit and nightly profiles still
   skip, because they do not build the folder. The gap that remains is the Windows folder: this unit read no result of a
   release run on Windows.

The folder does not carry fontTools or any other dev tool. The PyInstaller bootloader adds no obligation
(dependency_licences.md, §Distribution obligations, item 7).

### 5.2 Packaging layout (M5; revision 2026-10-12, U-D13)

Facts marked `verified` come from a wheel and an sdist that U-D13 built with hatchling 1.32.4 (`python -m hatchling
build`) from a scratch copy of main 7b9b4c9, with a dummy `resources/evidence/passed_tests.v1.json` added and its path
appended to `.gitignore`. Test IDs are defined in `test_plan.md` §5.7.

Revision 2026-10-13 (U-D14, claude-sonnet-5-5): the wheel table below was read again on main 76f054b. `build/dist` does
not exist in this worktree, so this unit built a wheel with `tests.packaging.support.build_wheel` into a scratch folder
(265 members, 179 `.py`, `verified`). That function builds from a copy of the tree without the evidence file (D-045f), so
the table's evidence row reads differently from the U-D13 original. `tests/packaging/test_pk03_reproducible_wheel.py`
gives `4 passed` (`verified` by running it).

Wheel. `pip wheel --no-build-isolation --no-deps . -w build/dist` builds it from `[tool.hatch.build.targets.wheel]`.

| Wheel member | Source | State on main 76f054b |
|---|---|---|
| `embodic/**` | `src/embodic`, `.py` files and package data such as `embodic/io/schema/project.v1.schema.json` | `verified` present: 179 `.py` files and the schema file |
| `embodic/_resources/themes/`, `icons/`, `examples/` | `resources/` through `force-include` | `verified` present: 11, 54 and 5 files |
| `embodic/_resources/fonts/` with `Inter/LICENSE.txt`, `JetBrainsMono/OFL.txt` and `FONTS.md` | `resources/fonts/` (OFL condition 2, §5.1) | `verified` present: 7 files |
| `embodic/_resources/evidence/` with `equations.v1.json`, `evidence.v1.json`, `manifest.v1.json` | `tools/sync_registry.py` copies | `verified` present |
| `embodic/_resources/evidence/passed_tests.v1.json` | the release gate (interfaces.md §3.1); git-ignored | absent from the wheel that `build_wheel` builds, by design (D-045f, D-046e; `test_pk03_the_session_wheel_leaves_out_evidence_a_release_run_left_in_the_tree`). The release profile's own wheel carries it, written by U-M5b, and PK-10 checks it there (`not tested` in this unit). U-D13 `verified` on main 7b9b4c9 that a git-ignored file there enters a wheel built straight from the tree |
| `embodic-<version>.dist-info/licenses/THIRD_PARTY_LICENSES.md` | `[project] license-files = ["THIRD_PARTY_LICENSES.md"]` (PEP 639), U-M5b | `verified` present as `embodic-0.0.1.dist-info/licenses/THIRD_PARTY_LICENSES.md` |
| embodic's own licence file | none | absent. Pending the user's choice. No unit writes `LICENSE` until the user decides |
| `tests/`, `.claude/`, `docs/`, `tools/`, `packaging/`, `requirements/` | none | `verified` absent: the top-level names of the wheel are `embodic` and `embodic-0.0.1.dist-info`. No document ships except the licence texts above |

Sdist. The sdist that U-M5c shipped in the folder (§5.1) holds `.github`, `.gitignore`, `CHANGELOG.md`, `PKG-INFO`,
`README.md`, `THIRD_PARTY_LICENSES.md`, `docs`, `packaging`, `pyproject.toml`, `requirements`, `resources`, `src`, `tests`
and `tools` (`verified` by listing it, 1,059 files). It leaves out `.claude/`, `build/` and the git-ignored evidence file.
`[tool.hatch.build.targets.sdist] exclude = [".claude/", "build/"]` does this, so `.claude/` stays out and `build/` stays
out if `.gitignore` ever changes (U-M5b; the sdist test in `test_pk03_reproducible_wheel.py` pins it). This closes the
U-D12 question of §1. A wheel built from the sdist has no evidence file, so its results read `not tested`. That is
correct, because no gate ran on it.

Lock files (REQ-N-06). uv writes one file per Python version, every line pinned with `--hash` (§5, row uv):

```
uv pip compile pyproject.toml --extra desktop --universal --python-version 3.11 --generate-hashes -o requirements/py311.txt
uv pip compile pyproject.toml --extra desktop-dev --universal --python-version 3.11 --generate-hashes -o requirements/py311-dev.txt
```

and the same for 3.12 and 3.13. `--universal` asks for one file valid on Windows and Linux. That uv's universal mode
with `--generate-hashes` lists the hashes of every platform's wheel is `inferred`; PK-02 checks Linux in this container
and PK-01 checks Windows in CI. Install with two commands, because `--require-hashes` needs a hash for every requirement
and the local wheel has none: `python -m pip install --require-hashes -r requirements/py311.txt`, then
`python -m pip install --no-deps build/dist/embodic-<version>-py3-none-any.whl`. `requirements/README.md` holds the
commands. No unit publishes to PyPI or anywhere else without the user's approval.

README.md sections, in English, each command given for Windows PowerShell and for Linux bash:

1. What embodic does (one paragraph) and the status words a result can carry.
2. Requirements: CPython 3.11, 3.12 or 3.13; Windows 10 or 11 x64, or Linux x86-64 (REQ-N-05).
3. Install: create a venv, install from the lock file, install the wheel (above).
4. Run the app: `embodic`.
5. Run the CLI: `embodic-cli compute`, `validate`, `export` (interfaces.md §12).
6. Check the installation: `embodic-cli selftest`, and the Tests dialog.
7. Run the tests: a dev install (`pip install -e .[desktop-dev]` from `requirements/py3xx-dev.txt`), then
   `python tools/ci.py --profile commit`.
8. Build the wheel, and record the test evidence with `python tools/ci.py --profile release`.
9. Build the PyInstaller folder (stretch, U-M5c): `python tools/build_bundle.py`.
10. Licences: `THIRD_PARTY_LICENSES.md`; embodic's own licence is pending the user's choice.

`docs/install/INSTALL.md` (English) is the long form of sections 2 to 9, with the expected output after each step, the
time each step took in the PK-06 walkthrough, and a troubleshooting section per platform. Fable writes
`docs/install/INSTALL_TH.md` from it (U-F1).

`THIRD_PARTY_LICENSES.md` structure. U-M5b assembles it from Agent 5's list (`dependency_licences.md`, "What the M5
packages must carry" and the "M5 distribution" section that U-S5c writes). It copies the source offer and the notice
wording from U-S5c verbatim and does not write its own.

1. A prominent notice first, saying that embodic uses Qt and PySide6 under LGPL-3.0, with the versions and the source location
   from U-S5c (LGPL-3.0 section 4 a and c, quoted in `dependency_licences.md`).
2. One section per runtime dependency and bundled asset, each with name, pinned version, SPDX identifier, copyright line,
   the path of the full text in the venv, wheel or repository, and how embodic uses it: NumPy 2.4.6 (BSD-3-Clause, with
   the notices of the bundled OpenBLAS, LAPACK and GCC runtime), PySide6-Essentials 6.11.2 and shiboken6 6.11.2
   (LGPL-3.0-only, the option embodic uses), Qt 6.11.2 (LGPL-3.0-only, with Qt's third-party notices for the bundled
   modules), Inter and JetBrains Mono (OFL-1.1, each family with its own text), and CPython (PSF-2.0, the
   PyInstaller folder only).
3. The full texts: OFL-1.1 for each font family, LGPL-3.0, and GPL-3.0, which LGPL-3.0 section 4 b requires beside it.
4. One line that embodic's own licence is pending the user's choice.

PyInstaller one-folder build (stretch, D-015; U-M5c). The spec is `packaging/pyinstaller/embodic.spec`, and
`tools/build_bundle.py` runs it and assembles the folder at `build/bundle/embodic`. One-folder only, never one-file, so
every Qt library stays a separate, replaceable file (`dependency_licences.md`, obligation 3). The tree below is the Linux
folder that U-M5c built (D-046h), listed read-only (`verified`); a Windows folder carries `.exe` names and is `not tested`.

```
build/bundle/embodic/            zipped for delivery; never published without the user's approval
  embodic                        windowed entry, embodic.ui.app:main (embodic.exe on Windows)
  embodic-cli                    console entry, embodic.cli:main (embodic-cli.exe on Windows)
  _internal/                     PyInstaller 6 contents folder: the Python runtime, compiled modules, and the Qt,
                                 PySide6 and shiboken6 libraries as separate files (PySide6/Qt/lib/libQt6*.so.6)
    embodic/_resources/          the same tree as in the wheel; its evidence/ holds the three registry files
  THIRD_PARTY_LICENSES.md
  licenses/                      LGPL-3.0.txt, GPL-3.0.txt, PYTHON-LICENSE.txt, numpy/ (17 files)
  source/                        embodic-<version>.tar.gz, embodic's sdist (LGPL-3.0 section 4 d, route 0,
                                 dependency_licences.md); it holds packaging/pyinstaller/embodic.spec, tools/build_bundle.py
                                 and requirements/ with the lock files (R7)
```

The folder has 444 files and 232,412,913 bytes, and no `.py` file (`verified`: the summary of `build_bundle.py` and
`test_frozen_package_holds_no_python_source`). There is no `SOURCE.md` and no Qt third-party notices file, because the
written offer is a user decision and the notices are `unresolved` (§5.1). D-046h records the results of U-M5c's run: build
exit 0, the smoke tests of `tests/bundle/test_bundle_smoke.py` `6 passed`, and the frozen `embodic-cli selftest` 45 of 45.
This unit read those results and did not repeat them. In a tree without the folder the same 6 tests skip under the
commit and nightly profiles. Under the release profile they fail instead (revision 2026-10-19, U-D24; D-068, U-M8q):
`tools/ci.py` builds the folder first and sets `EMBODIC_REQUIRE_BUNDLE=1`, and `require_bundle` in
`tests/bundle/bundle_gate.py` calls `pytest.fail` when the variable is set and `embodic-cli` is missing (`verified` by
reading).

`resource_root()` in a frozen build. It was `unresolved` whether `paths.py` finds `_internal/embodic/_resources`, because
it raises when `importlib.resources.files("embodic")` is not a `pathlib.Path`. The frozen selftest reads the registry
through `resource_root()` and the frozen GUI smoke loads an example, and D-046h records both as passing, so the folder
finds its resources (`inferred` from D-046h, not run here). A frozen build has no `.py` files, so the evidence check
compares versions only (interfaces.md §3.1).

PF baseline (REQ-N-01 to REQ-N-03, REQ-N-22). `tests/performance/baseline.json` is committed and rewritten only by a
release run with `--record-baseline`:

| Key | Value |
|---|---|
| `format`, `format_version` | `"embodic.pf-baseline"`, `1` |
| `embodic_version`, `git_commit`, `recorded_utc` | as in the evidence file |
| `machine` | `platform.platform()`, `platform.machine()`, the CPU model string, `os.cpu_count()`, total memory in GiB, `python`, `numpy`. No host name, user name or path |
| `cases` | PF-01 (`spiral_12c16p_default`, 20 warm runs: p50, p95 and the per-stage seconds of `ComputeOutcome.timings_s`), PF-02, PF-03 (offscreen platform, so `inferred` for a desktop session), PF-05 (`serpentine_16p_example`, `wave_16p_example`) |

PF-04 compares a run with this file. It fails when a case is more than 3 times its budget or more than 25 % slower than
the baseline (Phase 1 PF-04). The budgets stay `assumption` (Phase 1 PF-01 to PF-03); the baseline records, it does not
set targets.
