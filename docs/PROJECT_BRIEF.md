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
- The Instagram post (https://www.instagram.com/p/DWvb7wWkz4M/) could not be fetched (robots.txt). The user
  attached three screenshots on 2026-10-04; they are stored with provenance notes and Fable's reading in
  `docs/phase1/evidence/reference_images/README.md` (frame 1 and 2: "magnetless motor" render — concentrated
  spiral coils with fanned radial sides and nested stadium end-turns, 8 bright + 8 darker coils offset by half a
  pitch and overlapping; frame 3: an ECM PCB Stator octagonal board). The user added: "you can see more from
  ECM motor" (ECM PCB Stator Technology / PrintStator). No dimension or electrical value may be read from
  these images; they define the *look* of the target topology only (`inferred from image`).

## 2. Reference material (READ-ONLY — never modify)

| What | Where (container path) | Notes |
|---|---|---|
| Xcoil v3 source (the "existing HTML/JS") | `/home/claude/serpentine/src/` (engine.js, report.js, ui*.js, body.html, style.css, tests.js, view3d.js), `/home/claude/serpentine/parts/`, built file `/home/claude/serpentine/dist/xcoil.html`, `/home/claude/serpentine/TEST_PLAN.md` | Our own prior work; may be ported. Engine is UMD JS; `node /home/claude/serpentine/run-tests.js` runs 131 tests. |
| Repository `gouldpa00/magnetless_motor` | `/home/claude/embodic-ref/magnetless_motor/` (commit `c6ec327e3794f49f1f18af1b3256d7b5b4cc3e7b`, 2026-03-28). Gerbers unzipped in `gerbers/`. | **GPL-3.0**. Contains NO code: README.md, Altium `.PcbDoc`, Inventor `.ipt`, `.dwg`, Gerber zip. README: 6-layer PCB, 1 oz, 0.5 mm radial traces, wave winding, "16 coils equivalent per phase, three phases", top 3 layers identical, bottom 3 identical, inner hole 25 mm, 12-sided outline 93 mm across flats, 16 magnets 20×6×2 mm. Agent 5's Gerber parse (`docs/phase1/evidence/repo_survey.md` §1.4, supersedes Fable's first pass): each copper layer has 144 radial conductors from r = 18 to 38 mm at 2.5° pitch (~350–390 lines + ~674–696 arcs per layer), 617 vias 0.3/0.5 mm (576 on four regular rings + 41 in clusters), 3 terminal lands, layers G1 = G2 and G3 = G4 = Bottom, bottom group rotated 15° (mod 30°) from the top group, largest board radius 48.0 mm. The repo's board is a **wave winding**, not the spiral-coil board seen in the Instagram render. |
| Repository `cooked/kimotor` (KiCad PCB-motor plugin) | `/home/claude/embodic-ref/kimotor/` (commit `dc6cac3a`, 2024-06-09) | **GPL-2.0-only** (file headers; no LICENSE file), SWIG `pcbnew.ActionPlugin` + wxPython, NumPy, declares kicad_version 6.0. Reference for plugin architecture ONLY. **Do not copy code.** (Agent 5 notes its copper temperature coefficient is ~10× too high — do not reuse.) |
| Papers (batch 1, 7 PDFs) | `/mnt/user-data/uploads/paper/` | D01 Salim 2019; D02 Han et al. (SPARK wave winding); D03 Kesgin et al. (Litz/PCB); D04 Wang 2018 (Energies 11, 3383); D05 Jeon et al. (actuators-14-00424); D06 Neethu et al. (compare.pdf); D07 **Paul et al.** (Revised_manuscript_Final — wave-winding topologies) |
| Papers (batch 2, 13 PDFs; 2 duplicates of batch 1 → 18 unique papers) | `/mnt/user-data/uploads/Desktop/Fantastic Creature/FC-Smart_Actuator/papers/` | D08 Collijs & Vereecken UGent thesis (**concentrated spiral trapezoidal coils, 12 coils/side, 10 poles**); D09 **Tokgöz, Çakal, Keysan** (EPA-2020-0622, winding topology comparison); D10 Wang et al. 2019 (unequal-width concentric spiral); D11 **Li, Wang, Lv** (pattern optimisation, 12-slot/14-pole concentrated); D12 Saneie et al. (wire-wound); D13 Choi et al. (MEC); D14 **Moon et al.** (actuators-15-00327); D15 Pan et al. (8-layer spiral stepper); D16 Choi et al. (water pump); D17 Youn et al. (EMF imbalance); D18 Shuaibu et al. (review). Full table with page locations: `docs/phase1/evidence/evidence_register.md`. |
| Agent 5 Phase 1 outputs (read these first) | `docs/phase1/evidence/{repo_survey,kicad_plugin_evidence,evidence_register,evidence_gaps}.md` | KiCad 9.x findings (verified from official pages): SWIG bindings deprecated in 9.0, removal planned for 11.0; IPC API (`kicad-python`, MIT) works only with the PCB editor running, must be enabled in Preferences ▸ Plugins, each IPC plugin gets its own venv with KiCad's bundled Python and `requirements.txt`; can create/edit tracks, arcs, vias, zones and read the stack-up; no DRC call found. Evidence gaps G1–G8 (no validated multi-layer spiral inductance formula; eddy-loss coefficient disagreement; IPC-2221 values not in corpus; etc.). Candidate test oracles O1–O3 (UGent thesis Ke = 0.031 V·s/rad; Tokgöz R 1.07 Ω, L 14.8 µH; Wang 2019 R 2.15 Ω; Pan 2026 46.4 mN·m). |
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
