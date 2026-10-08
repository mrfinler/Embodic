Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5 (unit U-E8, 2026-10-09)

# Open engineering positions after M3

This note closes or schedules three items that M3 left open (D-036 e, D-036 a, D-016). Each section gives the position,
the evidence, one status label, the consequence, and the measurement behind it. Status labels follow the standing
orders: `verified` means read in the source or reproduced by running something.

Every number below comes from one script. It reuses the GR-22 and GR-20 pipelines, so its numbers are the numbers the
golden tests see.

```
cd /home/claude/wt/U-E8
PYTHONPATH=src /home/claude/embodic/.venv/bin/python docs/phase2/engineering/checks/u_e8_open_positions.py
```

Xcoil line numbers refer to `/home/claude/serpentine/src/engine.js` as read on 2026-10-09.

## 1. The overlap wave tap stubs and line leads carry current

### 1a. Star (XD-WAVE-001)

**Position.** The three tap stubs from the inner terminals to the star ring carry the full line current. embodic counts
them correctly as link copper at I_line² R. Xcoil's zero for the overlap wave is an omission in that one code path. It
is not a modelled choice.

**Evidence.**

- Connectivity, measured on `wave-analysis-overlap-l2-m3-p16-t2` (star, I_line = 0.8 A rms). Each `PhaseLink` path
  (47, 48, 49; net N; layer L1; width 0.6 mm; lengths 1.0, 3.1, 3.8 mm) starts on the minus terminal via of its phase
  at 0.0 mm (via 0 phase A, via 15 phase C, via 4 phase B). Each ends at r = 16.9000 mm, the radius of the ring arc
  (path 46). The ring copper reaches r = 17.4 mm (16.9 + 1.0 / 2) and the nearest terminal pad starts at r = 17.6 mm
  (17.9 − 0.6 / 2), so the ring does not touch a terminal via directly. Each stub is the only copper between a phase
  terminal and the star node. Kirchhoff's current law then gives I_stub,k = I_phase,k, which equals I_line in star
  (EQ-23 star branch).
- Xcoil's own rule for this copper. `interconnectResistance` adds every star tap stub to the link sum of its phase
  ("star: stubs belong to their phase", l.1367 to 1368). `applyConnection` multiplies that sum by I_line² (l.1423).
  The overlap path never calls `interconnectResistance`: its callers are l.1997, l.2479 and l.2542 only. Instead
  `computeWaveOverlap` builds the sums by hand with `link: [0, 0, 0]` (l.2172). Its `stub()` helper (l.2157) sets no
  `tap` field, so even the general rule would not see these stubs. Xcoil has no comment or warning that explains the
  zero.
- Measured loss. embodic P_ic = 7.422035e-03 W and Xcoil P_ic = 5.006617e-03 W, so embodic is +48.24 % higher. The
  difference is 2.415418e-03 W. I_line² ΣR(PhaseLink) = 0.64 × (4.777330e-04 + 1.480972e-03 + 1.815385e-03) Ω =
  2.415418e-03 W, equal to the difference to the printed digits. Each R is EQ-10 per primitive with Xcoil's operating
  resistivity 1.995013e-08 Ω·m and t = 0.0696 mm.
- Why +48 % and not more or less. Xcoil counts 5.006617e-03 / 0.64 = 7.823e-03 Ω, which is the three line leads (6.879e-04 +
  8.886e-04 + 1.4905e-03 Ω) plus the ring arc (4.756e-03 Ω). The stubs add 3.774e-03 Ω, which is 48.24 % of 7.823e-03 Ω.
  The ratio is a copper-length ratio of this one case, not a general constant.

**Status.** `verified`. The connectivity was reproduced by running, the current follows from Kirchhoff's current law
on that connectivity, and the loss rule was read in Xcoil l.1368 and l.1423. That Xcoil's zero is unintended is
`inferred`, because the code states no intent.

**Consequence.** Expected diff. XD-WAVE-001 stays, because embodic deliberately differs from Xcoil here. Its status
changes from `assumption` to `verified` with the reasoning above, and the Agent 2 sign-off becomes "confirmed (U-E8)".
That edit is in `tests/`, outside this unit's scope, so Fable routes it to Agent 3. Xcoil's star R_LL
(l.1422) omits the same stubs through its (2/3)Σl_k term. Whether embodic's R_LL differs on this case is `not tested`.

### 1b. Delta

**Position.** embodic counts the three line leads of the overlap delta at I_line² R, which gives 1.962909e-03 W. These
leads do carry current. Their current is I_ph or I_line, depending on where the external delta closure lands, and the
geometry does not decide that. embodic's value is therefore an upper bound. Xcoil's 0 W is below both possible values.

**Evidence.**

- Copper counted, measured on `wave-analysis-overlap-l2-m3-p16-t2-delta`. The interconnect consists of three `LineLead`
  paths only (93, 94, 95; nets U, W, V; layer L2; width 1 mm; lengths 2.4, 3.1, 5.2 mm). Each runs from a plus terminal
  via (vias 7, 8, 11 at r = 43.4, 42.7, 40.6 mm) to its line pad at r = 45.8 mm. No interconnect path ends on the
  three minus terminal vias (0, 4, 15 at r = 17.9, 20.7, 20.0 mm), so the delta closure is off-board. embodic warns
  `RANGE_WAVE_INTERCONNECT_EXTERNAL` (D-036 d). Xcoil's `INTERCONNECT_EXTERNAL` at l.2190 is unreachable, because the
  `else if (wantIc)` follows `if (wantIc || conn === 'open')` (l.2174).
- Which current. Each lead is the only copper between its pad and its phase. If the external jumper from the closing
  phase lands on the pad, the line current splits at the pad and the lead carries I_ph = I_line / √3. Then the loss is
  6.543030e-04 W. If the jumper lands on the plus terminal via, the lead carries I_line and the loss is 1.962909e-03 W.
  EQ-23's delta branch (I_line² Σs) assumes the second case, as Xcoil's general delta does (l.1428). That
  assumption holds when the line stub ends at an on-board delta junction.
- Xcoil. `computeWaveOverlap` starts with `icR = null` (l.2154) and assigns it only in the star branch (l.2172).
  `applyConnection` adds interconnect loss only `if (icR)` (l.1428), so the overlap delta reports 0 W. That is below
  the I_ph case, so Xcoil omits copper that carries current in either case.
- What embodic and Xcoil both leave out. Neither models the external closure wires. Section 3 describes the same gap.

**Status.** That the leads carry current is `verified` (connectivity by run, then Kirchhoff's current law). That
embodic's 1.962909e-03 W is an upper bound is `inferred`. The physical value is `unresolved`. To settle it, the spec
must name the closure point (for example "the delta jumper lands on the U, V, W pads"). Then this script's I_ph line
is the expected value. Another option is to give the minus terminals pads, as the open winding already does (l.2178),
so that the junction is on a defined pad.

**Consequence.** Expected diff and known limitation. Agent 3 adds a row (proposed id XD-WAVE-002) for the overlap
delta case, with embodic 1.962909e-03 W against Xcoil 0 W, status `inferred`, with this reason. GR-22 then compares the case
instead of skipping it. The P_ic of an overlap delta should carry the assumption text "line leads counted at line
current; the external delta closure is not modelled".

## 2. Serpentine strands > 1 and Xcoil's T-bus via placement

**Position.** No reported pair is a short, and both cases are the same mechanism. Every pair joins a strand end to the
terminal via of the same phase, which sits on the T bus that both touch. seeded-03 is a placement artifact, and moving the
via onto the bus centreline makes it DRC-clean. strands-3 has a real 0.1091 mm gap between same-node copper, below the
0.200 mm rule. No source shows that a fabricator accepts such a gap, and no via placement on the bus clears it.
Therefore the position is a spec revision for a later phase, not a fabrication waiver. The faithful port stays in
Phase 2 (D-013, D-036 a).

**Evidence.**

- What Xcoil does. The T via sits at the middle of the T bus, offset radially by (viaPad − wNear) / 2 (l.486). Xcoil's
  pad check skips the T bus and the last `skipLen = viaPad + J·pitch + 1.0` mm of every strand of a connected via
  (l.656 to 660). With J = 2 and J = 3 that is 2.742 mm and 3.400 mm. Xcoil therefore never measures these pairs. That
  is a check rule, not fabrication evidence.
- seeded-03 (J = 2, w = 0.416, s = 0.155, pad 0.6 mm). There are 4 `trace_via` violations per board (12 on 3 boards),
  all at −0.2078 mm. Every pair is a strand path against the terminal via of its own phase, with the foot point at the
  path end (0.000 mm along the path). The via centre is 0.3002 mm from each strand end, and rule 2b exempts a primitive
  only within pad / 2 = 0.3000 mm. The copper overlaps, so no gap exists to etch. Moving the two T vias radially by
  −0.0920 mm onto the bus centreline gives 0 violations on board 0 (measured).
- strands-3 (J = 3, w = 0.4, s = 0.2, pad 0.6 mm). There are 12 `trace_via` violations at +0.1091 mm, again strand
  ends against the terminal via of their own phase, at the path end. The via centre is 0.6091 mm from the neighbouring
  strand ends, and the clearance is 0.6091 − 0.2 − 0.3 = 0.1091 mm. Clearing 0.200 mm needs 0.700 mm. With the
  interconnect switched off (so no stub starts on the via), the script tested three changes. A radial offset of
  0.299 mm, the most that rule 2b still allows, leaves 12 violations at 0.1723 mm. An offset of 0 leaves 24 at
  0.1000 mm. A T-via pad of 0.418 mm clears the `trace_via` pairs but fails `annular_ring` at 0.059 mm (6 violations),
  and a pad of 0.420 mm still fails `trace_via` at 0.1991 mm. These are D-006 results, so the margin of 2 µm decides.
- The other 6 of the 18 strands-3 violations are `trace_trace` pairs between interconnect stubs and copper of the same
  node (PHASE_A against line lead U, PHASE_C against star stub N; −0.4000 mm and −0.0272 mm). They disappear when the
  interconnect is off. Their cause is not diagnosed here (XD-SER-002-06 says the same).

**Proposed spec rule (later phase).**

1. On a T bus with J ≥ 2 strands, put the terminal via centre on the bus centreline (radial offset 0, not
   (viaPad − wNear) / 2). For even J this makes rule 2b exempt the two central strand ends (`verified` on seeded-03).
2. Every strand end that rule 2b does not exempt must lie at least s + w/2 + pad/2 from the via centre (0.700 mm for
   strands-3). When the bus pitch a does not satisfy a ≥ s + w/2 + pad/2 (strands-3: a = 0.6008 mm, derived from the measured 0.6091 mm and the 0.1000 mm offset), move
   the via out of the bundle. Either extend the bus beyond the outermost strand end by at least s + w/2 + pad/2 of arc,
   or put the via on a radial stub off the bus. Rule 2 is `inferred` and not tested. The test that settles it is a
   prototype generator branch with the moved via and bus extension, run through `run_drc` on the seven strands > 1
   cases. The expected result is 0 `trace_via` violations of this kind and no new violation class.

Until then, the Phase 2 DRC report should say, for each such pair: "Strand end 0.109 mm from the terminal via of the
same phase (rule 0.200 mm). Both are on one node, so this is not a short circuit. The gap is below the clearance rule.
This is Xcoil's bus geometry, ported unchanged."

**Status.** The measurements are `verified` (reproduced by running). That fabricators accept a same-node gap below the
rule is `unresolved` (source gap G38). Proposed rule 1 is `verified` on seeded-03 only. Proposed rule 2 is `inferred`.

**Consequence.** Spec change for a later phase (rules 1 and 2, owner Agent 3 after Fable schedules it). Known
limitation in Phase 2, with the report wording above. XD-SER-002 rows keep `$.verdict`, and their Agent 2 sign-off
becomes "confirmed as faithful port; geometry fix scheduled (U-E8)".

## 3. Per-phase board stack, scope note for Phase 5

A per-phase stack puts one phase on each board, and embodic, like Xcoil (l.2535), leaves the star or delta connection
between boards to the user (`RANGE_SERPENTINE_INTERCONNECT_BOARDS`). Ke and P_ic of the stack therefore carry
`unresolved` (D-037 b). An honest model needs three inputs per board. First, the conductor from each phase terminal to
its node, given as a wire length and conductor cross-section, or as a connector with its contact resistance per contact. Second,
the location of the star point or of each delta closure (on a board, on a separate PCB, or at the drive). Third, the
temperature of that conductor. With those inputs, each lead is one resistance by the ρ_T L / A form that EQ-10 and
EQ-11 already use (EQ-11 for an annular barrel), with the EQ-10 copper constants (EV-53). Each lead then enters EQ-23
by its role, so no new equation is needed. A lead from a phase terminal to the drive is a line stub s_k at I_line. A
lead from a phase terminal to the star point is a link l_k at I_line. A delta closure lead is a link l_k at I_ph, and
it also enters the EQ-19 loop resistance. The line constant follows from the phase Ke by the EQ-09 star or delta
conversion once the connection is defined. Three things stay `assumption` until a source backs them. They are the conductor
area of a named wire gauge, a connector's contact resistance, and the lead temperature. G39 records them, because the
evidence register holds no wire-gauge table and no connector datasheet. The magnetic effect of the external leads is
not modelled (`not tested`).

## Files and ids

- Script: `docs/phase2/engineering/checks/u_e8_open_positions.py` (read-only use of the golden harness; no src or
  tests edits).
- New source gaps: G38 (same-node gap acceptance) and G39 (per-board interconnect inputs) in
  `docs/phase2/evidence/source_gaps_phase2.md`. No new EV row, because this unit read no new external source.
- EQ-23 and EQ-10 notes: `equation_specification.md`, revision 2026-10-09 (U-E8).
