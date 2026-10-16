"""Self-tests for the dumper's area function modules (tools/golden/functions/<area>.mjs)."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from harness import load_case

pytestmark = [
    pytest.mark.req("REQ-F-10"),
    pytest.mark.skipif(
        shutil.which("node") is None
        or not Path(os.environ.get("XCOIL_ENGINE", "/home/claude/serpentine/src/engine.js")).is_file(),
        reason="needs Node and the Xcoil engine",
    ),
]

REPO_ROOT = Path(__file__).resolve().parents[3]
DUMPER = REPO_ROOT / "tools" / "golden" / "dump_xcoil.mjs"
CODEC_URL = (REPO_ROOT / "tools" / "golden" / "lib" / "codec.mjs").as_uri()
LINE_3_4_5 = {"type": "line", "x1": 0, "y1": 0, "x2": 3, "y2": 4, "width": 0.2, "kind": "side"}


def _dump(tmp_path: Path, function_name: str, cases: list[dict]) -> subprocess.CompletedProcess[str]:
    functions_dir = tmp_path / "functions"
    functions_dir.mkdir()
    (functions_dir / "scratch.mjs").write_text(
        f"import {{ primFromRecord }} from '{CODEC_URL}';\n"
        f"export const FUNCTIONS = {{\n"
        f"  {function_name}: {{ required: ['prim'], run: (E, x) => E.primLength(primFromRecord(x.prim)) / 2 }},\n"
        f"}};\n",
        encoding="utf-8",
    )
    case_file = tmp_path / "scratch.json"
    case_file.write_text(
        json.dumps({"format": "embodic.golden-cases", "format_version": 1, "area": "scratch", "cases": cases}),
        encoding="utf-8",
    )
    return subprocess.run(
        ["node", str(DUMPER), str(case_file), "--out", str(tmp_path / "out")],
        env={**os.environ, "GOLDEN_FUNCTIONS_DIR": str(functions_dir)},
        capture_output=True,
        encoding="utf-8",
        check=False,
    )


def test_area_module_functions_join_the_m1_kernels(tmp_path: Path) -> None:
    """Catch a dumper that ignores the area module, or that drops the M1 kernels when an area module is loaded."""
    cases = [
        {"id": "half", "fn": "scratchHalfLength", "note": "", "tags": [], "inputs": {"prim": LINE_3_4_5}},
        {"id": "full", "fn": "primLength", "note": "", "tags": [], "inputs": {"prim": LINE_3_4_5}},
    ]
    result = _dump(tmp_path, "scratchHalfLength", cases)
    assert result.returncode == 0, result.stderr
    assert load_case(tmp_path / "out" / "half.json").calls[0].output == 2.5
    assert load_case(tmp_path / "out" / "full.json").calls[0].output == 5


def test_function_defined_twice_stops_the_dump(tmp_path: Path) -> None:
    """Catch an area module that silently replaces an M1 kernel, so two areas' fixtures disagree on one name."""
    cases = [{"id": "full", "fn": "primLength", "note": "", "tags": [], "inputs": {"prim": LINE_3_4_5}}]
    result = _dump(tmp_path, "primLength", cases)
    assert result.returncode != 0
    assert "function primLength is already defined by dump_xcoil.mjs" in result.stderr
    assert not (tmp_path / "out").exists()
