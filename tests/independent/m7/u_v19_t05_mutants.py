"""U-V19: run the REQ-T-05 tests on refusals that name only the first n refused equations (REQ-T-05 'every').

    python3 tests/independent/m7/u_v19_t05_mutants.py [--python /home/claude/embodic/.venv/bin/python] [--commit C]

Extracts a commit (default release 0.0.4, c25d8a9; U-V21 ran release 0.0.5, 42074f2) into a temporary git
repository, because record_main reads `git rev-parse HEAD`, and runs the REQ-T-05 tests of
test_record_passed_tests_gate.py and test_record_passed_tests.py on the original tools/record_passed_tests.py and on
three mutants that keep only the first 1, 2 or 4 refused equations before the refusal, printing each failed test. A
mutant that every test passes shows that 'every equation' is not asserted. The package under test is the installed
embodic of the given interpreter, whose src must equal that commit's.
"""

import argparse
import io
import re
import subprocess
import tarfile
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TOOL = "tools/record_passed_tests.py"
TESTS = ("tests/unit/results/test_record_passed_tests_gate.py", "tests/unit/results/test_record_passed_tests.py")
ANCHOR = "    if unproven:\n        return _refuse("


def run(python: str, root: Path) -> str:
    """Return pytest's summary line for the REQ-T-05 test files in root, then one line per failed test."""
    done = subprocess.run(
        [python, "-m", "pytest", "-q", "-rf", "-p", "no:cacheprovider", *TESTS],
        cwd=root,
        capture_output=True,
        text=True,
    )
    summary = re.findall(r"^(?:\d+ (?:passed|failed).*)$", done.stdout, re.MULTILINE)[-1]
    failed = re.findall(r"^FAILED (\S+)", done.stdout, re.MULTILINE)
    return "\n".join([summary, *(f"  failed {nodeid}" for nodeid in failed)])


def main() -> int:
    """Print the summary for the original tool and for each mutant."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--python", default="/home/claude/embodic/.venv/bin/python")
    parser.add_argument("--commit", default="c25d8a9")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        tar = subprocess.run(["git", "-C", str(REPO), "archive", args.commit], capture_output=True, check=True)
        with tarfile.open(fileobj=io.BytesIO(tar.stdout)) as archive:
            archive.extractall(root, filter="data")
        for step in (
            ["init", "-q"],
            ["add", "-A"],
            ["-c", "user.name=a4", "-c", "user.email=a4@local", "commit", "-qm", args.commit],
        ):
            subprocess.run(["git", *step], cwd=root, check=True)
        tool = root / TOOL
        source = tool.read_text(encoding="utf-8")
        assert source.count(ANCHOR) == 1, "the refusal of record_main moved; update ANCHOR"
        print(f"original: {run(args.python, root)}")
        for keep in (1, 2, 4):
            tool.write_text(source.replace(ANCHOR, f"    unproven = unproven[:{keep}]\n{ANCHOR}"), encoding="utf-8")
            print(f"mutant unproven[:{keep}]: {run(args.python, root)}")
        tool.write_text(source, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
