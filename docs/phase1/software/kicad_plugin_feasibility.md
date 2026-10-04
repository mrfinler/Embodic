Prepared by: Agent 3 — Senior Software Engineer — model: claude-opus-5-5

# KiCad 9.x plugin — engineering feasibility (Phase 1 draft, 2026-10-04)

Builds on Agent 5's `docs/phase1/evidence/kicad_plugin_evidence.md` (cited as **[A5 §n]**; its source list K1–K9). I did
not run or install KiCad. Additional pages I read on 2026-10-04 with WebFetch (summarised extracts — re-check before a
decision): KiCad 9.0 CLI manual https://docs.kicad.org/9.0/en/cli/cli.html; IPC "For Add-on Developers"
https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/; board file format
https://dev-docs.kicad.org/en/file-formats/sexpr-pcb/ and https://dev-docs.kicad.org/en/file-formats/sexpr-intro/; PyPI JSON
API for package metadata.

**Route labels in this file** (as in my task): **A = IPC API plugin with `kicad-python` (`kipy`)**, **B = legacy SWIG
`pcbnew` action plugin**, **C = no plugin, file export only** (`.kicad_pcb` writer as in Xcoil v3, optionally plus
`kicad-cli`). Note: Agent 5 uses A = SWIG and B = IPC.

## 1. Requirement and constraints

- User: Windows, KiCad 9.x, separate Python 3.11+ (brief §1). Engines must be Python and UI-agnostic (decision D-004,
  `docs/decision_log.md`).
- The tool must produce coil copper on several layers: tracks and arcs with width, through vias (centre, transfer,
  terminal), terminal pads, board outline (Edge.Cuts) with cut-out and holes; optionally zones and the stack-up.

## 2. Comparison

| Criterion | A — IPC API (`kipy`) | B — SWIG action plugin | C — file export (+ `kicad-cli`) |
|---|---|---|---|
| Status in 9.x | first released in 9.0, actively developed [A5 §1, K4] — verified (A5) | deprecated in 9.0, removal planned in 11.0 [A5 §2, K1] — verified (A5) | file format is the product's own; Xcoil writes version 20221018 (KiCad 7 era, `engine.js` l.2881) — verified (code) |
| Tracks / arcs / vias on a live board | `Track`, `ArcTrack`, `Via`, `Board.create_items` inside `begin_commit`/`push_commit` (kipy 0.8.0) [A5 §3] — verified (A5, wheel source); presence in kipy versions matching 9.0.x `inferred` (T2) | `PCB_TRACK`, `PCB_ARC`, `PCB_VIA` used by kimotor on KiCad 6–8 [A5 §2] — `inferred` for 9.x | not live: items are written to a file (`segment`, `arc` start/mid/end, `via`) — verified (code `exportKicad` l.2877–2929; syntax matches the format page extract) |
| Zones | `Zone`, `get_zones`, `refill_zones` [A5 §3] — verified (A5) | `ZONE`, `ZONE_FILLER` (kimotor) — inferred | possible in the file (`zone`); Xcoil writes none — verified (code) |
| Pads / footprints | reading verified; **creating** footprints/pads from scratch in 9.x `unresolved` [A5 §1] | `FootprintLoad` (kimotor) — inferred | inline `footprint` with `pad` (thru_hole/smd, circle/rect/oval) — verified (code l.2910–2916) |
| Board outline (Edge.Cuts) | `get_shapes` verified; creating graphic shapes `unresolved` (include in T2) | `PCB_SHAPE` (kimotor) — inferred | `gr_line`, `gr_arc`, `gr_circle` — verified (code l.2917–2926) |
| Stack-up | read: `Board.get_stackup()`, copper layer count (0.5.0 ↔ 9.0.5) [A5 §3] — verified; write `unresolved` | accessor name `unresolved` [A5 §1] | file `setup`/stack-up section possible; Xcoil writes only `(setup (pad_to_mask_clearance 0))` — verified (code l.2885); stack-up syntax to be confirmed (`unresolved`) |
| DRC | no DRC call in kipy 0.8.0 [A5 §1] | `unresolved` | `kicad-cli pcb drc --format json --exit-code-violations … INPUT_FILE` (formats `report` or `json`) is documented in the 9.0 CLI manual (exit code 5 when violations exist) — verified (doc extract), not tested |
| Undo / atomic update | commit API (begin/push/drop) [A5 §3] — verified | not documented in sources read — `unresolved` | n/a (new file; user opens or merges) |
| Needs KiCad running | yes, PCB editor open, API enabled in Preferences ▸ Plugins [A5 §1, K6] | yes (in-process) | no (KiCad only to open the file / run the CLI) |
| Python on Windows | KiCad's bundled interpreter by default, per-plugin venv under `${KICAD_CACHE_HOME}/python-environments/<id>`, dependencies installed on first load [A5 §3, K4] — verified; bundled version for 9.x `unresolved` | KiCad's embedded interpreter, no venv; installing NumPy into it `unresolved` (T1) | user's own Python 3.11+, any dependency — verified (brief) |
| Dependencies | `requirements.txt` (kicad-python pinned + NumPy); needs network or a wheel cache at first load (`unresolved`); kicad-python 0.4.0–0.8.0 need `protobuf>=5.29,<6`, `pynng` 0.8.x (≤0.5.0) or 0.9.x (≥0.6.0), `jsonschema` (≥0.7.0), `typing_extensions` (py < 3.13) — verified (PyPI JSON, 2026-10-04); pynng 0.9.0 ships cp311 win_amd64 wheels — verified (PyPI file list) | NumPy into KiCad's Python (kimotor needs it) — `unresolved` | none imposed by KiCad |
| Packaging | PCM zip with `metadata.json` (`runtime: "ipc"`, KiCad 9.0.1+) and `plugin.json` per schema `go.kicad.org/api/schemas/v1` [A5 §1, K5] — verified (A5); default IPC plugin directory `${KICAD_DOCUMENTS_HOME}/<version>/plugins`, Windows root typically `C:\Users\<username>\Documents\KiCad` — verified (doc extract); combined path `…\Documents\KiCad\9.0\plugins` — `inferred` | PCM zip, `plugins/` folder, `runtime: "swig"`; 9.0 folders `…\Documents\KiCad\9.0\scripting\plugins` / `…\3rdparty\plugins` — `inferred` [A5 §2] | standard Python packaging (wheel, PyInstaller), no KiCad packaging |
| UI | plugin is a separate process ("launched in standalone processes" [A5 §1]) → it can open the embodic window itself (`inferred`) | in-process wxPython dialogs (kimotor) — verified (kimotor source, A5) | standalone app only |
| Testability without KiCad | mapping `Board → item specs` fully unit-testable; kipy is a pure-Python package (wheel) → importable offline (`inferred`, check in Phase 2); live calls behind a small protocol with a fake implementation; integration tests need KiCad | `pcbnew` exists only inside KiCad's Python → mocks only (`inferred`) | fully testable offline: golden text, parse-back to numbers, optional `kicad-cli` DRC where KiCad is installed |
| Maintenance risk | medium: API grows per 9.0.x/10.x release, kipy version must match the KiCad version (`KiCad.check_version()` exists) [A5 §3] | **high**: removal planned in 11.0 | medium: file format evolves with major versions (`version` token = YYYYMMDD date [format page]); KiCad 9 layer ordinals vs Xcoil's 0…31 numbering `unresolved` (format pages read do not state it) |
| Licence | kicad-python **MIT** [K6]; separate process, embodic not linked into KiCad (`inferred`, not legal advice); PCM official repository requires a GPL-compatible licence for packages with code [A5 §2, K5] — verified (A5) | `pcbnew` is part of KiCad, GPL-3.0-or-later [K9]; whether an in-process plugin is a derivative work `unresolved` (legal question) | writing a documented text format implies no linking (`inferred`) |
| Same Python core | yes — thin adapter over `Board` | yes — thin adapter, but core must run in KiCad's embedded Python | yes — exporter over `Board` |

## 3. What KiCad DRC can and cannot check for a coil winding

- Xcoil's export assigns one net `WINDING` to all copper when the star/delta interconnect is drawn, otherwise
  `PHASE_A/B/C` (`engine.js` l.2886–2892) — verified (code). That is electrically correct: a star- or delta-connected winding
  is one connected net.
- KiCad's clearance rules apply between items of **different** nets; copper of the same net may touch (`inferred` from KiCad
  connectivity semantics; not confirmed on a page I read). Consequence: `kicad-cli pcb drc` (or the GUI DRC) cannot detect a
  turn-to-turn or coil-to-coil clearance violation inside one phase winding. It still checks edge clearance, hole and
  annular-ring rules, via/track-to-other-net clearance (with per-phase nets in an open connection), and dangling track ends
  (`inferred`).
- Therefore embodic's own geometric DRC (F-24) remains the authority for winding clearance, in every route. KiCad DRC is a
  complementary check, not a replacement (`inferred`).

## 4. One Python core for the standalone app and the plugin

```
                 ┌──────────────────────── embodic_core (stdlib + NumPy; no UI, no kipy, no pcbnew) ───────────────────────┐
 project.json ──►│ params → topology.spiral → Board (+ electrical elements) → drc → analysis (EQ-labelled) → Result      │
                 └──────────┬───────────────────────────────┬───────────────────────────────┬───────────────────────────────┘
                            │                               │                               │
                 embodic_io.export                  embodic_app (standalone UI)     embodic_kicad (adapter)
                 .kicad_pcb / DXF / SVG / PDF       user's Python 3.11+             Board → ItemSpec (nm, layer names)
                 (route C)                          ─ optional "Send to KiCad" ───► apply(ItemSpec, BoardAPI) via kipy
                                                      (external control, T3)        inside begin/push_commit
                                                                                    ▲
                                                    KiCad toolbar action (route A): plugin.json → main.py
                                                    (KiCad's Python venv: kicad-python + NumPy + vendored core)
```

Design points (`assumption`):
1. The adapter has two layers: a pure function `board_to_items(board) -> list[ItemSpec]` (integers in nm, KiCad layer
   names, net names) and a small `apply(items, api)` that converts specs to kipy objects and commits. Only `apply` imports
   `kipy`. Unit tests cover the first layer and run `apply` against a fake `api` (records calls); one integration test needs
   KiCad.
2. Two ways to reach a live board, sharing the adapter: (A1) toolbar plugin running in KiCad's venv with the core vendored
   into the PCM package; (A2) "external control": the standalone app (user's Python) connects to the running KiCad with
   kicad-python — avoids installing NumPy into KiCad's venv, but Windows socket discovery from a process not launched by KiCad
   is `unresolved` (A5 T3). The plugin launch passes `KICAD_API_SOCKET` and `KICAD_API_TOKEN` to the process (IPC
   add-on page) — verified (doc extract).
3. Python version: route A runs on KiCad's bundled Python, whose version for 9.x is `unresolved`. Until T2 reports it, keep
   `embodic_core` free of syntax/stdlib features newer than the lowest plausible version (`assumption`); the NumPy range is
   chosen afterwards (NumPy 2.4.x needs ≥ 3.11, 2.5.x ≥ 3.12 — verified PyPI).
4. Core vendoring: put the pure-Python core inside the plugin folder and list only `kicad-python==<pin>` and `numpy` in
   `requirements.txt`; whether `requirements.txt` may reference a local wheel is `unresolved` (`inferred` that vendoring is
   simpler).
5. Units: core in mm; nm conversion in the adapter (kipy units are nm [A5 §5]); `.kicad_pcb` in mm with y flipped.

## 5. Recommended route and staged plan (`assumption`, for user approval)

| Stage | Content | Exit criterion |
|---|---|---|
| Phase 2a | `embodic_core` (spiral generator, DRC, approved equations) + standalone UI + **route C** `.kicad_pcb` writer targeting the user's KiCad 9 format (confirmed by T0) + optional `kicad-cli pcb drc --format json` import | T0 passes on the user's machine; embodic DRC and KiCad DRC agree on everything KiCad can see |
| Phase 2b | **route A** thin IPC wrapper (A1 toolbar plugin; A2 external control if T3 passes); PCM zip; kicad-python pinned per T4 | T2 (and T3) pass; generated board identical (item counts, coordinates on the 1 nm grid) to the route-C file of the same project |
| not planned | route B (SWIG) — only as a fallback for a must-have feature that IPC lacks in 9.x, accepting removal in 11.0 | — |

Reasons: C works today with no KiCad coupling and is fully testable; A is the supported direction and keeps embodic out of
KiCad's process; B is deprecated with a removal date [A5 §2].

## 6. Smoke tests for the user (Windows + KiCad 9.x; Phase 2 supplies the small scripts — nothing to run now)

| ID | Purpose | Steps (plain language) | Record | Origin |
|---|---|---|---|---|
| T0 | Does KiCad 9 open an Xcoil-style board file? | Open `dist/xcoil.html` (Xcoil v3) in a browser, choose a sector-coil preset, press "KiCad", open the file in KiCad 9 PCB editor; then File ▸ Save | opens without error? layer names and count, arcs drawn as arcs, vias, pads, outline; the `(version …)` line and the layer list of the **saved** file (send it to the team) ; run Inspect ▸ Design Rules Checker and note the result | new (route C) |
| T1 | KiCad's bundled Python and SWIG names | minimal action plugin writing `sys.version`, `sys.executable`, `pcbnew.Version()`, NumPy import result, adding one track/arc/via | versions, folder where it appeared | A5 T1 (optional: only the Python version matters if route B stays unplanned) |
| T2 | IPC plugin end to end | enable the API in Preferences ▸ Plugins; install a test plugin (`plugin.json`, `main.py`, `requirements.txt` with kicad-python + NumPy) into `Documents\KiCad\9.0\plugins\<id>`; run it from the toolbar | venv created? NumPy installed? KiCad version; `get_stackup()`; copper layer count; one commit creating track, arc, via, zone **and an Edge.Cuts segment/arc/circle and a pad/footprint**; any DRC entry point | A5 T2 (extended) |
| T3 | External control from the user's Python 3.11+ | `pip install kicad-python==<pin>` in a normal venv, run a script with KiCad open | connects without environment variables? | A5 T3 |
| T4 | kicad-python version for the user's 9.0.x | repeat T3 with 0.4.0 / 0.5.0 / 0.6.0 | `check_version()` result | A5 T4 |
| T5 | KiCad DRC from the command line | `kicad-cli pcb drc --format json --exit-code-violations <T0 file>` | exit code, JSON produced | A5 T5 (CLI now documented, still untested) |
| T6 | Packaging | Plugin and Content Manager ▸ install from file with a test PCM zip (`runtime: "ipc"`) | installs? appears in toolbar? | new (`inferred` that PCM offers install-from-file) |

## 7. Open points

| # | Point | Status |
|---|---|---|
| K-1 | KiCad 9 bundled Python version on Windows (drives NumPy pin and core syntax floor) | unresolved (T1/T2) |
| K-2 | Creating footprints/pads and Edge.Cuts shapes through IPC in 9.0.x | unresolved (T2) |
| K-3 | KiCad 9 file-format version token and copper-layer ordinals for the writer | unresolved (T0) |
| K-4 | Stack-up write through IPC or in the file | unresolved |
| K-5 | Whether IPC plugin dependency installation works offline / behind a proxy | unresolved |
| K-6 | Licence of embodic itself (matters only for the official PCM repository) | unresolved (user decision) |
