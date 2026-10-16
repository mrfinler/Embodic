"""``embodic-cli selftest`` (REQ-F-18, UT-CLI-03): one line per check, the summary line and the exit code."""

import json
import signal
from pathlib import Path

import pytest

from embodic.api import version_info
from embodic.selftest import SELFTESTS, SelfTestCheck, SelfTestGroup


def fake(check_id: str, observed: float) -> SelfTestCheck:
    """Return a check that measures ``observed`` against an expected 1.0 ohm."""
    return SelfTestCheck(
        id=check_id,
        group=SelfTestGroup.CLOSED_FORM,
        title=f"fake {check_id}",
        source_test="tests/unit/cli/test_selftest_command.py::fake",
        expected=1.0,
        unit="ohm",
        measure=lambda _: observed,
        rel_tol=1e-9,
    )


@pytest.mark.req("REQ-F-18")
def test_ut_cli_03_every_check_passes_one_line_each_then_the_summary_and_exit_0(run) -> None:
    """Catches a check left out of the output, a summary that miscounts, or a passing run that exits non-zero."""
    code, stdout, stderr = run("selftest")
    lines = stdout.splitlines()
    assert (code, stderr) == (0, "")
    assert len(lines) == len(SELFTESTS) + 1 == 46
    assert [line.split()[:2] for line in lines[:-1]] == [["passed", check.id] for check in SELFTESTS]
    assert lines[-1] == "45 tests: 45 passed, 0 failed"


@pytest.mark.req("REQ-F-18")
def test_ut_cli_03_one_failing_check_exits_1_and_its_line_names_it(run, monkeypatch) -> None:
    """Catches a failure that exits 0, or a failure line that does not say which check or why."""
    monkeypatch.setattr("embodic.cli.commands.SELFTESTS", (fake("ST-GOOD", 1.0), fake("ST-BAD", 1.5)))
    code, stdout, _ = run("selftest")
    lines = stdout.splitlines()
    assert code == 1
    assert lines[0].split()[:2] == ["passed", "ST-GOOD"]
    assert lines[1].split()[:2] == ["failed", "ST-BAD"]
    assert lines[1].endswith("expected 1.0 ohm, observed 1.5 ohm, tolerance rel. 1e-09")
    assert lines[2] == "2 tests: 1 passed, 1 failed"


@pytest.mark.req("REQ-F-18")
def test_ut_cli_03_the_time_column_lines_up_for_the_longest_check_ids(run, monkeypatch) -> None:
    """Catches DEF-UV5-04: the two longest check IDs pushed their time 2 and 3 characters right of the other lines."""
    longest = sorted((check.id for check in SELFTESTS), key=len)[-2:]
    monkeypatch.setattr("embodic.cli.commands.SELFTESTS", tuple(fake(i, 1.0) for i in ("ST-SHORT", *longest)))
    code, stdout, _ = run("selftest")
    lines = stdout.splitlines()[:-1]
    assert (code, [line.split()[1] for line in lines]) == (0, ["ST-SHORT", *longest])
    assert len({line.index(" s", len(line) - 2) for line in lines}) == 1, lines


@pytest.mark.req("REQ-F-18")
def test_ut_cli_03_json_writes_the_selftest_document(run, monkeypatch, tmp_path: Path) -> None:
    """Catches --json that is parsed and ignored, or a file that is not the selftest_to_json document."""
    monkeypatch.setattr("embodic.cli.commands.SELFTESTS", (fake("ST-GOOD", 1.0), fake("ST-BAD", 1.5)))
    out = tmp_path / "selftest.json"
    code, _, _ = run("selftest", "--json", out)
    document = json.loads(out.read_text(encoding="utf-8"))
    assert code == 1
    assert sorted(document) == ["cancelled", "evidence_build_id", "results", "versions"]
    assert document["versions"]["embodic"] == version_info().embodic
    assert [(r["check_id"], r["verdict"], r["observed"]) for r in document["results"]] == [
        ("ST-GOOD", "passed", 1.0),
        ("ST-BAD", "failed", 1.5),
    ]


@pytest.mark.req("REQ-F-18")
def test_ut_cli_03_json_into_a_missing_folder_exits_1_before_running(run, monkeypatch, tmp_path: Path) -> None:
    """Catches a mistyped --json path found only after every check ran."""
    monkeypatch.setattr("embodic.cli.commands.SELFTESTS", (fake("ST-GOOD", 1.0),))
    code, stdout, stderr = run("selftest", "--json", tmp_path / "missing" / "selftest.json")
    assert (code, stdout) == (1, "")
    assert "error INVALID_CLI_OUTPUT_UNWRITABLE:" in stderr


@pytest.mark.req("REQ-F-18")
def test_ut_cli_03_ctrl_c_cancels_and_reports_the_rest_as_not_run(run, monkeypatch) -> None:
    """Catches Ctrl+C that kills the run without a summary, or that is swallowed and the checks go on."""

    def interrupt(_: Path) -> float:
        # os.kill(os.getpid(), SIGINT) is TerminateProcess on Windows and ends pytest itself (DEF-W-05)
        signal.raise_signal(signal.SIGINT)
        return 1.0

    first = SelfTestCheck(
        id="ST-CTRL-C",
        group=SelfTestGroup.CLOSED_FORM,
        title="presses Ctrl+C",
        source_test="tests/unit/cli/test_selftest_command.py::interrupt",
        expected=1.0,
        unit="",
        measure=interrupt,
    )
    monkeypatch.setattr("embodic.cli.commands.SELFTESTS", (first, fake("ST-LATER", 1.0), fake("ST-LAST", 1.0)))
    handler = signal.getsignal(signal.SIGINT)
    code, stdout, _ = run("selftest")
    lines = stdout.splitlines()
    assert code == 1
    assert lines[0].split()[:2] == ["passed", "ST-CTRL-C"]
    assert [line.removeprefix("not run").split()[0] for line in lines[1:3]] == ["ST-LATER", "ST-LAST"]
    assert [line.startswith("not run") for line in lines[1:3]] == [True, True]
    assert lines[3:] == ["3 tests: 1 passed, 0 failed, 2 not run"]
    assert signal.getsignal(signal.SIGINT) is handler
