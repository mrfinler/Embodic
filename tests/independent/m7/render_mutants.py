"""Print the Markdown mutant table of a product_mutants.py ``--json`` file, for the V3-0x records.

python tests/independent/m7/render_mutants.py <campaign.json>
"""

import json
import sys
from pathlib import Path


def cell(text: str) -> str:
    """Escape a table cell: pipes and backticks would break the row."""
    return text.replace("|", "\\|").replace("`", "'").replace("\n", " ")


def render(doc: dict) -> str:
    """One row per mutant: what it changes, the tests named before the run, the verdict and the failure quoted."""
    rows = [
        "| ID | Defect | File | Named killing tests | Verdict | First failing test | Disagreement (first assertion) |",
        "|---|---|---|---|---|---|---|",
    ]
    for mutant, outcome in zip(doc["mutants"], doc["outcomes"], strict=True):
        named = "; ".join(k.split("::")[-1] if "::" in k else k for k in mutant["killers"])
        failed = outcome["failed"][0].removeprefix("FAILED ").split(" - ")[0] if outcome["failed"] else "-"
        lines = [e.removeprefix("E").strip() for e in outcome["evidence"] if e.removeprefix("E").strip()]
        first = lines[1] if len(lines) > 1 and lines[0].startswith("AssertionError: seed") else (lines or ["-"])[0]
        rows.append(
            f"| {mutant['id']} | {cell(mutant['defect'])} | `src/embodic/{mutant['file']}` | {cell(named)} | "
            f"{outcome['verdict']} | {cell(failed)} | {cell(first[:180])} |"
        )
    return "\n".join(rows)


if __name__ == "__main__":
    print(render(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))))
