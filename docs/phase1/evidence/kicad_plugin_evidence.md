Prepared by: Agent 5 — Research & Evidence Specialist — model: claude-opus-5-5

# KiCad 9.x plugin routes — evidence (Windows focus)

Phase 1 draft, 2026-10-04. Sources: official KiCad pages only (dev-docs.kicad.org, docs.kicad.org,
kicad.org, pypi.org) read with WebFetch (12 fetches, 3 searches), plus a read-only inspection of the
MIT-licensed `kicad-python` 0.8.0 wheel downloaded from PyPI into Agent 5's scratchpad (not part of embodic).
WebFetch returns a summarised extract of each page; quotes below are as returned by that extract and should be
re-checked by Agent 3/6 against the live page before they become design decisions (status `verified` here
means "stated on the cited official page/file as read on 2026-10-04").
Direct `curl` to dev-docs.kicad.org / docs.kicad.org / gitlab.com was blocked by the egress proxy, so the
long single-page PCB Editor manual (docs.kicad.org/9.0/en/pcbnew/pcbnew.html) could not be read in full.

## 1. Summary table

| Topic | Route A: SWIG `pcbnew` ActionPlugin | Route B: IPC API (`kicad-python` / `kipy`) | Status |
|---|---|---|---|
| Status in 9.x | "deprecated as of KiCad 9.0 and will be removed in a future version"; removal planned "in KiCad 11.0" | First released in 9.0, "focused on a particular set of use cases", "actively developed" | verified [K1][K4] |
| Stability | "a raw binding layer rather than a true API, it is unstable and will generally change between KiCad major versions" | `kicad-python` classified "5 - Production/Stable" on PyPI; per-method version notes tie features to KiCad 9.0.3/9.0.5/9.0.8/10.0.x | verified [K1][K6][K7] |
| Editors | PCB editor (action plugins) | "KiCad 9 and 10 only support IPC API plugins in the PCB Editor" | verified [K1][K4] |
| Process model | In-process, KiCad's embedded Python | Plugin "launched in standalone processes"; socket path passed in environment variables; needs a running KiCad GUI ("not possible to use kicad-python … without KiCad running") | verified [K3][K4][K6] |
| Enable step | none documented | API server must be enabled in **Preferences > Plugins** | verified [K6] |
| Tracks / arcs / vias | yes (used by kimotor: `PCB_TRACK`, `PCB_ARC`, `PCB_VIA`) | `Track`, `ArcTrack`, `Via` classes; `Board.create_items`, `update_items`, `remove_items`, `begin_commit`/`push_commit`/`drop_commit` | A: inferred from kimotor (KiCad 6–8); B: verified in kipy 0.8.0 source [K7] |
| Zones | yes (kimotor `ZONE`, `ZONE_FILLER`) | `Zone` class, `get_zones()`, `refill_zones()` | A inferred; B verified [K7] |
| Footprints / pads | yes (kimotor `FootprintLoad`) | `FootprintInstance`, `Pad`, `get_footprints()`, `get_pads()`; creating new footprints/pads from scratch in 9.x | A inferred; B creation `unresolved` |
| Board stack-up read | API exists in KiCad C++; SWIG accessor name not verified | `Board.get_stackup()` → `BoardStackup`; `get_copper_layer_count()` "added 0.5.0 (with KiCad 9.0.5)" | A `unresolved`; B verified [K7] |
| Run DRC | not verified (kimotor commit "improved DRC" is not evidence of an API) | no DRC-run method found in `kipy/board.py` 0.8.0 (only DRC severity settings in `board_rules.py`) | `unresolved` for both |
| Plot/export | via SWIG plotters (not verified for 9.x) | 9.0 "has no support for plotting or exporting files" | A `unresolved`; B verified [K4] |
| Python interpreter (Windows) | KiCad's bundled Python (version for 9.x not found in official pages) | "On macOS and Windows, KiCad will continue to ship with its own Python interpreter, which will be used by the IPC system by default"; per-plugin virtual environment | A `unresolved` (version); B verified [K4] |
| Dependencies (numpy) | must be installed into KiCad's bundled Python (kimotor README shows the macOS route; Windows route not documented in sources read) | "a Python virtual environment will be created … and any declared dependencies will be installed"; venv at `${KICAD_CACHE_HOME}/python-environments/<plugin_identifier>`; kipy's validator: "missing requirements.txt, KiCad will not install any Python packages for your plugin" | A `unresolved`; B verified [K4][K8] |
| Packaging | PCM package, `plugins/` folder + `metadata.json` (`runtime: "swig"`) | `plugin.json` per schema `go.kicad.org/api/schemas/v1`; PCM `metadata.json` `runtime: "ipc"` (KiCad 9.0.1+) | verified [K4][K5] |
| Licence of the binding | `pcbnew` module is part of KiCad (GPL-3.0-or-later) | `kicad-python`: **MIT** | verified [K6][K9] |

## 2. Route A — SWIG `pcbnew` action plugins

- **Deprecation** (dev-docs "PCB Python Bindings", section "Deprecation notice"): deprecated as of 9.0, removal
  planned in 11.0 — https://dev-docs.kicad.org/en/apis-and-binding/pcbnew/ — `verified`.
- **Interface** (same page, section "'Action Plugin' Support" / "Typical Plugin Structure"): `defaults()`, `Run()`,
  properties `name`, `category`, `description`, optional `show_toolbar_button` (default False) and
  `icon_file_name` — `verified`. kimotor follows this pattern (`repo_survey.md` §2) — `verified`.
- **Search paths on Windows**: the extract of the same page listed `%KICAD_INSTALL_PATH%/share/kicad/scripting/plugins`
  and an `%APPDATA%`-based `kicad/scripting/plugins` path (the extract's wording "%APPDATA%/Roaming" looks garbled)
  — `unresolved` wording. The PCM 3rd-party location used by kimotor for 7.0 is
  `C:\Users\<USERNAME>\Documents\KiCad\7.0\3rdparty\plugins` (kimotor README) — `verified` for 7.0 only.
  For 9.0 the analogous folders `%USERPROFILE%\Documents\KiCad\9.0\scripting\plugins` and
  `…\9.0\3rdparty\plugins` are `inferred` by analogy, not verified.
- **Capabilities in 9.x**: class names used by kimotor (KiCad 6–8 era) are evidence that tracks, arcs, vias,
  zones, footprints, outline shapes and groups can be created through SWIG; whether all names are unchanged in 9.x
  is `unresolved` (the binding "will generally change between KiCad major versions").
- **Interpreter / numpy on Windows**: plugin runs inside KiCad's embedded interpreter; the user's separate
  Python 3.11+ is not used. The bundled Python version for KiCad 9.x on Windows was not found on official pages —
  `unresolved`. Installing numpy into the bundled interpreter on Windows is `unresolved` (test T1).
- **Licence implication**: KiCad source is "GNU General Public License (GPL) version 3 or greater"
  (https://www.kicad.org/about/licenses/) — `verified`. A SWIG plugin imports `pcbnew` into the KiCad process;
  whether that makes a distributed plugin a derivative work of KiCad is a legal question — `unresolved` (not legal
  advice). Practical constraint that *is* documented: packages with code in the official PCM repository "must be
  licensed under an open-source license compatible with the GNU GPL" (dev-docs "KiCad Addons") — `verified`.

## 3. Route B — IPC API with `kicad-python` (`import kipy`)

- **Scope in 9.x** (dev-docs "For Add-on Developers",
  https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/): supports KiCad 9.0 and up;
  "only supports communication with a running instance of the KiCad GUI"; "no support for plotting or exporting
  files"; no headless mode (added in 11); PCB Editor only in 9 and 10 — `verified`.
  The overview page (https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/, sections "Overall Design
  Principles", "Detailed information") describes Protocol Buffers over NNG and standalone plugin processes —
  `verified`.
- **Plugin location**: "The default directory for IPC plugins is `${KICAD_DOCUMENTS_HOME}/<version>/plugins`",
  Windows example root `C:\Users\<username>\Documents\KiCad` → `C:\Users\<username>\Documents\KiCad\9.0\plugins`
  (combination `inferred`). Plugins must provide `plugin.json` following `go.kicad.org/api/schemas/v1` — `verified`.
- **Interpreter and dependencies**: KiCad's own Python on Windows by default; per-plugin venv under
  `${KICAD_CACHE_HOME}/python-environments/<plugin_identifier>`; declared dependencies installed when the plugin
  is first loaded — `verified`. That `requirements.txt` is the declaration file is `verified` indirectly from
  kipy's packaging validator (`kipy/packaging/validate.py` lines 138–162 in the 0.8.0 wheel) which also warns if
  `kicad-python` is missing from it. A preference to select a different interpreter is mentioned but its name
  was not found — `unresolved`.
- **External interpreter**: because the API is a socket protocol, a script run from the user's own Python 3.11+
  with `kicad-python` installed can talk to a running KiCad (PyPI page: requires a running KiCad, API server
  enabled) — `inferred`; the Windows socket discovery for a script *not* launched by KiCad is `unresolved` (T3).
- **`kicad-python` facts** (https://pypi.org/project/kicad-python/ and wheel METADATA): latest 0.8.0 (2026-08-30),
  License-Expression MIT, Requires-Python ≥3.9, requires `protobuf>=5.29,<6`, `pynng>=0.9,<0.10`,
  `jsonschema>=4.23,<5` — `verified`. 0.8.0 is generated against `KICAD_API_VERSION = "10.0.6…"`
  (`kipy/kicad_api_version.py`); version notes inside `kipy/board.py`: 0.4.0 ↔ KiCad 9.0.3, 0.5.0 ↔ 9.0.5,
  0.6.0 ↔ 9.0.8, 0.7.0 ↔ 10.0.0/10.0.1, 0.8.0 ↔ 10.0.6/11.0 — `verified`. Which kipy version to pin for the user's
  exact 9.0.x release is `unresolved` (use `KiCad.check_version()` / `get_version()`, both present in
  `kipy/kicad.py`).
- **Board API (kipy 0.8.0, `kipy/board.py`)**: `save` (584), `save_as`, `revert` (603), `begin_commit` (609),
  `push_commit` (624), `drop_commit` (633), `create_items` (640), `get_tracks` (782), `get_vias` (791), `get_pads`
  (795), `get_footprints` (800), `get_shapes` (807), `get_zones` (856), `update_items` (885), `remove_items` (912),
  `get_stackup` (1124), `refill_zones` (1417); classes in `kipy/board_types.py`: `Track` (146), `ArcTrack` (229),
  `Pad` (1589), `Via` (1673), `FootprintInstance` (2065), `Zone` (2302) — `verified` (line numbers in the 0.8.0
  wheel). Methods without a version note are `inferred` to exist since ≤0.3.0 and hence in KiCad 9.0.x; to be
  confirmed by T2.
- **Licence implication**: `kicad-python` is MIT and talks to KiCad over IPC; embodic code calling it is not
  linked into KiCad's process (inferred). If embodic is ever published in the official PCM repository its licence
  must still be GPL-compatible (MIT, BSD, Apache-2.0 for GPL-3 are commonly regarded as compatible — inferred).

## 4. Unresolved items and proposed smoke tests (to be run by the user on Windows + KiCad 9.x)

| ID | Question | Proposed test (≈20 lines each; Phase 2 only — not implemented here) |
|---|---|---|
| T1 | SWIG: plugin folder, bundled Python version, numpy availability, 9.x class names | Minimal ActionPlugin whose `Run()` writes to a text file: `sys.version`, `sys.executable`, `pcbnew.Version()`, `__file__`; tries `import numpy`; adds one `PCB_TRACK`, one `PCB_ARC`, one `PCB_VIA` on F.Cu/B.Cu of an empty board; tries the stack-up accessor; calls `pcbnew.Refresh()`. Place in each candidate folder, use "Refresh Plugins", record where it appears. |
| T2 | IPC: enable API, venv creation, `requirements.txt` with numpy, create track/arc/via/zone in one commit, read stack-up and copper-layer count, check for any DRC entry point | `plugin.json` + `main.py` + `requirements.txt` (`kicad-python==<pinned>`, `numpy`) in `Documents\KiCad\9.0\plugins\<id>\`; log `KiCad().get_version()`, `board.get_stackup()`, `create_items([...])` inside `begin_commit/push_commit`; confirm venv path under `KICAD_CACHE_HOME`. |
| T3 | External interpreter (user's Python 3.11+) controlling KiCad 9.x | `pip install kicad-python==<pinned>` in a normal venv, run a script with KiCad open and API enabled; record whether it connects without environment variables. |
| T4 | Which `kicad-python` version matches the user's 9.0.x | Run T3 with 0.4.0, 0.5.0, 0.6.0; record `check_version()` result. |
| T5 | DRC from a plugin | Search 9.x for an IPC/SWIG DRC call; fallback is `kicad-cli pcb drc` (CLI exists in 9.0 docs: https://docs.kicad.org/9.0/en/cli/cli.html — page title seen in search results only, content not read → `unresolved`). |

## 5. Implications for embodic (for Agents 3 and 6; `inferred` unless noted)

1. Keep the calculation and geometry engines as a pure-Python package with no KiCad import, runnable on the
   user's Python 3.11+ (brief §1) — `assumption` (design choice).
2. Preferred KiCad adapter: IPC API via `kicad-python` (not deprecated, MIT, separate process, PCM `runtime: "ipc"`),
   PCB editor only in 9.x — `inferred` from §3.
3. SWIG adapter only as a fallback for features missing from the 9.x IPC API (possibly DRC/plot), knowing it is
   deprecated and planned for removal in 11.0 — `inferred` from §2.
4. Dependency weight matters: an IPC plugin's dependencies are pip-installed into a per-plugin venv on first load
   (needs network or a local wheel cache — `unresolved`), so the engine should avoid heavy native dependencies
   beyond NumPy unless T2 shows they install cleanly — `inferred`.
5. All geometry passed to KiCad must use KiCad internal units (nanometres in kipy, `StrokeAttributes.width` doc) —
   `verified` for kipy units statement (docs.kicad.org/kicad-python), SWIG units `unresolved`.

## 6. Source list (verified URLs, accessed 2026-10-04)

- [K1] KiCad dev-docs, "PCB Python Bindings" — https://dev-docs.kicad.org/en/apis-and-binding/pcbnew/ (sections: Deprecation notice; Introduction; "Action Plugin" Support; Typical Plugin Structure)
- [K3] same page, "'Action Plugin' Support"
- [K4] KiCad dev-docs, "IPC API" — https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/ and "For Add-on Developers" — https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/
- [K5] KiCad dev-docs, "KiCad Addons" (PCM packaging) — https://dev-docs.kicad.org/en/addons/
- [K6] PyPI, kicad-python — https://pypi.org/project/kicad-python/
- [K7] kicad-python 0.8.0 wheel (PyPI), `kipy/board.py`, `kipy/board_types.py`, `kipy/kicad.py`, `kipy/kicad_api_version.py`; online docs https://docs.kicad.org/kicad-python/board.html (the online page extract did not show the commit/create methods; the wheel source does)
- [K8] kicad-python 0.8.0 wheel, `kipy/packaging/validate.py` lines 138–162
- [K9] KiCad licences — https://www.kicad.org/about/licenses/
- Not useful: https://gitlab.com/kicad/packaging/kicad-win-builder/-/work_items/139 (refers to KiCad 6.0 / Python 3.9 only)
