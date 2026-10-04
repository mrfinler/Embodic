# embodic — Project Brief (shared by all agents)

Status: Phase 1 (survey, research, draft). No software implementation yet.
Coordinator and final reviewer: Fable 5.1. Team: six role agents (model alias `opus`, probed as claude-opus-5-5).

## 1. Goal

Build a new Python-based tool, branded **embodic**, for designing and analysing **3-phase spiral-coil
PCB stators** (coreless axial-flux) with **multi-layer configuration**, using the existing HTML tool
**Xcoil v3** as the reference for features, user flow, screens and calculation logic. Every piece of
calculation logic must be engineering-checked (equation specification + evidence) before it is reused.

User decisions already taken (2026-10-04):
- Brand: embodic (replaces Xcoil). UI colours: white / grey / black only as primary palette.
- Coil approach: **spiral coil** (concentrated planar spiral per coil) replaces the "sector coil" of Xcoil.
- Must support 3 phases and multi-layer stack-ups.
- NEW requirement: the tool should also work as a **KiCad plugin** if feasible. User runs **KiCad 9.x**.
- User has **Python 3.11+** installed on Windows (separate from KiCad's bundled Python).
- App type (Python desktop vs Python-backed web, and how a KiCad plugin fits) is to be PROPOSED in
  Phase 1 and approved by the user before Phase 2. Calculation engine and geometry engine must be Python.
- The user will attach a screenshot of an Instagram post (https://www.instagram.com/p/DWvb7wWkz4M/) that
  shows the intended spiral-coil layout; it could not be fetched (robots.txt). Until it arrives, treat the
  spiral-coil concept as derived from papers + the repository, and mark it `assumption`.

## 2. Reference material (READ-ONLY — never modify)

| What | Where (container path) | Notes |
|---|---|---|
| Xcoil v3 source (the "existing HTML/JS") | `/home/claude/serpentine/src/` (engine.js, report.js, ui*.js, body.html, style.css, tests.js, view3d.js), `/home/claude/serpentine/parts/`, built file `/home/claude/serpentine/dist/xcoil.html`, `/home/claude/serpentine/TEST_PLAN.md` | Our own prior work; may be ported. Engine is UMD JS; `node /home/claude/serpentine/run-tests.js` runs 131 tests. |
| Repository `gouldpa00/magnetless_motor` | `/home/claude/embodic-ref/magnetless_motor/` (commit `c6ec327e3794f49f1f18af1b3256d7b5b4cc3e7b`, 2026-03-28). Gerbers unzipped in `gerbers/`. | **GPL-3.0**. Contains NO code: README.md, Altium `.PcbDoc`, Inventor `.ipt`, `.dwg`, Gerber zip. README: 6-layer PCB, 1 oz, 0.5 mm radial traces, wave winding, "16 coils equivalent per phase, three phases", top 3 layers identical, bottom 3 identical, inner hole 25 mm, 12-sided outline 93 mm across flats, 16 magnets 20×6×2 mm. Gerber parse (Fable, 2026-10-04): 6 copper layers, aperture C,0.5 mm, ~1050 line segments per layer, copper radius ≈ 14.3–42.4 mm, 617 PTH vias 0.3 mm, 12 NPTH holes 3.1 mm, 3 octagonal terminal pads 3×2 mm, outline vertex radius ≈ 47.95 mm, inner hole radius 12.5 mm. |
| Repository `cooked/kimotor` (KiCad PCB-motor plugin) | `/home/claude/embodic-ref/kimotor/` (commit `dc6cac3a`, 2024-06-09) | **GPL-2.0**, SWIG `pcbnew.ActionPlugin` + wxPython, NumPy. Reference for plugin architecture ONLY. **Do not copy code.** |
| Papers (batch 1, 7 PDFs) | `/mnt/user-data/uploads/paper/` | Salim 2019 IET EPA; SPARK wave-winding ECCE 2021; Litz design optimisation; energies-11-03383 (Wang 2018); actuators-14-00424; Revised_manuscript_Final; compare.pdf |
| Papers (batch 2, 13 PDFs) | `/mnt/user-data/uploads/Desktop/Fantastic Creature/FC-Smart_Actuator/papers/` | PCB-stator thesis (UGent); Paul et al. EPA-2020-0622 (wave structures); Tokgöz et al.; unequal-width PCB winding; pattern optimisation (Moon et al.); Jeon et al. actuators-14-00424; actuators-15-00087; actuators-15-00327; electronics-15-00777; energies-18-02538; energies-19-01060; engproc-87-00013; SCI vol 29 |
| Brand assets | `/mnt/user-data/uploads/Desktop/Fantastic Creature/pitchdeck/resources/` | embodic logo (black on white), white variants, symbol (rounded triangle of three teardrops), wordmark, "elysium by embodic" sub-brand logo. |
| Company pitch deck | `/mnt/user-data/uploads/Desktop/Embodic-PDF.pdf` | Tone/brand only. Contains a personal name — **never copy personal data** into code or reports. |

User's machine (not reachable by agents): Windows, KiCad 9.x, Python 3.11+. Destination folder
`C:\Users\Sayoomphu\Desktop\embodic` (does not exist yet; Fable creates it from this repository).

## 3. Rules that bind every agent

1. **No fabrication.** Never invent data, references, equations, simulation or test results. If you did not
   verify it, say so.
2. **Every engineering claim carries a reference**: URL and/or file path + page/section/line. Prefer papers,
   textbooks, official documentation (KiCad docs, Python docs), manufacturer data.
3. **Status label on every claim and result** — exactly one of: `verified` (checked against evidence or
   reproduced), `inferred` (reasoned from evidence; give the reasoning), `assumption` (design choice without
   evidence), `unresolved` (unknown / needs test), `not tested`.
4. Check that a source actually applies to this topology (spiral coil, coreless axial flux, PCB) before using it.
5. Example numbers must be labelled as examples or assumptions. Computed results are never "measured".
6. Never claim magnetic balance, torque or efficiency from geometry or phase angles alone.
7. **Licences**: magnetless_motor is GPL-3.0, kimotor is GPL-2.0 → reference only, no code copying.
   Record licences of every proposed dependency.
8. **Language**: all software-facing text (UI strings, labels, warnings, chart labels, diagrams in mockups)
   in English; code identifiers and engineering terms in English. Internal documents in English. Fable
   reports to the user in Thai.
9. **Scope**: Phase 1 produces DRAFTS only (documents, diagrams, mockups). Do not implement the application.
10. **File ownership**: write only inside your own folder under `docs/phase1/<your folder>/`. Do not edit
    other agents' files; put cross-agent requests in your report's "Requests to other agents" section.
    Do not run `git` (Fable commits). Do not modify any reference material.
11. Report your model: the first line of every document you write is
    `Prepared by: Agent <n> — <role> — model: <exact model id from your own environment block>`.
12. Finish with a concise report: files written, key findings (with status labels), open questions,
    requests to other agents. Keep the report under ~600 words; details belong in the files.

## 4. Role folders

| Agent | Role | Folder |
|---|---|---|
| 1 | UX/UI Expert Designer | `docs/phase1/design/` |
| 2 | Motor Design Expert | `docs/phase1/engineering/` |
| 3 | Senior Software Engineer | `docs/phase1/software/` |
| 4 | Independent Verificator | `docs/phase1/verification/` |
| 5 | Research & Evidence Specialist | `docs/phase1/evidence/` |
| 6 | Software Architecture Specialist | `docs/phase1/architecture/` |

Shared decision log: `docs/decision_log.md` (written by Fable only).
