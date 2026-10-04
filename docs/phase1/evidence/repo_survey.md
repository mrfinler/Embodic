Prepared by: Agent 5 — Research & Evidence Specialist — model: claude-opus-5-5

# Repository survey — `gouldpa00/magnetless_motor` and `cooked/kimotor`

Phase 1 draft. Date of survey: 2026-10-04. Status labels follow PROJECT_BRIEF §3 rule 3.
`verified` = Agent 5 read the file or reproduced the number with the parser described in §1.4.
`inferred` = reasoning from verified facts; the reasoning is given. Nothing here was measured on hardware.

Method note (disclosure): the commit hash/date of both repositories were read with a read-only
`git log` before Agent 5 noticed the brief's "no git" rule; no other git command was run and no
reference file was modified. All other facts come from reading files or from the parser script kept
in Agent 5's scratchpad (not part of embodic). Parser source summary is in §1.4.

---

## 1. `gouldpa00/magnetless_motor`

### 1.1 Identity and licence

| Item | Value | Source | Status |
|---|---|---|---|
| Local path | `/home/claude/embodic-ref/magnetless_motor/` | brief §2 | verified |
| Commit | `c6ec327e3794f49f1f18af1b3256d7b5b4cc3e7b`, 2026-03-28 17:25:43 +0800, author `gouldpa00`, message "Update README.md" (two earlier README-only commits the same day: `0be69511…`, `b7dce487…`) | read-only `git log` | verified |
| Licence | GNU GPL **version 3**, 29 June 2007 (full text) | `LICENSE` lines 1–2 | verified |
| Consequence | Reference only, no copying of design data or text into embodic (brief rule 7) | brief §3 | verified (rule) |

### 1.2 Every file and what it is

| File | Size (B) | What it is | Status |
|---|---|---|---|
| `LICENSE` | 35,149 | GPL-3.0 text | verified |
| `README.md` | 496 | 12 lines of design notes (quoted in §1.3) | verified |
| `mini_wave-bb.PcbDoc` | 1,778,688 | Altium PCB document (OLE "Composite Document File V2"); contains the layer stack-up records in §1.5 | verified (`file`, string extraction) |
| `mini_wave-bb-3.zip` | 156,047 | Gerber + NC-drill fabrication package, 27 entries, all dated 2025-11-11 | verified (`zipfile` listing) |
| `gerbers/` | — | Unzipped copy of the zip (same 27 names and sizes); created for this project per brief | verified |
| `mini_stat.ipt` | 348,672 | OLE compound file; extension = Autodesk Inventor part (README: "ipt -> dwg -> pcb traces") | verified type; "Inventor" inferred from extension |
| `mini_stat-bb.dwg` | 49,887 | "DWG AutoDesk AutoCAD 2018/2019/2020" | verified (`file`) |
| `.git/` | — | repository metadata | verified |

Gerber package contents (layer names from `mini_wave-bb.EXTREP`; generator from the `TF.GenerationSoftware`
attribute "Altium Designer 25.8.1 (18)"; units `%MOMM*%`, format `%FSLAX44Y44*%`):

| File | Content | Status |
|---|---|---|
| `.GTL` / `.G1` / `.G2` / `.G3` / `.G4` / `.GBL` | Copper: Top, Layer 1–4, Bottom; `Layer_Physical_Order` = 1…6 respectively | verified |
| `.GTS` / `.GBS` | Solder mask top/bottom (6 octagon openings + 12 × Ø0.2032 mm flashes) | verified |
| `.GTP` / `.GBP` / `.GPT` / `.GPB` | Paste and pad-master layers (6 octagon flashes each) | verified |
| `.GTO` / `.GBO` | Overlays — empty (no draw commands) | verified |
| `.GM1` | Mechanical 1 = board outline (12 lines, 12 R3 arcs, 1 R12.5 arc) | verified |
| `.GKO` | Keep-out — empty | verified |
| `.GM` | "Profile": 35 line draws + 9 regions, all at r ≈ 48.06–48.07 mm; purpose not determined | verified counts; purpose `unresolved` |
| `.GD1` / `.GG1` | Drill drawing / drill guide | verified (names) |
| `.TXT` | Excellon drill, METRIC, LZ, format 4:4 | verified |
| `.DRR` | Drill report: T1 0.3 mm PTH × 617; T2 3.1 mm NPTH × 12 | verified |
| `.LDP` | Layer pair Top–Bottom, drill layers gtl,g1,g2,g3,g4,gbl (through vias only) | verified |
| `.REP`, `.EXTREP`, `.apr`, `-macro.APR_LIB`, `Status Report.Txt` | Altium output reports; output generated 11/11/2025 23:22 | verified |

### 1.3 README statements (verbatim facts)

`README.md` lines 1–12 (verified): 6-layer PCB, 1 oz copper outer and inner; "0.5mm radial traces, 2x 0.3/.5
vias"; "vias 2x sets of axial traces"; top three layers the same, bottom three the same; "Wave windings,
16 coils equivalent per phase, three phases"; workflow "ipt -> dwg -> pcb traces; add vias; copy rotate 12
times; copy to different layer, rotate (360/(12*2)); Add steps between coil loops, add start and end
points"; inner hole 25 mm dia; outer 12-sided polygon 93 mm across flats; "16x 20x6x2 magnets (to start)".

### 1.4 Gerber/Excellon parse (Agent 5 script, 2026-10-04)

Parser: minimal RS-274X reader (apertures `%ADD`, modal X/Y/I/J, G01/G02/G03, D01/D02/D03, G36/G37) and an
Excellon reader (modal coordinates, LZ 4:4). Board centre taken from the R12.5 mm inner-hole arc centre in
`.GM1` = (100.000, 100.000) mm; the 12 NPTH centroid coincides exactly. All radii below are from this centre
and refer to **track centre-lines** (add 0.25 mm for the copper edge of a 0.5 mm track).

**Apertures (verified):** D10/D11/D12 octagon 3 × 2 mm (rotations 150°, 210°, 180°), D17 C2.5, D18 C2.0,
D19 C0.5 (tracks), D20 C0.5 (via pads), D21 C0.254 (outline), D13–D15 octagon 3.2032 × 2.2032 (mask), D16
C0.2032 (mask), D24 C0.0254 (profile).

**Copper layers (verified counts):**

| Layer | Linear draws (by aperture) | Arc draws | Flashes | Centre-line length lines + arcs (mm) | r min–max (mm) |
|---|---|---|---|---|---|
| GTL (1) | 377 (374 C0.5, 3 C2.5) | 680 | 623 (617 via pads, 6 octagons) | 3039.1 + 1814.4 | 14.30–45.28 |
| G1 (2) | 389 (C0.5) | 674 | 617 | 3034.6 + 1760.8 | 14.30–42.40 |
| G2 (3) | 389 | 674 | 617 | 3034.6 + 1760.8 | 14.30–42.40 |
| G3 (4) | 351 | 696 | 617 | 2995.9 + 1838.7 | 14.30–42.40 |
| G4 (5) | 351 | 696 | 617 | 2995.9 + 1838.7 | 14.30–42.40 |
| GBL (6) | 364 (351 C0.5, 9 C2.5, 4 C2.0) | 696 | 623 | 3033.1 + 1838.7 | 14.30–45.28 |

So each layer has ≈ 1,040–1,060 C0.5 draw elements (lines **plus** arcs), not ≈ 1,050 line segments as
the brief's summary reads (correction; verified). Total centre-line copper path per layer ≈ 4.8 m (verified sum);
how it splits between phases is `unresolved` (needs net tracing, see §1.7).

**Layer identity (verified by set comparison of C0.5 segment end-points, 0.01 mm rounding):**
- G1 and G2: all 1,052 elements coincide (files differ only in draw order).
- G3 and G4: byte-identical apart from `G04` comment lines.
- GBL's 1,047 C0.5 elements coincide with G3/G4; GTL's 1,037 C0.5 elements are all contained in G1 (G1 has 15
  more) — top/bottom differ from their groups only near the terminals (inferred from the wide traces there).
- Top group vs bottom group: best rotational match at 15° (mod 30°) with 998 of ≈ 1,050 elements coinciding;
  consistent with README "rotate (360/(12*2))" = 15° (inferred).

**Active (radial) conductors (verified):** per layer 143–144 straight radial segments, each 20.0 mm long from
r = 18.0 to 38.0 mm, at a uniform 2.5° pitch on angles 1.25° + k·2.5° (one 5° gap on G1 = 143 segments).
144 = 360°/2.5°.
- Inferred: with 16 poles (16 magnets, README) the pole pitch is 22.5° = 9 conductors per pole = 3 per phase
  per pole per layer (3 phases). This matches "radial traces" + "wave windings". Connectivity was not traced.
- Inferred: the 20.0 mm active span equals the 20 mm magnet length, i.e. magnets probably placed radially over
  r ≈ 18–38 mm; the README does not state magnet placement (`assumption` until confirmed).
- Inferred: the remaining arcs/short segments (r 14.3–18 mm and 38–42.4 mm) are end turns ("steps between coil
  loops").

**Vias (verified, `.TXT` + `.DRR`):** 617 plated, Ø0.3 mm drill with Ø0.5 mm pads (D20) on all six layers:
- 576 on a regular grid: 144 each at r = 18.0, 18.5, 37.5 and 38.0 mm, angles 1.25° + k·2.5° (two staggered
  via radii at each end of every radial conductor = README "2x 0.3/.5 vias").
- 41 extra vias in clusters at ≈ 45°, 60°, 75°, 90°, 105°, 120° (5, 8, 5, 8, 5, 10 vias; r 38.0–40.0 mm).
  The 60°/90°/120° clusters connect to the terminals; the 45°/75°/105° clusters' role (star point or layer
  jumps) is `unresolved`.

**Terminals (verified):** six octagon flashes 3 × 2 mm per outer layer, in pairs at (45.5 mm, 60°)+(45.77 mm,
53.7°), (45.5, 90°)+(45.77, 83.7°), (45.5, 120°)+(45.77, 113.7°); each pair is joined by a 2.5 mm trace on
GTL, and on GBL 2.5/2.0 mm traces run from the pads to the via clusters at r 39.6–41 mm. → **three terminal
lands at 60°, 90°, 120°** (the brief's "3 octagonal terminal pads" is correct as lands; each is two flashes).
Inferred: three external terminals for three phases imply an internal star point or a delta; which one is
`unresolved`.

**Mounting holes (verified):** 12 NPTH Ø3.1 mm at r = 45.0 mm, angles 15° + k·30°.

**Outline (`.GM1`, verified):** 12 straight flats at 46.500 mm from the centre (93.0 mm across flats,
matches README), flat mid-angles 0° + k·30°; the 12 corners are R3.0 mm arcs **concentric with the 12
mounting holes** (arc centres at r = 45.0 mm); flat-to-arc tangent points at r = 47.949 mm; inner hole R12.5 mm
(Ø25 mm, matches README). Correction to the brief: 47.95 mm is the tangent-point radius, not a polygon vertex
radius; the outermost board extent is 45.0 + 3.0 = 48.0 mm (inferred from verified arc geometry).

### 1.5 Stack-up records in the Altium file (verified as stored; meaning inferred)

Extracted `V9_STACK_LAYERn_*` records from `mini_wave-bb.PcbDoc`:

| Order | Layer | Copper | Dielectric |
|---|---|---|---|
| — | Top solder | — | 0.4 mil, εr 3.5 |
| 1 | Top Layer | 1.4 mil (35.6 µm) | — |
| — | Dielectric 2 | — | PP-006 2.8 mil (71 µm), εr 4.1 |
| 2 | Layer 1 | 1.378 mil (35.0 µm) | — |
| — | Dielectric 5 | — | PP-006 2.8 mil, εr 4.1 |
| 3 | Layer 2 | 1.378 mil | — |
| — | Dielectric 1 (core) | — | FR-4 3.937 mil (100 µm), εr 4.8 |
| 4 | Layer 3 | 1.378 mil | — |
| — | Dielectric 6 | — | PP-006 2.8 mil, εr 4.1 |
| 5 | Layer 4 | 1.378 mil | — |
| — | Dielectric 9 | — | PP-006 2.8 mil, εr 4.1 |
| 6 | Bottom Layer | 1.4 mil | — |
| — | Bottom solder | — | 0.4 mil, εr 3.5 |

Sum ≈ 24.3 mil ≈ 0.62 mm (inferred arithmetic). These may be Altium template defaults rather than the
ordered build; the README only says "1oz" (consistent with 35 µm). Treat thickness as `unresolved`.

### 1.6 Topology statement

- **Verified (README):** wave winding, 3 phases, "16 coils equivalent per phase", 6 layers in two identical
  groups of 3, 0.5 mm radial traces, 16 magnets 20 × 6 × 2 mm, Ø25 mm hole, 93 mm 12-sided outline.
- **Verified (Gerbers):** 144 radial conductors per layer at 2.5°, r 18–38 mm; two-radius via rows at both ends;
  bottom group rotated 15° (mod 30°) relative to top group; three terminal lands.
- **Inferred:** a radial-conductor wave winding (similar in principle to the "radial winding" with 16 poles and
  144 "slots" of Tokgöz et al. 2020, `B2/EPA-2020-0622-FINAL.pdf` p.3 §2.2 — similarity only, no evidence of
  derivation). It is **not** a spiral (concentrated) coil design, so its geometry rules do not transfer
  directly to embodic's spiral coils; only manufacturing parameters (0.5 mm track, 0.3/0.5 mm via, 1 oz, 6
  layers, through vias) are reusable as examples.

### 1.7 What is NOT in the repository (verified by full file listing)

No source code or scripts; no equations or calculation method; no electrical parameters (resistance,
inductance, back-EMF, torque, Kt/Ke); no test or measurement data; no rotor drawing or magnet-placement
drawing beyond the README line (the `.ipt`/`.dwg` are named "mini_stat" = stator, inferred); no schematic or
netlist; no BOM; no phase/turn connection table. Phase connectivity, series/parallel arrangement and the
star/delta choice could be recovered only by tracing copper connectivity through vias (proposed in
`evidence_gaps.md` G11).

---

## 2. `cooked/kimotor`

| Item | Value | Source | Status |
|---|---|---|---|
| Local path | `/home/claude/embodic-ref/kimotor/` (shallow clone) | — | verified |
| Last commit | `dc6cac3a937509979b9e7b4e07e979a04d1e95a0`, 2024-06-09 17:01:03 +0200, "improved DRC" | read-only `git log`; `.git/packed-refs` | verified |
| Licence | **GPL-2.0-only**: SPDX header `GPL-2.0-only` in every `.py` and in `.github/workflows/release.yml`; `metadata.json` `"license": "GPL-2.0"`. There is **no LICENSE file** in the repository. | file headers | verified |
| Plugin API | SWIG `pcbnew.ActionPlugin` (`kimotor_action.py` line 24 `class KiMotor(pcbnew.ActionPlugin)` with `defaults()` and `Run()`); `__init__.py` calls `KiMotor().register()` | source | verified |
| GUI | wxPython (`import wx`, `wx.lib.agw.persist`); dialog generated by wxFormBuilder (`kimotor_gui.fbp` → `kimotor_gui.py`) | source | verified |
| Dependencies | NumPy (README "Requirements"; `import numpy` in solver/action/linalg) | README, source | verified |
| PCM metadata | `metadata.json`: schema `https://go.kicad.org/pcm/schemas/v1`, identifier `com.github.cooked.kimotor`, type `plugin`, version `0.1.99`, status `development`, `kicad_version` **"6.0"** | `metadata.json` | verified |
| Other KiCad versions seen | README install paths use `…/KiCad/7.0/3rdparty/plugins` (Windows `C:\Users\<USERNAME>\Documents\KiCad\7.0\3rdparty\plugins`); example board `kimotor-project.kicad_pcb` has file version 20240108, `generator_version "8.0"`; `kimotor_pcb_20_layers.kicad_pcb` version 20221018 | files | verified |
| Inference on 9.x | No evidence that kimotor was tested on KiCad 9.x | — | inferred (absence) |

**Files (verified listing):** `kimotor_action.py` (ActionPlugin, dialog logic, board generation), `kimotor_solver.py`
(coil path planners), `kimotor_linalg.py` (2-D line/circle geometry helpers), `kimotor_persist.py` (wx persistence
for spin controls), `kimotor_gui.py`/`.fbp` (GUI), `__init__.py`, `metadata.json`, `README.md`, `assets/` (icons,
screenshots), `kimotor-project/` (example KiCad project), `.github/workflows/release.yml` (packaging to the KiCad
PCM repository), `kimotor.code-workspace`, `kimotor_24x24.png`.

**Geometry generated — function names only (no code copied):**
- `kimotor_solver.py`: `coil_planner(type, r_in, r_out, dr, n_slot, n_loop, dir, start)`, `parallel(r1, r2, dr, th,
  turns, dir)`, `radial(r_in, r_out, dr, n_slot, n_loop, dir, start)`, `radial_old(...)` → two coil-path styles,
  "parallel" and "radial" (verified names; behaviour inferred from names).
- `kimotor_action.py`: `do_windings`, `coil_tracker`, `do_rings`, `do_junctions`, `do_terminals`, `do_outline`,
  `do_mounting_holes`, `do_thermal_zones`, `do_silkscreen`, `fillet`, `fillet_outline`, `stats_length`,
  `stats_rlc`, `udpate_lset`, `init_nets` (verified names).
- `pcbnew` identifiers used (verified grep, counts in brackets): `PCB_TRACK` (12), `PCB_ARC` (9), `PCB_VIA` (8),
  `PCB_SHAPE` (7), `ZONE` (4), `ZONE_FILLER`, `FootprintLoad` (3), `NETINFO_ITEM`, `LSET`, `PCB_GROUP`,
  `PCB_TEXT`, `EDA_ANGLE`, `VECTOR`/`VECTOR_VECTOR`, `wxPoint`, `SETTINGS_MANAGER`, `VIATYPE_THROUGH`, `Edge_Cuts`,
  `F_Cu`/`B_Cu`, `FromMM`/`ToMM`, `Refresh`, `GetBoard`. → kimotor creates tracks, arcs, through vias, zones,
  outline shapes, footprints from a library, groups and text via the SWIG API (inferred from identifiers).
- Observation (verified value, inferred judgement): `stats_rlc` uses copper resistivity 1.77e-8 Ω·m and a
  temperature coefficient written as 3.99e-2 per °C (`kimotor_action.py`, `stats_rlc`, ≈ line 1527). The
  temperature coefficient of copper is commonly ≈ 3.9e-3 per K, so this constant appears 10× too large
  (inferred; the papers in the corpus give the formula but no numeric α — see `evidence_gaps.md` G6). Do not
  reuse.

Use in embodic: architecture reference only (ActionPlugin registration, PCM `metadata.json`, wx dialog). No
code copying (GPL-2.0-only is also incompatible with GPL-3.0-only combinations and with permissive relicensing;
inferred, not legal advice).
