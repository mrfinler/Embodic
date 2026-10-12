"""UT-SLF-01 and UT-SLF-02: the self-test catalogue holds on this build and stays equal to its sources (REQ-F-25)."""

import ast
import json
import re
from pathlib import Path

import pytest

from embodic.io import project as project_module
from embodic.selftest import SELFTESTS, SelfTestVerdict, run_selftests

REPO = Path(__file__).resolve().parents[3]
CF09 = ["12-10", "12-14", "12-16", "18-16", "24-14", "24-22", "24-26", "9-8", "15-16"]
EXAMPLES = ["spiral_12c16p_default", "spiral_12c14p", "spiral_12c10p_d08", "serpentine_16p_example", "wave_16p_example"]
# The ID column of interfaces.md section 14, in table order.
SECTION_14_IDS = [
    "ST-CF01",
    "ST-CF04-R20",
    "ST-CF04-R60",
    "ST-CF04-ARC",
    "ST-CF04-VIA",
    "ST-CF06-KE",
    "ST-CF06-KT-STAR",
    "ST-CF06-KT-DELTA",
    "ST-CF06-RLL-STAR",
    "ST-CF06-RLL-DELTA",
    *(f"ST-CF09-{row}-PATTERN" for row in CF09),
    *(f"ST-CF09-{row}-KD1" for row in CF09),
    "ST-CF11-LENGTH",
    "ST-CF11-TURNS",
    "ST-CF10-LENGTH",
    *(f"ST-EX-{example}-HASH" for example in EXAMPLES),
    *(f"ST-EX-{example}-COMPUTES" for example in EXAMPLES),
    "ST-DRC-DEFAULT-CLEAN",
    "ST-DRC-DEFAULT-TRACE",
    "ST-IO-ROUNDTRIP",
    "ST-EXP-BUNDLE",
]


@pytest.mark.req("REQ-F-25")
def test_ut_slf_01_every_check_of_the_catalogue_passes_on_this_build_in_catalogue_order() -> None:
    """Catches a catalogue value that no longer holds, a check lost or reordered, or an ID used twice."""
    report = run_selftests(SELFTESTS)
    failures = {r.check_id: r.message for r in report.results if r.verdict is not SelfTestVerdict.PASSED}
    assert failures == {}
    assert [r.check_id for r in report.results] == SECTION_14_IDS
    assert len(SECTION_14_IDS) == len(set(SECTION_14_IDS)) == 45
    assert (report.ok, report.cancelled) == (True, False)


@pytest.mark.req("REQ-F-25")
def test_ut_slf_01_io_roundtrip_holds_when_the_two_saves_straddle_a_second_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Catches ST-IO-ROUNDTRIP stamping each save from the wall clock, which failed in PK-11 and UI-35."""
    seconds = iter(range(60))
    monkeypatch.setattr(project_module, "_utc_now", lambda: f"2026-10-08T12:00:{next(seconds):02d}Z")
    (roundtrip,) = [check for check in SELFTESTS if check.id == "ST-IO-ROUNDTRIP"]
    (result,) = run_selftests([roundtrip]).results
    assert (result.verdict, result.message) == (SelfTestVerdict.PASSED, "")


@pytest.mark.req("REQ-F-25")
def test_ut_slf_02_cf09_literals_equal_the_oracle_file() -> None:
    """Catches a CF-09 row changed in oracle_cases.json without the catalogue, or a pattern typed wrong."""
    cases = json.loads((REPO / "docs/phase2/engineering/oracle_cases.json").read_text(encoding="utf-8"))["cases"]
    rows = next(case for case in cases if case["case_id"] == "CF-09")["expected"][0]["value"]
    oracle = {f"ST-CF09-{r['Q']}-{r['poles']}-PATTERN": r["pattern"] for r in rows}
    oracle |= {f"ST-CF09-{r['Q']}-{r['poles']}-KD1": r["kd1"] for r in rows}
    catalogue = {check.id: check.expected for check in SELFTESTS if check.id.startswith("ST-CF09-")}
    assert catalogue == oracle


@pytest.mark.req("REQ-F-25")
def test_ut_slf_02_hash_literals_equal_the_pinned_hashes_of_test_examples() -> None:
    """Catches an example whose pinned hash moved in test_examples.py while the catalogue kept the old one."""
    source = (REPO / "tests/unit/embodic_io/project/test_examples.py").read_text(encoding="utf-8")
    assignment = next(
        node
        for node in ast.parse(source).body
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "EXAMPLE_HASHES" for t in node.targets)
    )
    pinned = ast.literal_eval(assignment.value)
    hashes = [check for check in SELFTESTS if check.id.endswith("-HASH")]
    catalogue = {check.id.removeprefix("ST-EX-").removesuffix("-HASH"): check.expected for check in hashes}
    assert catalogue == pinned


@pytest.mark.req("REQ-F-25")
def test_ut_slf_02_every_source_test_names_a_file_and_a_def_that_exist() -> None:
    """Catches a source test renamed or moved, which would leave a catalogue value with no test behind it."""
    missing = []
    for check in SELFTESTS:
        path, name = check.source_test.split("::")
        file = REPO / path
        if not file.is_file() or not re.search(rf"^def {re.escape(name)}\(", file.read_text(encoding="utf-8"), re.M):
            missing.append(check.source_test)
    assert missing == []
