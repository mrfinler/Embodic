# embodic — Shared Decision Log

Maintained by Fable 5.1 (coordinator). One entry per decision; agents propose, Fable records.

| ID | Date | Decision | Rationale / evidence | Status |
|---|---|---|---|---|
| D-001 | 2026-10-04 | Team model: all six role agents run on alias `opus`; a live probe reported `claude-opus-5-5`. Coordinator: Fable 5.1 (`claude-fable-5-1`). | The Agent tool exposes aliases (opus/fable/sonnet/haiku), not version pins; the probe is the only verification available. Serving model can differ if the harness falls back; every document carries the author agent's self-reported model id. | verified (probe) |
| D-002 | 2026-10-04 | Orchestration: subagents (Agent tool) for Phases 1–2; a Workflow is proposed only for the Phase 3 verification fan-out and only if the user explicitly asks for one. | Human approval gates and iterative defect loops suit persistent subagents; workflows are token-heavy and require explicit opt-in. | decided |
| D-003 | 2026-10-04 | Reference repository `gouldpa00/magnetless_motor` (GPL-3.0) and `cooked/kimotor` (GPL-2.0) are used as references only; no code is copied. | Licence incompatibility risk for a differently-licensed deliverable; magnetless_motor contains no code anyway. | decided |
| D-004 | 2026-10-04 | New requirement accepted: KiCad plugin capability (target KiCad 9.x). Architecture must keep the engines UI-agnostic so a plugin host and a standalone UI share them. | User request 2026-10-04; KiCad version confirmed by user. | decided |
| D-005 | 2026-10-04 | Version control: the project lives in a git repository (created in the cloud workspace, mirrored to `C:\Users\Sayoomphu\Desktop\embodic` including `.git`). Fable commits at the end of each wave. | Diff/rollback requirement of the brief. | decided |
