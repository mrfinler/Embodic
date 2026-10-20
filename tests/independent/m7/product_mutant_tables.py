"""Mutant tables of V3-02 to V3-05 (verification_plan.md part 3), read by product_mutants.py.

Every mutant names its killing tests and the disagreement their failure must show before it runs. ``SUITES`` is the
pass-criterion set of each campaign in the plan; a mutant that no named test kills is run against it before it is
called a survivor.
"""

from product_mutants import Mutant

D = "tests/unit/drc/test_run_drc.py::"
P = "tests/unit/drc/test_properties.py::"
APPROX = r"±|approx|assert .* == |!="

V3_02 = [
    Mutant(
        "V3-02-01", "Xcoil slack 0.004 mm in D-006", "drc/report.py",
        "DRC_EPSILON_MM: float = 1e-6", "DRC_EPSILON_MM: float = 0.004",
        (D + "test_ut_drc_03_one_micron_intrusion_is_exactly_one_new_violation_at_its_place",),
        r"assert \[\] == \[|Right contains",
    ),
    Mutant(
        "V3-02-02", "epsilon 0 in D-006", "drc/report.py",
        "DRC_EPSILON_MM: float = 1e-6", "DRC_EPSILON_MM: float = 0.0",
        (D + "test_ut_drc_03_inside_epsilon_passes",),
        r"passed",
    ),
    Mutant(
        "V3-02-03", "arc-arc pairs skipped by the narrow phase", "drc/engine.py",
        "            if not sel.any():\n                continue\n            pair = closest_pairs(",
        "            if not sel.any() or (arc_a and arc_b):\n                clearance_mm[sel] = np.inf\n"
        "                at_mm[sel] = 0.0\n                continue\n            pair = closest_pairs(",
        (D + "test_ut_drc_03_one_micron_intrusion_is_exactly_one_new_violation_at_its_place",),
        r"assert \[\] == \[|Right contains",
    ),
    Mutant(
        "V3-02-04", "rule 2 widened: a path end within the full pad of a via is on it", "drc/items.py",
        "and math.dist(e.point, (via.x_mm, via.y_mm)) <= via.pad_mm / 2",
        "and math.dist(e.point, (via.x_mm, via.y_mm)) <= via.pad_mm",
        ("tests/independent/m1/test_drc_agreement.py::test_run_drc_violation_sets_equal_brute_sweep_on_random_boards",
         P + "test_pr_01_drc_never_under_reports_and_reports_no_false_positive_on_200_random_sets"),
        r"Left contains|Right contains|missing|== |!=",
    ),
    Mutant(
        "V3-02-05", "rule 2b widened: the tap band is the full pad", "drc/items.py",
        "within = _centreline_distance_mm(items, candidates, via.x_mm, via.y_mm) <= via.pad_mm / 2",
        "within = _centreline_distance_mm(items, candidates, via.x_mm, via.y_mm) <= via.pad_mm",
        (D + "test_ut_drc_04_same_net_via_tap_band_is_half_the_via_pad",),
        r"assert \[\] == \[|Right contains",
    ),
    Mutant(
        "V3-02-06", "rule 2b widened: a tap exempts the whole path (D-037a reverted)", "drc/items.py",
        "yield from ((via_base + v, int(i)) for i in candidates[within])",
        "yield from ((via_base + v, int(i)) for i in candidates[np.isin(items.path[candidates], "
        "items.path[candidates[within]])])",
        (D + "test_ut_drc_04_same_net_via_tap_leaves_a_far_primitive_of_the_same_path_checked",
         D + "test_ut_drc_04_interconnect_tap_leaves_a_far_primitive_of_the_ring_checked"),
        r"assert \[\] == \[|Right contains",
    ),
    Mutant(
        "V3-02-07", "rule 5 widened: T-junctions across nets", "drc/items.py",
        "for e in (e for e in ends if e.path.layer == layer and e.path.net == net):",
        "for e in (e for e in ends if e.path.layer == layer):",
        (D + "test_ut_drc_04_path_end_on_a_path_of_another_net_is_reported",),
        r"set\(\) == |Right contains|Extra items in the right set",
    ),
    Mutant(
        "V3-02-08", "rule 5 widened: the T-junction reach is 1000 x COINCIDENCE_MM", "drc/items.py",
        "for hit in np.flatnonzero((distance_mm <= COINCIDENCE_MM) & (owner != e.path.id)):",
        "for hit in np.flatnonzero((distance_mm <= 1000 * COINCIDENCE_MM) & (owner != e.path.id)):",
        (D + "test_ut_drc_04_path_end_beyond_the_coincidence_tolerance_is_reported",),
        r"set\(\) == |Right contains|Extra items in the right set",
    ),
    Mutant(
        "V3-02-09", "D-006 band flipped: clearance equal to rule - epsilon is a violation", "drc/engine.py",
        "bad = np.flatnonzero(m.clearance_mm < required_mm[m.kind] - DRC_EPSILON_MM)",
        "bad = np.flatnonzero(m.clearance_mm <= required_mm[m.kind] - DRC_EPSILON_MM)",
        (D + "test_ut_drc_03_the_float_boundary_of_d006_is_rule_minus_epsilon_and_equal_passes",
         "tests/independent/m1/test_drc_agreement.py::test_intrusion_is_decided_by_d006"),
        r"== |!=|Left contains|Right contains",
    ),
    Mutant(
        "V3-02-11", "rule 5 dropped (the first, wrong spelling of V3-02-07 groups every path under net '')",
        "drc/items.py",
        "groups.setdefault((path.layer, path.net), []).append(path)",
        'groups.setdefault((path.layer, ""), []).append(path)',
        (D + "test_ut_drc_04_path_end_on_the_middle_of_a_line_of_a_same_net_path_is_a_junction",),
        r"set\(\) == |Left contains|Extra items in the left set",
    ),
    Mutant(
        "V3-02-10", "rule 2b band flipped: a via exactly pad/2 off the centreline is reported", "drc/items.py",
        "within = _centreline_distance_mm(items, candidates, via.x_mm, via.y_mm) <= via.pad_mm / 2",
        "within = _centreline_distance_mm(items, candidates, via.x_mm, via.y_mm) < via.pad_mm / 2",
        (D + "test_ut_drc_04_same_net_via_tap_band_is_half_the_via_pad",),
        r"== \[\]|Left contains",
    ),
    Mutant(
        "V3-02-12", "rule 5 widened: the landing group is the whole trunk path (DEF-UV16-01 reverted)", "drc/items.py",
        "landing |= (owner == owner[hit]) & (np.abs(slot - slot[hit]) <= 1)",
        "landing |= owner == owner[hit]",
        (D + "test_ut_drc_04_junction_end_group_is_exempt_only_from_the_primitive_the_end_lies_on",
         D + "test_ut_drc_04_branch_in_the_middle_of_a_line_leaves_the_return_main_primitive_checked",
         D + "test_ut_drc_04_wide_leg_on_a_coil_end_is_reported_against_the_coil_turn"),
        r"assert \[\] == \[|Right contains",
    ),
    Mutant(
        "V3-02-13", "interconnect tap widened: a tap exempts the whole ring (D-022c as before U-D25)", "drc/items.py",
        "yield from ((via_base + v, int(i)) for i in candidates[within])",
        "yield from ((via_base + v, int(i)) for i in candidates[within | (np.isin(items.path[candidates], "
        "items.path[candidates[within]]) & np.isin(items.path[candidates], list(interconnects)))])",
        (D + "test_ut_drc_04_interconnect_tap_leaves_a_far_primitive_of_the_ring_checked",),
        r"assert \[\] == \[|Right contains",
    ),
    Mutant(
        "V3-02-14", "rule 1 widened: a leading corner piece takes slot 0 again (DEF-UD25-01 reverted)", "drc/items.py",
        "        out.append(index)\n",
        "        out.append(max(0, index))\n",
        (D + "test_ut_drc_04_a_taper_at_a_path_end_belongs_to_one_main_primitive_only",),
        r"assert \[\] == \[|Right contains",
    ),
]  # fmt: skip

G = "tests/unit/generators/test_spiral_generate.py::"
S = "tests/independent/m2/test_spiral.py::"

V3_03 = [
    Mutant(
        "V3-03-01", "turn 0 off by one pitch (lies on turn 1)", "generators/spiral/turns.py",
        "return self.gap_mm / 2 + self.trace_width_mm / 2 + t * self.side_pitch_mm",
        "return self.gap_mm / 2 + self.trace_width_mm / 2 + (t + 1 if t == 0 else t) * self.side_pitch_mm",
        (G + "test_default_track_length_matches_cf11", S + "test_end_arc_radii_of_every_turn_match_own_construction"),
        APPROX,
    ),
    Mutant(
        "V3-03-02", "reversed arc keeps its start angle (a mirrored arc swept the wrong way)",
        "geometry/transforms.py",
        "return replace(p, start_rad=p.start_rad + p.sweep_rad, sweep_rad=-p.sweep_rad)",
        "return replace(p, start_rad=p.start_rad, sweep_rad=-p.sweep_rad)",
        (G + "test_every_path_is_continuous",
         S + "test_layer_y_is_the_reversed_mirror_of_layer_x_about_the_coil_centre_line"),
        r"continu|gap|dist|==|<=|assert",
    ),
    Mutant(
        "V3-03-03", "centre vias moved 1e-6 mm in x", "generators/spiral/generate.py",
        "                x_mm=x_mm,\n                y_mm=y_mm,\n                drill_mm=design.vias.drill_mm,",
        "                x_mm=x_mm + (1e-6 if role is ViaRole.CENTRE else 0.0),\n                y_mm=y_mm,\n"
        "                drill_mm=design.vias.drill_mm,",
        (S + "test_centre_vias_sit_on_each_coil_centre_line_at_own_radius",
         G + "test_eq01_centre_vias_sit_one_coil_pitch_of_2pi_over_q_apart"),
        APPROX,
    ),
    Mutant(
        "V3-03-04", "joint gap of 2e-6 mm before the lead to the centre via", "generators/spiral/artwork.py",
        "prims.append(lead(closing.lead_point, closing.centre_via, w, PrimitiveRole.LEAD))",
        "prims.append(lead((closing.lead_point[0] + 2e-6, closing.lead_point[1]), closing.centre_via, w, "
        "PrimitiveRole.LEAD))",
        (G + "test_every_path_is_continuous", S + "test_every_path_is_continuous_within_1e_6"),
        r"continu|gap|1e-06|<=|assert",
    ),
    Mutant(
        "V3-03-05", "joint gap of 2e-6 mm at the start of every side line (V3-03-04 respelled)",
        "generators/spiral/artwork.py",
        "prims.append(_line(start, end, w, PrimitiveRole.SIDE))",
        "prims.append(_line((start[0] + 2e-6, start[1]), end, w, PrimitiveRole.SIDE))",
        (G + "test_every_path_is_continuous", S + "test_every_path_is_continuous_within_1e_6"),
        r"continu|gap|1e-06|<=|assert",
    ),
]  # fmt: skip

K = "tests/unit/physics/test_kernels.py::"
C = "tests/unit/physics/test_closed_forms_m2e2.py::"

V3_04 = [
    Mutant(
        "V3-04-01", "EQ-05 cosh and sinh swapped (B_z and B_t terms)", "physics/field.py",
        "return base * (1.0 + e2b), base * (1.0 - e2b)", "return base * (1.0 - e2b), base * (1.0 + e2b)",
        (C + "test_cf03_coil_in_the_eq05_field_of_a_double_rotor",
         K + "test_field_is_mirrored_about_the_symmetry_plane"),
        APPROX,
    ),
    Mutant(
        "V3-04-02", "EQ-06 integrates abs(dr)", "physics/emf.py",
        "lam += bz * rm * (c2 - c1) * np.exp(-1j * harmonics * pole_pairs * am)",
        "lam += bz * rm * abs(c2 - c1) * np.exp(-1j * harmonics * pole_pairs * am)",
        (C + "test_eq06_reversed_path_reverses_the_phasor",
         "tests/independent/m2/test_physics_closed_forms.py::test_eq06_sector_loop_in_a_uniform_field_matches_the_closed_form"),
        APPROX,
    ),
    Mutant(
        "V3-04-03", "EQ-10 alpha 0.00393 read as 0.0039", "physics/analyse.py",
        'alpha = registry.constant("copper_temp_coeff_per_k").value',
        "alpha = 0.0039",
        (K + "test_cf04_track_resistance_at_20_and_60_degc", "tests/golden/m2_physics/test_physics_golden.py"),
        APPROX,
    ),
    Mutant(
        "V3-04-04", "EQ-12 divides by 12 instead of 24", "physics/emf.py",
        "return float(math.fsum(terms) / (24.0 * resistivity_ohm_m))",
        "return float(math.fsum(terms) / (12.0 * resistivity_ohm_m))",
        (C + "test_eq12_cf05_single_trace_at_full_precision",),
        APPROX,
    ),
    Mutant(
        "V3-04-05", "series sum drops its last member", "physics/circuit.py",
        "    for x in phasors:\n        total = total + x",
        "    for x in list(phasors)[:-1]:\n        total = total + x",
        ("tests/unit/physics/test_ut_phy_07_series_chain.py::"
         "test_ut_phy_07_series_chain_of_two_members_adds_as_a_phasor_sum",),
        APPROX,
    ),
]  # fmt: skip

E = "tests/unit/embodic_io/exporters/"

V3_05 = [
    Mutant(
        "V3-05-01", "SVG joint point taken from the next primitive's own coordinate", "io/svg_writer.py",
        "if here is None or math.dist(here, start) > 1e-6:", "if True:",
        (E + "test_n21_joint_continuity.py::test_n21_svg_writes_one_point_for_every_copper_joint",),
        r"joint|point|==|!=|assert",
    ),
    Mutant(
        "V3-05-02", "DXF outline: the end point of the first outer piece moved", "io/dxf_writer.py",
        '    for q in board.outline.outer:\n        dxf.prim(f"{prefix}BOARD_OUTLINE", q)',
        "    for k, q in enumerate(board.outline.outer):\n"
        "        if k == 0:\n"
        '            q = __import__("dataclasses").replace(q, sweep_rad=q.sweep_rad * (1 - 1e-4)) '
        'if hasattr(q, "sweep_rad") else __import__("dataclasses").replace(q, x2_mm=q.x2_mm + 0.01)\n'
        '        dxf.prim(f"{prefix}BOARD_OUTLINE", q)',
        (E + "test_dxf.py::test_ut_exp_02_outline_dxf_is_closed_outline_and_bore_only",),
        r"== 2|assert \d+ == 2|sum\(",
    ),
    Mutant(
        "V3-05-03", "'Key results' heading removed from the PDF", "io/report.py",
        'flow.heading("Key results")', "None",
        (E + "test_report_readme_bundle.py::test_report_key_results_are_named_with_display_labels_not_ids",
         "tests/independent/m4/test_exports_dxf_pdf_bundle.py"),
        r"Key results",
    ),
    Mutant(
        "V3-05-04", "design hash left out of the SVG metadata", "io/svg_writer.py",
        'stamp_attrs = " ".join(f"{name}={quoteattr(text)}" for name, text in metadata_fields(metadata))',
        'stamp_attrs = " ".join(f"{name}={quoteattr(text)}" for name, text in metadata_fields(metadata) '
        'if name != "design_hash")',
        (E + "test_svg.py::test_ut_io_06_svg_metadata_holds_the_stamp",),
        r"design_hash|None ==|== 'sha256",
    ),
]  # fmt: skip

CAMPAIGNS = {"V3-02": V3_02, "V3-03": V3_03, "V3-04": V3_04, "V3-05": V3_05}

SUITES = {
    "V3-02": ("tests/unit/drc",
              "tests/unit/property/wave/test_wave_properties.py::test_pr_13_run_drc_never_under_reports_on_a_wave_board",
              "tests/unit/property/serpentine/test_serpentine_properties.py::test_pr_13_drc_never_under_reports_on_serpentine_boards",
              "tests/independent/m1", "tests/independent/m3"),
    "V3-03": ("tests/unit/generators", "tests/unit/geometry", "tests/independent/m2/test_spiral.py"),
    "V3-04": ("tests/unit/physics", "tests/golden/m2_physics", "tests/independent/m2"),
    "V3-05": ("tests/unit/embodic_io/exporters", "tests/independent/m4/test_exports_dxf_pdf_bundle.py",
              "tests/independent/m4/test_exports_svg.py"),
}  # fmt: skip
