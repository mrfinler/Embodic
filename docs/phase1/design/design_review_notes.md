Prepared by: Agent 1 — UX/UI Expert Designer — model: claude-opus-5-5

# Review of Agent 6 drafts against the design spec (reconciliation round, 2026-10-04)

Read: `architecture/architecture_draft.md` §10, §10.1–10.2, §13, §19 and `architecture/requirements_draft.md` REQ-N-01…26,
REQ-T-01…14 (plus REQ-L-04/07/08, F-21/23/32/33, K-14/15 where they touch the UI). Most rows match the spec; mismatches
and gaps below. “Fixed” = changed in my files this round.

| # | Item | Agent 6 | My spec / mockups | Resolution |
|---|---|---|---|---|
| 1 | Status rule | REQ-T-03, §13: every used default / unsourced input → `assumption` | §10.4: ordinary assumed inputs only as tags | **Accept Agent 6.** Spec marked superseded. Effect: on the default design almost every result shows `assumption`. Request: the card shows `status_reasons` as a second line (“Equation: inferred · 3 inputs at default”) so the badge stays informative. |
| 2 | Default marker on inputs | REQ-T-06, F-21: every default field shows an assumption marker | not specified | **Fixed in spec**: dashed ◇ “default” chip after the label, removed on edit, “Reset to default”. Not yet in the mockups. |
| 3 | Initial focus in the place/export confirmation | REQ-F-33, `dialogs.py`: Cancel | “Review failures” | **Fixed**: Cancel · Review failures · Place anyway, focus on Cancel (mockup 05, spec). |
| 4 | Terminal location | `terminal_location: "outer"` only | Outer/Inner segmented control | **Fixed**: read-only “Outer rim” with reason (mockup 03, spec). |
| 5 | Terminal names in Phases | no model field | editable U/V/W/N | **Fixed**: removed from Phases; net names stay in Export (`kicad` section). |
| 6 | “Balanced” wording | REQ-T-11: explain as phasor symmetry | “Balanced” | **Fixed**: “Balanced phasors” + hint that it is no torque/balance claim (mockups 01, 02, 06). |
| 7 | DRC rule codes | `DRC_TRACE_VIA` style (§12) | `CLR-TRACE-VIA` | **Fixed** in mockup 05. |
| 8 | Element ids | §19 canonical ids | 8 ids differ | **Accept all**; mockups and handoff updated (`screen_to_view_map.md` §0). |
| 9 | Torque–speed results section | no result field for EQ-20 | Results nav lists it | **Gap** for Agent 6: add `torque_speed` (status `unresolved`, label “estimate”) or drop the section in P2. |
| 10 | Feasibility rail values (EQ-01/02/03), series turns per phase, balanced-Q list | not in `AnalysisResult` / API | shown in Coil and Layers rails | **Gap**: propose `Layout.derived: GeometryDerived` Traceables + `balanced_coil_counts(poles)` helper. |
| 11 | Breakpoints | two panes from 960 px (REQ-N-15) | tablet 768–1279 px | **Accept** 960 × 540 minimum; phone (mockup 06) only if C-B1. |
| 12 | Plugin window | compact mode of the standalone app via launcher (R3, REQ-K-15 *could*) | dialog, UX-AC-21 *must* | **Accept.** Open: in an R2-only setup (no T3) nothing can show the REQ-K-14 block message or the DRC note inside KiCad — needs a fallback (e.g. a message from the plugin action or a text report). |
| 13 | Target size measurement | AX-04 checks widget geometry ≥ 24 px | checkbox glyph 18 px inside a ≥ 32 px label | AX-04 must measure the clickable label area, not the glyph. |
| 14 | Greyscale mode | REQ-N-23: hatch none / 45° / 135° | hatch over the whole coil footprint | **Revised**: hatch only inside the coil eye (full-footprint hatch looked like crossing copper in mockup 07). REQ-N-23 wording still holds; please add “hatch never crosses copper”. |
| 15 | Contrast automation | AX-01 over theme pairs | — | `tokens.json` lists 47 light / 46 dark pairs with ratios (0 failures) plus the greyscale variant. |
| 16 | Phase colours | REQ-L-04: only if the user approves (UD-05) | proposed as default | Mockup 07 (pure greyscale) added next to 01 so the user can choose. |

No mismatch: REQ-N-02 (debounce/“Updating…”), N-11, N-12 (F6, Alt+1…6, 2 px + 2 px focus), N-14, N-16, N-24, N-25, N-26,
T-01, T-02, T-04, T-05 (“estimate”), T-07, T-10, T-13, T-14, L-07, L-08; §10 view list and MVVM split.
