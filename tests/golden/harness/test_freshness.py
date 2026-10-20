"""Self-tests for the fixture freshness check: every byte of a fresh dump is compared, except the Node patch (D-075).

The fixtures under test are copies of real committed ones, so no Node or Xcoil engine is needed. The "fresh" side stands
in for a dump taken after a container rebuild, which shipped another patch release of the same Node major line.
"""

import json
import math
import re
import shutil
from pathlib import Path

import pytest

from harness import DATA_DIR, fixture_drift

pytestmark = pytest.mark.req("REQ-F-10")

SAMPLE = sorted((DATA_DIR / "m1").glob("*.json"))[:3]
TARGET = SAMPLE[0].name


def _runtime(fixture: Path) -> str:
    runtime = json.loads(fixture.read_bytes())["producer"]["runtime"]
    assert isinstance(runtime, str)
    return runtime


def _edit(path: Path, old: bytes, new: bytes) -> None:
    raw = path.read_bytes()
    assert raw.count(old) == 1, old
    path.write_bytes(raw.replace(old, new))


def _set_runtime(path: Path, runtime: str) -> None:
    _edit(path, f'"runtime": "{_runtime(path)}"'.encode(), f'"runtime": "{runtime}"'.encode())


def _other_runtime(fixture: Path, *, major_step: int, tail: str) -> str:
    """Return a runtime string ``major_step`` Node majors away from the fixture's own, with ``tail`` as minor.patch."""
    match = re.fullmatch(r"node v(\d+)\.\d+\.\d+", _runtime(fixture))
    assert match is not None
    return f"node v{int(match[1]) + major_step}.{tail}"


def _nudge_one_value_by_one_ulp(path: Path) -> None:
    raw = path.read_bytes()
    calls, producer, rest = raw.partition(b'"producer"')
    literal = re.search(rb"-?\d+\.\d+(?:e[+-]?\d+)?", calls)
    assert literal is not None
    nudged = repr(math.nextafter(float(literal[0]), math.inf)).encode()
    assert float(nudged) != float(literal[0])
    path.write_bytes(calls[: literal.start()] + nudged + calls[literal.end() :] + producer + rest)
    assert json.loads(path.read_bytes()) != json.loads(raw)


@pytest.fixture
def dumps(tmp_path: Path) -> tuple[Path, Path]:
    """Return (fresh, committed) directories that start out as identical copies of three real fixtures."""
    fresh, committed = tmp_path / "fresh", tmp_path / "committed"
    for directory in (fresh, committed):
        directory.mkdir()
        for source in SAMPLE:
            shutil.copy(source, directory)
    return fresh, committed


def test_identical_dumps_are_fresh(dumps: tuple[Path, Path]) -> None:
    """Catch a freshness check that reports drift on a dump that equals the fixtures."""
    fresh, committed = dumps
    assert fixture_drift(fresh, committed) == []


@pytest.mark.parametrize("tail", ["22.0", "99.7"])
def test_another_release_of_the_same_node_major_line_is_fresh(dumps: tuple[Path, Path], tail: str) -> None:
    """Catch a check that fails the whole fixture set when a rebuilt image ships another Node release (D-075)."""
    fresh, committed = dumps
    for path in fresh.glob("*.json"):
        _set_runtime(path, _other_runtime(path, major_step=0, tail=tail))
    assert [_runtime(p) for p in fresh.glob("*.json")] != [_runtime(p) for p in committed.glob("*.json")]
    assert fixture_drift(fresh, committed) == []


def test_a_value_changed_by_one_ulp_is_stale_even_when_the_node_release_also_differs(dumps: tuple[Path, Path]) -> None:
    """Catch a check whose runtime allowance also hides a change to a recorded value."""
    fresh, committed = dumps
    for path in fresh.glob("*.json"):
        _set_runtime(path, _other_runtime(path, major_step=0, tail="22.0"))
    assert fixture_drift(fresh, committed) == []
    _nudge_one_value_by_one_ulp(committed / TARGET)
    assert [line.split(":")[0] for line in fixture_drift(fresh, committed)] == [TARGET]


@pytest.mark.parametrize("side", ["fresh", "committed"])
def test_a_node_major_line_change_is_stale(dumps: tuple[Path, Path], side: str) -> None:
    """Catch a check that accepts a dump from a different Node major line (D-075: only the patch may move)."""
    changed = dumps[0] if side == "fresh" else dumps[1]
    _set_runtime(changed / TARGET, "node v23.0.0")
    drift = fixture_drift(*dumps)
    assert [line.split(":")[0] for line in drift] == [TARGET]
    assert "producer.runtime" in drift[0]


@pytest.mark.parametrize("field", ["engine_sha256", "name"])
def test_engine_hash_and_producer_name_stay_exact(dumps: tuple[Path, Path], field: str) -> None:
    """Catch a check that lets the producer block change because its runtime field may."""
    fresh, committed = dumps
    _set_runtime(fresh / TARGET, _other_runtime(fresh / TARGET, major_step=0, tail="22.0"))
    value = json.loads((fresh / TARGET).read_bytes())["producer"][field]
    _edit(fresh / TARGET, f'"{field}": "{value}"'.encode(), f'"{field}": "{value[:-1]}0"'.encode())
    assert [line.split(":")[0] for line in fixture_drift(fresh, committed)] == [TARGET]


def test_whitespace_outside_the_runtime_value_is_compared(dumps: tuple[Path, Path]) -> None:
    """Catch a check that compares parsed JSON, which would accept a re-serialised fixture."""
    fresh, committed = dumps
    _edit(fresh / TARGET, b'"name": "xcoil-v3", "runtime"', b'"name": "xcoil-v3",  "runtime"')
    assert json.loads((fresh / TARGET).read_bytes()) == json.loads((committed / TARGET).read_bytes())
    assert [line.split(":")[0] for line in fixture_drift(fresh, committed)] == [TARGET]


def test_missing_and_extra_fixture_files_are_stale(dumps: tuple[Path, Path]) -> None:
    """Catch a check that compares only the files both directories share."""
    fresh, committed = dumps
    (fresh / SAMPLE[1].name).unlink()
    (fresh / "orphan.json").write_bytes((committed / TARGET).read_bytes())
    named = sorted(line.split(":")[0] for line in fixture_drift(fresh, committed))
    assert named == sorted([SAMPLE[1].name, "orphan.json"])


@pytest.mark.parametrize("damage", ["no-runtime", "not-json"])
def test_a_fixture_without_a_readable_runtime_is_stale_not_a_crash(dumps: tuple[Path, Path], damage: str) -> None:
    """Catch a check that raises on a malformed fixture instead of reporting it."""
    fresh, committed = dumps
    if damage == "no-runtime":
        _edit(fresh / TARGET, f', "runtime": "{_runtime(fresh / TARGET)}"'.encode(), b"")
    else:
        (fresh / TARGET).write_bytes(b"{")
    assert [line.split(":")[0] for line in fixture_drift(fresh, committed)] == [TARGET]
