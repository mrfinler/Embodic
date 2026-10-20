"""Freshness of the golden fixtures against a fresh Xcoil dump (D-075).

A fixture records the Node release that wrote it in ``producer.runtime`` (``node v22.22.2``). A rebuilt image can ship
another release of the same major line whose dump is identical in everything else. ``fixture_drift`` compares every byte
of a fresh dump with the committed fixtures except the value of that one field, where only the major line must agree.
Recorded values, the engine sha256 and the producer name stay exact.
"""

import json
import re
from pathlib import Path

_RUNTIME_FIELD = b'"runtime": '
_BLANKED_RUNTIME_FIELD = _RUNTIME_FIELD + b"null"
_NODE_RELEASE = re.compile(r"node v(?P<major>\d+)\.\d+\.\d+")
_CONTEXT_BYTES = 24


def fixture_drift(fresh_dir: Path, committed_dir: Path) -> list[str]:
    """Return one line per way a fresh dump differs from the committed fixtures; empty when the fixtures are fresh."""
    fresh = {p.name: p.read_bytes() for p in fresh_dir.glob("*.json")}
    committed = {p.name: p.read_bytes() for p in committed_dir.glob("*.json")}
    drift = [f"{name}: missing from the fresh dump" for name in sorted(committed.keys() - fresh.keys())]
    drift += [f"{name}: not among the committed fixtures" for name in sorted(fresh.keys() - committed.keys())]
    for name in sorted(committed.keys() & fresh.keys()):
        problem = _fixture_problem(fresh[name], committed[name])
        if problem is not None:
            drift.append(f"{name}: {problem}")
    return drift


def _fixture_problem(fresh: bytes, committed: bytes) -> str | None:
    fresh_split, committed_split = _blank_runtime(fresh), _blank_runtime(committed)
    if fresh_split is None or committed_split is None:
        return "has no single string-valued producer.runtime to compare"
    (fresh_rest, fresh_runtime), (committed_rest, committed_runtime) = fresh_split, committed_split
    if fresh_rest != committed_rest:
        return f"bytes differ, {_first_difference(fresh_rest, committed_rest)}"
    if not _same_node_major_line(fresh_runtime, committed_runtime):
        return (
            f"producer.runtime {fresh_runtime!r} is not on the Node major line of the committed {committed_runtime!r}"
        )
    return None


def _blank_runtime(raw: bytes) -> tuple[bytes, str] | None:
    """Return the fixture bytes with the value of ``producer.runtime`` replaced, and that value."""
    try:
        runtime = json.loads(raw)["producer"]["runtime"]
    except (ValueError, KeyError, TypeError):
        return None
    if not isinstance(runtime, str):
        return None
    field = _RUNTIME_FIELD + json.dumps(runtime).encode()
    if raw.count(field) != 1:
        return None
    return raw.replace(field, _BLANKED_RUNTIME_FIELD), runtime


def _same_node_major_line(fresh: str, committed: str) -> bool:
    if fresh == committed:
        return True
    fresh_release, committed_release = _NODE_RELEASE.fullmatch(fresh), _NODE_RELEASE.fullmatch(committed)
    return (
        fresh_release is not None
        and committed_release is not None
        and fresh_release["major"] == committed_release["major"]
    )


def _first_difference(fresh: bytes, committed: bytes) -> str:
    shared = min(len(fresh), len(committed))
    offset = next((i for i in range(shared) if fresh[i] != committed[i]), shared)
    window = slice(max(offset - _CONTEXT_BYTES, 0), offset + _CONTEXT_BYTES)
    return f"first at byte {offset}: fresh {fresh[window]!r}, committed {committed[window]!r}"
