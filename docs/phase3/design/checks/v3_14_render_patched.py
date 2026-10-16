"""U-S9 lever, part 2: render the V3-14 copy fixes in a real export.

    /home/claude/embodic/.venv/bin/python -I docs/phase3/design/checks/v3_14_render_patched.py . <new folder>

Copies src/ and resources/ into the new folder, applies every fix of v3_14_copy_check.FIXES there, writes the PDF report
of spiral_12c16p_default with the CLI, prints the PDF's DRC header line read back with pypdf, and prints the suggestion
reason check_value gives for a 60 mm air gap (DEF-UV8-01). The worktree itself is not changed.
"""

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

from pypdf import PdfReader

LEVER = Path("docs/phase3/design/checks/v3_14_copy_check.py")
EXAMPLE = Path("resources/examples/spiral_12c16p_default.embodic.json")
CLI = "import sys; sys.path.insert(0, sys.argv[1]); from embodic.cli import main; sys.exit(main(sys.argv[2:]))"
CLAMP = (
    "import sys; sys.path.insert(0, sys.argv[1]);"
    "from embodic.model.validate import check_value; from embodic.model.fields import field_specs;"
    "from embodic.model.vocabulary import TopologyKind;"
    "spec = next(s for s in field_specs(TopologyKind.SPIRAL) if s.pointer == '/rotor/air_gap_mm');"
    "(i,) = check_value(spec, '/rotor/air_gap_mm', 60.0); print(i.code, '|', i.suggestion.reason)"
)


def main() -> int:
    """Render the patched copy and print what a user would read; return the first non-zero exit code."""
    root, work = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    if work.exists():
        sys.exit(f"{work} exists; pass a folder that does not exist yet")
    sys.dont_write_bytecode = True  # keep the checks folder free of __pycache__
    spec = importlib.util.spec_from_file_location("lever", root / LEVER)
    lever = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lever)
    shutil.copytree(root / "src", work / "src")
    shutil.copytree(root / "resources", work / "resources")
    lever.apply_fixes(root, work)
    pdf = work / "report.pdf"
    export = [sys.executable, "-I", "-c", CLI, str(work / "src"), "export", str(root / EXAMPLE), "--format", "pdf"]
    run = subprocess.run(["nice", "-n", "19", *export, "-o", str(pdf)], capture_output=True, text=True, check=False)
    print("export exit", run.returncode, run.stderr.strip()[-300:])
    lines = [line for page in PdfReader(pdf).pages for line in page.extract_text().splitlines()]
    print("PDF DRC header:", [line for line in lines if line.startswith("Check ")])
    clamp = subprocess.run([sys.executable, "-I", "-c", CLAMP, str(work / "src")], capture_output=True, text=True)
    print("clamp reason:", clamp.stdout.strip(), clamp.stderr.strip()[-300:])
    return run.returncode or clamp.returncode


if __name__ == "__main__":
    sys.exit(main())
