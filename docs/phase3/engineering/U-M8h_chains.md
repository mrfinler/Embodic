# U-M8h chain table (Agent 3, claude-opus-5-5), D-058d

Every result of `analyse()` before (main 6319959) and after (branch unit/U-M8h, commit 3be203f), as computed. Status of
every row: `verified` (ran). Badge (i) is the shipped registry, `load_registry()`; in this tree it reads 0 passed tests
because `resources/evidence/passed_tests.v1.json` is absent, so (i) shows the badge of a build without evidence. Badge
(ii) is the same registry with every linked test passed. "Assumed inputs" is the length of the "n assumed inputs" tag.

Reproduce (scripts in `scratchpad/U-M8h/`):

```
git archive 6319959 src resources | tar -x -C U-M8h/base
PYTHONPATH=U-M8h/base/src python U-M8h/chain_table.py <example> U-M8h/before/<example>.json
PYTHONPATH=<worktree>/src python U-M8h/chain_table.py <example> U-M8h/after/<example>.json
python U-M8h/compare.py U-M8h/before U-M8h/after
```

## The rule as built

`traced(..., eq_ids=own, built_from=(...))` gives `own` first, then the chain of each source in order, each EQ-ID once
(`src/embodic/results/traceable.py`, `chain`). A source is a Traceable or an `Intermediate`. analyse() names each
unreported value once, where it is produced:

| Intermediate | Chain | Code that produces it |
|---|---|---|
| rho_t | 10 | `copper_resistivity_ohm_m` (EQ-10 rho_T) |
| field | 05, plus 04 for a block magnet | `field_table`, `field_harmonic`, `pole_arc_ratio_mm` (EQ-04 only for a block magnet) |
| flux_linkage | 06, field | `integrate_path` |
| path_r | 10, rho_t | `path_resistance_ohm` |
| via_r | 11, rho_t | `via_resistance_ohm` |
| phase_emf | 07, flux_linkage | `solve_phase_circuit` EMF phasors |
| phase_r | 07, path_r, via_r | `solve_phase_circuit` phase resistance |
| phase_current | 09 | `i_ph = i_line / sqrt(3)` for delta (registry formula of EQ-09: "delta: I_ph = I_line/sqrt(3)") |
| interconnect_r | 23, path_r, rho_t | `interconnect_resistance` |
| line_emf | 18, phase_emf | `_line_phasors` (docstring: EQ-18) |
| ideal_chain | 27, field | `_ideal_integral` |

The own equations of each result are those it listed before, minus what a source now supplies. The first EQ-ID of every
result is unchanged, so the tolerance and the UI chip do not move.

## Summary per example
- spiral_12c10p_d08: 50 results; values identical: True []; eq_ids changed: 29 (set changed: 21, order only: 8); badge changed under (i) or (ii): 0 []
- spiral_12c14p: 50 results; values identical: True []; eq_ids changed: 41 (set changed: 41, order only: 0); badge changed under (i) or (ii): 0 []
- spiral_12c16p_default: 50 results; values identical: True []; eq_ids changed: 41 (set changed: 41, order only: 0); badge changed under (i) or (ii): 0 []
- serpentine_16p_example: 63 results; values identical: True []; eq_ids changed: 38 (set changed: 30, order only: 8); badge changed under (i) or (ii): 0 []
- wave_16p_example: 55 results; values identical: True []; eq_ids changed: 34 (set changed: 26, order only: 8); badge changed under (i) or (ii): 0 []

No value changes (repr of every value equal) and no badge changes under (i) or (ii) in any example. The tag grows where
a chain gains an equation with equation-level assumptions.

## D08 (spiral_12c10p_d08, arc magnets, no DC link): every result

| path | quantity | eq_ids (EQ- prefix dropped) before -> after | badge (i) shipped | badge (ii) all tests passed | assumed inputs |
|---|---|---|---|---|---|
| ke_phase_v_s_per_rad | ke_phase_v_s_per_rad | 06, 07, 05 | not tested | inferred | 14 |
| ke_line_v_s_per_rad | ke_line | 09, 06, 07, 05 | not tested | inferred | 16 |
| ke_line_peak_v_s_per_rad | ke_line_peak | 18, 09, 06, 07, 05 -> **18, 09, 07, 06, 05** | not tested | inferred | 17 |
| kt_n_m_per_a | kt | 09, 06, 07, 05 | not tested | inferred | 16 |
| kv_rpm_per_v | kv | 09, 06, 07, 05 | not tested | inferred | 16 |
| winding_factor_1 | utilisation_factor_k_u | 27, 06, 07, 05 | not tested | inferred | 15 |
| resistance_phase_20c_ohm | resistance_phase_20c | 10, 11 -> **10, 11, 07** | not tested | inferred | 10 -> 11 |
| resistance_phase_operating_ohm | resistance_phase_operating | 10, 11 -> **10, 11, 07** | not tested | inferred | 10 -> 11 |
| resistance_line_ohm | resistance_line | 23, 10, 11 -> **23, 10, 11, 07** | not tested | inferred | 11 -> 12 |
| emf_phase_rms_v | emf_phase_rms | 06, 07, 05 | not tested | inferred | 15 |
| torque_n_m | torque | 09, 06, 07, 05 | not tested | inferred | 17 |
| loss_copper_w | loss_copper | 10, 11 -> **10, 11, 07, 09** | not tested | inferred | 11 -> 14 |
| loss_eddy_w | loss_eddy | 12, 05 -> **12, 05, 10** | not tested | inferred | 18 -> 20 |
| loss_circulating_w | loss_circulating | 07 -> **07, 06, 05, 10, 11** | not tested | inferred | 12 -> 23 |
| loss_delta_circulating_w | loss_delta_circulating | 19, 06, 07, 05 -> **19, 07, 06, 05, 10, 11, 23** | not tested | inferred | 21 -> 27 |
| loss_interconnect_w | loss_interconnect | 23, 10 | not tested | verified | 9 |
| loss_total_w | loss_total | 26, 10, 11, 12, 07, 19, 23, 09, 06, 05 -> **26, 10, 11, 07, 09, 12, 05, 06, 19, 23** | not tested | inferred | 35 |
| output_power_w | output_power | 26, 09, 06, 07, 05 | not tested | inferred | 19 |
| efficiency | efficiency | 26, 10, 11, 12, 07, 19, 23, 09, 06, 05 -> **26, 09, 06, 07, 05, 10, 11, 12, 19, 23** | not tested | inferred | 35 |
| motor_constant_n_m_per_sqrt_w | motor_constant | 26, 09, 06, 10, 11, 07, 05 -> **26, 09, 06, 07, 05, 10, 11** | not tested | inferred | 28 |
| thd_phase | thd_phase | 18, 06, 07, 05 -> **18, 07, 06, 05** | not tested | inferred | 14 |
| thd_line | thd_line | 18, 06, 07, 05 -> **18, 07, 06, 05** | not tested | inferred | 14 |
| current_density_a_per_mm2 | current_density | 22 -> **22, 09** | not tested | verified | 4 -> 5 |
| skin_depth_mm | skin_depth | 13, 10 | not tested | verified | 8 |
| inductance_estimate_h | inductance_estimate | 14, 27 -> **14, 27, 06, 07, 05** | unresolved | unresolved | 9 -> 17 |
| ipc_guideline_current_a | ipc_guideline_current | 15 -> **15, 09** | unresolved | unresolved | 6 -> 8 |
| mass_copper_g | mass_copper | 16 | not tested | assumption | 5 |
| mass_laminate_g | mass_laminate | 16 | not tested | assumption | 5 |
| temperature_rise_k | temperature_rise | 17, 26, 10, 11, 12, 07, 19, 23, 09, 06, 05 -> **17, 26, 10, 11, 07, 09, 12, 05, 06, 19, 23** | not tested | assumption | 37 |
| edge_leakage_fraction | edge_leakage_fraction | 05 | not tested | assumption | 10 |
| layers[0].z_mm | layer_z_mm | 05 | not tested | inferred | 8 |
| layers[0].b1_peak_mid_radius_t | b1_peak_mid_radius_t | 05, 04 -> **05** | not tested | inferred | 11 -> 9 |
| layers[1].z_mm | layer_z_mm | 05 | not tested | inferred | 8 |
| layers[1].b1_peak_mid_radius_t | b1_peak_mid_radius_t | 05, 04 -> **05** | not tested | inferred | 11 -> 9 |
| phases[0].ke_peak_v_s_per_rad | phase_ke_peak | 06, 07, 05 | not tested | inferred | 14 |
| phases[0].emf_phasor_angle_rad | phase_emf_phasor_angle | 06, 07, 05 | not tested | inferred | 14 |
| phases[0].resistance_20c_ohm | phase_resistance_20c | 10, 11 -> **10, 11, 07** | not tested | inferred | 10 -> 11 |
| phases[0].resistance_operating_ohm | phase_resistance_operating | 10, 11 -> **10, 11, 07** | not tested | inferred | 10 -> 11 |
| phases[0].circulating_loss_w | phase_circulating_loss | 07 -> **07, 06, 05, 10, 11** | not tested | inferred | 12 -> 23 |
| phases[1].ke_peak_v_s_per_rad | phase_ke_peak | 06, 07, 05 | not tested | inferred | 14 |
| phases[1].emf_phasor_angle_rad | phase_emf_phasor_angle | 06, 07, 05 | not tested | inferred | 14 |
| phases[1].resistance_20c_ohm | phase_resistance_20c | 10, 11 -> **10, 11, 07** | not tested | inferred | 10 -> 11 |
| phases[1].resistance_operating_ohm | phase_resistance_operating | 10, 11 -> **10, 11, 07** | not tested | inferred | 10 -> 11 |
| phases[1].circulating_loss_w | phase_circulating_loss | 07 -> **07, 06, 05, 10, 11** | not tested | inferred | 12 -> 23 |
| phases[2].ke_peak_v_s_per_rad | phase_ke_peak | 06, 07, 05 | not tested | inferred | 14 |
| phases[2].emf_phasor_angle_rad | phase_emf_phasor_angle | 06, 07, 05 | not tested | inferred | 14 |
| phases[2].resistance_20c_ohm | phase_resistance_20c | 10, 11 -> **10, 11, 07** | not tested | inferred | 10 -> 11 |
| phases[2].resistance_operating_ohm | phase_resistance_operating | 10, 11 -> **10, 11, 07** | not tested | inferred | 10 -> 11 |
| phases[2].circulating_loss_w | phase_circulating_loss | 07 -> **07, 06, 05, 10, 11** | not tested | inferred | 12 -> 23 |
| emf_waveform_v | emf_waveform | 18, 06, 07, 05 -> **18, 07, 06, 05** | not tested | inferred | 16 |

## Drive results (wave_16p_example; D08 has no DC link)

| path | quantity | eq_ids before -> after | badge (i) | badge (ii) | assumed inputs |
|---|---|---|---|---|---|
| torque_speed.speed_rpm | torque_speed_rpm | 20, 14, 09, 23 -> **20, 14, 27, 06, 07, 05, 09, 23, 10, 11** | unresolved | unresolved | 23 -> 36 |
| torque_speed.torque_n_m | torque_speed_torque | 20, 14, 09, 23 -> **20, 14, 27, 06, 07, 05, 09, 23, 10, 11** | unresolved | unresolved | 23 -> 36 |
| torque_speed.power_w | torque_speed_power | 20, 14, 09, 23 -> **20, 14, 27, 06, 07, 05, 09, 23, 10, 11** | unresolved | unresolved | 23 -> 36 |
| torque_speed.no_load_speed_rpm | no_load_speed | 20, 14, 09, 23 -> **20, 09, 06, 07, 05** | unresolved | unresolved | 23 -> 26 |
| torque_speed.base_speed_rpm | base_speed | 20, 14, 09, 23 -> **20, 14, 27, 06, 07, 05, 09, 23, 10, 11** | unresolved | unresolved | 23 -> 36 |

`no_load_speed` drops EQ-14 and EQ-23: `no_load_speed_rpm` takes only Ke, the DC link, the modulation and the
connection (`src/embodic/physics/drive.py` l.61). The other four take the chains of inductance_estimate, ke_line and
resistance_line, the three values `torque_speed_envelope` is called with.

## Block magnets (spiral_12c16p_default; spiral_12c14p gives the same rows): changed results

| path | quantity | eq_ids (EQ- prefix dropped) before -> after | badge (i) shipped | badge (ii) all tests passed | assumed inputs |
|---|---|---|---|---|---|
| ke_phase_v_s_per_rad | ke_phase_v_s_per_rad | 06, 07, 05 -> **06, 07, 05, 04** | not tested | inferred | 14 -> 16 |
| ke_line_v_s_per_rad | ke_line | 09, 06, 07, 05 -> **09, 06, 07, 05, 04** | not tested | inferred | 16 -> 18 |
| ke_line_peak_v_s_per_rad | ke_line_peak | 18, 09, 06, 07, 05 -> **18, 09, 07, 06, 05, 04** | not tested | inferred | 17 -> 19 |
| kt_n_m_per_a | kt | 09, 06, 07, 05 -> **09, 06, 07, 05, 04** | not tested | inferred | 16 -> 18 |
| kv_rpm_per_v | kv | 09, 06, 07, 05 -> **09, 06, 07, 05, 04** | not tested | inferred | 16 -> 18 |
| winding_factor_1 | utilisation_factor_k_u | 27, 06, 07, 05 -> **27, 06, 07, 05, 04** | not tested | inferred | 15 -> 17 |
| resistance_phase_20c_ohm | resistance_phase_20c | 10, 11 -> **10, 11, 07** | not tested | inferred | 10 -> 11 |
| resistance_phase_operating_ohm | resistance_phase_operating | 10, 11 -> **10, 11, 07** | not tested | inferred | 10 -> 11 |
| resistance_line_ohm | resistance_line | 23, 10, 11 -> **23, 10, 11, 07** | not tested | inferred | 11 -> 12 |
| emf_phase_rms_v | emf_phase_rms | 06, 07, 05 -> **06, 07, 05, 04** | not tested | inferred | 15 -> 17 |
| torque_n_m | torque | 09, 06, 07, 05 -> **09, 06, 07, 05, 04** | not tested | inferred | 17 -> 19 |
| loss_copper_w | loss_copper | 10, 11 -> **10, 11, 07, 09** | not tested | inferred | 11 -> 14 |
| loss_eddy_w | loss_eddy | 12, 05 -> **12, 05, 04, 10** | not tested | inferred | 18 -> 22 |
| loss_circulating_w | loss_circulating | 07 -> **07, 06, 05, 04, 10, 11** | not tested | inferred | 12 -> 25 |
| loss_delta_circulating_w | loss_delta_circulating | 19, 06, 07, 05 -> **19, 07, 06, 05, 04, 10, 11, 23** | not tested | inferred | 21 -> 29 |
| loss_total_w | loss_total | 26, 10, 11, 12, 07, 19, 23, 09, 06, 05 -> **26, 10, 11, 07, 09, 12, 05, 04, 06, 19, 23** | not tested | inferred | 35 -> 37 |
| output_power_w | output_power | 26, 09, 06, 07, 05 -> **26, 09, 06, 07, 05, 04** | not tested | inferred | 19 -> 21 |
| efficiency | efficiency | 26, 10, 11, 12, 07, 19, 23, 09, 06, 05 -> **26, 09, 06, 07, 05, 04, 10, 11, 12, 19, 23** | not tested | inferred | 35 -> 37 |
| motor_constant_n_m_per_sqrt_w | motor_constant | 26, 09, 06, 10, 11, 07, 05 -> **26, 09, 06, 07, 05, 04, 10, 11** | not tested | inferred | 28 -> 30 |
| thd_phase | thd_phase | 18, 06, 07, 05 -> **18, 07, 06, 05, 04** | not tested | inferred | 14 -> 16 |
| thd_line | thd_line | 18, 06, 07, 05 -> **18, 07, 06, 05, 04** | not tested | inferred | 14 -> 16 |
| current_density_a_per_mm2 | current_density | 22 -> **22, 09** | not tested | verified | 4 -> 5 |
| inductance_estimate_h | inductance_estimate | 14, 27 -> **14, 27, 06, 07, 05, 04** | unresolved | unresolved | 9 -> 19 |
| ipc_guideline_current_a | ipc_guideline_current | 15 -> **15, 09** | unresolved | unresolved | 6 -> 8 |
| temperature_rise_k | temperature_rise | 17, 26, 10, 11, 12, 07, 19, 23, 09, 06, 05 -> **17, 26, 10, 11, 07, 09, 12, 05, 04, 06, 19, 23** | not tested | assumption | 37 -> 39 |
| phases[0].ke_peak_v_s_per_rad | phase_ke_peak | 06, 07, 05 -> **06, 07, 05, 04** | not tested | inferred | 14 -> 16 |
| phases[0].emf_phasor_angle_rad | phase_emf_phasor_angle | 06, 07, 05 -> **06, 07, 05, 04** | not tested | inferred | 14 -> 16 |
| phases[0].resistance_20c_ohm | phase_resistance_20c | 10, 11 -> **10, 11, 07** | not tested | inferred | 10 -> 11 |
| phases[0].resistance_operating_ohm | phase_resistance_operating | 10, 11 -> **10, 11, 07** | not tested | inferred | 10 -> 11 |
| phases[0].circulating_loss_w | phase_circulating_loss | 07 -> **07, 06, 05, 04, 10, 11** | not tested | inferred | 12 -> 25 |
| phases[1].ke_peak_v_s_per_rad | phase_ke_peak | 06, 07, 05 -> **06, 07, 05, 04** | not tested | inferred | 14 -> 16 |
| phases[1].emf_phasor_angle_rad | phase_emf_phasor_angle | 06, 07, 05 -> **06, 07, 05, 04** | not tested | inferred | 14 -> 16 |
| phases[1].resistance_20c_ohm | phase_resistance_20c | 10, 11 -> **10, 11, 07** | not tested | inferred | 10 -> 11 |
| phases[1].resistance_operating_ohm | phase_resistance_operating | 10, 11 -> **10, 11, 07** | not tested | inferred | 10 -> 11 |
| phases[1].circulating_loss_w | phase_circulating_loss | 07 -> **07, 06, 05, 04, 10, 11** | not tested | inferred | 12 -> 25 |
| phases[2].ke_peak_v_s_per_rad | phase_ke_peak | 06, 07, 05 -> **06, 07, 05, 04** | not tested | inferred | 14 -> 16 |
| phases[2].emf_phasor_angle_rad | phase_emf_phasor_angle | 06, 07, 05 -> **06, 07, 05, 04** | not tested | inferred | 14 -> 16 |
| phases[2].resistance_20c_ohm | phase_resistance_20c | 10, 11 -> **10, 11, 07** | not tested | inferred | 10 -> 11 |
| phases[2].resistance_operating_ohm | phase_resistance_operating | 10, 11 -> **10, 11, 07** | not tested | inferred | 10 -> 11 |
| phases[2].circulating_loss_w | phase_circulating_loss | 07 -> **07, 06, 05, 04, 10, 11** | not tested | inferred | 12 -> 25 |
| emf_waveform_v | emf_waveform | 18, 06, 07, 05 -> **18, 07, 06, 05, 04** | not tested | inferred | 16 -> 18 |

## Serpentine and wave: changed results
## serpentine_16p_example

63 results; values identical: True []; eq_ids changed: 38 (set changed: 30, order only: 8); badge changed under (i) or (ii): 0 []

| path | quantity | eq_ids (EQ- prefix dropped) before -> after | badge (i) shipped | badge (ii) all tests passed | assumed inputs |
|---|---|---|---|---|---|
| ke_line_peak_v_s_per_rad | ke_line_peak | 18, 09, 06, 07, 05 -> **18, 09, 07, 06, 05** | not tested | inferred | 17 |
| resistance_phase_20c_ohm | resistance_phase_20c | 10, 11 -> **10, 11, 07** | not tested | inferred | 14 -> 15 |
| resistance_phase_operating_ohm | resistance_phase_operating | 10, 11 -> **10, 11, 07** | not tested | inferred | 14 -> 15 |
| resistance_line_ohm | resistance_line | 23, 10, 11 -> **23, 10, 11, 07** | not tested | inferred | 15 -> 16 |
| loss_copper_w | loss_copper | 10, 11 -> **10, 11, 07, 09** | not tested | inferred | 15 -> 18 |
| loss_eddy_w | loss_eddy | 12, 05 -> **12, 05, 10** | not tested | inferred | 22 -> 24 |
| loss_circulating_w | loss_circulating | 07 -> **07, 06, 05, 10, 11** | not tested | inferred | 16 -> 27 |
| loss_delta_circulating_w | loss_delta_circulating | 19, 06, 07, 05 -> **19, 07, 06, 05, 10, 11, 23** | not tested | inferred | 25 -> 31 |
| loss_total_w | loss_total | 26, 10, 11, 12, 07, 19, 23, 09, 06, 05 -> **26, 10, 11, 07, 09, 12, 05, 06, 19, 23** | not tested | inferred | 39 |
| efficiency | efficiency | 26, 10, 11, 12, 07, 19, 23, 09, 06, 05 -> **26, 09, 06, 07, 05, 10, 11, 12, 19, 23** | not tested | inferred | 39 |
| motor_constant_n_m_per_sqrt_w | motor_constant | 26, 09, 06, 10, 11, 07, 05 -> **26, 09, 06, 07, 05, 10, 11** | not tested | inferred | 32 |
| thd_phase | thd_phase | 18, 06, 07, 05 -> **18, 07, 06, 05** | not tested | inferred | 14 |
| thd_line | thd_line | 18, 06, 07, 05 -> **18, 07, 06, 05** | not tested | inferred | 14 |
| current_density_a_per_mm2 | current_density | 22 -> **22, 09** | not tested | verified | 8 -> 9 |
| inductance_estimate_h | inductance_estimate | 14, 27 -> **14, 27, 06, 07, 05** | unresolved | unresolved | 9 -> 17 |
| ipc_guideline_current_a | ipc_guideline_current | 15 -> **15, 09** | unresolved | unresolved | 10 -> 12 |
| temperature_rise_k | temperature_rise | 17, 26, 10, 11, 12, 07, 19, 23, 09, 06, 05 -> **17, 26, 10, 11, 07, 09, 12, 05, 06, 19, 23** | not tested | assumption | 41 |
| layers[0].b1_peak_mid_radius_t | b1_peak_mid_radius_t | 05, 04 -> **05** | not tested | inferred | 11 -> 9 |
| layers[1].b1_peak_mid_radius_t | b1_peak_mid_radius_t | 05, 04 -> **05** | not tested | inferred | 11 -> 9 |
| layers[2].b1_peak_mid_radius_t | b1_peak_mid_radius_t | 05, 04 -> **05** | not tested | inferred | 11 -> 9 |
| layers[3].b1_peak_mid_radius_t | b1_peak_mid_radius_t | 05, 04 -> **05** | not tested | inferred | 11 -> 9 |
| layers[4].b1_peak_mid_radius_t | b1_peak_mid_radius_t | 05, 04 -> **05** | not tested | inferred | 11 -> 9 |
| layers[5].b1_peak_mid_radius_t | b1_peak_mid_radius_t | 05, 04 -> **05** | not tested | inferred | 11 -> 9 |
| phases[0].resistance_20c_ohm | phase_resistance_20c | 10, 11 -> **10, 11, 07** | not tested | inferred | 14 -> 15 |
| phases[0].resistance_operating_ohm | phase_resistance_operating | 10, 11 -> **10, 11, 07** | not tested | inferred | 14 -> 15 |
| phases[0].circulating_loss_w | phase_circulating_loss | 07 -> **07, 06, 05, 10, 11** | not tested | inferred | 16 -> 27 |
| phases[1].resistance_20c_ohm | phase_resistance_20c | 10, 11 -> **10, 11, 07** | not tested | inferred | 14 -> 15 |
| phases[1].resistance_operating_ohm | phase_resistance_operating | 10, 11 -> **10, 11, 07** | not tested | inferred | 14 -> 15 |
| phases[1].circulating_loss_w | phase_circulating_loss | 07 -> **07, 06, 05, 10, 11** | not tested | inferred | 16 -> 27 |
| phases[2].resistance_20c_ohm | phase_resistance_20c | 10, 11 -> **10, 11, 07** | not tested | inferred | 14 -> 15 |
| phases[2].resistance_operating_ohm | phase_resistance_operating | 10, 11 -> **10, 11, 07** | not tested | inferred | 14 -> 15 |
| phases[2].circulating_loss_w | phase_circulating_loss | 07 -> **07, 06, 05, 10, 11** | not tested | inferred | 16 -> 27 |
| emf_waveform_v | emf_waveform | 18, 06, 07, 05 -> **18, 07, 06, 05** | not tested | inferred | 16 |
| torque_speed.speed_rpm | torque_speed_rpm | 20, 14, 09, 23 -> **20, 14, 27, 06, 07, 05, 09, 23, 10, 11** | unresolved | unresolved | 27 -> 40 |
| torque_speed.torque_n_m | torque_speed_torque | 20, 14, 09, 23 -> **20, 14, 27, 06, 07, 05, 09, 23, 10, 11** | unresolved | unresolved | 27 -> 40 |
| torque_speed.power_w | torque_speed_power | 20, 14, 09, 23 -> **20, 14, 27, 06, 07, 05, 09, 23, 10, 11** | unresolved | unresolved | 27 -> 40 |
| torque_speed.no_load_speed_rpm | no_load_speed | 20, 14, 09, 23 -> **20, 09, 06, 07, 05** | unresolved | unresolved | 27 -> 30 |
| torque_speed.base_speed_rpm | base_speed | 20, 14, 09, 23 -> **20, 14, 27, 06, 07, 05, 09, 23, 10, 11** | unresolved | unresolved | 27 -> 40 |

## wave_16p_example

55 results; values identical: True []; eq_ids changed: 34 (set changed: 26, order only: 8); badge changed under (i) or (ii): 0 []

| path | quantity | eq_ids (EQ- prefix dropped) before -> after | badge (i) shipped | badge (ii) all tests passed | assumed inputs |
|---|---|---|---|---|---|
| ke_line_peak_v_s_per_rad | ke_line_peak | 18, 09, 06, 07, 05 -> **18, 09, 07, 06, 05** | not tested | inferred | 17 |
| resistance_phase_20c_ohm | resistance_phase_20c | 10, 11 -> **10, 11, 07** | not tested | inferred | 10 -> 11 |
| resistance_phase_operating_ohm | resistance_phase_operating | 10, 11 -> **10, 11, 07** | not tested | inferred | 10 -> 11 |
| resistance_line_ohm | resistance_line | 23, 10, 11 -> **23, 10, 11, 07** | not tested | inferred | 11 -> 12 |
| loss_copper_w | loss_copper | 10, 11 -> **10, 11, 07, 09** | not tested | inferred | 11 -> 14 |
| loss_eddy_w | loss_eddy | 12, 05 -> **12, 05, 10** | not tested | inferred | 18 -> 20 |
| loss_circulating_w | loss_circulating | 07 -> **07, 06, 05, 10, 11** | not tested | inferred | 12 -> 23 |
| loss_delta_circulating_w | loss_delta_circulating | 19, 06, 07, 05 -> **19, 07, 06, 05, 10, 11, 23** | not tested | inferred | 21 -> 27 |
| loss_total_w | loss_total | 26, 10, 11, 12, 07, 19, 23, 09, 06, 05 -> **26, 10, 11, 07, 09, 12, 05, 06, 19, 23** | not tested | inferred | 35 |
| efficiency | efficiency | 26, 10, 11, 12, 07, 19, 23, 09, 06, 05 -> **26, 09, 06, 07, 05, 10, 11, 12, 19, 23** | not tested | inferred | 35 |
| motor_constant_n_m_per_sqrt_w | motor_constant | 26, 09, 06, 10, 11, 07, 05 -> **26, 09, 06, 07, 05, 10, 11** | not tested | inferred | 28 |
| thd_phase | thd_phase | 18, 06, 07, 05 -> **18, 07, 06, 05** | not tested | inferred | 14 |
| thd_line | thd_line | 18, 06, 07, 05 -> **18, 07, 06, 05** | not tested | inferred | 14 |
| current_density_a_per_mm2 | current_density | 22 -> **22, 09** | not tested | verified | 4 -> 5 |
| inductance_estimate_h | inductance_estimate | 14, 27 -> **14, 27, 06, 07, 05** | unresolved | unresolved | 9 -> 17 |
| ipc_guideline_current_a | ipc_guideline_current | 15 -> **15, 09** | unresolved | unresolved | 6 -> 8 |
| temperature_rise_k | temperature_rise | 17, 26, 10, 11, 12, 07, 19, 23, 09, 06, 05 -> **17, 26, 10, 11, 07, 09, 12, 05, 06, 19, 23** | not tested | assumption | 37 |
| layers[0].b1_peak_mid_radius_t | b1_peak_mid_radius_t | 05, 04 -> **05** | not tested | inferred | 11 -> 9 |
| layers[1].b1_peak_mid_radius_t | b1_peak_mid_radius_t | 05, 04 -> **05** | not tested | inferred | 11 -> 9 |
| phases[0].resistance_20c_ohm | phase_resistance_20c | 10, 11 -> **10, 11, 07** | not tested | inferred | 10 -> 11 |
| phases[0].resistance_operating_ohm | phase_resistance_operating | 10, 11 -> **10, 11, 07** | not tested | inferred | 10 -> 11 |
| phases[0].circulating_loss_w | phase_circulating_loss | 07 -> **07, 06, 05, 10, 11** | not tested | inferred | 12 -> 23 |
| phases[1].resistance_20c_ohm | phase_resistance_20c | 10, 11 -> **10, 11, 07** | not tested | inferred | 10 -> 11 |
| phases[1].resistance_operating_ohm | phase_resistance_operating | 10, 11 -> **10, 11, 07** | not tested | inferred | 10 -> 11 |
| phases[1].circulating_loss_w | phase_circulating_loss | 07 -> **07, 06, 05, 10, 11** | not tested | inferred | 12 -> 23 |
| phases[2].resistance_20c_ohm | phase_resistance_20c | 10, 11 -> **10, 11, 07** | not tested | inferred | 10 -> 11 |
| phases[2].resistance_operating_ohm | phase_resistance_operating | 10, 11 -> **10, 11, 07** | not tested | inferred | 10 -> 11 |
| phases[2].circulating_loss_w | phase_circulating_loss | 07 -> **07, 06, 05, 10, 11** | not tested | inferred | 12 -> 23 |
| emf_waveform_v | emf_waveform | 18, 06, 07, 05 -> **18, 07, 06, 05** | not tested | inferred | 16 |
| torque_speed.speed_rpm | torque_speed_rpm | 20, 14, 09, 23 -> **20, 14, 27, 06, 07, 05, 09, 23, 10, 11** | unresolved | unresolved | 23 -> 36 |
| torque_speed.torque_n_m | torque_speed_torque | 20, 14, 09, 23 -> **20, 14, 27, 06, 07, 05, 09, 23, 10, 11** | unresolved | unresolved | 23 -> 36 |
| torque_speed.power_w | torque_speed_power | 20, 14, 09, 23 -> **20, 14, 27, 06, 07, 05, 09, 23, 10, 11** | unresolved | unresolved | 23 -> 36 |
| torque_speed.no_load_speed_rpm | no_load_speed | 20, 14, 09, 23 -> **20, 09, 06, 07, 05** | unresolved | unresolved | 23 -> 26 |
| torque_speed.base_speed_rpm | base_speed | 20, 14, 09, 23 -> **20, 14, 27, 06, 07, 05, 09, 23, 10, 11** | unresolved | unresolved | 23 -> 36 |

## Pins changed (test files only; no golden data file changed)

| File | Before | After | Why |
|---|---|---|---|
| tests/golden/m2_physics/test_analyse_layouts.py l.229 | ke_line_peak (18, 09, 06, 07, 05) | (18, 09, 07, 06, 05) | own 18, 09, then line_emf = 18 on phase_emf = 07 on flux = 06 on field = 05 |
| tests/unit/ui/results/test_checks_charts_compare_guide.py l.92 | back-EMF chart eq_ids[:2] (18, 06) | (18, 07) | emf_waveform is 18 on phase_emf (07, 06, 05) |
| tests/unit/physics/test_emf_chain.py | unchanged, passes | | the new chains are supersets |

## Questions for Agent 2 (the code does not settle them)

1. Phase current. analyse() forms I_ph = I_line / sqrt(3) for delta, I_line otherwise. The registry formula of EQ-09
   states exactly this, so phase_current is named EQ-09. That adds EQ-09 to loss_copper, current_density and
   ipc_guideline_current (and keeps it in loss_total, where it was before). Is the current conversion EQ-09?
2. ke_phase. EQ-09's formula begins "Ke_ph = |E1|/omega_m" and ADR-0003's worked example lists EQ-09 for phase Ke. The
   code takes ke1 = mean |E1| of the EQ-07 phasors, already in V*s/rad (EQ-06 Ke_n form). ke_phase has no EQ-09 before
   or after. Does it need it?
3. ke_line_peak keeps its own pair (EQ-18, EQ-09). The code forms it through `_line_phasors`, which names only EQ-18,
   and thd_line on the same phasors lists no EQ-09. Which is right?
4. Validity flags do not travel with `built_from`. output_power, thd_phase, thd_line, inductance_estimate,
   loss_circulating, phase_circulating_loss and loss_eddy hold EQ-05 but not the EC-05 flag, so an e_edge above 10 %
   would cap ke_phase and not them. Should a result take the validity flags of what it is built from?
5. edge_leakage_fraction keeps the chain (EQ-05). Its metric is built from the field (EQ-04 for a block magnet) and the
   EQ-06 integrand weights. Should its chain hold them?
6. loss_delta_circulating takes the EMF, resistance and interconnect chains also for star, where its value is the
   constant 0.
7. The drive speed axis depends only on the no-load speed inside `torque_speed_envelope`, but takes the chain of the
   whole call (inductance, ke_line, resistance_line).
8. b1_peak_mid_radius_t drops EQ-04 for arc magnets (D08, serpentine, wave): `pole_arc_ratio_mm` returns the given
   ratio there and evaluates EQ-04 only for a block magnet. Confirm.
