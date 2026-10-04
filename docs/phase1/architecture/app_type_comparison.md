Prepared by: Agent 6 — Software Architecture Specialist — model: claude-opus-5-5

# embodic — Application-type comparison and proposal (Phase 1 draft, 2026-10-04)

**This is a proposal for the user to approve before Phase 2** (BRIEF §1: "App type … is to be PROPOSED in Phase 1 and
approved by the user"). It is recorded as ADR-0005 with status *Proposed*. Status labels per BRIEF §3. Sources are
listed in §9 with keys [S1]…[S20]; licence and Windows-support facts come from official pages or from the PyPI
metadata published by each project (accessed 2026-10-04).

## 1. What does not depend on the choice

These points hold for every option below and are decided elsewhere (coordinator constraints / ADR-0001…0004):

- The calculation engine and the geometry engine are pure Python packages (BRIEF §1) with no UI or KiCad imports
  (ADR-0001). Engineering results are therefore **identical** across options — "engineering calculations" is not a
  differentiator (the task statement says so; `inferred` from ADR-0001).
- A `.kicad_pcb` file writer works without KiCad running and is the baseline KiCad route (ADR-0004, REQ-K-01).
- The KiCad 9.x plugin uses the IPC API (`kicad-python`, MIT) in a separate process with KiCad's bundled Python and a
  per-plugin virtual environment whose dependencies are pip-installed on first load (A5-KI §3, `verified`); the SWIG
  route is deprecated in 9.0 with removal planned for 11.0 (A5-KI §2, `verified`).
- The user runs Windows with Python 3.11+ (BRIEF §1) and KiCad 9.x.

Hence the real question is: **which standalone front-end, and how does it relate to the KiCad plugin?**

## 2. Options

| Option | Description |
|---|---|
| **A. Python desktop app** | Native window, same process as the engine. Candidate toolkits: A1 PySide6 (Qt for Python), A2 wxPython, A3 Tkinter, A4 Dear PyGui. |
| **B. Python-backed web app (local only)** | Engine behind a local HTTP server bound to 127.0.0.1; UI in the user's browser. B1 FastAPI (or Flask) + hand-written HTML/TypeScript/SVG front-end; B2 NiceGUI (Python-defined UI on FastAPI/Vue); B3 Streamlit. Optional native window via pywebview. |
| **C. Hybrid** | Python core + KiCad 9 IPC plugin as one front-end + one standalone front-end (C-A = with a desktop UI from A, C-B = with a web UI from B). C is not an alternative to A/B but the **structure** in which one of them is used. |

## 3. Evidence: licence, Windows support, footprint

Wheel sizes are those of the latest Windows x64 wheel on PyPI for CPython 3.11 (or abi3/universal) on 2026-10-04;
they indicate download weight, not installed size.

| Candidate | Licence (official statement) | Windows support evidence | Python | Win x64 wheel | Notes | Status |
|---|---|---|---|---|---|---|
| PySide6 6.11.2 | "LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only"; "available under both Open Source (LGPLv3 or GPLv2 or GPLv3) and commercial license" [S1] | PyPI classifiers "Operating System :: Microsoft :: Windows"; `win_amd64` and `win_arm64` abi3 wheels [S1] | ≥ 3.10, < 3.15 | PySide6-Essentials 76.9 MB (+ shiboken6 1.2 MB); full PySide6 adds PySide6-Addons 168.2 MB [S1] | LGPL obligations (dynamic linking keeps app code non-LGPL; user must be able to replace/relink Qt; licence text + notice; Qt source or written offer) [S2] | verified |
| wxPython 4.3.1 | "wxWindows Library License" [S3]; = LGPL "with an exception stating that derived works in binary form may be distributed on the user's own terms" [S4] | Classifiers Windows 7/10/11; `cp311-win_amd64` wheel [S3] | ≥ 3.10 | 18.5 MB [S3] | A KiCad SWIG plugin can use wx: kimotor imports `wx` (kimotor_action.py l.11) and documents only a NumPy install (README l.11–19) → wx is available in KiCad's embedded Python (`inferred`); availability inside an **IPC** plugin venv `unresolved` | verified (licence, wheels) |
| Tkinter (stdlib) | Part of CPython (PSF licence) | "available … on Windows systems"; "an optional module"; "the official Python binary release bundles Tcl/Tk 8.6" [S5] | stdlib | 0 (bundled) | Whether KiCad's bundled Python ships tkinter: `unresolved` | verified (doc statements) |
| Dear PyGui 2.3.1 | MIT [S6] | Classifier "Windows 10"; `cp311-win_amd64` wheel [S6] | ≥ 3.8 | 1.9 MB [S6] | Immediate-mode GPU UI | verified |
| FastAPI 0.142.2 / Flask 3.1.3 + uvicorn 0.54.0 | MIT / BSD-3-Clause / BSD-3-Clause [S7] | Pure-Python wheels ("OS Independent"); FastAPI pulls pydantic + pydantic-core (native, `cp311-win_amd64` 2.1 MB) [S7] | ≥ 3.10 / ≥ 3.9 | ≈ 0.1 MB each + pydantic-core 2.1 MB | Front-end in HTML/TS/SVG to be written separately | verified |
| NiceGUI 3.17.1 | MIT [S8] | "OS Independent"; "acts as webserver (accessed by the browser) or in native mode (eg. desktop window)" [S8] | ≥ 3.10 | 8.6 MB + ≈ 25 direct dependencies (aiohttp, orjson, uvicorn[standard], watchfiles, python-socketio, …) [S8] | — | verified |
| Streamlit 1.65.0 | Apache-2.0 [S9] | PyPI metadata (no OS classifier) [S9] | ≥ 3.10 | — | Script re-run execution model | verified (licence) |
| pywebview 6.2.1 (optional native window for B) | BSD-3-Clause [S10] | Windows needs pythonnet (".NET 4.0" or newer) and the WebView2 Runtime for Chromium rendering [S11] | ≥ 3.8 | — | Extra runtime prerequisite on Windows | verified (doc statement) |
| PyInstaller 6.22.3 (bundling, any option) | GPL-2.0 with an exception: bundles "can be shipped with whatever license you want, as long as it complies with the licenses of your dependencies" [S12] | Windows wheels; classifiers Python 3.10–3.15 [S12] | ≥ 3.8, < 3.16 | — | Build tool only | verified |
| NumPy (engine) | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 [S13] | Windows wheels | **2.5.x requires ≥ 3.12**; 2.4.6 is the newest with `cp311-win_amd64` (12.6 MB) [S13] | — | Pin per Python version (REQ-N-05) | verified |
| kicad-python 0.8.0 (plugin) | MIT [S14] | Pure Python; needs protobuf ≥ 5.29 < 6, pynng 0.9, jsonschema ≥ 4.23 < 5 [S14] | ≥ 3.9 | 0.2 MB | Version ↔ KiCad 9.0.x mapping `unresolved` (A5-KI T4) | verified |

Test-tool facts used in §4: pytest-qt 4.5.0 MIT [S15]; Playwright 1.63.0 Apache-2.0, Windows wheel 38.6 MB plus browser
download [S15]; axe-core 4.13.0 MPL-2.0 (npm) [S16]; three.js 0.186.1 MIT (npm) [S16] — `verified` (registry metadata).

## 4. Comparison

Ratings: ++ strong, + adequate, o weak/needs work, − poor. Each rating is a judgement (`inferred`) from the evidence in §3
and the reasoning given; nothing was prototyped in Phase 1 (`not tested`).

| Criterion | A1 PySide6 | A2 wxPython | A3 Tkinter | A4 Dear PyGui | B1 FastAPI + HTML/TS/SVG | B2 NiceGUI | B3 Streamlit |
|---|---|---|---|---|---|---|---|
| 2-D vector coil rendering, zoom/pan (≈10⁴ lines/arcs with width) | ++ retained scene graph (QGraphicsView), true arcs and pen widths, vector export via QSvgGenerator (`inferred`, not benchmarked) | + `wx.GraphicsContext` drawing; no built-in retained scene graph comparable to Qt's in core wx (`inferred`) | o Canvas items scale coordinates but not line widths (`inferred`); slow with many items (`unresolved`) | + GPU drawing fast; stroke styling and arc primitives limited (`inferred`) | ++ SVG in the browser — Xcoil v3 already renders and zooms its coil as SVG via `viewBox` (XC `ui.js` l.163, 274–290, 377, `verified`) | + same browser SVG, but custom JS component needed for efficient zoom/pan (`inferred`) | − no persistent interactive canvas without custom components (`inferred`) |
| Optional 3-D view | + Qt Quick 3D / OpenGL widgets (in PySide6-Addons, +168 MB) (`inferred`) | o OpenGL canvas, more manual work | − | + 3-D via drawing API only | ++ WebGL; Xcoil uses three.js r128 (XC `view3d.js` l.1, `verified`) | + same via custom element | o |
| Interactive controls (forms, tables, validation feedback) | ++ | ++ native widgets | + | + | ++ | ++ | + (re-runs script on each change) |
| Engineering calculations | identical (Python core) | identical | identical | identical | identical | identical | identical |
| Install on Windows for this user (Python 3.11+) | + `pip install embodic[desktop]` (≈ 78 MB download); PyInstaller one-folder bundle feasible | + `pip install`, 18.5 MB | ++ nothing extra (if tkinter installed) | ++ 1.9 MB | + `pip install`; app starts a local server and opens the browser; port selection, possible firewall prompt (`unresolved`) | o many native deps (§3) | o |
| Packaged distribution (no Python needed) | + PyInstaller one-folder (Qt DLLs replaceable → LGPL relink condition can be met, `inferred` from [S2]); large bundle | + | + | + | + PyInstaller bundle that starts server + browser; or pywebview window (needs WebView2 + pythonnet [S11]) | o | o |
| Maintenance / extensibility | ++ one language (Python); mature, stable APIs (`inferred`) | + one language; smaller ecosystem for custom drawing (`inferred`) | o limited widgets/theming | o immediate-mode paradigm unusual for form-heavy engineering tools (`inferred`) | o two languages (Python + TypeScript/HTML/CSS) and an HTTP API contract to version | + Python only, but large dependency surface and framework-driven upgrades (§3) | o app structure dictated by re-run model |
| Fit to user workflow (KiCad user, wants plugin, Python 3.11+) | + separate window next to KiCad; plugin stays UI-less (§5) | + same toolkit family as KiCad itself (`inferred`), but SWIG-era benefit lost with IPC | + | o | + browser tab next to KiCad; a plugin process could even host the server (§5) | + | o |
| Headless testability | + pytest-qt [S15] with an offscreen Qt platform (`inferred`, not tested) | o fewer test tools (`inferred`) | o | o | ++ API tests without browser + Playwright headless [S15] | + | o |
| Accessibility (REQ-N-11…16) | + Qt implements accessibility for its own widgets; custom views need a `QAccessibleInterface` [S17]; automated audits mostly manual (Narrator, contrast script) (`inferred`) | + native widgets inherit platform accessibility (`inferred`) | o (`unresolved`) | − immediate-mode UIs generally expose no accessibility tree (`inferred`, not verified for 2.3.1) | ++ WCAG is defined for web content [S18]; axe-core automated audits [S16] | + (generated DOM; audit possible) | o |
| Security surface | ++ no network listener | ++ | ++ | ++ | o local HTTP server must bind 127.0.0.1, check Origin/Host and use a per-session token (DNS-rebinding/CSRF, `inferred`) | o same | o same |
| Licensing for a possibly closed or GPL-compatible embodic | + LGPL obligations manageable (dynamic linking, notices, source offer) [S2]; also compatible with GPL-3 distribution (`inferred`) | ++ wxWindows licence binary exception [S4] | ++ | ++ MIT | ++ permissive stack [S7] | ++ MIT (+ deps to audit) | ++ Apache-2.0 |
| Footprint if the UI ever had to run **inside** KiCad's plugin venv | − PySide6-Essentials 77 MB pip-installed on first plugin load | o 18.5 MB | ? tkinter presence `unresolved` | + 1.9 MB | + small (FastAPI/uvicorn/pydantic-core ≈ 3 MB) | o | o |

### 4.1 Key differentiators (reasoning)

1. **Rendering quality is not the deciding factor** between A1 and B1: both render the required 2-D vector geometry well
   (`inferred`); B1 has an existence proof in Xcoil (`verified` as above), A1 relies on a mature scene graph (`inferred`).
   A3/A4/B3 are weaker for a zoomable, width-accurate copper view.
2. **Maintainability favours a single language.** The user asked for readable, maintainable code (task statement). A1
   keeps engine, UI and plugin in Python; B1 adds a TypeScript/HTML/CSS front-end and an HTTP contract that must be
   versioned in step with the engine (`inferred`). B2 avoids the second language but brings ≈ 25 direct dependencies (§3)
   and framework-driven upgrades.
3. **Accessibility evidence favours the browser** (WCAG is web-native, axe-core automates checks); A1 can meet the same
   criteria with Qt's built-in widget accessibility [S17] plus a contrast script and manual Narrator checks, at the cost of
   less automation (`inferred`). This is the main argument *for* B1.
4. **KiCad integration is not a differentiator if the plugin stays UI-less** (proposed in §5). It only becomes one if
   the full UI must run inside KiCad's plugin venv: then B1 is light (≈ 3 MB) and A1 heavy (77 MB first-load install).
   Running a Python front-end in the user's own Python and talking to KiCad as an IPC client (T3) avoids this for both.
5. **Security and robustness favour A**: no listener, no port, no browser variance (`inferred`).
6. **Licensing**: all options can satisfy a GPL-compatible or proprietary licence; A1 carries the most obligations
   (LGPL notice, relinkable Qt, source offer [S2]) — manageable but must be planned (ADR-0008).

## 5. How the KiCad plugin fits (applies to C-A and C-B)

Proposed shape of the plugin (details in ADR-0004 and architecture_draft.md §9):

```
KiCad 9.x PCB editor ──(IPC, local socket)──► embodic_kicad_plugin  (KiCad's bundled Python, per-plugin venv:
                                               kicad-python + embodic core + NumPy, no GUI toolkit)
   action 1 "Apply embodic project"  : read <board>.embodic.json (or the project last saved by the standalone app),
                                       compute with embodic core, replace previously placed embodic items in ONE commit
   action 2 "Import stack-up"        : read Board.get_stackup() → write it for the standalone app
   action 3 "Open embodic" (could)   : start the standalone app (user's Python 3.11+) as a child process that inherits
                                       KiCad's IPC environment variables and connects as an IPC client (needs T3)
Standalone embodic (user's Python) ──(optional, IPC client, T3)──► KiCad
Standalone embodic ──► .kicad_pcb file (always available, no KiCad needed)
```

Reasoning (`inferred`): keeping GUI toolkits out of KiCad's per-plugin venv minimises first-load installation risk
(offline install is `unresolved`, A5-GAP G13) and decouples the front-end decision from KiCad's Python version (also
`unresolved`). Whether a plugin can show any dialog without a toolkit is `unresolved` → error feedback via a log file and,
if T2 finds a mechanism, a KiCad-side message.

## 6. Recommendation (proposal for user approval)

**Proposed: Option C-A — hybrid architecture with a PySide6 (Qt) desktop application as the standalone front-end,
a UI-less KiCad 9 IPC plugin as the second front-end, and the `.kicad_pcb` file writer as the always-available
fallback.** Status: `assumption` (design choice) until the user approves; supporting arguments are `inferred` from §3–§5.

Why (not development ease alone):
1. One language end-to-end (engine, UI, plugin) → best fit for the maintainability requirement (REQ-N-08/09).
2. No network listener, works offline (REQ-N-17), no browser variance, in-process calls → simplest robust runtime for a
   single-user engineering tool on Windows.
3. Rendering and interaction needs (2-D vector, zoom/pan, forms, tables) are met by a mature retained-mode toolkit;
   optional 3-D is possible later (PySide6-Addons) without changing the core.
4. Licence obligations (LGPL-3) are known and manageable [S2]; Qt is also available commercially if ever needed [S1].
5. The plugin decision is independent (§5), so the front-end can be replaced later (e.g. by B1) without touching the
   engine or the plugin (ADR-0001).

**Second choice: C-B1** (local web UI: FastAPI + hand-written TypeScript/SVG front-end) — choose this instead if the
user values browser-native accessibility tooling, the visual continuity with Xcoil's HTML/SVG UI, or wants the full UI
to run from inside KiCad's plugin process. **Not recommended**: A3 Tkinter (rendering/theming/accessibility limits),
A4 Dear PyGui (accessibility), B3 Streamlit (execution model unsuited to an interactive vector canvas), B2 NiceGUI
(dependency surface vs. benefit). A2 wxPython is a credible alternative to A1 with a lighter licence, but its advantage
— KiCad's SWIG Python ships wx (`inferred`) — disappears with the IPC route, and its custom-drawing ecosystem is smaller
(`inferred`).

## 7. Limitations and risks of the recommendation

| # | Limitation / risk | Mitigation | Status |
|---|---|---|---|
| L1 | Download/bundle size (PySide6-Essentials ≈ 77 MB wheel; bundle larger) | Depend on `PySide6-Essentials` only (not the `PySide6` meta-package that adds 168 MB Addons); 3-D view optional extra | verified (sizes) / assumption (mitigation) |
| L2 | LGPL compliance work: licence text, notice in About box, relinkable Qt DLLs, source offer | PyInstaller **one-folder** mode (DLLs remain separate files); THIRD_PARTY_LICENSES; checklist in release process | inferred from [S2] |
| L3 | Automated accessibility testing is weaker than axe-core in a browser | Contrast computed from theme tokens in CI (AX-01), keyboard-only scripted test with pytest-qt (AX-02), widget-size check (AX-04), Narrator checklist (AX-06) | inferred |
| L4 | Custom geometry view items are not exposed to screen readers by default [S17] | Provide an accessible text alternative: coil/phase table and layer table always available next to the drawing (REQ-F-13) | inferred |
| L5 | Performance of CPython for DRC/EMF loops (REQ-N-01) — same risk for every option | Vectorised NumPy kernels, symmetry reuse, stage caching (architecture_draft.md §11) | inferred; to be measured (PF-01) |
| L6 | The full UI cannot run inside KiCad without installing Qt into KiCad's venv | UI-less plugin; launcher action via T3; file-based exchange as fallback | unresolved (T2/T3) |
| L7 | Users without Python need the bundle; bundle signing/SmartScreen behaviour on Windows not investigated | Phase 2 packaging task; document "pip" route first | unresolved |
| L8 | No prototype was built in Phase 1 | Phase 2 starts with a 2-day spike: render the default layout (≈ 10⁴ primitives) in QGraphicsView and measure frame time and memory | not tested |
| L9 | No phone/tablet use: Agent 1 analysed Xcoil's tablet and phone layouts (`docs/phase1/design/ux_analysis.md` §5); a desktop app targets windows ≥ 1280 × 720 only | If mobile viewing matters to the user, that is an argument for C-B1 | inferred |
| L10 | Agent 3 measured a ≈ 45× CPython slowdown on the DRC kernel vs V8 (`docs/phase1/software/calculation_flow_and_port_notes.md` §4) — applies to every option because the engine is Python | NumPy kernels, staged recompute, worker thread (architecture_draft.md §11) | verified (measurement by Agent 3) / inferred (mitigation) |

## 8. Decisions requested from the user

1. Approve C-A (PySide6 desktop + UI-less IPC plugin + `.kicad_pcb` writer), or choose C-B1 / another option.
2. Intended licence of embodic (proprietary, MIT/BSD/Apache, GPL-3)? It affects PCM distribution (REQ-K-13) and the
   dependency allow-list (ADR-0008).
3. Is a no-Python Windows bundle required in Phase 2, or is `pip install` into the existing Python 3.11+ sufficient?
4. Should the full UI be launchable from inside KiCad (REQ-K-10, depends on T3), or is "apply project from file" enough?

## 9. Sources (accessed 2026-10-04)

- [S1] PySide6 / PySide6-Essentials / PySide6-Addons on PyPI — https://pypi.org/project/PySide6/ (JSON metadata `https://pypi.org/pypi/PySide6/json`: license_expression, requires_python, classifiers, wheel files and sizes; description section "Licensing")
- [S2] The Qt Company, "Obligations of the GPL and LGPL" — https://www.qt.io/licensing/open-source-lgpl-obligations (dynamic vs static linking; re-link right; source delivery; notice)
- [S3] wxPython on PyPI — https://pypi.org/project/wxPython/ (4.3.1, licence field, Windows classifiers, wheels)
- [S4] wxWidgets licence page — https://www.wxwidgets.org/about/licence/
- [S5] Python docs, `tkinter` — https://docs.python.org/3/library/tkinter.html (introduction; threading model)
- [S6] Dear PyGui on PyPI — https://pypi.org/project/dearpygui/
- [S7] FastAPI https://pypi.org/project/fastapi/ ; Flask https://pypi.org/project/Flask/ ; uvicorn https://pypi.org/project/uvicorn/ ; pydantic-core https://pypi.org/project/pydantic-core/
- [S8] NiceGUI on PyPI — https://pypi.org/project/nicegui/ (features list, requires_dist)
- [S9] Streamlit on PyPI — https://pypi.org/project/streamlit/
- [S10] pywebview on PyPI — https://pypi.org/project/pywebview/
- [S11] pywebview installation guide — https://pywebview.flowrl.com/guide/installation.html (Windows: pythonnet, WebView2 Runtime)
- [S12] PyInstaller licence — https://pyinstaller.org/en/stable/license.html ; PyPI https://pypi.org/project/pyinstaller/
- [S13] NumPy on PyPI — https://pypi.org/project/numpy/ (release files: 2.4.6 `cp311-win_amd64`; 2.5.0+ requires_python ≥ 3.12)
- [S14] kicad-python on PyPI — https://pypi.org/project/kicad-python/ ; A5-KI §3
- [S15] pytest-qt https://pypi.org/project/pytest-qt/ ; Playwright https://pypi.org/project/playwright/
- [S16] npm registry: axe-core https://registry.npmjs.org/axe-core/latest ; three https://registry.npmjs.org/three/latest
- [S17] Qt 6 docs, "Accessibility for QWidget Applications" — https://doc.qt.io/qt-6/accessible-qwidget.html
- [S18] W3C WCAG 2.2 — https://www.w3.org/TR/WCAG22/
- [S19] Xcoil v3 reference UI `/home/claude/serpentine/src/ui.js` l.163, 274–290, 377; `view3d.js` l.1 (read-only)
- [S20] kimotor (GPL-2.0, reference only) `/home/claude/embodic-ref/kimotor/kimotor_action.py` l.6, l.11; `README.md` l.11–19

Pages that did not yield the needed statement (not used as evidence): https://doc.qt.io/qtforpython-6/licenses.html
(navigation only in the fetched extract); https://doc.qt.io/qt-6/accessible.html (overview only);
https://dev-docs.kicad.org/en/apis-and-binding/pcbnew/ (no mention of wxPython).
