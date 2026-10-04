Prepared by: Agent 6 — Software Architecture Specialist — model: claude-opus-5-5

# embodic — Decisions the user must take before Phase 2 (consolidated, 2026-10-04)

These are merged from the documents of all agents (reconciliation round 1). A recommendation is a proposal
(`assumption`), not a decision. Sources: A1 = `design/design_spec_draft.md` §14; A2 = `engineering/topology_analysis.md` §7
and `answers_to_agents.md`; A3 = `software/migration_mapping.md` §3, `dependency_and_tooling_draft.md` §6,
`kicad_plugin_feasibility.md` §6–7; A5 = `evidence/evidence_gaps.md`, `kicad_plugin_evidence.md` §4; A6 = this folder.
Already decided by the user (BRIEF §1): embodic brand, white/grey/black primary palette, spiral coils, 3 phases,
multi-layer, KiCad 9.x plugin if feasible, Python engines. Decided by Fable, therefore not listed: D-006 (DRC acceptance
rule) and D-007 (result status rule) in `docs/decision_log.md`.

| ID | Decision | Options | Recommended option and reason | Consequence if deferred | Source |
|---|---|---|---|---|---|
| UD-01 | Application type | desktop PySide6 (C-A) / local web UI (C-B1) | C-A: one language, offline, no local server (ADR-0005) | Phase 2 UI cannot start; Agent 1 keeps desktop and phone layouts | A6, A1 |
| UD-02 | Licence of embodic | proprietary / MIT, BSD or Apache-2.0 / GPL-3.0 | decide now; choose a GPL-compatible licence if a KiCad PCM listing is wanted | dependency allow-list and PCM eligibility stay open | A6, A3, A5 |
| UD-03 | Windows bundle that needs no Python, in Phase 2? | yes / no (pip install into Python 3.11+) | no in Phase 2: the user already has Python; bundle later | bundle work stays unscheduled | A6, A3 |
| UD-04 | KiCad integration depth | plugin applies a saved project / plugin also opens the full embodic window (needs T3) | apply-from-file, plus launcher if T3 passes: no GUI toolkit in KiCad's Python | plugin scope and Agent 1's plugin window stay open | A6, A1, A3 |
| UD-05 | Phase colours | muted colour-blind-checked phase colours (data only) / pure greyscale + hatching | muted phase colours with a greyscale mode always available | Agent 1 must maintain both themes | A1, A3, A6 |
| UD-06 | Dark mode in the first release | yes / no | no; colour tokens already prepared | none (light only) | A1 |
| UD-07 | UI density | compact (14 px text, 32 px controls) / comfortable (16 px, 40 px) | compact on desktop | none (compact default) | A1 |
| UD-08 | Serpentine and wave generators | keep / defer / drop | defer; generator interface kept; wave first if added later | users who need them keep using Xcoil v3 | A3, A6, A2 |
| UD-09 | Keep the 16-magnet rotor (20 × 6 × 2 mm blocks) | yes / no (free pole count, arc magnets) | yes: matches the default 12/16 design and the D09 oracle | default rotor stays an assumption | A2 |
| UD-10 | Rotor arrangement | double / single with yoke / single without yoke | double: symmetric field, smallest layer-to-layer EMF spread | field-model default stays an assumption | A2 |
| UD-11 | Blind/buried vias | allowed / through vias only | through only by default; blind/buried as an option after a fabricator quote | series layer pairs limited by coil-eye space | A2 |
| UD-12 | Operating targets | supply voltage, speed, torque, cooling | give values (even ranges) | turns and series/parallel grouping cannot be sized; only per-turn constants | A2 |
| UD-13 | The Instagram render: exact target or style reference? | exact board (may need a wave winding) / style reference | style reference: spiral coils already decided | risk of scope growth to wave windings | A2, A5 |
| UD-14 | Default phase connection | star / delta | star: no triplen circulating current | star used as an assumption | A2 |
| UD-15 | Machine for the performance target (< 1 s recompute) | user's laptop spec (CPU, cores, RAM, Windows) | give the spec of the laptop actually used | performance requirement stays an assumption | A6 |
| UD-16 | Offline installation needed? | yes / no | answer now; if yes, ship a local wheel folder for app and plugin | plugin first load may fail without internet | A3, A6 |
| UD-17 | UI spelling | British / American | British: matches the engineering documents | British used by default | A1 |
| UD-18 | Product name inside the brand | "embodic" + design name / "embodic PCB stator" / "Elysium by embodic" | "embodic" + design name | default used | A1 |
| UD-19 | Coil polarity convention | positive coil = clockwise seen from the F.Cu (rotor 1) side / other | accept (Agent 2 convention) | default used in drawings and exports | A1, A2 |
| UD-20 | 3-D view in Phase 2 | yes / no | no: 2-D only, 3-D kept possible | none | A1, A3 |
| UD-21 | Run smoke tests T0–T6 on the user's Windows PC with KiCad 9.x | at the start of Phase 2 / later | at the start of Phase 2 (short scripts supplied by Agent 3) | KiCad file format, bundled Python, kicad-python version and plugin route stay unresolved | A5, A3, A6 |
| UD-22 | Patent review (ECM claims) before any product release | review / no review | attorney review before release; keep risky options switchable | legal risk at release time | A5 |
| UD-23 | Obtain paywalled sources | IPC-2152 (or 2221B), IEC 60028, Bumby 2005, Dai Pré & Bianchi 2006 / none | obtain IPC-2152 and the 2006 paper first | related results keep `assumption`/`unresolved` labels | A5, A2 |
| UD-24 | Build and measure one embodic reference board (R, L, Ke) | yes in Phase 3 / no | yes: first in-house validation case | inductance and multi-layer EMF stay unvalidated | A5, A2 |
| UD-25 | May the team (through the user) contact the D09 paper's authors for the turns per coil? | yes / no | yes: Agent 4's inversion gives 7 or 8 turns, not decidable from the paper; unblocks oracle O2 | oracle O2 (OR-02, OR-07) stays blocked | A5, A4 |
| UD-26 | Keep Xcoil v3 as a read-only legacy tool | keep / retire | keep until UD-08 is settled | none | A3 |
| UD-27 | Is FEMM (free 2-D magnetics solver for Windows) available, or may it be installed, on the user's PC? | install FEMM / no FEA until Phase 3 | install: enables field validation OR-11 (EQ-05) and per-layer B_z checks | EQ-05 field validation waits until Phase 3; Ke/torque badges cannot rise above `inferred` | A4 |

## Revision 2026-10-04 (defect fixes)

Added Agent 4's two user questions (UD-25 reworded to the turns per coil with Agent 4 as source; new UD-27 FEMM). D-006 and
D-007 are Fable's decisions and are not listed as user decisions.
