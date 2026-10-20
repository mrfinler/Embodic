"""TR-01 currency (D-083c, D-084a): a manual record counts for the version under test as an exact token.

The stamp `embodic_version` of a record counts only when it is the version alone or the version followed by white
space and a note. `0.0.4` must not match `0.0.40` or `0.0.4rc1`. The version under test is the one in
`src/embodic/__init__.py` of the tree that holds the script, read as text. A venv that imports another tree's `embodic`
(a worktree under the dev venv of the main checkout, U-D26 weak point 3) must not change it.
"""

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

import embodic

TOOL = Path(__file__).resolve().parents[3] / "tools" / "trace_matrix.py"
ROW = "REQ-N-07"
TREE_VERSION = "9.9.9"


def _load_trace_matrix() -> ModuleType:
    spec = importlib.util.spec_from_file_location("trace_matrix", TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


trace_matrix = _load_trace_matrix()


def _record(stamp: str):
    return trace_matrix.ManualRecord(
        req=ROW, test_id="PK-06", record="pyproject.toml", embodic_version=stamp, result="passed"
    )


@pytest.mark.req("REQ-T-09", "REQ-N-10")
@pytest.mark.parametrize(
    "stamp",
    ["0.0.4", "0.0.4 (release c25d8a9)", "0.0.4\trestamped by the D-061d ruling of U-V18"],
    ids=["bare", "with-release", "tab-and-ruling"],
)
def test_tr01_a_stamp_that_is_the_version_alone_or_the_version_and_a_note_counts(stamp):
    """Catches an exact-token rule that is too strict for the stamps the index holds, `0.0.4 (release c25d8a9)`."""
    record = _record(stamp)
    assert trace_matrix.counted_records([record], "0.0.4") == ([record], [])


@pytest.mark.req("REQ-T-09", "REQ-N-10")
@pytest.mark.parametrize(
    "stamp",
    [
        "0.0.40",
        "0.0.40 (release c25d8a9)",
        "0.0.4rc1",
        "0.0.4.dev1",
        "0.0.4.post1",
        "0.0.4+local",
        "0.0.44",
        "v0.0.4",
        " 0.0.4",
        "",
    ],
)
def test_tr01_a_stamp_that_only_begins_with_the_version_is_stale(stamp):
    """Catches the prefix match of D-083c: 0.0.4rc1 comes before 0.0.4 and 0.0.40 is a later release (D-084a)."""
    record = _record(stamp)
    counted, stale = trace_matrix.counted_records([record], "0.0.4")
    assert counted == []
    assert len(stale) == 1
    assert repr(stamp) in stale[0] and "D-061d" in stale[0]


def _init_file(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


@pytest.mark.req("REQ-T-09", "REQ-N-10")
def test_tr01_the_version_is_read_from_the_text_of_an_init_file(tmp_path):
    """Catches a reader that imports the package: the file below would exit if it ran."""
    init = _init_file(
        tmp_path / "__init__.py", '"""Doc."""\n\nraise SystemExit("must not run")\n__version__ = "1.2.3"\n'
    )
    assert trace_matrix.read_version(init) == "1.2.3"


@pytest.mark.req("REQ-T-09", "REQ-N-10")
@pytest.mark.parametrize("text", ['"""Doc."""\n', "__version__ = 3\n", "__version__ = some_call()\n"])
def test_tr01_an_init_file_without_a_version_string_is_refused_and_named(tmp_path, text):
    """Catches a reader that returns None or an empty version, which would let every stamp count or none."""
    init = _init_file(tmp_path / "__init__.py", text)
    with pytest.raises(ValueError, match="__version__"):
        trace_matrix.read_version(init)


@pytest.fixture
def other_tree(tmp_path: Path) -> dict[str, Path]:
    """Return a copy of the script inside a tree whose `embodic` is TREE_VERSION, with a must row that has no test."""
    tree = tmp_path / "tree"
    (tree / "tools").mkdir(parents=True)
    (tree / "src" / "embodic").mkdir(parents=True)
    shutil.copy(TOOL, tree / "tools" / "trace_matrix.py")
    _init_file(tree / "src" / "embodic" / "__init__.py", f'"""Other tree."""\n\n__version__ = "{TREE_VERSION}"\n')
    (tree / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    requirements = tmp_path / "requirements.md"
    requirements.write_text(
        f"| {ROW} | amended | statement | source | must | acceptance | M5 | owner | TEST-01 |\n", encoding="utf-8"
    )
    report = tmp_path / "report.json"
    report.write_text("[]", encoding="utf-8")
    return {"script": tree / "tools" / "trace_matrix.py", "requirements": requirements, "report": report}


def _run_in_other_tree(tree: dict[str, Path], stamp: str, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    record = {
        "req": ROW,
        "test_id": "PK-06",
        "record": "pyproject.toml",
        "embodic_version": stamp,
        "result": "passed",
    }
    records = tmp_path / "records.json"
    records.write_text(json.dumps([record]), encoding="utf-8")
    argv = [
        sys.executable,
        str(tree["script"]),
        f"--report={tree['report']}",
        f"--requirements={tree['requirements']}",
        f"--out={tmp_path / 'matrix.md'}",
        "--fail-untested-through=M5",
        f"--manual-records={records}",
    ]
    return subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", check=False)


@pytest.mark.req("REQ-T-09", "REQ-N-10")
def test_tr01_a_record_of_the_version_in_the_tree_of_the_script_counts(other_tree, tmp_path):
    """Catches a version taken from the import: here `embodic` imports as another version than the tree's."""
    assert embodic.__version__ != TREE_VERSION
    done = _run_in_other_tree(other_tree, f"{TREE_VERSION} (release abc1234)", tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "manual: 1" in done.stdout
    assert "stale" not in done.stdout


@pytest.mark.req("REQ-T-09", "REQ-N-10")
def test_tr01_a_record_of_the_imported_version_is_stale_when_the_tree_says_otherwise(other_tree, tmp_path):
    """Catches a version taken from the import: a record of the imported build must not cover a row of this tree."""
    done = _run_in_other_tree(other_tree, f"{embodic.__version__} (release abc1234)", tmp_path)
    assert done.returncode == 1, done.stdout + done.stderr
    assert "manual: 0" in done.stdout
    assert [line for line in done.stdout.splitlines() if "stale" in line and "D-061d" in line]
    assert f"not counted for {TREE_VERSION}" in done.stdout
