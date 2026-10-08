"""Check the icon set against the toolstrip contract and the drawing rules.

Usage, from the repository root::

    python tools/design/check_icons.py

Lists every ``TOOLSTRIP`` icon stem of interfaces.md section 11 that has no ``resources/icons/<stem>.svg``, and every
icon that breaks design_spec.md section 7: the root element must be the shared 24 px ``currentColor`` header, no
colour other than ``currentColor`` or ``none`` may appear, the file must be well-formed XML, and ``ICONS.md`` must list
it. Exit code 1 when anything is listed.
"""

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ICONS = REPO / "resources" / "icons"
INTERFACES = REPO / "docs" / "phase2" / "architecture" / "interfaces.md"
HEAD = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
)
PAINT = re.compile(r'\b(?:fill|stroke|color|stop-color)="([^"]*)"')


def toolstrip_stems(text: str) -> list[str]:
    """Return the ``icon=`` stems of the ``TOOLSTRIP`` tuple in interfaces.md, in contract order."""
    block = re.search(r"^TOOLSTRIP: tuple\[ToolstripAction, \.\.\.\] = \((.*?)^\)", text, re.M | re.S)
    if block is None:
        raise SystemExit(f"TOOLSTRIP tuple not found in {INTERFACES.relative_to(REPO)}")
    return re.findall(r'icon="([^"]+)"', block.group(1))


def rule_problems(path: Path, listed: str) -> list[str]:
    """Return the section 7 rules one icon breaks."""
    text = path.read_text(encoding="utf-8")
    problems = []
    if not text.startswith(HEAD):
        problems.append("root element differs from the shared 24 px currentColor header")
    try:
        ET.fromstring(text)
    except ET.ParseError as err:
        problems.append(f"not well-formed XML ({err})")
    colours = {v for v in PAINT.findall(text)} - {"currentColor", "none"}
    if colours or re.search(r"#[0-9a-fA-F]{3,6}\b|rgb\(", text):
        problems.append(f"fixed colour {sorted(colours) or 'in a style'}; use currentColor")
    if f"`{path.name}`" not in listed:
        problems.append("missing from ICONS.md")
    return [f"{path.name}: {p}" for p in problems]


def main() -> int:
    """Print every finding; return 1 when there is one."""
    stems = toolstrip_stems(INTERFACES.read_text(encoding="utf-8"))
    missing = [s for s in dict.fromkeys(stems) if not (ICONS / f"{s}.svg").is_file()]
    listed = (ICONS / "ICONS.md").read_text(encoding="utf-8")
    files = sorted(ICONS.glob("*.svg"))
    problems = [p for f in files for p in rule_problems(f, listed)]
    for s in missing:
        print(f"TOOLSTRIP icon without a file: {s} (expected resources/icons/{s}.svg)")
    for p in problems:
        print(f"rule: {p}")
    print(
        f"check_icons: {len(set(stems))} TOOLSTRIP stems, {len(missing)} without a file; "
        f"{len(files)} icons, {len(problems)} rule findings"
    )
    return 1 if missing or problems else 0


if __name__ == "__main__":
    sys.exit(main())
