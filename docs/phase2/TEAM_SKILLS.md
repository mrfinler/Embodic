Prepared by: Fable 5.1 — coordinator — model: claude-fable-5-1

# Phase 2 team: roles, skills to load, and dispatch rules (checked 2026-10-04)

Orchestration follows the pstack poteto-mode Orchestrate playbook (store: `~/.claude/orchestrate/embodic/`,
standing orders in `preferences.md`, units in `units.tsv`, verdicts in `ledger.tsv`, decisions in `decisions.tsv`).
Every unit is a fresh `pstack:poteto-agent` on model `opus` (Opus 5.5, user requirement) with a consolidated brief
(GOAL / SCOPE / CONTEXT / ACCEPTANCE / VERIFY / TIMEBOX / FORBIDDEN / REPORT / STANDING). Fable (Fable 5.1) coordinates,
merges, and does final acceptance; it writes no application code.

Skill availability was checked against this session's skill list before dispatch. Skills marked (opt) are loaded
only when the unit touches that topic.

| Role | Units | Skills to load first | Why |
|---|---|---|---|
| Agent 1 UX/UI | U-S4 design spec v1, icons, themes; later U-I4 review | `dataviz` (palette validator for red/blue/green phases, chart rules), `pstack:unslop`, `pstack:technical-writing`, `pstack:principle-experience-first`; (opt) `modern-web-guidance:modern-web-guidance` only if an HTML artefact is produced | Colour-blind check of the user's phase colours, chart conventions, clean specs |
| Agent 2 Motor design | U-S2 equation spec v1, spiral generator algorithm, oracle cases; Phase 3 reviews | `pstack:principle-explain-the-number`, `pstack:principle-prove-it-works`, `pstack:technical-writing`, `pstack:unslop` | Every number explained and reproduced by a script; clean spec prose |
| Agent 3 Software (workers 3a…3e, one per milestone) | U-I1…U-I5 | `pstack:architect` (design before code), `mattpocock-skills:tdd` (golden/closed-form tests first), `pstack:principle-model-the-domain`, `pstack:principle-type-system-discipline`, `pstack:principle-boundary-discipline`, `pstack:principle-build-the-lever`, `pstack:principle-test-behavior-not-implementation`, `pstack:deslop` (before each commit), `pstack:no-comments`; U-I4 adds `pstack:create-verification-skill` (project `verify` skill driving the Qt app offscreen) and `dataviz`; U-I5 adds `pstack:benchmark-checklist` and `engineering:documentation` | Data-shape-first implementation, rerunnable checks, clean diffs, a driver skill for the UI |
| Agent 4 Independent verification | U-V1 independent tests against the interfaces; U-V2 Phase 3 verification; regression after optimisation | `pstack:principle-test-behavior-not-implementation`, `pstack:blast-radius`, `pstack:benchmark-checklist`, `mattpocock-skills:tdd`; (opt) `pstack:interrogate` for the Phase 3 adversarial pass | Independent expectations, defect-detecting tests, honest numbers |
| Agent 5 Research & evidence | U-S3 evidence register JSON + remaining sources + dependency licences | `mattpocock-skills:research` (primary-source research captured as Markdown), `pstack:technical-writing`, `pstack:unslop` | Cited findings in the repo |
| Agent 6 Architecture | U-S1 architecture/interfaces/requirements/test plan v1 + work breakdown | `pstack:architect`, `engineering:architecture` (ADR format), `engineering:system-design`, `mattpocock-skills:codebase-design`, `mattpocock-skills:domain-modeling`, `pstack:principle-foundational-thinking`, `pstack:principle-model-the-domain`, `pstack:principle-separate-before-serializing-shared-state`, `pstack:technical-writing` | Types and module seams before code; file ownership that prevents shared writes |
| Fable coordinator | briefs, merges, acceptance, Thai reports | `pstack:poteto-mode` (loaded), principles read this session: foundational-thinking, sequence-verifiable-units, separate-before-serializing-shared-state, guard-the-context-window, build-the-lever, prove-it-works, model-the-domain, test-behavior-not-implementation; `pstack:show-me-your-work` trail in the store | Program ownership, not code |

Dispatch rules applied (from poteto-mode): fresh agent per unit with consolidated scope; one writer per worktree/branch
for code; documents per owned folder; verifier separate from worker; coordinator never edits code; completions are
queue events (recorded in `units.tsv`/`inbox/`), reviewed as units, not inline; timebox in every brief.

Known limitation: the Agent tool in this session has no `run_in_background` option, so a wave is dispatched as one
parallel message and drained when all its agents return.
