Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5

# What the star-of-slots check establishes (DEF-UV8-04, U-E14, 2026-10-17)

The spiral design view prints "Balanced." or "Not balanced ..." next to the coil and pole counts
(`src/embodic/ui/strings/design.py` l.218 to l.219 and l.225 to l.228). This document states what that check proves and
what it does not. Agent 1 writes the user copy in U-S9. The copy must not claim more than section 1 states.

Status labels follow the standing orders: `verified` means read in the source or reproduced by running something. No
statement here comes from a test of a built machine.

## 1. What the check establishes

The check reads two integers, the coil count Q and the pole count 2p, plus the manual phase assignment when the user sets
one. It reads no geometry, no field and no material data.

1. Each coil k gets one electrical position, (k·p mod Q)·2π/Q (`src/embodic/winding/star_of_slots.py` l.40 to l.42). A
   reversed coil adds π (l.71). Each coil counts once, with weight 1 (l.71). `verified` (read in the code).
2. The check passes when the set of signed positions of phase B equals the set of phase A rotated by 120°, and the set of
   phase C equals the set of A rotated by 240° (l.61 to l.79). The arithmetic is exact integers in units of 360°/(12Q),
   so a coil on a belt edge never falls either way by rounding (EQ-08, `docs/phase2/engineering/equation_specification.md`
   l.194 to l.197; spiral_generator_spec.md G7). `verified` (read in the code and the spec).
3. The automatic assignment is the published one for the 12-coil, 10-pole case. CF-09 reproduces "AabBCcaABbcC", the
   connection diagram of D08 Fig. 3.7 (PDF p.36, printed p.31), and eight more combinations
   (`docs/phase2/engineering/oracle_cases.json` CF-09, status `verified`). Only the 12/10 pattern has a published
   reference. The other eight check the code against the rule, not against a source. EQ-08 as a whole is `inferred` (equation_specification.md l.209).
4. The pre-check Q mod 3 = 0 and (Q/t) mod 3 = 0, t = gcd(Q, p) (`src/embodic/winding/feasibility.py` l.42) matches
   EV-89 (Tessarolo 2019 eq. 15) and EV-90 (Alberti and Bianchi, slide 5). It is a pre-check only. The exact set
   comparison of item 2 decides (feasibility.py l.43). `verified` (read in the code and the evidence register).
5. With one phase per layer pair (option M4), the check is not a star of slots. "Balanced." then means Q = 2p
   (feasibility.py l.37 to l.39). Phases B and C come from rotating the layer pairs. That rule is `inferred` from the
   star-of-slots arithmetic and has no source in the evidence register (equation_specification.md l.211 to l.216).

**The engineering statement.** A pass means that the winding pattern is a symmetric 3-phase pattern. Assume that every
coil produces the same EMF waveform, shifted only by its electrical position. That holds for identical, equally spaced
coils in a field that repeats every pole pair (EQ-08 validity, equation_specification.md l.202). Then the three phase EMF phasors are
equal in magnitude and 120° apart at the fundamental. The same set rotation gives, at harmonic n, equal magnitudes n·120°
apart. The fundamental part follows from item 2 and is `verified` by reading. The harmonic part is `inferred` (my
derivation from item 2, not stated in a source). The statement is a property of the pattern. It does not describe a
built machine.

## 2. What the check does not establish

Each item names an effect that the two integers cannot see.

| Not established | Why the check cannot see it | Source | Status |
| --- | --- | --- | --- |
| Equal phase EMF magnitudes in the designed copper | Every coil has weight 1 (star_of_slots.py l.71). Real coils differ when their turns, radial extent, layer position or field differ. Option M4 puts each phase on its own layer pair, so each phase sits at its own axial distance from the magnets. | star_of_slots.py l.71; feasibility.py l.37 to l.39 | `inferred` |
| MMF balance and the pull force on the rotor | D11 keeps the coil-to-phase pattern and changes only the bridge connection between coils. The turn distribution between go and back sides changes (Table I, p.3). Alternating outer and inner bridges "might cause unbalance of MMF vector, higher harmonics or larger pull force on rotor" (D11 §IV, p.4). EV-46 records the pull force: 0.026 N for the outer bridge against 0.68 N and 0.65 N for two inner-bridge types. | D11 p.3 §II.D and p.4 §IV; EV-46 | `verified` (read in D11; the force values as recorded in EV-46) |
| Electrical balance: equal phase resistance and inductance | Link and stub copper differ per phase (EQ-23 l_k, s_k). Fabrication tolerance is outside the model. | EQ-23 formula (equation_registry.json) | `inferred` |
| Torque, torque ripple and cogging | Torque needs the EMF magnitude and the current (EQ-09, EQ-20). Ripple needs the EMF harmonics and the drive current waveform. The check computes neither. | EQ-09 "ripple not included" (equation_specification.md EQ-09 limitations) | `not tested` |
| Efficiency and losses, including the delta circulating current | Losses come from EQ-07, EQ-10, EQ-12 and EQ-26. The check reads no resistance and no harmonic amplitude. | EQ-26 (equation_registry.json) | `not tested` |
| Equal parallel paths | The check covers the series pattern. The parallel-path rule (a divides t) is `inferred` with no textbook source. | equation_specification.md l.217 to l.219; EV-89 and EV-90 do not cover parallel paths (build_registry.py EXTRA_SOURCES, EQ-08) | `inferred` |

The analysis does compute one EMF phasor per phase from the field model (`src/embodic/physics/analyse.py` l.362). That
phasor is an estimate under EQ-06 and its assumptions, not a measurement. The "Balanced." text does not read it
(`src/embodic/ui/viewmodels/session.py` l.606 to l.614). `verified` (read in the code).

**The no-claims rule.** Standing orders rule 2 (the brief's rule 6) forbids balance claims from geometry or phase
angles alone. The check uses phase angles only. "Balanced." with no qualifier therefore reads as the claim that the rule
forbids. The
accurate term is "symmetric 3-phase winding". Fable rules on scope (DEF-UV8-04). This is the engineering reading that
the ruling can use.

## 3. The sentence the user copy must match

The engineering truth for the pass case is "Symmetric 3-phase winding pattern (star of slots). The three phases are 120°
apart. This is a property of the pattern, not a measured balance of the motor."

The copy may be shorter. It must keep these three facts.

- The pass is about the winding pattern, not the built motor.
- It names the method or the pattern ("star of slots", "symmetric", "pattern").
- It names no torque, efficiency, ripple, or magnetic balance.

The hint `hint-combination.balanced` ("Balanced: q = {q}, periodicity t = {t}.", design.py l.218) follows the same rule,
for example "Symmetric 3-phase pattern: q = {q}, periodicity t = {t}." The fail case says what fails: "No symmetric
3-phase pattern for {coils} coils and {poles} poles."

## 4. How to re-check

- Code lines: `src/embodic/winding/star_of_slots.py` l.40 to l.79, `src/embodic/winding/feasibility.py` l.27 to l.46,
  `src/embodic/ui/viewmodels/session.py` l.606 to l.640, read on worktree U-E14 (main 3440241).
- D08: `B2/799354017-Pcb-stator-thesis.pdf` p.36, text read with `pdftotext -layout -f 36 -l 37`.
- D11: `B2/Performance_Improvement_by_Pattern_Optimization_of_PCB_Winding_in_Coreless_AFPM_Motor.pdf` p.3 to p.4. The
  text layer of that PDF is shifted by 29 code points. Shifting each character back recovers the quoted sentences.
