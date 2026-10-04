"""Self-tests for the committed M1 fixture set: case list agreement, coverage and reproducibility."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from harness import DATA_DIR, EXACT, Verdict, compare_sequence, decode_nonfinite, load_area

REPO_ROOT = Path(__file__).resolve().parents[3]
DUMPER = REPO_ROOT / "tools" / "golden" / "dump_xcoil.mjs"
M1_CASES = REPO_ROOT / "tools" / "golden" / "cases" / "m1.json"
ENGINE = Path(os.environ.get("XCOIL_ENGINE", "/home/claude/serpentine/src/engine.js"))


def _case_list() -> list[dict]:
    return json.loads(M1_CASES.read_text(encoding="utf-8"))["cases"]


def test_m1_fixtures_match_the_case_list() -> None:
    """Catch an orphan or missing fixture, or a case edited in m1.json without regenerating its fixture."""
    fixtures = load_area("m1")
    cases = {c["id"]: c for c in _case_list()}
    assert sorted(fixtures) == sorted(cases)
    for case_id, case in cases.items():
        fixture = fixtures[case_id]
        assert fixture.fn == case["fn"], case_id
        if "inputs" in case:
            echoed = compare_sequence([fixture.calls[0].inputs], [decode_nonfinite(case["inputs"])], EXACT)
            assert echoed.verdict is Verdict.MATCH, f"{case_id}: {echoed.describe()}"
        else:
            assert len(fixture.calls) == case["seeded"]["count"], case_id


def test_m1_fixture_set_covers_the_brief() -> None:
    """Catch a pruned case list that drops coverage the U-M1d brief, GR-17 or GR-18 require."""
    fixtures = load_area("m1")
    assert len(fixtures) >= 60
    tags = set().union(*(f.tags for f in fixtures.values()))
    required = {"line", "arc", "ccw", "cw", "gt180", "zero-length", "collinear", "crossing", "touching"}
    required |= {"mirror", "rotation", "nonfinite-input", "nonfinite-output", "signed-zero"}
    assert required <= tags, required - tags

    explicit = [f for f in fixtures.values() if "seeded" not in f.tags]
    discretize_inputs = [f.calls[0].inputs for f in explicit if f.fn == "discretize"]
    for step in ("hMax", "dAngMax", "sagTol"):
        assert any(step in inputs for inputs in discretize_inputs), step
    assert any(not {"hMax", "dAngMax", "sagTol"} & set(inputs) for inputs in discretize_inputs)
    h_max = [inputs["hMax"] for inputs in discretize_inputs if inputs.get("hMax")]
    assert min(h_max) <= 0.1 and max(h_max) >= 2

    for kind in ("random", "touching", "crossing", "collinear", "parallel"):
        assert len(fixtures[f"segsegdist-seeded-{kind}"].calls) == 1000, kind


def test_m1_fixtures_carry_engine_provenance() -> None:
    """Catch a fixture written without the engine hash that ties it to one Xcoil build."""
    hashes = {f.engine_sha256 for f in load_area("m1").values()}
    assert len(hashes) == 1
    (engine_hash,) = hashes
    assert len(engine_hash) == 64 and set(engine_hash) <= set("0123456789abcdef")


@pytest.mark.skipif(shutil.which("node") is None or not ENGINE.is_file(), reason="needs Node and the Xcoil engine")
def test_m1_fixtures_equal_a_fresh_dump(tmp_path: Path) -> None:
    """Catch fixtures that are stale against the case list or engine, or a dumper that is not deterministic."""
    subprocess.run(["node", str(DUMPER), str(M1_CASES), "--out", str(tmp_path)], check=True, capture_output=True)
    committed = sorted(p.name for p in (DATA_DIR / "m1").glob("*.json"))
    assert sorted(p.name for p in tmp_path.glob("*.json")) == committed
    stale = [name for name in committed if (tmp_path / name).read_bytes() != (DATA_DIR / "m1" / name).read_bytes()]
    assert stale == []
