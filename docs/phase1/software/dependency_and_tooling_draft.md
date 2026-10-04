Prepared by: Agent 3 — Senior Software Engineer — model: claude-opus-5-5

# Dependencies, tooling and packaging — draft (Phase 1, 2026-10-04)

Principle (`assumption`): the calculation/geometry core depends on the Python standard library and NumPy only; everything
else is an optional extra of the UI, the exporters, the KiCad adapter or development. Licence, version and Python
requirement of every package below were read from the PyPI JSON API (`https://pypi.org/pypi/<name>[/<version>]/json`,
fields `license_expression` / `license` / classifiers, `requires_python`, `requires_dist`, file list) on 2026-10-04 —
`verified (PyPI metadata)`. "Latest" means latest on that date. Nothing was installed on the user's machine; every
installation statement is **not tested** unless stated. UI technology and app type are decided by Agent 6 and the user; I
only list candidates.

## 1. Runtime — core (`embodic_core`)

| Package | Version proposal | Licence | Python | Purpose | Status |
|---|---|---|---|---|---|
| CPython | ≥ 3.11 (user has 3.11+) | PSF | — | language, stdlib (`math`, `dataclasses`, `enum`, `json`, `zipfile`, `zlib`, `hashlib`, `logging`) | user statement (brief) |
| NumPy | provisional `numpy>=1.26,<2.5`; final range after KiCad's bundled Python is known (T1/T2) | 2.4.4: `BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0`; 1.26.4: BSD-3-style text | 2.4.4 ≥ 3.11; 2.5.3 (latest) ≥ 3.12; 2.2.6 ≥ 3.10; 1.26.4 ≥ 3.9 | vectorised kernels: discretisation, DRC pair distances, EMF/eddy integration, inductance sums (`calculation_flow_and_port_notes.md` §4) | verified (PyPI); cp311 `win_amd64` wheels exist for 1.26.4, 2.2.6, 2.3.5, 2.4.4 — verified (PyPI file list); used here only with 2.4.4 on Linux — Windows not tested |

Not proposed for the core: Shapely (BSD 3-Clause, bundles GEOS; segments instead of true arcs), SciPy, Numba, Cython
(reasons in the port notes §4–5).

## 2. Runtime — optional extras

### 2.1 Standalone UI candidates (decision: Agent 6 + user)

| Package | Latest | Licence | Python | Would provide | Note | Status |
|---|---|---|---|---|---|---|
| PySide6 (Qt for Python) | 6.11.2 | `LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only` | ≥ 3.10, < 3.15 | native desktop UI, 2-D canvas (QGraphicsView), file dialogs | LGPL obligations when bundling (dynamic linking, replaceable libraries) — `inferred`, not legal advice | verified (PyPI) |
| pyqtgraph | 0.14.0 | MIT | ≥ 3.10 | fast plots (EMF, torque–speed), optional OpenGL 3-D | needs a Qt binding | verified (PyPI) |
| wxPython | 4.3.1 | wxWindows Library Licence | ≥ 3.10 | desktop UI (same toolkit family as KiCad) | — | verified (PyPI) |
| pywebview | 6.2.1 | BSD 3-Clause | ≥ 3.8 | Python-backed web UI in a native window (HTML/CSS/JS front end, three.js for 3-D as in Xcoil) | reuses the Xcoil UI idea; front end in JS, engine in Python | verified (PyPI) |
| matplotlib | 3.11.2 | Matplotlib licence (BSD-style text) | ≥ 3.11 | charts in the PDF report or a simple UI | — | verified (PyPI) |
| three.js | r128 vendored in Xcoil (`/home/claude/serpentine/vendor/three.LICENSE`: MIT) | MIT | — | 3-D view in a web front end | only relevant for a web-based UI | verified (file) |

### 2.2 Export and report

| Package | Latest | Licence | Python | Purpose | Proposal | Status |
|---|---|---|---|---|---|---|
| (own writers) | — | embodic's | — | SVG, DXF R12, `.kicad_pcb` from the shared Board model (Xcoil writers are small: `engine.js` l.2796–2929) | **yes** — no dependency | verified (code size) |
| stdlib `zipfile` | — | PSF | — | ZIP archives (replaces Xcoil `makeZip`) | **yes** | verified (stdlib) |
| reportlab | 5.0.1 | BSD licence (PyPI text) | ≥ 3.9, < 4 | PDF report | option A for the report; option B: port Xcoil's dependency-free PDF writer (`report.js`, our own code) | verified (PyPI) |
| ezdxf | 1.4.4 | MIT (classifier) | ≥ 3.10 | DXF read/write | only if DXF import is wanted | verified (PyPI) |

### 2.3 KiCad adapter / plugin (`embodic_kicad`)

| Package | Version | Licence | Python | Purpose | Status |
|---|---|---|---|---|---|
| kicad-python (`kipy`) | pin per user's KiCad 9.0.x after T4; available 0.4.0 (2025-07-08), 0.5.0, 0.6.0, 0.7.0, 0.8.0 (Agent 5: 0.4.0 ↔ 9.0.3, 0.5.0 ↔ 9.0.5, 0.6.0 ↔ 9.0.8, 0.7.0 ↔ 10.0.0/1, 0.8.0 ↔ 10.0.6) | MIT (0.5.0 shows no licence field on PyPI) | ≥ 3.9 | IPC API client | verified (PyPI; version mapping from `kicad_plugin_evidence.md` §3) |
| protobuf | `>=5.29,<6` (required by every kicad-python 0.4.0–0.8.0); 5.29.5 | 3-Clause BSD | 5.29.5: ≥ 3.8 | kipy transport | verified (PyPI `requires_dist`) |
| pynng | 0.8.x for kicad-python ≤ 0.5.0; 0.9.x for ≥ 0.6.0 | MIT | — | kipy transport (NNG) | verified (PyPI); 0.9.0 has cp311 `win_amd64` wheel — verified (file list) |
| jsonschema | `>=4.23,<5` (kicad-python ≥ 0.7.0) | MIT | 4.26.0: ≥ 3.10 | kipy packaging validation | verified (PyPI) |
| typing_extensions | `>=4.13.2` for Python < 3.13 | PSF-2.0 | ≥ 3.9 | kipy typing | verified (PyPI) |

## 3. Development tooling

| Tool | Latest | Licence | Python | Use | Required? | Status |
|---|---|---|---|---|---|---|
| pytest | 9.1.1 | MIT | ≥ 3.10 | unit, regression, cross-check tests | yes | verified (PyPI) |
| ruff | 0.16.10 | MIT | ≥ 3.7 | lint + format | yes | verified (PyPI) |
| mypy | 2.4.0 | MIT | ≥ 3.10 | static typing of `embodic_core` | optional | verified (PyPI) |
| hypothesis | 6.168.3 | MPL-2.0 | ≥ 3.10 | property-based tests (geometry invariants: continuity, clearance) | optional; dev-only, not shipped | verified (PyPI) |
| build | 1.6.1 | MIT | ≥ 3.10 | build sdist/wheel | yes | verified (PyPI) |
| hatchling or setuptools | 1.32.4 / 84.0.0 | MIT / MIT | ≥ 3.10 | build backend | one of them | verified (PyPI) |
| PyInstaller | 6.22.3 | "GPLv2-or-later with a special exception which allows to use PyInstaller to build and distribute non-free programs (including commercial ones)" | ≥ 3.8, < 3.16 | Windows desktop bundle | only for the desktop distribution | verified (PyPI licence text) |
| Node.js | user's dev machine / this container (v22.22.2) | not checked here | — | regenerate JS snapshots for the cross-check harness only | dev-only, not shipped | not tested on Windows |

Practices (`assumption`): pinned lock file for CI (`pip-compile`-style or `uv`; tool not chosen), `ruff` + `pytest` in CI on
Windows and Linux, a generated third-party licence list shipped with every distribution.

## 4. Packaging options

### 4.1 Source layout and `pyproject.toml` (sketch — draft text, not a file in the repository)

```toml
[project]
name = "embodic"
requires-python = ">=3.11"            # revisit after T2 (KiCad's bundled Python)
dependencies = ["numpy>=1.26,<2.5"]   # provisional

[project.optional-dependencies]
ui     = ["<chosen UI toolkit>"]      # e.g. PySide6 or pywebview (Agent 6 / user decision)
report = ["reportlab>=5"]             # only if option A for the PDF report is chosen
kicad  = ["kicad-python==<pin from T4>"]
dev    = ["pytest", "ruff", "mypy", "hypothesis", "build"]

[project.scripts]
embodic = "embodic_app.__main__:main"           # standalone UI
embodic-cli = "embodic_core.cli:main"           # headless compute/export (N-13)
```

Package split (placeholders for Agent 6): `embodic_core`, `embodic_io`, `embodic_app`, `embodic_kicad`; the import rule
"core imports no UI/KiCad module" is enforced by a test (port notes §6.1).

### 4.2 Distribution channels

| Channel | Content | Who uses it | Status |
|---|---|---|---|
| Developer install | `pip install -e .[ui,dev]` in a venv from the repository | team, power user | not tested |
| Desktop bundle | PyInstaller one-folder build `embodic\embodic.exe` (Python + NumPy + UI toolkit inside) | user without Python setup | not tested |
| KiCad PCM package (route A) | zip with `metadata.json` (`runtime: "ipc"`) and the plugin folder: `plugin.json`, `main.py`, `requirements.txt` (kicad-python pin, NumPy), vendored pure-Python `embodic_core`, icon | KiCad users | layout per `kicad_plugin_evidence.md` §1/§3 (verified there); exact zip structure for IPC plugins `unresolved` → T6 |
| Exported files (route C) | `.kicad_pcb`, DXF, SVG, PDF, project JSON | everyone | — |

## 5. Installation on the user's Windows machine (draft walkthrough — not tested)

Destination folder: `%USERPROFILE%\Desktop\embodic` (placeholder; the actual account name is not written into project documents, code, UI, logs or exports).

1. Check Python: open *Command Prompt* → `py -3.11 --version` (or the installed 3.11+ version).
2. Create a virtual environment inside the project folder: `cd %USERPROFILE%\Desktop\embodic` → `py -3.11 -m venv .venv`
   → `.venv\Scripts\activate`.
3. Install: `python -m pip install --upgrade pip` → `pip install -e .[ui]` (adds `[dev]` for tests).
4. Run: `embodic` (standalone UI) or `embodic-cli compute project.json --out results.json`.
5. Self-check: `pytest` (with `[dev]`).
6. KiCad (Phase 2b): enable the API server in KiCad ▸ Preferences ▸ Plugins (Agent 5 [K6]); install the PCM zip (T6) or copy
   the plugin folder into `%USERPROFILE%\Documents\KiCad\9.0\plugins\<id>` (i.e. `C:\Users\<user>\Documents\…`) (path `inferred`); first start creates the
   plugin venv and installs the requirements (needs internet — `unresolved` behind a proxy).
7. Optional KiCad CLI DRC: `kicad-cli pcb drc --format json --exit-code-violations board.kicad_pcb` (documented for 9.0,
   not tested); `kicad-cli` location on Windows not verified.

## 6. Open questions

| # | Question | Who |
|---|---|---|
| D-1 | KiCad 9 bundled Python version (sets NumPy range and the core's syntax floor) | user via T1/T2 |
| D-2 | UI technology (Qt desktop vs Python-backed web) — decides PySide6/pyqtgraph vs pywebview/three.js | Agent 6 + user |
| D-3 | PDF report: reportlab or port of Xcoil's own writer | Agent 6 |
| D-4 | Licence of embodic (affects PCM official repository eligibility and LGPL/GPL considerations of bundled UI libraries) | user |
| D-5 | Offline installation need (wheel cache for the plugin venv and the desktop install) | user |

## Revision 2026-10-04 (defect fixes)

- Observation O-d (Agent 4): the Windows account name from the brief was removed from the install walkthrough (§5) and
  replaced by `%USERPROFILE%` / `C:\Users\<user>` placeholders.
