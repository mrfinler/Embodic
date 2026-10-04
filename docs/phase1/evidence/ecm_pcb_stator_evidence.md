Prepared by: Agent 5 — Research & Evidence Specialist — model: claude-opus-5-5

# ECM PCB Stator (E-Circuit Motors) — public technical evidence and patent-overlap notes

Phase 1 draft, 2026-10-04. Sources: public patent databases (Google Patents, Justia — both mirror USPTO
data), ECM's official site pcbstator.com, and the user-supplied images in `reference_images/`.
Method limits (disclosure): patent texts were read through WebFetch, which returns an extract produced by a
summarising model; claim texts marked "quoted" were returned as verbatim quotes but **must be re-checked against
the USPTO full text (ppubs.uspto.gov) before any legal use**. Patent PDF download and USPTO direct access were
blocked by the egress proxy. Status labels: `verified` = stated in the cited source as read; `marketing claim` =
from ECM marketing pages, not independently supported; `inferred — legal review needed` = Agent 5's reading of a
possible overlap. **We are not lawyers. Nothing here is a freedom-to-operate, infringement or validity opinion.**

## 1. Reference images (Agent 5's own reading; all `inferred from image`)

| Image | Reading |
|---|---|
| `instagram_DWvb7wWkz4M_frame1_magnetless_motor_render.png` | Dense, evenly spaced straight radial conductors over the whole annulus; nested U-shaped end-turn groups at the outer rim (8 bright positions at ≈45°, plus 8 darker positions offset ≈22.5°, apparently a second layer group seen through) and nested end-turn groups near the hub; rows of via dots near both ends of the radial conductors; I count **8** mounting holes on the rim (Fable's README says six); central toothed hole with four slot-shaped pads. Whether each nested group is a concentrated spiral coil or the outer end-turns of a wave winding cannot be decided from one rendered layer at this resolution → `unresolved`. |
| `…frame2_rotor_overlay.png` | Same board with an animated rotor/arrow overlay; no new geometry. |
| `ecm_pcb_stator_octagonal_board_user_supplied.png` | Octagonal green board, large central bore, fine radial traces across the full annulus (no visible concentrated coils), **nine** terminal pads in three groups of three near the lower edge, a few small holes. Consistent with the radial-conductor/serpentine style of ECM's patents (§2) — inferred. No dimensions. |

Cross-check with the same-named repository (verified parse, interpretation inferred; script in Agent 5 scratchpad):
`gouldpa00/magnetless_motor` layer G1 has outer end-turn arcs of 6 radii (13.5–16.4 mm) centred on 12 axes at
r = 26 mm, angles 0° + k·30° (G3: 15° + k·30°), and inner end-turn arcs concentric with the board centre (radii
14.3–17.2 mm) that are short (4–6° span) and located at ≈20° and ≈25° (mod 30°), i.e. **not** centred on the coil
axes. Nested outer caps + short offset inner steps form a series wave-like path, matching the README "Wave windings
… Add steps between coil loops". So a "spiral-looking" render can be a wave winding with nested outer end-turns;
the Instagram render (8 + 8 positions) is a different variant from the 12-position Gerber board (inferred).

## 2. ECM patents reviewed

Assignee for all: E-Circuit Motors, Inc. (Google Patents shows "eCircuit Motors Inc"); inventor Steven Robert Shaw
(plus George Harder Milheim where noted). Inventor/assignee list: https://patents.justia.com/inventor/steven-robert-shaw
(pages 1–2) — `verified`.

| Patent | Title / dates / status | What it discloses about coil structure | Location | Status |
|---|---|---|---|---|
| **US 10,170,953 B2** | Planar composite structures and assemblies for axial flux motors and generators. Priority 2015-10-02, filed 2017-12-22 (CIP of 15/611,359; family incl. US 9,800,109, 9,673,684, 9,673,688), granted 2019-01-01; 30 claims; independent claims 1, 9, 14, 15, 17; Google Patents: active, anticipated expiry 2036-06-30 | **Radial conductors** with inner and outer end turns forming a **serpentine** pattern routed in a single conductive layer (not spiral coils); radial traces "organized in three parallel groups connected by blind or buried vias" (FIG. 3); serpentine pattern from terminal to terminal that "encircles center point three times" (FIG. 9); end turns distributed across two layers (FIGS. 5A–5B, 7A–7B); subassemblies connected **in series** so that the turn count is three times greater; radial conductors of a layer connected to corresponding radial conductors of other layers by vias (parallel). No trace-width grading mentioned in the extract. | https://patents.google.com/patent/US10170953 ; claims: https://patents.justia.com/patent/10170953 | verified (extract) |
| **US 11,336,130 B1** | Low-loss planar winding configurations for an axial flux machine. Inventors Shaw, Milheim. Filed/priority 2021-08-17, granted 2022-05-17; 18 claims; independent 1 and 12; anticipated expiry 2041-08-17; PCT/US2022/013965 and CN/EP/KR/JP/CA/AU/MX/TW/ZA counterparts listed | All vias interconnecting two layers placed **radially on one side** of the annular active region (inner vias omitted), end turns of one layer on the opposite side; layers joined **in series** through those vias. Dependent claim 3: the traces form part of a **serpentine** shaped winding; dependent claim 4: part of a **spiral** shaped winding. FIG. 10: "complete single phase connection for a sixteen-pole, three-turn winding"; FIGS. 4A vs 5A: with vs without inner vias; outer vias also used for parallel connection and heat spreading (FIGS. 1, 8–11). No width grading per extract. | https://patents.google.com/patent/US11336130B1/en ; https://patents.justia.com/patent/11336130 | verified (extract) |
| **US 9,800,109** | Structures and methods for controlling losses in printed circuit boards. Filed 2016-09-30, granted 2017-10-24 | Claim 1: radial traces joined at the outer radius by an interconnect (end turn) whose radiused inner edge follows the "Corner Equation" r(θ) = r_d + (r_s − r_d)e^(−(θ−θ_s)/α). Description: end-turn interconnect "split longitudinally into two or more parallel paths" (slits) to reduce eddy-current-induced current crowding (FIGS. 9–11); multilayer conductors linked by vias (FIGS. 8, 12, 13, 15); radial traces described as uniform width (extract) | https://patents.justia.com/patent/9800109 | verified (extract) |
| **US 10,256,690** | Same title; filed 2018-10-19 (continuation of 15/852,972 = US 10,170,953), granted 2019-04-09; 19 claims; independent 1, 11, 14, 17 | Claim 1: end-turn interconnect with radiused inner edge whose curvature "varies continuously as a function of arc length"; claim 11: piecewise-linear dr/dθ; claim 14: DC current-density minimum ≥ 50 % of maximum across the interconnect; slits only in dependent claim 9 / description (FIG. 9). No width-vs-radius claim. | https://patents.justia.com/patent/10256690 | verified (extract) |
| US 9,859,763 | Same title, granted 2018-01-02 | not reviewed | Justia inventor list | — |
| **US 10,211,694** | Structures and methods for thermal management in printed circuit board stators. Filed 2018-10-19, granted 2019-02-19; 20 claims; independent 1, 7, 15 | Claim 1 (quoted in extract): radial "first elongated conductive elements" with inner and outer end turns, plus "second elongated conductive element(s)" located radially inside the inner or outside the outer radius of the active conductors, **thermally but not electrically** connected to them; claim 7 multilayer with vias; heat-sink connection via outer elements | https://patents.justia.com/patent/10211694 | verified (extract) |
| **US 12,424,901 B2** | Planar stator configurations for axial flux machines. Shaw, Milheim; filed 2023-02-24, granted 2025-09-23; 20 claims | Stator segments with different winding characteristics (e.g. 4 vs 2 turns), Y/delta/separate-pair terminal schemes (FIGS. 8A–8C), eddy-current braking sheet; no trace geometry claims per extract | https://patents.justia.com/patent/12424901 | verified (extract) |
| Others (titles only, not reviewed) | 11,626,779 (discrete segments with different winding characteristics); 11,527,933 & 11,831,211 (stator/rotor design for periodic torque); 11,751,330 & 12,495,493 (magnetic-material-filled PCB stators); 12,538,411 (integrated cooling); 12,609,567 (pocketed back iron); 12,665,534 (tapped stator); 11,005,322 & 11,855,484 (rotor assemblies); 9,673,688 (magnet assembly); EP 3 652 843 A1 (improved planar composite structures) | — | Justia inventor pages; Google Patents search result | titles verified |

Summary of ECM's disclosed coil structure (inferred from the reviewed patents): radial conductors over the active
annulus with inner/outer end turns, arranged as **serpentine (wave-like) windings encircling the centre**, many
layers with radial conductors paralleled by (blind/buried) vias, layer groups connected **in series** to raise turns,
special end-turn corner shapes and slit end turns for loss control, and thermal-only copper. Spiral windings appear
only as a dependent-claim alternative in US 11,336,130 (claim 4). **No trace-width grading** with radius was found
in the reviewed patents (`not found`, extract-based).

## 3. ECM official pages (all `marketing claim`)

- "ECM Printed Circuit Board Stator Technology Overview", https://pcbstator.com/overviews/printed-circuit-board-stator-electric-motor/
  (published 2023-09-17, modified 2025-05-27): "continuous coil design and encapsulated windings"; PrintStator
  generates "Gerber and drawing files"; "stacked stator" designs for higher voltage (2017); efficiencies "greater than
  90%"; "66% reduction in weight, a 70% reduction in axial length"; "up to 15% increases in efficiency"; "up to 30db
  quieter"; "zero cogging and smooth torque".
- "PCB Stator Technology", https://pcbstator.com/pcb-stator-technology/: three patents filed 2016 (thermal management;
  winding losses; magnet assembly), "total of 10 patents" by 2019; "up to 80% less copper"; example motors at 91, 92
  and 93 % efficiency. No layer counts, copper weights, trace widths or via details are published there.

## 4. Possible overlap with embodic (all `inferred — legal review needed`; not legal advice)

| # | Patent / claim element | Possible embodic feature | Why it might overlap / might not |
|---|---|---|---|
| R1 | US 10,170,953 cl. 1: radial conductors and inner end turns on one layer forming portions of windings of **two phases**; second layer with radial conductors; **each** first-layer radial conductor via-connected to a corresponding second-layer radial conductor | Multi-phase spiral coils on the same layer, with radial sides duplicated on another layer and joined by vias (parallel layers or multi-via sides) | Overlap risk if every radial side is via-paired to another layer; a spiral pair joined only by one inner-end via may not meet "each … radial conductors" |
| R2 | US 10,170,953 cl. 9: first-layer and second-layer winding portions **in series**, same current, plus per-conductor vias | Classic two-layer spiral pair (in on top, via, out on bottom) — described generally in D02 p.1 | Series pairing is common; overlap depends on the per-radial-conductor via element |
| R3 | US 10,170,953 cl. 14/15: stacked subassemblies, blind/buried vias, winding portion that "circumscribes a region … at least once" | Multi-layer spiral stacks with buried vias | Spiral coils do not encircle the board centre, but "circumscribes a first region" is undefined here — needs claim construction |
| R4 | US 10,170,953 cl. 17: one phase has more end-turn conductors than another | Phase-asymmetric end-turn routing | Avoid unless needed; check |
| R5 | US 11,336,130 cl. 1/12 + cl. 4 (**spiral**): all layer-interconnect vias located radially on one side **outside** the active region, end turns of the other layer on the opposite side, layers in series | Spiral coils with all vias moved to the outer (or inner) rim outside the magnet annulus | **Highest attention item**: a spiral design with all vias outside the active annulus maps onto cl. 1 + cl. 4. A conventional spiral with its via in the coil eye (inside the active annulus) differs (inferred) |
| R6 | US 9,800,109 cl. 1 / US 10,256,690 cl. 1, 11, 14, 17: end-turn inner edge with exponential "Corner Equation" or continuously varying curvature; slit end turns | Smooth (spline/clothoid) end-turn corners; split end turns for eddy-loss reduction | Constant-radius arcs have constant curvature (inferred: outside "varies continuously"); avoid exponential/clothoid corner shapes and slit end turns until reviewed |
| R7 | US 10,211,694 cl. 1: thermal-only copper elements inside/outside the active radii, thermally but not electrically connected | Heat-spreading copper pours/fingers at the rim or hub | Overlap risk if embodic adds such features; electrically connected copper or plain zones may differ |

Notes for legal review: (i) expiry dates are Google Patents' "anticipated" values and legal status can change;
(ii) US patents cover the US only — family members (EP, CN, JP …) matter for other markets; (iii) earlier public
literature on spiral and concentric PCB coils exists (e.g. D02 p.1 citing Gambetta & Ahfock 2009; D04 2018; D09 2020;
D10 2019) — whether that affects validity is a legal question; (iv) re-read all claims in full from USPTO.

## 5. Not found / not accessed

- No ECM technical paper or whitepaper with coil dimensions was found in the time box (a "technical note on PCB stator
  motors for reaction wheels" is announced on newswire sites — not read; ECM brochure PDF on a CDN — not read).
- No ECM statement on trace width grading, copper weight, layer count or via size on official pages read.
- Full claim sets of US 9,859,763, 11,626,779, EP 3 652 843 A1 — not reviewed.
