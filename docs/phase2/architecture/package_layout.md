Prepared by: Agent 6 - Software Architecture Specialist - model: claude-opus-5-5

# embodic Phase 2 package layout, import rules and dependencies (build contract v1, 2026-10-04)

This file fixes where code, tests and resources live, which module may import which, and which third-party packages are
allowed. It replaces `docs/phase1/architecture/architecture_draft.md` §4 and §15.1 (KiCad parts removed, generators and
Qt-free view-models added). Unit ownership of each path is in `work_breakdown.md`.

## 1. Repository tree

```
embodic/
  pyproject.toml                 PEP 621 metadata, extras, tool config (ruff, mypy, pytest, import-linter)
  README.md                      English; install, run, test, package (U-M5b)
  THIRD_PARTY_LICENSES.md        generated licence list (U-M5b)
  CHANGELOG.md
  .github/workflows/ci.yml       calls tools/ci.py (U-M1a)
  requirements/                  lock files with hashes: py311.txt, py312.txt, py313.txt (+ -dev) (U-M5b)
  src/embodic/
    __init__.py                  __version__ only
    units.py                     Unit vocabulary, conversions, quantisation helper
    errors.py                    Severity, IssueCategory, ValidationIssue, Suggestion, Unbuildable, message catalogue
    paths.py                     resource_root() via importlib.resources
    model/                       vocabulary.py (TopologyKind, Phase, ViaSpan, ConnectionTopology; U-M1b) design.py rotor.py stackup.py layers.py vias.py connection.py outline.py
                                 operating.py materials.py analysis_options.py drc_rules.py
                                 winding_specs.py fields.py draft.py provenance.py validate.py
    results/                     status.py traceable.py registry.py analysis_result.py formatting.py
    winding/                     feasibility.py star_of_slots.py winding_factors.py plan.py
    geometry/                    primitives.py transforms.py discretise.py paths.py circuit.py layout.py
                                 arrays.py outline.py fasteners.py hashing.py details.py (TopologyDetail records)
    generators/                  __init__.py (GENERATORS, build_layout)  base.py (Generator protocol, details)
      spiral/                    artwork.py turns.py placement.py vias.py interconnect.py generate.py
      serpentine/                port of Xcoil serpentine (module split mirrors engine.js sections)
      wave/                      port of Xcoil wave: involute.py jog.py chord.py overlap.py generate.py
    drc/                         rules.py distance.py broad_phase.py symmetry.py check.py
    physics/                     magnets.py field.py edge.py emf.py circuit_solution.py constants.py
                                 resistance.py losses.py inductance.py thermal.py mass.py drive.py analyse.py
    outcome.py                   ComputeOutcome, VersionInfo (shared by api, io, ui, cli)
    io/                          board_dump.py project.py canonical.py migrations.py examples.py
                                 schema/project.v1.schema.json
                                 svg_writer.py dxf_writer.py pdf_writer.py report.py readme_writer.py bundle.py
    api.py                       compute, compute_project, outcome_to_json, StageCache
    cli/                         __main__.py commands.py
    ui/
      strings/                   __init__.py (merges, rejects duplicate keys) shell.py design.py results.py export.py
      theme.py                   ThemeTokens, load_theme, resolve_theme (Qt-free)
      toolstrip.py               TOOLSTRIP action table (Qt-free)
      viewmodels/                observable.py session.py outcome.py results.py export.py appearance.py (Qt-free)
      views/                     Qt widgets: main_window.py toolstrip_bar.py geometry_view.py style.py
                                 new_design_dialog.py coil_panel.py phase_panel.py layer_panel.py board_rotor_panel.py
                                 results_view.py results_rail.py charts.py status_badge.py checks_view.py
                                 export_view.py dialogs.py equation_view.py examples_gallery.py
      workers.py                 QThreadPool compute worker, debounce, latest-wins cancellation
      app.py                     QApplication, theme, logging, crash handler, autosave, entry point `embodic`
  resources/                     shipped in the wheel as embodic/_resources (hatchling force-include)
    icons/                       monochrome SVG drawn with currentColor; file stem = ToolstripAction.icon (Agent 1)
    themes/                      light.json, dark.json derived from Agent 1 tokens.json (Agent 1)
    examples/                    <example_id>.embodic.json, one file per example with its own title block;
                                 no shared index file, list_examples() scans the folder (U-M2f, U-M3a, U-M3b)
    evidence/                    equations.v1.json, evidence.v1.json, synced copies (tools/sync_registry.py)
  tests/
    conftest.py                  markers: req, eq, slow, manual; offscreen Qt for tests/ui
    unit/<package>/              Agent 3 units
    golden/harness/              comparators, tolerance map, non-finite decoding
    golden/data/<area>/          committed Xcoil dumps
    golden/<area>/               comparison tests per area (m1, physics, serpentine, wave)
    golden/expected_diffs/<area>.toml   one allow-list per owning unit
    ui/<area>/                   pytest-qt tests
    static/                      AST lints: MT-04 to MT-07, LG-01 to LG-08
    independent/                 Agent 4 only
    performance/  packaging/
  tools/
    ci.py                        one entry for every gate profile (commit, nightly, release)
    trace_matrix.py              REQ markers -> matrix, TR-01/TR-02
    sync_registry.py             docs/phase2/engineering + evidence JSON -> resources/evidence, with SHA-256 check
    golden/dump_xcoil.mjs        Node dumper, reads /home/claude/serpentine read-only
    golden/cases/<unit>.json     case lists, one file per owning unit
    golden/param_map/<topology>.json  embodic field -> Xcoil parameter names (serpentine, wave)
    contrast_check.py            AX-01, AX-08, AX-09 from resources/themes and resources/icons
    build_bundle.py              PyInstaller one-folder attempt (stretch)
  docs/                          role folders; docs/install/INSTALL.md (English) and INSTALL_TH.md (Fable)
```

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
    "embodic.ui.views -> PySide6.**",
    "embodic.ui.views.** -> PySide6.**",
    "embodic.ui.views.** -> shiboken6.**",
    "embodic.ui.workers -> PySide6.**",
    "embodic.ui.app -> PySide6.**",
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

U-M1a's verify step runs `lint-imports` on the skeleton and on a scratch module that breaks each contract once (the
scratch module is deleted before commit). If C2 or C4 cannot name an external package that is never imported, that
contract moves into the MT-07 AST scan and this section is amended through Fable.

Two rules are AST scans because they concern the standard library or call sites: no network modules (`socket`, `http`,
`urllib.request`) anywhere in `src` (PK-07, REQ-N-17) and no built-in `sum()` over floats or `round()` on coordinates in
physics, DRC and geometry (MT-06).

## 4. Configuration that other gates read

| Tool | Setting | Value |
|---|---|---|
| ruff | `target-version`, `line-length`, rule sets | `py311`, 120, `E,F,W,I,N,UP,B,C90,D,RUF`; `mccabe.max-complexity = 10`; pydocstyle convention `numpy` |
| mypy | strict on | `src/embodic` except `embodic.ui.views`, `embodic.ui.app`, `embodic.ui.workers` (Qt stubs vary across PySide6 versions; checked non-strict) |
| pytest | markers, default options | `req`, `eq`, `slow`, `manual`; `-p no:cacheprovider` on CI; `QT_QPA_PLATFORM=offscreen` set in `tests/ui/conftest.py` |
| coverage | scope, thresholds | `src/embodic` minus Qt views; 90 % lines, 80 % branches (REQ-N-10, `assumption`) |

## 5. Dependencies

Versions, licences and Python ranges were read from the PyPI JSON API on 2026-10-04 by Agent 6 (`verified (PyPI
metadata)`); nothing was installed on the user's machine. "Pin" is the version the lock files start from.

| Package | Pin | Range | Licence (PyPI) | Python | Scope | Reason |
|---|---|---|---|---|---|---|
| numpy | 2.4.4 | `>=2.2,<2.5` | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | >= 3.11 | core | vectorised DRC and EMF kernels; 2.4.x is the last line installable on Python 3.11 (Phase 1 REQ-N-05 evidence) |
| PySide6-Essentials | 6.11.2 | `>=6.11,<6.12` | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only | >= 3.10, < 3.15 | extra `desktop` | the approved UI toolkit (D-010); Essentials only: no Addons, no QtWebEngine |
| pytest | 9.1.1 | `>=9,<10` | MIT | >= 3.10 | dev | test runner |
| pytest-qt | 4.5.0 | `>=4.5,<5` | MIT | >= 3.9 | dev | UI tests on the offscreen platform |
| ruff | 0.16.10 | `==0.16.10` | MIT | >= 3.7 | dev | lint and format; exact pin because rule sets change between minors |
| import-linter | 2.15 | `>=2.15,<3` | BSD 2-Clause | >= 3.10 | dev | contracts C1 to C4 |
| mypy | 2.4.0 | `>=2.4,<3` | MIT | >= 3.10 | dev | REQ-N-08 strict typing of the core |
| hypothesis | 6.168.3 | `>=6.168,<7` | MPL-2.0 | >= 3.10 | dev | property tests PR-01 to PR-14 (brief: "DRC never under-reports", rotation symmetry) |
| pytest-cov | 7.1.0 | `>=7,<8` | MIT | >= 3.9 | dev | REQ-N-10 coverage gate |
| ezdxf | 1.4.4 | `>=1.4,<2` | MIT (classifier) | >= 3.10 | dev (test-only) | independent DXF parser and audit for UT-EXP-02; never imported by `src` |
| pypdf | 6.19.0 | `>=6,<7` | BSD-3-Clause | >= 3.9 | dev (test-only) | independent PDF parser for UT-EXP-03 |
| jsonschema | 4.26.0 | `>=4.23,<5` | MIT | >= 3.10 | dev (test-only) | keeps the published project schema and the hand-written loader in step (UT-IO-03) |
| PyInstaller | 6.22.3 | `>=6.22,<7` | GPLv2-or-later with the bootloader exception (Agent 3, PyPI text) | >= 3.8, < 3.16 | build (stretch) | one-folder Windows bundle attempt (D-015); build tool only, nothing of it enters `src` |

Not used, with the reason: reportlab (the PDF writer is a port of Xcoil's own dependency-free `report.js`), platformdirs
(Qt's `QStandardPaths` gives the per-user log and recovery folders inside the UI adapter), pyqtgraph and matplotlib
(charts draw with Qt's own painter; one plotting stack fewer), Shapely and SciPy (Phase 1 port notes §4 to §5), kicad-python
(D-009). Adding any other package needs a reason recorded here and Fable's approval.

The Python standard library covers JSON, hashing, ZIP, XML parsing in tests, logging and `importlib.resources`.
