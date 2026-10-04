Prepared by: Fable 5.1 — coordinator and final reviewer — model: claude-fable-5-1 (configured id; serving model may differ)

# embodic — Phase 1 draft: summary and index (2026-10-04)

Phase 1 covered survey, research and drafting only. No application code exists yet. The draft is submitted for the
user's approval before Phase 2 (specification + development) starts. Independent verification (Agent 4) ran twice;
all 22 defects found are closed and verified, one minor defect (DEF-23, labelling of the edge-correction calibration)
remains open and is scheduled for the start of Phase 2.

## 1. Team and process (verified)

| Role | Agent | Model (self-reported in every file) | Folder |
|---|---|---|---|
| Coordinator / final reviewer | Fable 5.1 | claude-fable-5-1 | `docs/` root, `decision_log.md` |
| 1 UX/UI | Agent 1 | claude-opus-5-5 | `design/` |
| 2 Motor design | Agent 2 | claude-opus-5-5 | `engineering/` |
| 3 Software engineering | Agent 3 | claude-opus-5-5 | `software/` |
| 4 Independent verification | Agent 4 | claude-opus-5-5 | `verification/` |
| 5 Research & evidence | Agent 5 | claude-opus-5-5 | `evidence/` |
| 6 Architecture | Agent 6 | claude-opus-5-5 | `architecture/` |

Waves: 1 (Agents 5 → 2 → 1, 3, 6 in parallel, Agent 5 follow-up), 1b (reconciliation Agents 1, 2, 6), 2 (Agent 4
review), 2b (defect fixes, all owners), 2c (re-verification, second fixes, final re-verification). One Opus rate-limit
interruption (session limit, reset 18:40 CST) delayed wave 2c by about 15 minutes; no agent was switched to another model.

## 2. What was found (status labels per PROJECT_BRIEF §3)

- Reference repository `gouldpa00/magnetless_motor` (GPL-3.0): Altium/Inventor/Gerber files only, no code. The board is a
  **radial-conductor wave winding** (144 radial conductors per layer, 6 layers in two groups rotated 15°, 617 vias) —
  `verified` from the Gerbers (`evidence/repo_survey.md`). It is not a spiral-coil board.
- The Instagram render (user screenshots) shows 8 + 8 overlapping coil positions; it fits concentrated spiral coils and
  it fits a wave winding equally well — `unresolved`. It is treated as a style reference (UD-13).
- 18 unique papers were registered with page-level locations (`evidence/evidence_register.md`, 79 EV rows plus a
  candidate-oracle table). ECM PCB Stator patents were surveyed (`evidence/ecm_pcb_stator_evidence.md`); a patent review
  is recommended before any release (`inferred — legal review needed`).
- KiCad 9.x (official pages, `verified`): SWIG action plugins are deprecated in 9.0 (removal planned for 11.0); the IPC
  API (`kicad-python`, MIT) works only with the PCB editor running, needs enabling in Preferences ▸ Plugins, and each
  plugin gets its own venv on KiCad's bundled Python. Nothing has been run on the user's machine (`not tested`).
- Existing Xcoil v3 engine: 131/131 tests pass (`verified`); two defects found by Agent 2 and confirmed by Agent 4 —
  `starOfSlots` rejects balanced combinations such as 12/14 because of floating-point ties, and the sector generator fits
  0 turns where the UGent thesis built 3 (`verified, reproduced`). Field model, 1-turn EMF, resistance and the 1-D limit
  were reproduced independently.

## 3. What is proposed (all `assumption` until the user approves)

- Topology: concentrated **spiral coils, 12 coils / 16 poles**, all three phases on every layer, k_w1 = 0.866, with
  12/10 (thesis oracle) and 12/14 also supported; 16/16 only as a one-phase-per-layer-pair variant
  (`engineering/topology_analysis.md`, concept drawing `spiral_coil_concept.svg`).
- Equation specification EQ-01…EQ-22 with gate verdicts (reuse / reuse with change / cannot verify yet / replace) and a
  machine-readable registry (`engineering/equation_registry_draft.json`); frozen oracle cases
  (`engineering/oracle_cases_draft.json`).
- App type: **PySide6 desktop application + UI-less KiCad 9 IPC plugin + `.kicad_pcb` writer** (option C-A); second
  choice: local web UI (C-B1). `architecture/app_type_comparison.md` §6–7.
- Architecture: pure-Python engines (`embodic.geometry / winding / physics / drc / results / io`), thin UI / CLI / plugin
  adapters, one primitive geometry model shared by all exporters, traceable result objects (value, unit, EQ-ID, evidence,
  assumptions, status), versioned JSON project file. 98 requirements with acceptance criteria, 9 ADRs, test plan with
  traceability matrix (`architecture/`).
- UX/UI: white/grey/black design system with tokens (`design/tokens.json`), 8 static mockups (desktop steps, phone
  variant, pure-greyscale variant, 880 × 600 KiCad window), accessibility criteria UX-AC-01…22 (`design/`).
- Independent test strategy IT-01…IT-56 and a defect register (`verification/`).

## 4. Decisions already taken

`docs/decision_log.md` D-001…D-007 (team model, orchestration, licences of references, KiCad requirement, version
control, DRC acceptance rule without slack, result-status rule). Decisions the **user** must take: 27 items in
`architecture/user_decisions_needed.md` (UD-01…UD-27); the Thai summary lists the ones that block Phase 2.

## 5. Limitations (from `verification/phase1_gate_recommendation.md`, final list)

Render topology unresolved; KiCad smoke tests T0–T6 not run; no measured oracle for a 3-phase stator with more than two
layers; radial-edge leakage handled by a calibrated correction from one FEA case (`assumption`); no equation validated
yet, so physics badges will show `inferred` at best; strict DRC means Xcoil's default design would fail it; the
concentric-loop length formula over-estimates true spirals by 4–23 %; "verified" in these documents means "read in the
source" or "reproduced", never "confirmed by experiment"; Python performance not measured; mockups are static; embodic
licence open; patent review needed.

## 6. Index

- `../PROJECT_BRIEF.md`, `../decision_log.md`
- `evidence/`: repo_survey, kicad_plugin_evidence, evidence_register, evidence_gaps, ecm_pcb_stator_evidence,
  reference_images/
- `engineering/`: topology_analysis, spiral_coil_concept (.svg/.md), equation_specification_draft,
  equation_registry_draft.json, oracle_cases_draft.json, existing_logic_review, answers_to_agents, checks/
- `software/`: feature_inventory, migration_mapping, calculation_flow_and_port_notes, kicad_plugin_feasibility,
  dependency_and_tooling_draft
- `design/`: ux_analysis, design_spec_draft, design_handoff_for_agent3, screen_to_view_map, tokens.json,
  design_review_notes, mockups/ (html + png), xcoil_screens/
- `architecture/`: requirements_draft, app_type_comparison, architecture_draft, test_plan_draft,
  user_decisions_needed, decisions/ADR-0001…0009
- `verification/`: phase1_verification_report, independent_test_strategy, defect_list, phase1_gate_recommendation,
  checks/
