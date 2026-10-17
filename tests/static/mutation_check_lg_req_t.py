"""Lever for U-M7d: apply one product mutation at a time, run the test that must catch it and always revert.

    python tests/static/mutation_check_lg_req_t.py [NAME ...]

With no name every mutation runs. Each mutation edits one tracked file, runs the named tests with `-x`, prints the
assertion lines that disagree and restores the file from the text it read, then checks `git diff` is empty for it. The
exit code is 1 when a mutated run does not end with failed tests (pytest exit 1; a pass cannot see its defect and
exit 4 is a wrong test id) or a file stays dirty.
"""

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LG_WORDING = "tests/static/test_lg_wording.py"
LG_EXPORTS = "tests/unit/embodic_io/exporters/test_lg_exports.py"
LG_NAMES = "tests/static/test_lg_brand_and_names.py"
STAMP = "tests/unit/embodic_io/exporters/test_stamp_fields.py"
DISCLOSURE = "tests/unit/ui/results/test_disclosure_every_row.py"
PLANTED_ADDRESS = "alice.smith" + chr(64) + "corp.example"  # built here so this file holds no address literal
ENGINE_ID = 'f"embodic {metadata.embodic_version} export"'


@dataclass(frozen=True)
class Mutation:
    """One edit of a tracked file and the tests that must fail under it."""

    path: str
    old: str
    new: str
    tests: tuple[str, ...]


MUTATIONS = {
    "lg03-source": Mutation(
        "src/embodic/ui/strings/results.py",
        '"drc.column.clearance": "Clearance\\n(mm)"',
        '"drc.column.clearance": "Measured\\n(mm)"',
        (f"{LG_WORDING}::test_lg03_source_strings_never_call_a_computed_value_measured",),
    ),
    "lg03-pdf": Mutation(
        "src/embodic/io/report.py",
        '(MARGIN + 130, "Least clearance")',
        '(MARGIN + 130, "Least measured")',
        (f"{LG_EXPORTS}::test_lg03_exports_and_disclosure_never_call_a_computed_value_measured",),
    ),
    "lg04-source": Mutation(
        "src/embodic/ui/strings/design.py",
        '"phase-balance-status.balanced": "Symmetric 3-phase pattern."',
        '"phase-balance-status.balanced": "Balanced."',
        (f"{LG_WORDING}::test_lg04_source_strings_make_no_balance_torque_or_efficiency_claim",),
    ),
    "lg05-readme": Mutation(
        "src/embodic/io/readme_writer.py",
        ENGINE_ID,
        'f"Xcoil {metadata.embodic_version} export"',
        (
            f"{LG_EXPORTS}::test_lg05_exports_and_disclosure_carry_no_program_name",
            f"{LG_WORDING}::test_lg05_source_strings_carry_no_program_name_beyond_the_board_dump_format",
        ),
    ),
    "lg06-source": Mutation(
        "src/embodic/io/readme_writer.py",
        ENGINE_ID,
        f'f"embodic {{metadata.embodic_version}} export, contact {PLANTED_ADDRESS}"',
        (
            f"{LG_NAMES}::test_lg06_code_and_resources_carry_no_e_mail_address_home_path_or_personal_name",
            f"{LG_EXPORTS}::test_lg06_exports_carry_no_e_mail_address_home_path_or_personal_name",
        ),
    ),
    "t01-chip": Mutation(
        "src/embodic/ui/views/status_badge.py",
        'self.setText(self.eq_id or text(f"results.eq.tag-{kind_tag}"))',
        'self.setText(self.eq_id or "")',
        (
            "tests/ui/qt_results/test_t01_every_card.py::test_t01_a_result_without_an_eq_id_shows_a_kind_tag_and_never_nothing",
        ),
    ),
    "t01-toggle": Mutation(
        "src/embodic/ui/views/results_view.py",
        "        set_revealed(self.how, shown)\n",
        "        set_revealed(self.how, False)\n",
        (
            "tests/ui/qt_results/test_t01_every_card.py::test_t01_tab_then_space_opens_the_details_of_each_of_the_30_cards",
        ),
    ),
    "t02-bare-float": Mutation(
        "src/embodic/physics/analyse.py",
        'thd_phase=tr("thd_phase", thd(amplitudes), Unit.ONE, ("EQ-18", "EQ-06"), emf_refs),',
        "thd_phase=thd(amplitudes),",
        (
            "tests/unit/results/test_real_examples_traceability.py::test_t02_every_number_of_every_example_is_a_traceable",
        ),
    ),
    "t06-br": Mutation(
        "src/embodic/model/provenance.py",
        "if _measurable(m.pointer, values) and m.source.strip()}",
        "if _measurable(m.pointer, values) and m.source.strip() and not m.pointer.startswith('/rotor')}",
        (
            "tests/unit/results/test_measured_retires_assumption.py::test_t06_marking_br_measured_with_a_source_removes_it_from_the_assumed_inputs",
        ),
    ),
    "t07-project": Mutation(
        "src/embodic/io/project.py",
        '"app_version": embodic.__version__,',
        '"app_version": "0.0.0",',
        (f"{STAMP}::test_t07_project_json_holds_the_embodic_version_the_design_hash_and_a_utc_date",),
    ),
    "t07-readme": Mutation(
        "src/embodic/io/exporters.py",
        '        ("embodic_version", metadata.embodic_version),\n        ("engine_version", metadata.engine_version),\n',  # noqa: E501
        '        ("engine_version", metadata.engine_version),\n',
        (
            f"{STAMP}::test_t07_readme_carries_the_versions_of_the_outcome_and_a_generated_utc_line",
            f"{STAMP}::test_t14_readme_names_the_embodic_version_of_the_outcome",
        ),
    ),
    "t07-pdf": Mutation(
        "src/embodic/io/exporters.py",
        'generated_utc=datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),',
        'generated_utc=datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M"),',
        (f"{STAMP}::test_t07_pdf_text_holds_a_generated_utc_value",),
    ),
    "t08-flag": Mutation(
        "src/embodic/physics/analyse.py",
        "SKIN_DEPTH_FRACTION = 1.0 / 3.0",
        "SKIN_DEPTH_FRACTION = 10.0",
        (
            "tests/unit/physics/test_skin_depth_validity_flag.py::test_t08_a_trace_of_0_4_skin_depths_flags_the_resistance_and_the_eddy_results",
        ),
    ),
    "t09-gate": Mutation(
        "tools/trace_matrix.py",
        "return 1 if unmarked or unknown or record_problems or untested else 0",
        "return 1 if unknown or record_problems or untested else 0",
        ("tests/unit/base/test_trace_matrix_gate.py::test_gate_exits_1_and_names_a_test_without_a_req_marker",),
    ),
    "t13-origin": Mutation(
        "src/embodic/ui/viewmodels/results.py",
        "            origin = ref.provenance.value\n",
        '            origin = "example"\n',
        (f"{DISCLOSURE}::test_t13_inputs_show_user_example_and_measured_where_they_apply",),
    ),
    "t13-input-line": Mutation(
        "src/embodic/ui/viewmodels/results.py",
        "    for ref in t.inputs:\n        if ref.provenance is not None:",
        "    for ref in t.inputs[:-1]:\n        if ref.provenance is not None:",
        (f"{DISCLOSURE}::test_t13_every_input_line_names_where_the_value_came_from",),
    ),
    "t13-copy-trace": Mutation(
        "src/embodic/ui/viewmodels/results.py",
        "for s in disclosure(row, registry)]\n    return",
        "for s in disclosure(row, registry)[:-1]]\n    return",
        (f"{DISCLOSURE}::test_t13_copy_trace_holds_every_disclosure_line_of_every_row",),
    ),
    "l04-tint": Mutation(
        "resources/themes/light.json",
        '"surface": "#ffffff"',
        '"surface": "#fffffe"',
        ("tests/unit/ui/shell/test_theme_chrome_tokens.py::test_every_chrome_token_has_equal_red_green_and_blue",),
    ),
}


def run(name: str) -> bool:
    """Apply one mutation, run its tests, print the disagreement and revert; return True when the tests failed."""
    mutation = MUTATIONS[name]
    path = REPO / mutation.path
    original = path.read_text(encoding="utf-8")
    assert original.count(mutation.old) == 1, f"{name}: the anchor text occurs {original.count(mutation.old)} times"
    path.write_text(original.replace(mutation.old, mutation.new), encoding="utf-8")
    try:
        env = dict(os.environ, PYTHONPATH=str(REPO / "src"), QT_QPA_PLATFORM="offscreen")
        argv = [
            sys.executable,
            "-m",
            "pytest",
            *mutation.tests,
            "-p",
            "no:cacheprovider",
            "-q",
            "-x",
            "--no-header",
            "-W",
            "ignore",
        ]
        done = subprocess.run(argv, cwd=REPO, env=env, capture_output=True, text=True, check=False, timeout=500)
        shown = [
            line for line in done.stdout.splitlines() if line.startswith(("E  ", "FAILED", "ERROR")) or "passed" in line
        ]
        print(f"=== {name}: pytest exit {done.returncode}")
        for line in shown[:6]:
            print("   ", line[:200])
    finally:
        path.write_text(original, encoding="utf-8")
    clean = subprocess.run(["git", "diff", "--quiet", "--", mutation.path], cwd=REPO, check=False).returncode == 0
    print(f"    reverted: {'clean' if clean else 'DIRTY'}")
    return done.returncode == 1 and clean


if __name__ == "__main__":
    results = [run(name) for name in (sys.argv[1:] or MUTATIONS)]
    sys.exit(0 if all(results) else 1)
