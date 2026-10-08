"""Check that the M4 screenshot checklist covers every screen of screens.md.

Usage, from the repository root::

    python tools/design/check_checklist.py

Fails when a ``screens.md`` section 1 to 14 (with its subsections) has no row in ``screenshot_checklist.md``, or when a
backticked objectName in the Focus column is defined nowhere: not in ``screens.md``, ``design_spec.md`` or the
interfaces.md ``TOOLSTRIP`` ids. Templates such as ``res-<key>-how`` match any key. Exit code 1 on a finding.
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DESIGN = REPO / "docs" / "phase2" / "design"
INTERFACES = REPO / "docs" / "phase2" / "architecture" / "interfaces.md"
NAME = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9<>]+)+")


def screen_sections(text: str) -> set[str]:
    """Return the section numbers 1 to 14 of screens.md, subsections included (``8. ... and 9.`` gives both)."""
    found = set()
    for heading in re.findall(r"^#{2,3} (.+)$", text, re.M):
        for number in re.findall(r"(?:^|and )(\d+(?:\.\d+)?)\.? ", heading):
            if int(number.split(".")[0]) <= 14:
                found.add(number)
    return found


def main() -> int:
    """Print every finding; return 1 when there is one."""
    screens = (DESIGN / "screens.md").read_text(encoding="utf-8")
    known_text = screens + (DESIGN / "design_spec.md").read_text(encoding="utf-8")
    known_text += " ".join(re.findall(r'id="(act-[^"]+)"', INTERFACES.read_text(encoding="utf-8")))
    names = set(NAME.findall(known_text)) | set(re.findall(r"`#?([a-z][a-z0-9-]*)`", known_text))
    templates = [re.compile(re.escape(n).replace(re.escape("<key>"), "[a-z0-9-]+") + "$") for n in names if "<" in n]
    rows = [
        [c.strip() for c in line.strip("|").split("|")]
        for line in (DESIGN / "screenshot_checklist.md").read_text(encoding="utf-8").splitlines()
        if re.match(r"\| S\d+ \|", line)
    ]
    covered = {r[1] for r in rows}
    findings = [f"screens.md section {s} has no row" for s in sorted(screen_sections(screens) - covered)]
    for r in rows:
        for focus in re.findall(r"`([^`]+)`", r[7]):
            if focus not in names and not any(t.match(focus) for t in templates):
                findings.append(f"{r[0]}: focus objectName {focus} is defined nowhere")
    for f in findings:
        print(f)
    print(f"check_checklist: {len(rows)} rows, sections covered {sorted(covered)}, {len(findings)} findings")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
