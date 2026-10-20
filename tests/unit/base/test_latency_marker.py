"""REQ-N-02 (D-074): the `latency` marker sits on the GUI tests that assert a tick gap or a wall-clock latency bound.

These tests collect tests/ui in a child pytest process, as the latency gate of tools/ci.py does, and read what
`-m latency` selects. Nothing runs.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
WORKER = "tests/ui/qt_shell/test_worker_and_errors.py"
TYPING = "tests/ui/qt_shell/test_n02_typing_preview.py"
STEPPING = "tests/ui/qt_shell/test_stepping_timing.py"

# The three D-074 measured on the Windows release run of 0.0.2: they assert the largest gap between 10 ms GUI ticks.
TICK_GAP_TESTS = {
    f"{WORKER}::test_ui05_event_loop_answers_within_100ms_during_a_3s_compute",
    f"{TYPING}::test_n02_10_keystroke_echo_while_a_preview_result_arrives",
    f"{TYPING}::test_n02_10_keystroke_echo_when_a_preview_result_lands_and_typing_goes_on",
}
# The others in tests/ui that assert a wall-clock latency of REQ-N-02: the 300 ms debounce within 50 ms (N02-1), a
# cancel within 50 ms of the keystroke (N02-7), a cancel that ends a scene build early (DEF-U-M8n-01), and the 300 ms
# wait of a step (UI-46, within 50 ms) with five steps 50 ms apart that make one preview (UI-48).
WALL_CLOCK_TESTS = {
    f"{TYPING}::test_n02_1_and_2_typing_previews_once_after_300_ms_and_return_commits_without_a_second_compute",
    f"{TYPING}::test_n02_7_a_keystroke_cancels_the_preview_in_flight_at_once",
    f"{WORKER}::test_def_u_m8n_01_a_cancel_during_the_scene_build_ends_it_early_and_no_result_reaches_the_shell",
    f"{STEPPING}::test_ui46_s1_a_step_previews_once_300_ms_after_the_key",
    f"{STEPPING}::test_ui48_s3_five_steps_at_50_ms_preview_once_with_the_last_value",
}


def collect_ui(report: Path, expression: str) -> tuple[set[str], dict[str, dict[str, object]]]:
    """Return (the node IDs `-m expression` selects in tests/ui, every collected test's report record by node ID)."""
    pytest.importorskip("PySide6")
    argv = [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", "-m", expression]
    done = subprocess.run(
        [*argv, f"--req-report={report}", "tests/ui"], cwd=REPO, capture_output=True, text=True, check=False
    )
    assert done.returncode == 0, done.stdout + done.stderr
    selected = {line for line in done.stdout.splitlines() if "::" in line}
    return selected, {r["nodeid"]: r for r in json.loads(report.read_text(encoding="utf-8"))}


@pytest.fixture(scope="module")
def latency_collection(tmp_path_factory):
    """Return collect_ui's answer for `latency`."""
    return collect_ui(tmp_path_factory.mktemp("latency") / "req_report.json", "latency")


@pytest.mark.req("REQ-N-02")
def test_the_latency_marker_is_registered_and_selects_the_gui_timing_tests_and_no_other_ui_test(latency_collection):
    """Catches a timing test left in the long process, or an unregistered marker (--strict-markers fails collection)."""
    selected, _ = latency_collection

    assert selected == TICK_GAP_TESTS | WALL_CLOCK_TESTS


@pytest.mark.req("REQ-N-02")
def test_the_tick_gap_tests_stay_slow_so_the_commit_profile_still_leaves_them_out(tmp_path):
    """Catches a mark that replaced the old ones: `slow` keeps the 3 s compute out of every commit."""
    selected, _ = collect_ui(tmp_path / "req_report.json", "latency and slow")

    assert selected == TICK_GAP_TESTS


@pytest.mark.req("REQ-N-02")
def test_no_latency_test_carries_an_eqt_marker(latency_collection):
    """Catches a latency test that realises a registry test, which the evidence step would see as not run.

    tools/record_passed_tests.py reads the main report only, where a latency test is `not run`. Until it reads both, an
    eqt ID on such a test would count as one that did not pass and fail the release.
    """
    selected, records = latency_collection

    assert sorted(nodeid for nodeid in selected if records[nodeid]["eqt"]) == []
