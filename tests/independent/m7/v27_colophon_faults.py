"""U-V27: seed colophon faults into a copy of the report writer and run the colophon test against each (DEF-UV27-01).

    python3 tests/independent/m7/v27_colophon_faults.py [--commit 6d50d0b] [--python <dev venv python>]

The product is `git archive <commit>`; the instrument is this working tree's `tests/independent/m4`, copied over the
archive, so the test under trial is the one on disk. Each case applies one text edit to `src/embodic/io/report.py`
(none for `clean`), runs `test_colophon_is_the_last_line_of_the_report` with PYTHONPATH set to the copy's src, and
reads the D08 report three ways: pypdf layout mode (what the test reads), pypdf plain mode, and `pdftotext -layout`
(the reading the test used before, where installed). A fault is `killed` when the clean run passes and the seeded run
fails; the first assertion line is printed.
"""

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
INSTRUMENT = Path(__file__).resolve().parents[1] / "m4"
TEST = "tests/independent/m4/test_exports_dxf_pdf_bundle.py::test_colophon_is_the_last_line_of_the_report"
REPORT = "src/embodic/io/report.py"
LAST_ROW = "    doc.row(MARGIN, [(MARGIN, COLOPHON)])\n"
DRAWINGS = "    for index, board in enumerate(boards, start=1):\n"
COLOPHON = "Set in Inter and JetBrains Mono, SIL Open Font License 1.1."


@dataclass(frozen=True)
class Case:
    """One seeded fault: its name, what it does, and the text of report.py it replaces."""

    name: str
    effect: str
    old: str
    new: str


CASES = (
    Case("clean", "the report as committed", LAST_ROW, LAST_ROW),
    Case(
        "top",
        "drawn last, but placed at the top of the last page, above the drawing and the legend",
        LAST_ROW,
        "    doc.row(PAGE_H - MARGIN, [(MARGIN, COLOPHON)])\n",
    ),
    Case(
        "early",
        "moved before the drawing pages, to the foot of the inputs page",
        DRAWINGS + "        _drawing(doc, index, board, inks, mode is PhaseRenderMode.GREYSCALE_HATCH)\n" + LAST_ROW,
        LAST_ROW + DRAWINGS + "        _drawing(doc, index, board, inks, mode is PhaseRenderMode.GREYSCALE_HATCH)\n",
    ),
    Case("twice", "once at the foot of the inputs page and once at the end", DRAWINGS, LAST_ROW + DRAWINGS),
)

READ = """
import json, subprocess, sys
sys.path.insert(0, sys.argv[4])
from pathlib import Path
import pypdf
import embodic
from embodic.api import compute_project
from embodic.io.report import write_report_pdf
pdf = Path(sys.argv[2])
write_report_pdf(compute_project(Path(sys.argv[1])), pdf)
pages = pypdf.PdfReader(pdf).pages
readings = {
    "pypdf layout": "\\n".join(p.extract_text(extraction_mode="layout") for p in pages),
    "pypdf plain": "\\n".join(p.extract_text() for p in pages),
}
if sys.argv[3] != "absent":
    readings["pdftotext -layout"] = subprocess.run(
        [sys.argv[3], "-layout", str(pdf), "-"], capture_output=True, text=True, check=True
    ).stdout.replace("\\f", "\\n")
print(json.dumps({"embodic": embodic.__file__, "readings": readings}))
"""


def pytest(python: str, root: Path) -> tuple[int, str]:
    """Run the colophon test in root against root/src; return the exit code and the summary plus the first E line."""
    env = {**os.environ, "PYTHONPATH": str(root / "src")}
    done = subprocess.run(
        [python, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rf", TEST],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
    )
    summary = re.findall(r"^\d+ (?:passed|failed).*$", done.stdout, re.MULTILINE)
    first = re.findall(r"^E\s+(.*)$", done.stdout, re.MULTILINE)
    return done.returncode, "; ".join([*summary[-1:], *first[:1]])


def readings(python: str, root: Path) -> tuple[str, dict[str, str]]:
    """Write the D08 report from root/src; return the embodic it imported and the verdict of each reading."""
    pdftotext = shutil.which("pdftotext") or "absent"
    example = root / "resources" / "examples" / "spiral_12c10p_d08.embodic.json"
    done = subprocess.run(
        [python, "-I", "-c", READ, str(example), str(root / "d08.pdf"), pdftotext, str(root / "src")],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(done.stdout)
    out = {}
    for name, text in data["readings"].items():
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        verdict = "pass" if lines[-1] == COLOPHON and text.count(COLOPHON) == 1 else "fail"
        out[name] = f"{verdict}: last line {lines[-1]!r}, colophon count {text.count(COLOPHON)}"
    if pdftotext == "absent":
        out["pdftotext -layout"] = "absent on this machine"
    return data["embodic"], out


def main() -> int:
    """Print the clean and every seeded result; exit 1 when the clean run fails or a fault is not killed."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--commit", default="HEAD")
    parser.add_argument("--python", default="/home/claude/embodic/.venv/bin/python", help="the dev venv python")
    args = parser.parse_args()
    tar = subprocess.run(["git", "-C", str(REPO), "archive", args.commit], capture_output=True, check=True).stdout
    failures = 0
    for case in CASES:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with tarfile.open(fileobj=io.BytesIO(tar)) as archive:
                archive.extractall(root, filter="data")
            shutil.rmtree(root / "tests" / "independent" / "m4")
            shutil.copytree(
                INSTRUMENT, root / "tests" / "independent" / "m4", ignore=shutil.ignore_patterns("__pycache__")
            )
            target = root / REPORT
            text = target.read_text(encoding="utf-8")
            assert text.count(case.old) == 1, f"{REPORT}: the seeded text moved ({case.name})"
            target.write_text(text.replace(case.old, case.new), encoding="utf-8")
            code, result = pytest(args.python, root)
            imported, read = readings(args.python, root)
            assert Path(imported).is_relative_to(root), f"the reading imported {imported}, not the copy"
        expected = case.name == "clean"
        ok = (code == 0) == expected
        failures += not ok
        verdict = ("clean passes" if ok else "CLEAN FAILS") if expected else ("killed" if ok else "NOT KILLED")
        print(f"{case.name}: {case.effect}")
        print(f"  test: exit {code}; {result}")
        for name, line in read.items():
            print(f"  {name}: {line}")
        print(f"  {verdict}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
