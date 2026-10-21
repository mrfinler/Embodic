"""Fail when uat_walkthrough.md quotes UI text that neither the product source nor the 0.0.6 probe dump holds.

A quote is a "double-quoted" or **bold** span outside code. The source is every file under src/embodic (labels,
the issue catalogue, the PDF writer); the dump is uat_probe_0.0.6.json, the text the 0.0.6 candidate wheel showed
offscreen, which holds the filled-in templates ("34 required fields left"). A double-quoted span may be part of a longer
string, such as one line of a message. A bold span names a control, so it must equal one whole string. Run from the
repository root:

    python3 docs/phase4/design/checks/uat_quote_check.py
"""

import ast
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WALKTHROUGH = HERE.parent / "uat_walkthrough.md"
DUMP = HERE / "uat_probe_0.0.6.json"
SOURCE = HERE.parents[3] / "src" / "embodic"
# Words the walkthrough defines for its own record boxes; they are not product text.
OWN_WORDS = {"Judge", "Judge.", "P", "F", "N"}


def normalise(text: str) -> str:
    return text.replace("\u00a0", " ").replace("\\u2212", "\u2212").replace("\\u00a0", " ").replace("\\n", "\n")


def strings_of(node) -> list[str]:
    if isinstance(node, str):
        return [node]
    if isinstance(node, dict):
        return [s for value in node.values() for s in strings_of(value)]
    if isinstance(node, list):
        return [s for value in node for s in strings_of(value)]
    return []


def corpus() -> tuple[str, set[str]]:
    sources = [path.read_text(encoding="utf-8") for path in sorted(SOURCE.rglob("*.py"))]
    shown = strings_of(json.loads(DUMP.read_text(encoding="utf-8")))
    literals = {
        node.value
        for source in sources
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    whole = {normalise(s).strip() for s in literals | set(shown)}
    return normalise("\n".join(sources + shown)), whole


def quotes(markdown: str) -> list[tuple[int, str]]:
    found = []
    in_fence = False
    for number, line in enumerate(markdown.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        prose = re.sub(r"`[^`]*`", "", line)
        found += [(number, "bold", m) for m in re.findall(r"\*\*(.+?)\*\*", prose)]
        found += [(number, "quote", m) for m in re.findall(r'"([^"]+)"', re.sub(r"\*\*", "", prose))]
    return found


def found(kind: str, quote: str, text: str, whole: set[str]) -> bool:
    if quote in OWN_WORDS:
        return True
    return normalise(quote) in whole if kind == "bold" else normalise(quote) in text


def main() -> int:
    text, whole = corpus()
    spans = quotes(WALKTHROUGH.read_text(encoding="utf-8"))
    misses = [(n, kind, q) for n, kind, q in spans if not found(kind, q, text, whole)]
    for number, kind, quote in misses:
        print(f"uat_walkthrough.md:{number}: {kind} span not in the product: {quote!r}")
    print(f"{len(spans)} quotes, {len(misses)} not found")
    return 1 if misses else 0


if __name__ == "__main__":
    sys.exit(main())
