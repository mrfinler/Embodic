# Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5
# Builds docs/phase2/engineering/equation_registry.json from the Phase 1 draft registry plus the Phase 2 changes below.
# The spec (equation_specification.md) is the human-readable source; check_consistency.py verifies that both agree.
# Run: python3 docs/phase2/engineering/checks/build_registry.py
import copy
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(ENG)))
PHASE1 = os.path.join(ROOT, "docs", "phase1", "engineering", "equation_registry_draft.json")
ALL = ["spiral", "serpentine", "wave"]
GOLDEN = "relative 1e-9 vs Xcoil engine.js at function level, same inputs, Xcoil-compatible constants injected"


def tests(eq, *kinds):
    """Test IDs: EQT-<nn>-GR golden regression, -CFxx closed-form case, -O1/-O2 literature oracle, -EC validity check, -UT unit."""
    return [f"EQT-{eq[3:]}-{k}" for k in kinds]


PATCH = {
    "EQ-01": dict(applies_to=ALL, golden_functions=["derive", "deriveWave", "slotAngle"], gate_verdict="reuse",
                  formula_add="serpentine phase offset theta_shift = 2*tau/m (m = 3), tau/2 (m = 2), tau = pi/p",
                  tests=tests("EQ-01", "GR", "UT1")),
    "EQ-02": dict(applies_to=["spiral"], golden_functions=[], replaced_functions=["sectorFeasible", "maxSectorTurns", "maxSectorTurnsFor"],
                  gate_verdict="replace", tests=tests("EQ-02", "CF10", "CF11", "UT1"),
                  reference_update={"spiral_mode_with_eye_pad0.6_clr0.8": 3, "spiral_mode_with_eye_pad1.2_clr0.8": 3,
                                    "limiting_reason_with_eye_pad1.2": "loop", "limiting_reason_with_eye": "loop",
                                    "closing_with_eye": "half (revision 2026-10-05, U-E3b)",
                                    "note": "Phase 2 eye rule (centre via on the coil centre line, EQ-25) replaces the Phase 1 placement on the lead line; "
                                            "12/16 -> 10 and 18/16 -> 7 unchanged; D08 pad 0.6 mm -> 3 (was 2). min_side_length 2w gives 18/16 loop count 7 "
                                            "(8th right side 0.607 mm < 1.0 mm); concentric test mode keeps 3 / 11 / 8"}),
    "EQ-03": dict(applies_to=ALL, golden_functions=["primLength", "primsLength", "discretize"], gate_verdict="reuse",
                  tests=tests("EQ-03", "GR", "CF04", "CF10", "CF11")),
    "EQ-04": dict(applies_to=ALL, golden_functions=[], gate_verdict="replace", tests=tests("EQ-04", "UT1")),
    "EQ-05": dict(applies_to=ALL, golden_functions=["fieldHarmonic", "fieldSetup"], gate_verdict="reuse with change",
                  changes=["alpha_p(r) for block magnets (EQ-04)", "temperature-dependent B_r", "configurable odd harmonic set (default 1..13)",
                           "EC-05 edge add-on", "one rotor type drives field, inductance and inertia (Xcoil Q-3)"],
                  tests=tests("EQ-05", "GR", "CF01", "CF03", "EC", "O1", "O2")),
    "EQ-06": dict(applies_to=ALL, golden_functions=["analyze", "analyzeWave", "analyzeElements"], gate_verdict="reuse",
                  tests=tests("EQ-06", "GR", "CF02", "CF03", "O1", "O2")),
    "EQ-07": dict(applies_to=ALL, golden_functions=["analyze", "analyzeWave", "analyzeElements"], gate_verdict="reuse with change",
                  changes=["series connection of layer groups for the spiral generator", "per-coil elements from the spiral generator",
                           "report that the circulating loss uses the fundamental only"],
                  tests=tests("EQ-07", "GR", "CF07")),
    "EQ-08": dict(applies_to=["spiral", "wave"], golden_functions=["beltPhase", "beltSign", "slotAngle"],
                  replaced_functions=["starOfSlots", "balancedSectorList"], gate_verdict="replace",
                  formula_add="exact belts: a_k = 12 (k p mod Q) in units of 360/(12 Q) deg; belt = floor((a_k + Q)/(2 Q)) mod 6 (half-open belts); "
                              "balance = signed angle sets of B and C equal those of A shifted by 4Q and 8Q units",
                  tests=tests("EQ-08", "CF09", "GR", "UT1")),
    "EQ-09": dict(applies_to=ALL, golden_functions=["applyConnection"], gate_verdict="reuse", tests=tests("EQ-09", "GR", "CF06", "O1")),
    "EQ-10": dict(applies_to=ALL, golden_functions=["copperResistivity", "traceResistance", "primsResistance", "interconnectResistance"],
                  gate_verdict="reuse", tests=tests("EQ-10", "GR", "CF04", "O2")),
    "EQ-11": dict(applies_to=ALL, golden_functions=["viaBarrelArea"], gate_verdict="reuse with change",
                  changes=["plating thickness and vias per transition as inputs", "count every via in the current path",
                           "barrel length = distance between the two connected layers (analyzeWave uses one adjacent-layer spacing / floor(L/2): "
                           "keep as an Xcoil-compatible option, label assumption)"],
                  tests=tests("EQ-11", "GR", "CF04")),
    "EQ-12": dict(applies_to=ALL, golden_functions=["analyze", "analyzeWave", "analyzeElements"], gate_verdict="reuse",
                  tests=tests("EQ-12", "GR", "CF05")),
    "EQ-13": dict(applies_to=ALL, golden_functions=["skinDepthMm"], gate_verdict="reuse", tests=tests("EQ-13", "GR", "CF05")),
    # Revision 2026-10-16 (U-E12, D-049 d): embodic implements form (a) and does not port Xcoil's current-sheet model, so the
    # gate names no golden function; EQT-14-GR is withdrawn and EQT-14-CF12 checks the code against the formula.
    "EQ-14": dict(applies_to=ALL, golden_functions=[],
                  replaced_functions=["windingInductance", "conductorsSerpentine", "conductorsWave", "conductorsFromElements"],
                  formula="L_m = (3*mu0/(4*pi))*(N*k_w1)^2*(D_o^2 - D_i^2)/(p^2*delta'), delta' = 2*l_m + 2*g + t_s "
                          "(form (a) only; Xcoil's current-sheet model is not ported, D-049 d)",
                  gate_verdict="cannot verify yet", tests=tests("EQ-14", "CF12", "O2")),
    "EQ-15": dict(applies_to=ALL, golden_functions=["ipc2221Current"], gate_verdict="cannot verify yet", tests=tests("EQ-15", "GR")),
    "EQ-16": dict(applies_to=ALL, golden_functions=["massThermal"], gate_verdict="reuse with change",
                  changes=["copper density 8.89 g/cm3 (EV-53) instead of 8.96", "laminate density per stack-up entry with source", "holes and mask"],
                  tests=tests("EQ-16", "GR", "UT1")),
    "EQ-17": dict(applies_to=ALL, golden_functions=["massThermal"], gate_verdict="reuse with change",
                  changes=["cite h (D01 10 W/m2K vs Xcoil default 30)", "conduction path and enclosure option", "validate vs O3 (D10) when runnable"],
                  tests=tests("EQ-17", "GR")),
    "EQ-18": dict(applies_to=ALL, golden_functions=["emfWaveform", "lineWaveform"], gate_verdict="reuse", tests=tests("EQ-18", "GR")),
    "EQ-19": dict(applies_to=ALL, golden_functions=["applyConnection"], gate_verdict="reuse with change",
                  changes=["zero-sequence reactance once EQ-14 is validated; until then label the result an upper bound"],
                  tests=tests("EQ-19", "GR", "CF07")),
    "EQ-20": dict(applies_to=ALL, golden_functions=["torqueSpeed", "inverterVoltage", "driveAnalysis"], gate_verdict="cannot verify yet",
                  formula_add="inverter fundamental: SVPWM V_LL,rms = V_dc/sqrt2; SPWM sqrt3 V_dc/(2 sqrt2); six-step sqrt6 V_dc/pi; open phases (full bridge) "
                              "V_dc/sqrt2 or 4 V_dc/(pi sqrt2); pull-out T_po = m (E/Z)(V - E R/Z)/omega; pull-in T_pi = T_po - J omega f_e (Xcoil estimate)",
                  tests=tests("EQ-20", "GR")),
    "EQ-21": dict(applies_to=ALL, golden_functions=[], gate_verdict="replace", tests=tests("EQ-21", "UT1")),
    "EQ-22": dict(applies_to=ALL, golden_functions=["analyze", "analyzeWave", "analyzeElements", "applyConnection"], gate_verdict="reuse",
                  tests=tests("EQ-22", "GR")),
}

NEW = [
    {"id": "EQ-23", "name": "Line-to-line resistance and interconnect copper",
     "formula": "star: R_LL = (2/3) sum_k (R_k + l_k + s_k) + (2/3)(n_1 + n_2) (n = neutral-ring segments); delta: branch b_k = R_k + l_k, "
                "R_LL = (1/3) sum_k b_k (S - b_k)/S + (2/3) sum_k s_k, S = sum b_k; P_ic = I_line^2 (sum s + sum l + sum n) (star), "
                "I_line^2 sum s + I_ph^2 sum l (delta)",
     "variables": [{"symbol": "R_k", "unit": "ohm", "meaning": "phase winding resistance"}, {"symbol": "l_k", "unit": "ohm", "meaning": "link copper of phase k"},
                   {"symbol": "s_k", "unit": "ohm", "meaning": "line stub copper"}, {"symbol": "n_i", "unit": "ohm", "meaning": "neutral ring segment"}],
     "sources": [], "source_notes": "network identities (series/parallel resistors); engine.js applyConnection lines 1418-1429, interconnectResistance 1361-1374",
     "gate_verdict": "reuse", "status": "verified", "tolerance": {"value": "relative 1e-12 (identity)", "basis": "exact network algebra"},
     "dominant_assumptions": ["finished copper thickness", "temperature"],
     "reference_case": {"source": "oracle_cases.json CF-06", "inputs": {"branches_ohm": [1.0, 1.1, 1.2]}, "expected": {"R_LL_star": 2.2, "R_LL_delta": 0.731313131}, "tolerance": "relative 1e-9"},
     "applies_to": ALL, "golden_functions": ["applyConnection", "interconnectResistance"], "tests": tests("EQ-23", "GR", "CF06")},
    {"id": "EQ-24", "name": "Involute end-turn spacing of the interleaved wave winding",
     "formula": "involute of base radius r_b: P(t) = r_b (cos(phi0 + t) + t sin(phi0 + t), sin(phi0 + t) - t cos(phi0 + t)); two copies rotated by d_phi "
                "are equidistant with normal spacing r_b d_phi; nesting requires r_b d_phi >= w_end + s",
     "variables": [{"symbol": "r_b", "unit": "mm", "meaning": "base radius"}, {"symbol": "d_phi", "unit": "rad", "meaning": "slot angle between neighbouring tracks"}],
     "sources": [], "source_notes": "classical involute property (normal of an involute is tangent to the base circle); engine.js comment lines 1449-1455; "
                                     "textbook source not in corpus; reproduced numerically (CF-08)",
     "gate_verdict": "reuse", "status": "verified", "tolerance": {"value": "absolute 1e-4 mm (sampled)", "basis": "CF-08 sampling resolution"},
     "dominant_assumptions": ["end-turn width", "clearance"],
     "reference_case": {"source": "oracle_cases.json CF-08", "inputs": {"r_b_mm": 20.0, "d_phi_deg": 2.0}, "expected": {"spacing_mm": 0.6981317}, "tolerance": "absolute 1e-4 mm"},
     "applies_to": ["wave"], "golden_functions": ["invol", "involutePoint", "involutePrims", "biarc", "waveTrack", "deriveWave", "maxWaveTurns"],
     "tests": tests("EQ-24", "GR", "CF08")},
    {"id": "EQ-25", "name": "Spiral coil centre-via eye, lead and terminal stub",
     "formula": "via on the coil centre line at r_v = r_hi, m = max(pad, w)/2; r_lo = max((d_(N-1) + w/2 + s + m)/sin(pi/Q), r_end,N-1 + w_in/2 + s + m); "
                "r_hi = R_out,N-1 - w_out/2 - s - m; fits iff r_hi - r_lo >= (k - 1)(max(pad, w)/2 + pad/2 + s); "
                "lead = the last left side d_(N-1) ends at radius r_v, then one arc at r_v to the centre line (revision 2026-10-05, U-E3); "
                "half closing (revision 2026-10-05, U-E3b, k = 1, pad <= w): last turn = outer arc + right side d_(N-1) ending on the via at "
                "r_v = d_(N-1)/sin(pi/Q), used when it builds more turns than the full closing; terminal via at r_T = r_outer + s + pad/2, "
                "angle min(angle of start corner, pi/Q - asin((max(pad, bw) + s)/(2 r_T)))",
     "variables": [{"symbol": "pad", "unit": "mm", "meaning": "via pad diameter"}, {"symbol": "k", "unit": "1", "meaning": "centre vias per coil (series groups)"},
                   {"symbol": "r_T", "unit": "mm", "meaning": "terminal via ring radius"}],
     "sources": [], "source_notes": "geometry rules of spiral_generator_spec.md G5-G6, derived from engine.js sectorViaSpot (2269-2273) and sectorCoilX (2285-2328); "
                                     "the centre line is the only locus shared by layer X and its mirror Y",
     "gate_verdict": "replace", "status": "inferred", "tolerance": {"value": "exact (counts), relative 1e-6 (lengths)", "basis": "deterministic geometry"},
     "dominant_assumptions": ["via pad", "clearance", "series group count"],
     "reference_case": {"source": "oracle_cases.json CF-10, CF-11", "inputs": {"case": "default 12/16, pad 0.6"}, "expected": {"N_eye": 10, "r_v_mm": 30.7}, "tolerance": "exact / 1e-4 mm"},
     "applies_to": ["spiral"], "golden_functions": [], "replaced_functions": ["sectorViaSpot", "sectorCoilX", "chainCoils"],
     "tests": tests("EQ-25", "CF10", "CF11", "UT1")},
    {"id": "EQ-26", "name": "Loss sum, efficiency and motor constant",
     "formula": "P_loss = P_Cu + P_eddy + P_circ + P_delta,circ + P_ic; P_out = T omega_m; eta = P_out/(P_out + P_loss); K_m = T/sqrt(P_Cu)",
     "variables": [{"symbol": "eta", "unit": "1", "meaning": "efficiency (electromagnetic, no bearing/windage)"}],
     "sources": [], "source_notes": "definitions; engine.js applyConnection 1430-1434",
     "gate_verdict": "reuse", "status": "verified", "tolerance": {"value": "relative 1e-12 (identity)", "basis": "definition"},
     "dominant_assumptions": ["all upstream assumptions (EQ-06, EQ-10, EQ-12)", "mechanical losses omitted"],
     "reference_case": {"source": "arithmetic", "inputs": {"P_out": 10.0, "P_loss": 2.5}, "expected": {"eta": 0.8}, "tolerance": "exact"},
     "applies_to": ALL, "golden_functions": ["applyConnection"], "tests": tests("EQ-26", "GR")},
    {"id": "EQ-27", "name": "Numerical utilisation factor and analytic distribution factor",
     "formula": "k_u = Ke1 / (sum over series conductors of integral B_z1 r dr over the magnet span) (Xcoil 'kw1'); serpentine k_d = sin(N gamma/2)/(N sin(gamma/2)), "
                "gamma = p d_alpha (radial) or p (w + s)/r_mean (parallel); wave k_d = |sum_i w_i e^{j gamma (i - (q-1)/2)}| / sum_i w_i, w_0 = 2p - 1, w_i = 2p",
     "variables": [{"symbol": "k_u", "unit": "1", "meaning": "utilisation factor (numeric)"}, {"symbol": "k_d", "unit": "1", "meaning": "distribution factor"}],
     "sources": ["EV-59", "EV-26"], "source_notes": "D15 eq. 6 p.7 (average of per-turn factors); D04 eq. 1 p.5 (distribution factor); engine.js analyze 975-986, analyzeWave 2073-2077",
     "gate_verdict": "reuse with change", "status": "inferred",
     "changes": ["rename Xcoil 'kw1' to utilisation factor k_u (it includes radial field variation and end effects)",
                 "label the parallel-style serpentine k_d as a mean-radius approximation", "spiral: k_w from EQ-08, not from kdAnalytic"],
     "tolerance": {"value": "golden 1e-9", "basis": "port equivalence; information output only"},
     "dominant_assumptions": ["magnet shape alpha_p(r)"],
     "reference_case": {"source": "arithmetic", "inputs": {"N": 1}, "expected": {"k_d": 1.0}, "tolerance": "exact"},
     "applies_to": ALL, "golden_functions": ["analyze", "analyzeWave", "analyzeElements"], "tests": tests("EQ-27", "GR")},
    {"id": "EQ-28", "name": "Rotor inertia estimate",
     "formula": "J = n_R (0.5 m_mag (r_1^2 + r_2^2) + 0.5 m_yoke r_Y^2); m_mag = pi (r_2^2 - r_1^2) l_m alpha_p rho_NdFeB; m_yoke = pi r_Y^2 l_m rho_steel, r_Y = r_2 + 2 mm",
     "variables": [{"symbol": "J", "unit": "kg*m^2", "meaning": "rotor inertia"}],
     "sources": [], "source_notes": "ring/disc inertia (standard mechanics); densities 7.5 and 7.85 g/cm3 unsourced in engine.js line 2556; yoke = magnet thickness, r_Y = r_2 + 2 mm are Xcoil assumptions",
     "gate_verdict": "reuse with change", "status": "assumption",
     "changes": ["cite NdFeB and steel densities", "use the user's rotor inertia when given (Xcoil already does)"],
     "tolerance": {"value": "none claimed", "basis": "densities and yoke geometry assumed"},
     "dominant_assumptions": ["magnet and steel densities", "yoke geometry"],
     "reference_case": {"source": "arithmetic", "inputs": {}, "expected": {}, "tolerance": "golden only"},
     "applies_to": ALL, "golden_functions": ["rotorInertiaEstimate"], "tests": tests("EQ-28", "GR")},
    {"id": "EQ-29", "name": "Inter-layer capacitance (parallel-plate upper bound)",
     "formula": "C_i = eps0 eps_r min(A_Cu,i, A_Cu,i+1)/t_diel,i",
     "variables": [{"symbol": "eps_r", "unit": "1", "meaning": "relative permittivity of the dielectric"}],
     "sources": [], "source_notes": "parallel-plate capacitor (standard); full-overlap upper bound; engine.js stackCapacitance 1180-1188; eps_r table DIELECTRICS unsourced",
     "gate_verdict": "reuse with change", "status": "assumption",
     "changes": ["source eps_r per dielectric (datasheet)", "label the value an upper bound (full overlap, no fringing)"],
     "tolerance": {"value": "none claimed", "basis": "overlap and eps_r assumed"},
     "dominant_assumptions": ["eps_r", "dielectric thickness"],
     "reference_case": {"source": "arithmetic", "inputs": {"A_mm2": 1000, "t_mm": 0.2, "eps_r": 4.5}, "expected": {"C_F": 1.99215e-10}, "tolerance": "relative 1e-4"},
     "applies_to": ALL, "golden_functions": ["stackCapacitance"], "tests": tests("EQ-29", "GR")},
    {"id": "EQ-30", "name": "DRC clearance measurement and acceptance",
     "formula": "clearance(a, b) = min distance between discretised centre-line segments - (w_a + w_b)/2 (pads: distance to pad outline); "
                "violation iff clearance < rule - eps, eps <= 1e-6 mm (D-006); discretisation error bounded by the sagitta tolerance and subtracted (conservative)",
     "variables": [{"symbol": "eps", "unit": "mm", "meaning": "numerical tolerance <= 1e-6 mm"}],
     "sources": [], "source_notes": "decision D-006; engine.js runDrc 756, computeWave 1929, computeWaveOverlap 2147, computeSector 2429 use tol = 0.004 mm (slack)",
     "gate_verdict": "reuse with change", "status": "inferred",
     "changes": ["remove the 0.004 mm slack (D-006)", "golden comparison of DRC values within 1e-9; pass/fail agreement only outside [rule - 0.004, rule)",
                 "conservative arc discretisation (subtract the sagitta bound)"],
     "tolerance": {"value": "values 1e-9 vs Xcoil; decision per D-006", "basis": "D-006"},
     "dominant_assumptions": ["fabricator clearance rule"],
     "reference_case": {"source": "engine_probe.js", "inputs": {"Xcoil DEFAULTS serpentine": True},
                        "expected": {"traceClearance_mm": 0.19901108, "Xcoil_ok": True, "embodic_violation": True}, "tolerance": "relative 1e-9 on the value"},
     "applies_to": ALL,
     "golden_functions": ["runDrc", "drcLayer", "drcPadVsLayer", "drcObjects", "drcLayerObjects", "drcInterconnect", "padsClearance", "padSegClearance",
                          "segSegDist", "ptSegDist", "canonicalSegments", "makeGrid", "gridQuery"],
     "tests": tests("EQ-30", "GR", "UT1")},
]

DEF23 = {
    "basis": "D09 p.4 sec. 3.1 (scalar-potential model misses radial edge leakage; B_r(r) curve-fitted from FEA, eq. 7 p.5). Calibration quantity: "
             "D09 Fig. 7 plots |B| 'at the middle of the magnet' (caption p.4, axial position not stated); EC-05 uses it as a proxy for B_z at the copper. "
             "Near the radial ends |B| contains a radial component, so the B_z deficit is at least as large: e_edge is probably a lower bound (inferred). "
             "Fit residual <= 0.02 in k; ONE calibration case -> calibration inferred",
    "transfer_basis": "scaling the decay length with G and keeping D_e = 0.47 for rotors with other magnet thickness, alpha_p, pole pitch or "
                      "block/T-arrangement magnets is untested",
    "threshold_basis": "10 % is a design choice (D-017). The calibration case sits at 5.6-5.8 %, so 10 % allows about 1.7x extrapolation of the single-case "
                       "calibration. It is not derived from the +/-8 % O1 tolerance (errors between 8 % and 10 % already exceed that band)",
    "independence": "D09 is both the calibration source and oracle O2: O2 cannot validate EC-05. O1 (D08) is the only independent check and depends on the "
                    "G10 gap reading (e_edge 4.21 % at G 1.4 mm, 5.11 % at G 1.7 mm, Agent 4 v12)",
    # Typed fields of requirements.md section 6 (DEF-M2b-01); the prose keys above keep the reasoning.
    "threshold": 0.10,
    "metric_bound": "lower_bound",
    "calibration_status": "inferred",
    "transfer_status": "assumption",
    "threshold_status": "assumption",
    "independent_oracles": ["OR-01"],
    "dependent_oracles": ["OR-07", "OR-08"],
}

# DEF-M2b-03. Physical and material constants only; formula coefficients (1/24, IPC-2221 k/b/c) stay in the formula with its sources.
# Names match embodic.model.materials.MaterialOverrides where a user override exists.
RHO_CU = {"name": "copper_resistivity_20c_ohm_m", "value": 1.7241e-8, "unit": "ohm_m", "source": "EV-53", "status": "verified",
          "basis": "IACS annealed copper at 20 degC, NBS Handbook 100 p.2"}
ALPHA_CU = {"name": "copper_temp_coeff_per_k", "value": 0.00393, "unit": "per_K", "source": "EV-53", "status": "verified",
            "basis": "IACS temperature coefficient at 20 degC, NBS Handbook 100 p.3"}
DENSITY_CU = {"name": "copper_density_g_per_cm3", "value": 8.89, "unit": "g_per_cm3", "source": "EV-53", "status": "verified",
              "basis": "IACS density, NBS Handbook 100 p.4"}
DENSITY_LAMINATE = {"name": "laminate_density_g_per_cm3", "value": 1.85, "unit": "g_per_cm3", "source": None, "status": "assumption",
                    "basis": "Xcoil engine.js l.1151 and l.1377 (FR-4), no datasheet in the evidence register"}
DENSITY_NDFEB = {"name": "ndfeb_density_g_per_cm3", "value": 7.5, "unit": "g_per_cm3", "source": "EV-93", "status": "inferred",
                 "basis": "Xcoil engine.js l.2556 value; EV-93 (HGT Table IV) reads 7.4-7.7 g/cm3 for sintered NdFeB, so 7.5 lies "
                          "inside one manufacturer's class range, not a grade value (revision 2026-10-08, U-E5)"}
DENSITY_STEEL = {"name": "steel_density_g_per_cm3", "value": 7.85, "unit": "g_per_cm3", "source": None, "status": "assumption",
                 "basis": "Xcoil engine.js l.2556, no datasheet in the evidence register"}
# Revision 2026-10-08 (U-E5): CODATA 2022 values (EV-84, EV-85); EV-86 (SI Brochure 9 §2.3.1) says mu_0 is no longer exactly
# 4*pi*1e-7. The code constants (losses.py MU0_H_PER_M, Xcoil EPS0) are Agent 3's to change.
MU_0 = {"name": "vacuum_permeability_h_per_m", "value": 1.25663706127e-6, "unit": "H_per_m", "source": "EV-84", "status": "verified",
        "basis": "CODATA 2022 (EV-84, NIST allascii row 'vacuum mag. permeability', u = 2.0e-16 H/m); EV-86: mu_0 is measured, "
                 "not exactly 4*pi*1e-7. Xcoil engine.js l.11 and src/embodic/physics/losses.py use 4*pi*1e-7 (relative -1.3e-10)"}
EPS_0 = {"name": "vacuum_permittivity_f_per_m", "value": 8.8541878188e-12, "unit": "F_per_m", "source": "EV-85", "status": "verified",
         "basis": "CODATA 2022 (EV-85, NIST allascii row 'vacuum electric permittivity', u = 1.4e-21 F/m); EV-86: eps_0 is measured. "
                  "Xcoil engine.js l.1181 uses 8.854e-12 (relative -2.1e-5)"}
CONSTANTS = {
    "EQ-10": [RHO_CU, ALPHA_CU], "EQ-11": [RHO_CU, ALPHA_CU], "EQ-12": [RHO_CU, ALPHA_CU],
    "EQ-16": [DENSITY_CU, DENSITY_LAMINATE], "EQ-28": [DENSITY_NDFEB, DENSITY_STEEL],
    "EQ-13": [RHO_CU, ALPHA_CU, MU_0], "EQ-14": [MU_0], "EQ-29": [EPS_0],
}

# Result labels (interfaces.md Traceable.label); every other equation gets an explicit null.
LABELS = {"EQ-14": "estimate", "EQ-15": "guideline (unverified)", "EQ-19": "upper bound", "EQ-20": "estimate", "EQ-28": "estimate",
          "EQ-29": "upper bound"}

# Dominant assumption text -> PROPERTY field patterns whose measured value retires it (REQ-T-06: only property fields take
# `measured`). A design field here would hide the assumption whenever that input is used, so none is listed.
THICKNESS = "/stackup/layers/*/thickness_mm"
ASSUMPTION_FIELDS = {
    "B_r (grade, temperature)": ["/rotor/remanence_t"],
    "mu_r (no datasheet value, G23)": ["/rotor/recoil_permeability"],
    "mu_r": ["/rotor/recoil_permeability"],
    "member resistances (copper thickness)": [THICKNESS],
    "finished copper thickness t": [THICKNESS],
    "finished copper thickness": [THICKNESS],
    "copper thickness": [THICKNESS],
    "PCB copper resistivity = IACS (G6)": ["/materials/copper_resistivity_20c_ohm_m/value"],
    "plating thickness t_p": ["/vias/plating_um"],
    "laminate density": ["/materials/laminate_density_g_per_cm3/value"],
    "film coefficient h": ["/operating/convection_h_w_m2k"],
}
ASSUMPTION_STATUS = {"standard source missing": "unresolved", "coefficient 1/24 (by derivation)": "inferred"}

# DEF-M2b-02: evidence entries that support part of an equation; the equation status stays as it is.
EXTRA_SOURCES = {
    "EQ-15": (["EV-82", "EV-83"], "EV-82 and EV-83 state the IPC-2221 coefficients second-hand; the standard's own text is not read (G5)"),
    "EQ-20": (["EV-24", "EV-92"], "EV-24 (D06 eq. 2) supports only the torque relation T = m E I / omega; EV-92 (Microchip AN955, "
                                  "an induction-motor note) gives the SPWM and SVPWM linear limits only; the six-step fundamental and "
                                  "the pull-out and pull-in formulas still have no source (revision 2026-10-08, U-E5)"),
    # Revision 2026-10-08 (U-E5).
    "EQ-08": (["EV-89", "EV-90"], "EV-89 (Tessarolo 2019, eq. 15) states the balance condition Q/(3t) integer and EV-90 (Alberti and "
                                  "Bianchi slides) defines t = gcd(Q, p); neither covers parallel paths (G30), so `a | t` stays inferred"),
    "EQ-18": (["EV-91"], "EV-91 (D09 Table 7 p.8) is an oracle THD value only; D09 defines no THD basis, so the THD definition "
                         "stays unresolved (G31) (revision 2026-10-08, U-E5)"),
}


def typed_fields(e):
    """Add label, constants and object-form dominant assumptions; return the assumption texts seen."""
    e["label"] = LABELS.get(e["id"])
    e["constants"] = copy.deepcopy(CONSTANTS.get(e["id"], []))
    texts = list(e["dominant_assumptions"])
    e["dominant_assumptions"] = [{"text": t, "status": ASSUMPTION_STATUS.get(t, "assumption"), "fields": ASSUMPTION_FIELDS.get(t, [])}
                                 for t in texts]
    if e["id"] in EXTRA_SOURCES:
        ev_ids, note = EXTRA_SOURCES[e["id"]]
        e["sources"] = e["sources"] + ev_ids
        e["source_notes"] = f"{e['source_notes']}; {note}"
    return set(texts)


def build():
    p1 = json.load(open(PHASE1))
    reg = {k: copy.deepcopy(v) for k, v in p1.items() if k != "equations"}
    reg["prepared_by"] = "Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5"
    reg["schema"] = ("embodic equation registry v1.0 (Phase 2, 2026-10-04) - source: equation_specification.md; generated by checks/build_registry.py "
                     "from docs/phase1/engineering/equation_registry_draft.json")
    reg["golden_tolerance_default"] = GOLDEN
    reg["fields_added_in_v1"] = {"applies_to": "topologies that use the equation", "golden_functions": "engine.js functions whose numerics the port must reproduce (1e-9)",
                                 "replaced_functions": "engine.js functions that are NOT ported bug-for-bug", "changes": "required changes for 'reuse with change'",
                                 "tests": "EQT-<nn>-GR golden, -CFxx closed form (oracle_cases.json), -O1/-O2 literature oracle, -EC validity check, -UTn unit test"}
    reg["fields_added_in_v1"].update({
        "label": "result label (estimate / guideline (unverified) / upper bound) or null",
        "constants": "physical and material constants {name, value, unit (embodic.units.Unit), source (EV id or null), status, basis}",
        "dominant_assumptions": "objects {text, status, fields}; fields = FIELDS property patterns whose measured value retires the assumption",
    })
    reg["notes"] = list(p1["notes"]) + ["v1.0: EQ-23...EQ-30 added for the serpentine/wave port (D-013); EC-05 labels per DEF-23; EQ-02 eye counts per EQ-25",
                                        "v1.0 rev. U-E2 (2026-10-05): DEF-M2b-01 EC-05 typed fields; DEF-M2b-02 EV-24 on EQ-20, EV-82/EV-83 on EQ-15, "
                                        "unsourced equations listed in equation_specification.md 'Source and unit gaps'; DEF-M2b-03 label, constants, "
                                        "object-form dominant_assumptions",
                                        "v1.0 rev. U-E10 (2026-10-13, D-046 d): for a test ID EQT-nn-CFxx the closed-form case CF-xx of "
                                        "oracle_cases.json (its inputs, expected values and tolerances) governs over the equation's Phase 1 "
                                        "reference_case and tolerance texts, which stay as the Phase 1 record; the texts that differ are the EQ-06 "
                                        "tolerance (1e-4 vs CF-02 1e-9 and CF-03 1e-5) and the EQ-12 and EQ-13 reference_case (Xcoil rho, 1e-4 and "
                                        "5e-3 mm vs CF-05 1e-9); eqt_map_review.md section b",
                                        "v1.0 rev. U-E12 (2026-10-16, D-049 d): EQ-14 is the one 'cannot verify yet' entry without an "
                                        "Xcoil port. embodic implements form (a) (src/embodic/physics/estimates.py inductance_estimate_h, "
                                        "called from analyse.py l.408); the current-sheet functions move to replaced_functions; "
                                        "EQT-14-GR is withdrawn (nothing to compare) and EQT-14-CF12 (oracle_cases.json CF-12) checks "
                                        "the code against the form (a) formula. The status stays unresolved and the label estimate"]
    eqs = []
    for e in p1["equations"]:
        e = copy.deepcopy(e)
        patch = PATCH[e["id"]]
        for k, v in patch.items():
            if k == "formula_add":
                e["formula"] = e["formula"] + "; " + v
            elif k == "reference_update":
                e["reference_case"]["expected"].update(v)
            else:
                e[k] = v
        if e["id"] == "EQ-05":
            e["validity_checks"][0].update(DEF23)
        eqs.append(e)
    eqs.extend(copy.deepcopy(NEW))
    seen = set().union(*(typed_fields(e) for e in eqs))
    stale = (set(ASSUMPTION_FIELDS) | set(ASSUMPTION_STATUS)) - seen
    assert not stale, f"assumption texts not in any equation: {sorted(stale)}"
    assert set(LABELS) | set(CONSTANTS) | set(EXTRA_SOURCES) <= {e["id"] for e in eqs}
    reg["equations"] = eqs
    return reg


if __name__ == "__main__":
    reg = build()
    path = os.path.join(ENG, "equation_registry.json")
    with open(path, "w") as f:
        json.dump(reg, f, indent=1, ensure_ascii=False)
    json.load(open(path))
    counts = {}
    for e in reg["equations"]:
        counts[e["gate_verdict"]] = counts.get(e["gate_verdict"], 0) + 1
    print("wrote", path, "|", len(reg["equations"]), "equations |", counts)
