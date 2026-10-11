"""Drive the embodic desktop app offscreen and write the evidence to build/verify/<UTC timestamp>/.

Run from the repository root with the project's virtual environment::

    .venv/bin/python .claude/skills/verify/verify.py                 # doctor, e2e tests, 41 rows, UI-09
    .venv/bin/python .claude/skills/verify/verify.py --acceptance    # and copy shots to build/screens/acceptance
    .venv/bin/python .claude/skills/verify/verify.py --rows S04 S07  # only these rows (the e2e tests still run)
    .venv/bin/python .claude/skills/verify/verify.py --doctor        # the read-only checks only

The run writes report.json beside the PNGs: what ran, what passed, and what is `not tested`. Exit code 0 when the
doctor, every e2e test and every captured row passed.
"""

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TOOLS = ("pdftoppm", "pdftotext", "pdffonts", "pdfinfo")
SCALES = ("1", "1.5", "2")
NOT_TESTED = {
    "UI-09 text clipping": "a judgement on the three scaling grabs; no machine check (Agent 1 reviews them)",
    "UI-20 rotor-angle overlay": "not implemented in this build (REQ-F-30 is a could)",
    "S33 Tests dialog": "moved to M5 (D-042a): no Tests dialog (`tests-table`) exists in this build",
    "U+00A0 between number and unit": "a still image cannot tell U+00A0 from a space",
    "S36 and S38 numbers": "shot_measure.py measures the 1280 x 800 panes and the gallery only",
    "keyboard in the file dialog": "the Windows build uses the native dialog; AX-02 opens through the Examples gallery",
}


def env() -> dict[str, str]:
    """Return the environment every child process runs in: offscreen Qt, this checkout's sources first."""
    paths = [str(REPO / "src"), str(REPO), os.environ.get("PYTHONPATH", "")]
    return {**os.environ, "QT_QPA_PLATFORM": "offscreen", "PYTHONPATH": os.pathsep.join(p for p in paths if p)}


def run(argv: list[str], **extra: str) -> subprocess.CompletedProcess[str]:
    """Run a child process from the repository root and capture its output."""
    return subprocess.run(argv, cwd=REPO, env={**env(), **extra}, capture_output=True, text=True, check=False)


def doctor() -> dict[str, object]:
    """Answer "is this checkout worth driving?" without changing anything."""
    probe = (
        "import embodic, PySide6; from embodic.ui.fonts import FONT_FILES, font_file; "
        "missing = [f for files in FONT_FILES.values() for f in files if not font_file(f).is_file()]; "
        "print(embodic.__file__); print(PySide6.__version__); print(missing)"
    )
    done = run([sys.executable, "-c", probe])
    lines = done.stdout.splitlines()
    checks = {
        "python": sys.version.split()[0],
        "imports": done.returncode == 0,
        "embodic from this checkout": bool(lines) and Path(lines[0]).is_relative_to(REPO / "src"),
        "pyside6": lines[1] if len(lines) > 1 else None,
        "bundled fonts present": len(lines) > 2 and lines[2] == "[]",
        "poppler tools": {tool: shutil.which(tool) is not None for tool in TOOLS},
    }
    tools_ok = all(checks["poppler tools"].values())  # type: ignore[union-attr]
    checks["passed"] = bool(checks["imports"] and checks["embodic from this checkout"]) and tools_ok
    checks["passed"] = checks["passed"] and bool(checks["bundled fonts present"])
    if done.returncode:
        checks["error"] = done.stderr.strip().splitlines()[-1:]
    return checks


def e2e(out: Path) -> dict[str, object]:
    """Run tests/ui/qt_e2e (walkthroughs, AX-02, AX-04, UI-09, review fixes) and read each outcome."""
    junit = out / "e2e_junit.xml"
    argv = [sys.executable, "-m", "pytest", "tests/ui/qt_e2e", "-q", "-p", "no:cacheprovider", "-rx"]
    done = run([*argv, f"--junitxml={junit}"])
    outcomes: dict[str, str] = {}
    for case in ET.parse(junit).getroot().iter("testcase"):
        kinds = {child.tag for child in case}
        skipped = case.find("skipped")
        xfail = skipped is not None and "xfail" in (skipped.get("type", "") + skipped.get("message", ""))
        if kinds & {"failure", "error"}:
            outcome = "failed"
        else:
            outcome = "xfailed" if xfail else "skipped" if skipped is not None else "passed"
        outcomes[f"{case.get('classname')}::{case.get('name')}"] = outcome
    (out / "e2e_pytest.txt").write_text(done.stdout + done.stderr, encoding="utf-8")
    return {"exit_code": done.returncode, "summary": done.stdout.strip().splitlines()[-1:], "tests": outcomes}


def capture(out: Path, rows: list[str], *flags: str, **extra: str) -> list[dict[str, object]]:
    """Run the acceptance lever and return its JSON line per row."""
    argv = [sys.executable, "-m", "tests.ui.qt_shell.capture_acceptance", str(out), *rows, *flags]
    done = run(argv, **extra)
    lines = [json.loads(line) for line in done.stdout.splitlines() if line.startswith("{")]
    if done.returncode:
        lines.append({"row": "lever", "files": [], "notes": [f"exit {done.returncode}: {done.stderr[-400:]}"]})
    return lines


def row_status(row: dict[str, object]) -> str:
    """Return passed, not tested or failed for one lever line."""
    notes = [str(n) for n in row["notes"]]  # type: ignore[union-attr]
    if any(n.startswith("error") for n in notes) or (not row["files"] and not notes):
        return "failed"
    return "passed" if row["files"] else "not tested"


def shot_measure(shots: Path, out: Path) -> dict[str, object]:
    """Stage S22 (1280 x 800, results tab) and S39 (gallery, row 1 selected) under the names shot_measure.py reads."""
    stage = out / "shot_measure_input"
    stage.mkdir(exist_ok=True)
    pairs = {
        "S22_light_1280x800.png": "u-m4e_canvas-60-40_spiral_12c10p_d08_1280x800.png",
        "S39_light_dialog.png": "u-m4e_gallery-selected_light.png",
    }
    for source, staged in pairs.items():
        if (shots / source).is_file():
            shutil.copy(shots / source, stage / staged)
    done = run([sys.executable, "docs/phase2/design/checks/shot_measure.py", str(stage)])
    return {"exit_code": done.returncode, "output": done.stdout.strip().splitlines(), "inputs": pairs}


def main(argv: list[str] | None = None) -> int:
    """Run the verification and write report.json; return 0 when everything that ran passed."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--acceptance", action="store_true", help="copy the shots to build/screens/acceptance")
    parser.add_argument("--doctor", action="store_true", help="only the read-only checks")
    parser.add_argument("--rows", nargs="*", default=[], help="checklist row ids to capture (default all 41)")
    args = parser.parse_args(argv)
    started = dt.datetime.now(dt.UTC)
    out = REPO / "build" / "verify" / started.strftime("%Y%m%dT%H%M%SZ")
    shots = out / "shots"
    shots.mkdir(parents=True)
    head = run(["git", "rev-parse", "--short", "HEAD"]).stdout.strip()
    report: dict[str, object] = {"started_utc": started.isoformat(timespec="seconds"), "commit": head}
    report["doctor"] = checks = doctor()
    print(f"doctor: {'pass' if checks['passed'] else 'FAIL'}", flush=True)
    if args.doctor or not checks["passed"]:
        (out / "report.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
        print(out.relative_to(REPO) / "report.json")
        return 0 if checks["passed"] else 1
    report["e2e"] = tests = e2e(out)
    print(f"e2e: {tests['summary']}", flush=True)
    rows = capture(shots, args.rows)
    report["rows"] = {str(r["row"]): {**r, "status": row_status(r)} for r in rows}
    print(f"rows: {sum(r['status'] == 'passed' for r in report['rows'].values())} of {len(rows)} captured", flush=True)
    scaling = [capture(out / "scaling", [], "--scaling", QT_SCALE_FACTOR=s)[0] for s in SCALES]
    report["ui09_scaling"] = {s: {**r, "status": row_status(r)} for s, r in zip(SCALES, scaling, strict=True)}
    report["shot_measure"] = shot_measure(shots, out)
    report["not_tested"] = NOT_TESTED
    failed_tests = [name for name, outcome in tests["tests"].items() if outcome == "failed"]  # type: ignore[union-attr]
    failed_rows = [r for r, v in report["rows"].items() if v["status"] == "failed"]  # type: ignore[union-attr]
    report["passed"] = not failed_tests and not failed_rows and tests["exit_code"] == 0
    report["failed"] = {"tests": failed_tests, "rows": failed_rows}
    if args.acceptance:
        target = REPO / "build" / "screens" / "acceptance"
        shutil.rmtree(target, ignore_errors=True)
        shutil.copytree(shots, target)
        report["acceptance_dir"] = str(target.relative_to(REPO))
    report["finished_utc"] = dt.datetime.now(dt.UTC).isoformat(timespec="seconds")
    (out / "report.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(out.relative_to(REPO) / "report.json")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
