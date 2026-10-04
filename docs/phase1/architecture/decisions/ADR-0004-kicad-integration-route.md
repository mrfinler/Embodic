Prepared by: Agent 6 — Software Architecture Specialist — model: claude-opus-5-5

# ADR-0004: KiCad integration — `.kicad_pcb` writer as baseline, IPC API plugin as the plugin route, no SWIG

**Status:** Proposed — amended 2026-10-04 (plugin window, two-layer adapter, no silent remap, Python floor; citations corrected); details still depend on T1–T6
**Date:** 2026-10-04
**Deciders:** User (plugin expectations), Fable 5.1 — consulted: Agent 5 (evidence), Agent 3

## Context

Evidence (A5-KI; official KiCad pages, the kicad-python PyPI page and the kicad-python 0.8.0 wheel source — each item
cited to the page or file that actually contains it, per Agent 4 DEF-12):
- SWIG `pcbnew` bindings: "deprecated as of KiCad 9.0", removal planned "in KiCad 11.0"; "unstable … will generally change
  between KiCad major versions" (A5-KI §1–§2, [K1]).
- IPC API (KiCad dev-docs "IPC API" / "For Add-on Developers", [K4]): first released in 9.0; PCB editor only in 9 and 10;
  requires a running KiCad GUI; plugins run as standalone processes; per-plugin virtual environment with KiCad's bundled
  Python on Windows, declared dependencies installed on first load; "no support for plotting or exporting files".
- Enable step — the API server must be enabled in **Preferences ▸ Plugins**: stated on the kicad-python **PyPI page**
  ([K6], https://pypi.org/project/kicad-python/), not on the dev-docs page.
- `requirements.txt` as the dependency declaration file: from the kicad-python 0.8.0 wheel,
  `kipy/packaging/validate.py` l.138–164 ([K8]; warns when `requirements.txt` or `kicad-python` in it is missing), not
  from the dev-docs page.
- kipy 0.8.0 offers commits (`begin_commit`/`push_commit`/`drop_commit`), `create_items`, `update_items`, `remove_items`,
  `Track`, `ArcTrack`, `Via`, `Zone`, `get_stackup`, `get_copper_layer_count` (0.5.0 ↔ 9.0.5); no DRC-run method
  (A5-KI §3).
- `kicad-python` is MIT; KiCad is GPL-3.0-or-later; PCM code packages must be GPL-compatible open source (A5-KI §2–§3).
- Unresolved: bundled Python version, offline venv install, external-interpreter connection, kipy ↔ 9.0.x version
  mapping, DRC from a plugin (A5-KI §4 T1–T5; A5-GAP G13).
- The user runs KiCad 9.x and wants a plugin "if feasible" (BRIEF §1, DL D-004).

## Decision

1. **R1 (baseline, must):** `embodic.io.kicad_pcb_writer` writes a complete `.kicad_pcb` from the `Layout` (ADR-0002). It
   works without KiCad running and is the fallback whenever the plugin is unavailable.
2. **R2 (plugin, must if T2/T4 pass):** `embodic_kicad_plugin` — an IPC API plugin (PCM `runtime: "ipc"`) with actions
   "Apply embodic project" (one commit, replaces only previously placed embodic items) and "Import stack-up". It is
   **UI-less**: its venv contains only `kicad-python`, the embodic core and NumPy (no GUI toolkit, no server).
3. **R3 (could, needs T3):** action "Open embodic" starts the standalone app as a child process that inherits KiCad's IPC
   environment variables (`KICAD_API_SOCKET`, `KICAD_API_TOKEN` — Agent 3 `kicad_plugin_feasibility.md` §4, `verified (doc
   extract)` there) and acts as an IPC client.
4. **No SWIG** dependency. A SWIG fallback requires a superseding ADR backed by T1/T2 results showing an essential gap.
5. KiCad DRC is not callable from the IPC plugin per current evidence (A5-KI §1); embodic's own DRC is the reference,
   also because KiCad clearance rules do not apply within one net, so turn-to-turn clearance of one phase is invisible to
   KiCad (Agent 3 §3, `inferred`). `kicad-cli pcb drc --format json` is documented for 9.0 (Agent 3 §2, `verified (doc
   extract)`) and becomes an optional complementary check after T5.

Route-label mapping: R1 = Agent 3 route C; R2 = Agent 3 route A (A1) = Agent 5 route B; R3 = Agent 3 A2; SWIG = Agent 3
route B = Agent 5 route A. Agent 3 reaches the same recommendation (file route first, IPC second, SWIG not planned —
`kicad_plugin_feasibility.md` §5).

## Options Considered

### Option A: File writer only
| Dimension | Assessment |
|---|---|
| Complexity | Low |
| Cost | Low — port of Xcoil's writer |
| Scalability | Medium |
| Team familiarity | High (Xcoil precedent, validated with kiutils) |

**Pros:** no KiCad process or version coupling; works today. **Cons:** not a plugin (user requirement); manual import step;
no stack-up read-back.

### Option B: IPC plugin + file writer, no SWIG (chosen)
| Dimension | Assessment |
|---|---|
| Complexity | Medium — process model, versions, item tracking |
| Cost | Medium |
| Scalability | High — IPC is the supported, "actively developed" route (A5-KI §1) |
| Team familiarity | Low/medium — new API; smoke tests needed |

**Pros:** non-deprecated, MIT binding, separate process (crash isolation, `inferred`), single-undo commits, stack-up read.
**Cons:** requires running GUI and enabled API; first-load dependency install; capability gaps (no plot/DRC).

### Option C: SWIG ActionPlugin with a wxPython dialog (kimotor pattern)
| Dimension | Assessment |
|---|---|
| Complexity | Medium |
| Cost | Medium now, high later (rewrite before KiCad 11) |
| Scalability | Low — deprecated |
| Team familiarity | Medium (kimotor reference, GPL-2.0, code must not be copied — DL D-003) |

**Pros:** in-process, wx available (`inferred` from kimotor imports). **Cons:** deprecated in 9.0, removal planned 11.0;
unstable between major versions; licence question of in-process use `unresolved` (A5-KI §2).

### Option D: IPC plugin with SWIG fallback for missing features
**Pros:** covers potential IPC gaps. **Cons:** two KiCad adapters to maintain, one of them deprecated; no gap is yet proven
essential (DRC can be done by embodic). Deferred until T1/T2.

## Trade-off Analysis

B satisfies the plugin wish on the supported API while A's writer guarantees a working path regardless of the smoke-test
outcomes. Keeping the plugin UI-less trades in-KiCad dialogs for a minimal, robust venv; R3 can restore an integrated
experience if T3 succeeds.

## Consequences

- Easier: long-term KiCad compatibility (no SWIG removal risk); crash isolation; testable adapter (pure mapping function).
- Harder: user must enable the API server; plugin feedback channel without a GUI toolkit is `unresolved` (log file at
  minimum); kipy version pinning per KiCad 9.0.x.
- Revisit: after T1–T5; when KiCad 10/11 adds headless IPC (A5-KI §3: "no headless mode (added in 11)").

## Action Items

1. [ ] User (Phase 2 start): run T1–T5 smoke tests (A5-KI §4), Agent 3's T0 (= KS-01: open a generated `.kicad_pcb`,
       save, report the format version KiCad writes) and T6 (PCM install from file).
2. [ ] Fable: decide the core's Python floor after T1 (architecture_draft.md §17 R10).
3. [ ] Agent 3: port the `.kicad_pcb` writer; implement `embodic.io.kicad_items` as a pure mapping `Layout → ItemSpec` (shared by writer and plugin) testable
       without KiCad.
4. [ ] Agent 4: KX-01…KX-08 parser and adapter tests; KS-02…KS-06 manual checklist.
5. [ ] Fable: decide core distribution into the plugin venv (published wheel vs vendored core — Agent 3 prefers vendoring)
       after T2.

## Amendment 1 — reconciliation round 1 (2026-10-04)

- **Two-layer adapter adopted** (Agent 3): pure `embodic.io.kicad_items.layout_to_item_specs` (core; also used by the
  `.kicad_pcb` writer, so file and live placement are identical on the 1 nm grid) + thin `embodic_kicad_plugin.apply`
  behind a `BoardApi` protocol (`KipyBoardApi`, `FakeBoardApi` for KX-08).
- **Agent 1's plugin dialog** (880 × 600, tabs, UX-AC-21) is realised as a compact window of the standalone app started by
  the plugin's launcher action (R3, needs T3). The plugin venv still contains no GUI toolkit. Without T3 the plugin only
  applies the project file and reports through its log.
- **No silent layer remap** (REQ-K-14): every placement path blocks when the board has fewer copper layers than the
  design.
- **Python floor**: core in 3.11 syntax, no 3.12-only features; if KiCad bundles ≤ 3.9 the core is not vendored and the
  plugin uses R3 or R1 only; 3.10 allows a small downgrade (architecture_draft.md §18.1 item 1).

## Revision 2026-10-04 (defect fixes)

- DEF-12: Context now cites `requirements.txt` to kicad-python 0.8.0 `kipy/packaging/validate.py` l.138–164 and the
  "Preferences ▸ Plugins" enable step to the kicad-python PyPI page, not to the KiCad dev-docs page.
