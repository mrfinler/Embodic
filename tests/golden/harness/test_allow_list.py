"""Self-tests for the expected-diffs allow-list reader and its application to comparisons."""

from pathlib import Path

import pytest

from harness import (
    EXPECTED_DIFFS_DIR,
    KERNEL,
    KERNEL_MM,
    AllowListError,
    DiffKind,
    Verdict,
    apply_allow_list,
    compare_scalar,
    compare_sequence,
    load_allow_list,
)

pytestmark = pytest.mark.req("REQ-F-10")

ENTRY = """
schema_version = 1

[[diff]]
id = "XD-T-001"
case = "segsegdist-*"
path = "$[*].x1"
eq_id = "EQ-30"
reason = "exact kernel replaces the discretised one"
agent2_signoff = "A2 2026-10-04"
agent4_signoff = "A4 2026-10-04"
"""

OVERRIDE = """
schema_version = 1

[[diff]]
id = "XD-T-002"
case = "primlength-arc-ccw-270"
eq_id = "EQ-03"
reason = "port sums in a different order"
tolerance = { rel = 1e-9, abs = 0.0 }
agent2_signoff = "A2"
agent4_signoff = "A4"
"""


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "area.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_committed_m1_allow_list_parses_and_is_empty() -> None:
    """Catch a malformed m1.toml, or an M1 deviation recorded without going through this schema."""
    assert load_allow_list(EXPECTED_DIFFS_DIR / "m1.toml") == ()


def test_allow_list_reads_every_field(tmp_path: Path) -> None:
    """Catch a reader that drops the EQ-ID, the reason or a sign-off."""
    (entry,) = load_allow_list(_write(tmp_path, OVERRIDE))
    assert (entry.id, entry.case, entry.path, entry.eq_id) == ("XD-T-002", "primlength-arc-ccw-270", "*", "EQ-03")
    assert entry.reason == "port sums in a different order"
    assert (entry.agent2_signoff, entry.agent4_signoff) == ("A2", "A4")
    assert entry.tolerance is not None
    assert (entry.tolerance.rel, entry.tolerance.abs) == (1e-9, 0.0)


@pytest.mark.parametrize(
    ("edit", "message"),
    [
        (lambda t: t.replace('eq_id = "EQ-30"\n', ""), "missing eq_id"),
        (lambda t: t.replace('eq_id = "EQ-30"', 'eq_id = "EQ-3"'), "eq_id"),
        (lambda t: t.replace('reason = "exact kernel replaces the discretised one"', 'reason = ""'), "reason"),
        (lambda t: t.replace('agent4_signoff = "A4 2026-10-04"\n', ""), "missing agent4_signoff"),
        (lambda t: t + 'owner = "someone"\n', "unknown key owner"),
        (lambda t: t.replace("schema_version = 1", "schema_version = 2"), "schema_version"),
        (lambda t: t + "tolerance = { rel = -1e-9, abs = 0.0 }\n", "tolerance"),
        (lambda t: t + "tolerance = { rel = 1e-9 }\n", "tolerance"),
        (lambda t: t + t.split("schema_version = 1", 1)[1], "duplicate id XD-T-001"),
    ],
)
def test_allow_list_rejects_entries_outside_the_schema(tmp_path: Path, edit, message: str) -> None:
    """Catch an allow-list entry that skips its EQ-ID, reason or sign-off, or carries an unusable override."""
    with pytest.raises(AllowListError, match=message):
        load_allow_list(_write(tmp_path, edit(ENTRY)))


def test_allow_listed_difference_is_reported_as_expected(tmp_path: Path) -> None:
    """Catch an allow-listed diff still failing, or an entry excusing a path or case it does not name."""
    entries = load_allow_list(_write(tmp_path, ENTRY))
    golden = [{"x1": 1.0, "y1": 2.0}, {"x1": 3.0, "y1": 4.0}]
    shifted_x = [{"x1": 1.0, "y1": 2.0}, {"x1": 3.5, "y1": 4.0}]
    result = apply_allow_list(compare_sequence(golden, shifted_x, KERNEL_MM), "segsegdist-crossing", entries)
    assert result.verdict is Verdict.EXPECTED
    assert [(d.path, d.allow_id) for d in result.diffs] == [("$[1].x1", "XD-T-001")]

    shifted_y = [{"x1": 1.0, "y1": 2.0}, {"x1": 3.0, "y1": 4.5}]
    assert apply_allow_list(compare_sequence(golden, shifted_y, KERNEL_MM), "segsegdist-crossing", entries).verdict is (
        Verdict.MISMATCH
    )
    assert apply_allow_list(compare_sequence(golden, shifted_x, KERNEL_MM), "ptsegdist-interior", entries).verdict is (
        Verdict.MISMATCH
    )


def test_allow_list_tolerance_override_bounds_the_excuse(tmp_path: Path) -> None:
    """Catch an override that excuses any drift instead of only drift within its own bound."""
    entries = load_allow_list(_write(tmp_path, OVERRIDE))
    within = compare_scalar(23.56194490192345, 23.56194490192345 * (1 + 5e-10), KERNEL)
    beyond = compare_scalar(23.56194490192345, 23.56194490192345 * (1 + 5e-9), KERNEL)
    assert within.verdict is beyond.verdict is Verdict.MISMATCH
    assert apply_allow_list(within, "primlength-arc-ccw-270", entries).verdict is Verdict.EXPECTED
    assert apply_allow_list(beyond, "primlength-arc-ccw-270", entries).verdict is Verdict.MISMATCH


def test_allow_list_override_does_not_excuse_structural_diffs(tmp_path: Path) -> None:
    """Catch a numeric override excusing a length change; an entry without override does excuse it."""
    length_diff = compare_sequence([1.0, 2.0], [1.0], KERNEL)
    assert length_diff.diffs[0].kind is DiffKind.LENGTH
    with_override = load_allow_list(_write(tmp_path, OVERRIDE))
    assert apply_allow_list(length_diff, "primlength-arc-ccw-270", with_override).verdict is Verdict.MISMATCH
    without_override = load_allow_list(_write(tmp_path, ENTRY.replace('path = "$[*].x1"\n', "")))
    assert apply_allow_list(length_diff, "segsegdist-crossing", without_override).verdict is Verdict.EXPECTED
