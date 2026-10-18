Prepared by Agent 2 (Motor Design), model claude-opus-5-5. Unit U-E20, D-059b, 2026-10-18.

# Result chains of analyse() (fix wave F4)

This document rules on the eight questions of `docs/phase3/engineering/U-M8h_chains.md` ("Questions for Agent 2").
It gives the expected chain of every D08 result and lists the defects the rulings imply. It reads main ac14878, which
already holds the U-M8h chain code (`src/embodic/physics/analyse.py` l.274 to l.280 build the intermediates). Status
labels follow standing order 2. No number in this document is a measurement.

The check is `docs/phase3/engineering/checks/f4_chain_audit.py`. It computes the five shipped examples through
`embodic.api.compute`, compares every chain with the rulings, and runs the probes that sections A and C quote. It
writes nothing. Run it from the repository root:

```
PYTHONPATH=src python docs/phase3/engineering/checks/f4_chain_audit.py
```

`EXPECTED_D08` in that script is the machine-readable copy of section B, for a test to pin. Chains below drop the
`EQ-` prefix.

## A. Rulings on the eight questions

### A.1 The phase current conversion is EQ-09

Ruling. Yes. `phase_current` is EQ-09 for star and delta. Status: verified (read).

References. Registry EQ-09 formula: "star: Ke_LL = sqrt(3)*Ke_ph, I_ph = I_line; delta: Ke_LL = Ke_ph,
I_ph = I_line/sqrt(3)". `equation_specification.md` EQ-09 (l.223 to l.224) says the same. The code is
`analyse.py` l.325 to l.326.

Consequences.

- loss_copper (10, 11, 07, 09), current_density (22, 09) and ipc_guideline_current (15, 09) are right.
- loss_interconnect needs EQ-09 too, which U-M8h did not add. `interconnect_loss_w` forms `I_line / sqrt(3)` for delta
  itself (`src/embodic/physics/interconnect.py` l.224 to l.226). For star it puts I_line through the link copper, which
  is EQ-09's `I_ph = I_line`. The registry EQ-23 formula names I_ph for delta. The chain is (23, 10, 09). Status:
  inferred. Part 5 of the check reproduces the delta kernel with example sums (0.26 W both ways).
- ipc_guideline_current keeps (15, 09), but EQ-09 is its own equation, not a source. The code never reads I_ph there.
  It converts the phase capacity to a line capacity, times sqrt(3) for delta (`analyse.py` l.415). That is the inverse
  of the EQ-09 identity. The chain is the same. The code should name EQ-09 in `eq_ids` instead of
  `built_from=(phase_current,)`.

### A.2 ke_phase needs no EQ-09

Ruling. No. ke_phase stays (06, 07, 05), plus 04 for a block magnet. Status: inferred.

Reasons.

- The code applies no EQ-09 step to ke_phase. The phase phasors are already per mechanical rad/s
  (`CircuitSolution.phase_emf_phasor_v_s_per_rad`, `src/embodic/physics/circuit.py` l.48), and
  `ke_ph = abs(emf[ph][0])` (`analyse.py` l.318). Nothing divides by omega_m.
- "Ke_ph = |E1|/omega_m" in EQ-09 is the definition that EQ-06 already carries for a path. The registry EQ-06 formula
  reads "Ke_n = |sum_seg B_z,n(r_m, z_L)*r_m*dr*exp(-j*n*p*theta_m)| (T*mm^2 x 1e-6 = V*s/rad)", and its variable Ke_n
  is the "peak EMF constant of harmonic n per mechanical rad/s". EQ-07 sums the path phasors into the phase phasor. So
  ke_phase is EQ-06's Ke_1 of the EQ-07 phase phasor.
- ADR-0003 l.72 gives one row to three results ("Phase Ke, line Ke, torque at the operating point") with the chain
  EQ-04 to EQ-09. That row is the union of three chains. It does not give EQ-09 to phase Ke alone.
- The badge loses no evidence. OR-01 carries EQT-05-O1 and EQT-06-O1 as well as EQT-09-O1
  (`tests/unit/physics/test_oracles.py` l.90), and EQ-05 and EQ-06 stay in the chain.

### A.3 ke_line_peak drops EQ-09, and thd_line is right

Ruling. ke_line_peak is (18, 07, 06, 05), plus 04 for a block magnet. thd_line (18, 07, 06, 05) is right. Status:
inferred.

Reasons.

- EQ-09's Ke_LL is a fundamental quantity. The registry EQ-09 `source_notes` end with "fundamental only", and the spec
  gives "Validity: fundamental" (l.227).
- ke_line_peak is the peak of the synthesised line waveform over all harmonics (`analyse.py` l.400 and l.404). The line
  phasors are EQ-18: "star line EMF = phase difference; delta line EMF = phase EMF minus the three-phase mean" (spec
  l.405 to l.406, `_line_phasors` l.778). No sqrt(3) factor and no other EQ-09 identity enters.
- The run shows that the two are different quantities. For D08, ke_line / ke_phase = 1.732050807569 (EQ-09) and
  ke_line_peak / ke_line = 0.984027138 (Part 5).
- EQT-09-O1 can stay linked to EQ-09. D08's reference value 0.0309 V*s/rad comes from 1.47 V at 454 rpm through
  EQ-09's Ke = E/omega_m (spec l.228 to l.229). That conversion is on the measured side, not in the model chain.

Consequence. The pin at `tests/golden/m2_physics/test_analyse_layouts.py` l.229 changes to
`("EQ-18", "EQ-07", "EQ-06", "EQ-05")`.

### A.4 A result takes the validity flags of what it is built from

Ruling. Yes. Status: verified for the rule (read). The gap in the code is verified (ran, Part 3).

References.

- ADR-0003 decision 2 (l.36 to l.43). The badge is the weakest of the chain's evidence, the test state and "the
  validity cap: a violated validity limit of an EQ in the chain ⇒ `unresolved`".
- `docs/phase2/architecture/interfaces.md` l.1412 to l.1414. "A result's chain includes the chains of the intermediate
  results it uses."
- Registry EC-05 `rule`: "e_edge <= 0.10: no badge cap; one-sided tolerance add-on +e_edge (model high) on Ke, EMF,
  torque and EMF-derived results, limitation listed; e_edge > 0.10: badge capped at unresolved".

A result takes these five things from each source.

1. The source's equations, and so their evidence status and test state (interfaces.md l.1412). A value cannot be
   trusted more than the equations it was computed with.
2. The equation-level assumptions of that chain. `traced` already builds them from the full chain
   (`src/embodic/results/traceable.py` l.145 to l.147).
3. The validity flags evaluated for this design on that chain, with their effect. A `cap` flag caps the result. A
   `limitation` flag is listed on the result. A field outside the EQ-05 validity range gives an EMF outside it, and
   every value computed from that EMF is outside it too. ADR-0003 says "an EQ in the chain", and item 1 puts the
   source's equations in the chain.
4. The source's inputs, for the tag (ADR-0003 decision 3; `traceable.py` l.139 to l.141). The code lists them by hand.
5. A trust label of a source equation, "estimate" or "guideline (unverified)". A value computed from an estimate is an
   estimate.

A result does not take these three things.

- A bound label, "upper bound" or "lower bound". It states the error direction of one quantity. A sum with terms that
  are not bounds loses it, and a ratio can invert it. EQ-19's P_delta,circ is an upper bound (spec l.419). An upper
  bound on P_loss makes eta = P_out / (P_out + P_loss) a lower bound at best, yet the code labels efficiency "upper
  bound" (DEF-UE20-02). The label belongs only to the quantity its equation computes. Status: inferred.
- The number of a graded flag's add-on, unless the result is proportional to the field. The EC-05 sign "model high by
  e_edge" holds for Ke, EMF, Kt, torque and output power at a fixed operating point. It does not hold for Kv, which
  goes with 1/Ke_LL, for THD, which is a ratio, or for losses that go with B^2 or |E_i - E_grp|^2. No code reads
  `one_sided_addon` today (only `status.py` l.67 and `traceable.py` l.177 name it), so nothing visible changes. Status:
  inferred.
- The source's tolerance. The result's first EQ-ID gives it (`traceable.py` l.159).

The code gap. `traced` combines only the flags its caller passes (`traceable.py` l.146), and an `Intermediate` holds no
flags (l.44 to l.48). Part 3 sets the EC-05 threshold to 0, so that e_edge caps, and marks every linked test passed.
Eleven D08 results built from the EQ-05 field then keep their badge while ke_phase reads `unresolved`. They are
loss_eddy, loss_circulating, output_power, thd_phase, thd_line, inductance_estimate (already `unresolved` through
EQ-14), the two layers' b1_peak_mid_radius_t and the three phases' circulating_loss. Two other flags have the same gap,
by reading of `analyse.py`.

- RANGE_SKIN_DEPTH is absent from loss_circulating, the phase circulating losses, loss_delta_circulating,
  loss_interconnect and the drive results (l.522 to l.529, l.565 to l.577, l.585). All of them are built from the
  resistances.
- INTERNAL_INTERCONNECT_UNCLASSIFIED is absent from loss_delta_circulating, which is built from `interconnect_r`
  (l.568 to l.576).

No shipped example raises either flag (not tested).

### A.5 edge_leakage_fraction holds EQ-04 for a block magnet, and no EQ-06

Ruling. The chain is (05) for an arc magnet and (05, 04) for a block magnet. Status: inferred.

Reasons.

- The EC-05 weight is w = |B_z,1(r_m, z_L)*r_m*dr| (registry EC-05 `metric`). B_z,1 is the EQ-05 field. For a block
  magnet that field uses the alpha_p(r) of EQ-04 (`src/embodic/physics/emf.py` l.42 to l.44). So the metric is built
  from `field`.
- EQ-06 does not enter. The registry defines the whole metric inside the check of EQ-05, segment selection included
  ("over EMF-producing segments inside the magnet span"). The code computes the weights in the flux-linkage loop
  (`emf.py` l.170 to l.172), but the docstring assigns them to EC-05 (l.129). The EQ-12 eddy sums come from the same
  loop, and loss_eddy holds no EQ-06 either (kept in section B). Adding EQ-06 would also break the rule of
  `tests/unit/physics/test_emf_chain.py` l.20, which wants EQ-07 beside every EQ-06.
- `traced_validity_metric` takes no `built_from` (`traceable.py` l.184 to l.199). Its badge reads the own equation
  only (l.200, `_uncapped_badge`). It should read the uncapped badge of the whole chain, combined with the calibration
  and transfer statuses as today. On the shipped registry no badge changes. EQ-04 is `verified`, and the transfer
  status `assumption` stays the weakest (inferred; Part 3 prints `assumption` for the arc-magnet D08).

### A.6 loss_delta_circulating is EQ-19 alone for star and open

Ruling. For star and open, loss_delta_circulating is (19) with no validity flag. For delta it stays
(19, 07, 06, 05, 10, 11, 23), plus 04 for a block magnet. Status: inferred.

Reasons.

- For star and open the code computes nothing. The value is the constant 0.0 (`analyse.py` l.385 to l.389).
- EQ-19 is valid for "delta connection, m = 3" (spec l.418). A star or open winding has no closed mesh, so no
  zero-sequence current flows and 0 W is exact for that connection. It does not depend on the field, the EMF or a
  resistance.
- Today it carries their chain and the EC-05 flag (Part 4 prints value 0.0, validity ['EC-05']). With EC-05 capping,
  the exact 0 W reads `unresolved` (Part 3).
- EQ-19 stays as its own EQ-ID. It names the quantity, gives the tolerance and the chip, and `traced` refuses a
  computed result without an EQ-ID (`traceable.py` l.142).

General rule. A result whose value is a constant of the connection takes its own EQ-ID and nothing else. The same rule
gives loss_interconnect (23) for an open connection (`interconnect.py` l.227 to l.228). All five shipped examples are
star, so the delta and open branches are not exercised (not tested).

loss_total keeps EQ-19 through the star loss_delta_circulating (19). It loses the "upper bound" label (A.4).

### A.7 The drive speed axis takes the no-load speed chain

Ruling. torque_speed.speed_rpm is (20, 09, 06, 07, 05), the chain of no_load_speed, plus 04 for a block magnet.
torque_n_m, power_w and base_speed_rpm keep the full chain. Status: verified (read and ran).

Reasons. `torque_speed_envelope` sets `rpm_end = no_load_speed_rpm(ke, dc_link_v, modulation, connection) * 1.15` and
`speed[i] = rpm_end * i / (points - 1)` (`src/embodic/physics/drive.py` l.152 to l.158). Resistance and inductance do
not enter the axis. Part 5 runs the kernel with R 0.5 and 2.0 ohm and L 1e-4 and 5e-3 H (example values). The speed
axes are equal, the torque curves differ, and the axis equals linspace(0, 1.15 n_0, 121). power_w is torque times speed
and base_speed reads both arrays (`analyse.py` l.601, l.644), so they keep the torque curve's chain.

### A.8 b1_peak_mid_radius_t holds no EQ-04 for an arc magnet

Ruling. Confirmed. Status: verified (read and ran).

References. The spec EQ-04 validity reads "Arc magnets keep constant α_p" (l.97). `pole_arc_ratio_mm` returns the
given ratio for an `ArcMagnet` and evaluates EQ-04 only for a block magnet (`emf.py` l.42 to l.44).
`pole_arc_ratio_eq_ids` matches it (l.47 to l.49). Part 5 prints alpha_p 0.72 at r 20, 30 and 40 mm and no EQ-ID for
D08, and 0.766838, 0.510148 and 0.382331 with EQ-04 for spiral_12c16p_default.

Consequence. For an arc magnet alpha_p is the input `/rotor/magnet/pole_arc_ratio`. For a block magnet EQ-04 computes
it from `/rotor/magnet/width_mm`. Neither pointer is in `field_refs` (`analyse.py` l.342 to l.351). Part 5 prints
False for the first one. Both have provenance `example` in the shipped examples, so the tag of every EMF result misses
them. The tag still shows the text "alpha_p (magnet shape)", an EQ-05 dominant assumption with no `fields`
(DEF-UE20-08).

## B. Expected chains of the D08 example

D08 is spiral_12c10p_d08, with arc magnets, a star connection and no DC link. "Same" means equal to the "after" column of
U-M8h_chains.md, which equals the code on ac14878 (Part 1 compares all 50 rows). Rows for k = 0 to 1 (layers) and
k = 0 to 2 (phases) share one line.

| path | expected chain | U-M8h after | why it differs |
|---|---|---|---|
| ke_phase_v_s_per_rad | 06, 07, 05 | same | |
| ke_line_v_s_per_rad | 09, 06, 07, 05 | same | |
| ke_line_peak_v_s_per_rad | 18, 07, 06, 05 | 18, 09, 07, 06, 05 | A.3. No EQ-09 identity forms it. |
| kt_n_m_per_a | 09, 06, 07, 05 | same | |
| kv_rpm_per_v | 09, 06, 07, 05 | same | |
| winding_factor_1 | 27, 06, 07, 05 | same | |
| resistance_phase_20c_ohm | 10, 11, 07 | same | |
| resistance_phase_operating_ohm | 10, 11, 07 | same | |
| resistance_line_ohm | 23, 10, 11, 07 | same | |
| emf_phase_rms_v | 06, 07, 05 | same | |
| torque_n_m | 09, 06, 07, 05 | same | |
| loss_copper_w | 10, 11, 07, 09 | same | A.1 confirms the EQ-09. |
| loss_eddy_w | 12, 05, 10 | same | |
| loss_circulating_w | 07, 06, 05, 10, 11 | same | |
| loss_delta_circulating_w | 19 | 19, 07, 06, 05, 10, 11, 23 | A.6. Star, so the value is the constant 0.0. |
| loss_interconnect_w | 23, 10, 09 | 23, 10 | A.1. The link current is I_ph. |
| loss_total_w | 26, 10, 11, 07, 09, 12, 05, 06, 19, 23 | same | EQ-19 now comes from the own EQ-ID of loss_delta_circulating_w. |
| output_power_w | 26, 09, 06, 07, 05 | same | |
| efficiency | 26, 09, 06, 07, 05, 10, 11, 12, 19, 23 | same | |
| motor_constant_n_m_per_sqrt_w | 26, 09, 06, 07, 05, 10, 11 | same | |
| thd_phase | 18, 07, 06, 05 | same | |
| thd_line | 18, 07, 06, 05 | same | A.3 |
| current_density_a_per_mm2 | 22, 09 | same | |
| skin_depth_mm | 13, 10 | same | |
| inductance_estimate_h | 14, 27, 06, 07, 05 | same | |
| ipc_guideline_current_a | 15, 09 | same | A.1. EQ-09 is its own equation, not a source. |
| mass_copper_g | 16 | same | |
| mass_laminate_g | 16 | same | |
| temperature_rise_k | 17, 26, 10, 11, 07, 09, 12, 05, 06, 19, 23 | same | |
| edge_leakage_fraction | 05 | same | A.5. A block magnet adds 04. |
| layers[k].z_mm | 05 | same | See open question E.1. |
| layers[k].b1_peak_mid_radius_t | 05 | same | A.8 |
| phases[k].ke_peak_v_s_per_rad | 06, 07, 05 | same | |
| phases[k].emf_phasor_angle_rad | 06, 07, 05 | same | |
| phases[k].resistance_20c_ohm | 10, 11, 07 | same | |
| phases[k].resistance_operating_ohm | 10, 11, 07 | same | |
| phases[k].circulating_loss_w | 07, 06, 05, 10, 11 | same | |
| emf_waveform_v | 18, 07, 06, 05 | same | |

(revision 2026-10-18, U-E21; D-060d) The `layers[k].z_mm` row above no longer holds. Its expected chain is empty. The
stack-up gives the copper z from the inputs alone, so the value takes no field equation and its kind tag is `derived`.
D-060d in `docs/decision_log.md` answers open question E.1 this way. `EXPECTED_D08` in
`docs/phase3/engineering/checks/f4_chain_audit.py` and in `tests/unit/physics/test_expected_chains.py` carries `()` for
both rows. The other 48 rows of this table stand.

Rows of the other examples that the rulings change (Part 2, `EXPECTED_OTHER`). All four examples are star.

| example | path | expected chain | U-M8h after | ruling |
|---|---|---|---|---|
| spiral_12c16p_default, spiral_12c14p (block) | ke_line_peak_v_s_per_rad | 18, 07, 06, 05, 04 | 18, 09, 07, 06, 05, 04 | A.3 |
| same | edge_leakage_fraction | 05, 04 | 05 | A.5 |
| same | loss_delta_circulating_w | 19 | 19, 07, 06, 05, 04, 10, 11, 23 | A.6 |
| same | loss_interconnect_w | 23, 10, 09 | 23, 10 | A.1 |
| serpentine_16p_example, wave_16p_example (arc) | ke_line_peak_v_s_per_rad, loss_delta_circulating_w, loss_interconnect_w | as D08 | as D08 | A.3, A.6, A.1 |
| same | torque_speed.speed_rpm | 20, 09, 06, 07, 05 | 20, 14, 27, 06, 07, 05, 09, 23, 10, 11 | A.7 |
| same | torque_speed.no_load_speed_rpm | 20, 09, 06, 07, 05 | same | |
| same | torque_speed.torque_n_m, power_w, base_speed_rpm | 20, 14, 27, 06, 07, 05, 09, 23, 10, 11 | same | |

Expected flags and labels of D08, which a test can pin with the chains.

- EC-05 on every result built from the field. These are all rows with 05 in the chain except three:
  edge_leakage_fraction (its own flag, present today), layers[k].z_mm (not built from the field, E.1) and
  loss_delta_circulating_w (A.6). The rule adds EC-05 to the eleven results that Part 3 prints as "NO FLAG", the two
  z_mm rows excepted.
- "upper bound" only on loss_delta_circulating_w. No bound label on loss_total_w, efficiency or temperature_rise_k.
  "estimate" stays on inductance_estimate_h, "guideline (unverified)" on ipc_guideline_current_a, and "lower bound" on
  edge_leakage_fraction, which is the EC-05 metric bound (`traceable.py` l.206).

## C. Defects

Every row reproduces with the command at the top of this document. Owner of the code: Agent 3, through Fable.

| ID | Defect | Reproduce | Expected | Severity |
|---|---|---|---|---|
| DEF-UE20-01 | Validity flags do not travel with `built_from` (A.4). | Part 3 prints "NO FLAG" and badge `inferred` for loss_eddy_w, loss_circulating_w, output_power_w, thd_phase, thd_line, both b1_peak_mid_radius_t and the three circulating_loss_w. It prints "NO FLAG" for inductance_estimate_h, `unresolved` through EQ-14. ke_phase_v_s_per_rad prints "flag" and `unresolved`. | Each result carries the flags of its sources, so all eleven read `unresolved` when e_edge exceeds the threshold. RANGE_SKIN_DEPTH and INTERNAL_INTERCONNECT_UNCLASSIFIED travel the same way. | High. The badge shows more trust than D-007 allows. |
| DEF-UE20-02 | A bound label travels along the chain (A.4). `traced` takes the first label of the chain (`traceable.py` l.162). | Part 4 prints 'upper bound' for loss_total_w, efficiency and temperature_rise_k of D08, where P_delta is 0.0. The PDF report (`src/embodic/io/report.py` l.116) and the result cards (`src/embodic/ui/viewmodels/results.py` l.90, l.106, l.265) show the label. | Only loss_delta_circulating_w carries "upper bound". Trust labels still travel. | Medium. The label states the wrong direction for efficiency. |
| DEF-UE20-03 | loss_delta_circulating_w for star and open takes the EMF, resistance and interconnect chains and the EC-05 flag, though its value is the constant 0.0 (A.6). | Part 1 DIFF row. Part 4 prints value 0.0, validity ['EC-05']. Part 3 prints badge `unresolved`. | Chain (19), no flag, for star and open. | Medium. |
| DEF-UE20-04 | ke_line_peak_v_s_per_rad holds EQ-09 (A.3). | Part 1 DIFF row. Part 5 prints ke_line_peak / ke_line = 0.984027138. | (18, 07, 06, 05), plus 04 for a block magnet. The pin at test_analyse_layouts.py l.229 changes. | Low. No badge changes on the shipped registry. |
| DEF-UE20-05 | loss_interconnect_w lacks EQ-09 (A.1). | Part 1 DIFF row. Part 5 prints the delta kernel equal to I_line^2 sum s + (I_line/sqrt3)^2 sum l. | (23, 10, 09). | Low. |
| DEF-UE20-06 | edge_leakage_fraction lacks EQ-04 for a block magnet. `traced_validity_metric` takes no `built_from`, and its badge reads one equation (A.5). | Part 2 DIFF rows of spiral_12c16p_default and spiral_12c14p. | (05, 04). Badge = weakest of the chain's uncapped badge, the calibration status and the transfer status. | Low. No badge changes today. |
| DEF-UE20-07 | torque_speed.speed_rpm takes the chain of the whole envelope call (A.7). | Part 2 DIFF rows of serpentine_16p_example and wave_16p_example. Part 5 prints the axis equal for two R and L pairs. | (20, 09, 06, 07, 05), plus 04 for a block magnet. The badge stays `unresolved` (EQ-20 `cannot verify yet`). The tag shrinks to that of no_load_speed. | Low. |
| DEF-UE20-08 | Used inputs are missing from `inputs`, so the tag misses them: `/rotor/magnet/pole_arc_ratio` (arc) and `/rotor/magnet/width_mm` (block) from `field_refs` (`analyse.py` l.342 to l.351), and `/operating/ambient_temperature_degc` from ipc_guideline_current (l.409, l.734 to l.741). | Part 5 prints False for the pole-arc ratio in the ke_phase inputs and for the ambient temperature in the ipc inputs. The block width follows from the static `field_refs` list (read). | Every pointer the calculation reads is in `inputs`, so the tag lists it when its provenance is `example` or `default`. | Low. |

## D. What I ran

The check on the worktree at ac14878, `PYTHONPATH=/home/claude/wt/U-E20/src /home/claude/embodic/.venv/bin/python
docs/phase3/engineering/checks/f4_chain_audit.py`, exit 0. The shipped registry has 0 passed tests in this tree, so
Part 3 marks every linked test passed itself. The excerpt keeps whole lines and drops the others:

```
registry v1+75a1fa2f8018.c01a66176ad6; EQ-19 label 'upper bound'; passed tests 0
Part 1. D08 chains, code vs ruling
  results computed 50, rows in EXPECTED_D08 50, unmatched paths set()
  DIFF spiral_12c10p_d08 ke_line_peak_v_s_per_rad: code 18, 09, 07, 06, 05 | ruling 18, 07, 06, 05
  DIFF spiral_12c10p_d08 loss_delta_circulating_w: code 19, 07, 06, 05, 10, 11, 23 | ruling 19
  DIFF spiral_12c10p_d08 loss_interconnect_w: code 23, 10 | ruling 23, 10, 09
  spiral_12c10p_d08: 50 rows compared, 3 differ from the ruling
Part 2. Rows of other examples named by the rulings
  DIFF spiral_12c16p_default edge_leakage_fraction: code 05 | ruling 05, 04
  DIFF wave_16p_example torque_speed.speed_rpm: code 20, 14, 27, 06, 07, 05, 09, 23, 10, 11 | ruling 20, 09, 06, 07, 05
Part 3. D08, EC-05 threshold 0 (e_edge caps), every linked test passed
  e_edge = 0.017380
  flag    ke_phase_v_s_per_rad                   badge unresolved  chain 06, 07, 05
  NO FLAG output_power_w                         badge inferred    chain 26, 09, 06, 07, 05
  flag    loss_delta_circulating_w               badge unresolved  chain 19, 07, 06, 05, 10, 11, 23
Part 4. D08 (star) labels and the delta circulating loss
  label 'upper bound'              efficiency (chain 26, 09, 06, 07, 05, 10, 11, 12, 19, 23)
  loss_delta_circulating_w value 0.0, validity ['EC-05']
Part 5. Kernel facts
  Q3 D08 star: ke_line_peak / ke_line = 0.984027138 (1 only for a fundamental-only waveform)
  Q7 speed axis equal for R 0.5/2.0 ohm and L 1e-4/5e-3 H: True; torque equal: False; axis == linspace(0, 1.15 n0): True
```

`ruff check` and `ruff format --check` pass on the script. I ran no test suite.

## E. Follow-ups and open questions

Follow-ups.

1. Agent 3 fixes DEF-UE20-01 to DEF-UE20-08 in one wave and pins section B (chains, flags and labels) in a test, for
   example next to `tests/unit/physics/test_emf_chain.py`. One possible shape, an assumption that the code worker may
   replace: `Intermediate` gains `validity`; `traced` unions its own flags with those of every source, keyed by code;
   `field` is built after e_edge, with the EC-05 flag; the explicit `emf_validity` arguments that the sources then
   supply go away.
2. Agent 4 verifies the rulings with its own script and expected values.
3. Agent 2 can state in the registry EC-05 `rule` which results take the numeric add-on (A.4). The registry is not
   edited in this unit.

Open questions.

1. layers[k].z_mm is a `derived` geometry value with the chain (05). The copper z comes from the stack-up, not from the
   field, yet the value takes EQ-05's badge (`inferred`). Should a derived value carry an EQ-ID at all? Status:
   unresolved.
2. ke_phase is the mean of the phases' |E1| (`analyse.py` l.320). No registry or spec text states that mean. For a
   winding whose phases differ, the mean hides the spread. This notes a missing definition and says nothing about
   balance. Status: unresolved.
3. The OR-01 docstring names EQ-07 and EQ-18 in the chain it checks (`test_oracles.py` l.95), but the test carries
   only EQT-05-O1, EQT-06-O1 and EQT-09-O1. Should EQ-07 and EQ-18 link an O1 test? Status: unresolved.
