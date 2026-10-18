"""REQ-T-11 reviewer lister (U-V14): every shown text that names balance, torque or efficiency, where the UI shows it.

    QT_QPA_PLATFORM=offscreen PYTHONPATH=src python tests/independent/m7/v14_t11_review.py

The places are those of test_plan.md section 5.8.3: the results table (the cards of `result_rows` with their
'How was this computed' disclosure, and the Torque-speed tab of `torque_speed_charts`), the equation guide
(`equation_topic` for every equation) and the PDF report of each packaged example (text read with pypdf). The word
pattern is Agent 4's own, not the product scanner's: a word that starts with balanc, imbalanc, unbalanc, torque or
efficien, ignoring case. The reviewer reads the printed lines; this script makes no verdict. For each torque or
efficiency card it also prints the Inputs section of its disclosure, so the reader sees whether the value rests on more
than geometry and phase angles.
"""

import hashlib
import re
import sys
import tempfile
from pathlib import Path

import pypdf

from embodic.api import compute_project
from embodic.io.report import write_report_pdf
from embodic.results.registry import load_registry
from embodic.ui.viewmodels.results import disclosure, equation_topic, result_rows, torque_speed_charts

REPO = Path(__file__).resolve().parents[3]
EXAMPLES = REPO / "resources" / "examples"
ALLOWLIST = REPO / "tests" / "static" / "lg_allowlist.toml"
WORD = re.compile(r"(?<![a-z])(?:balanc|imbalanc|unbalanc|torque|efficien)\w*", re.IGNORECASE)


def shown(line: str) -> bool:
    """Return True when a shown line names balance, torque or efficiency."""
    return WORD.search(line) is not None


def guide_lines(registry) -> list[str]:
    """Return the guide lines that name balance, torque or efficiency, with the equation and the row label."""
    out = []
    for eq_id in registry.equations:
        topic = equation_topic(eq_id, registry)
        lines = [("title", topic.title), *((label, v) for label, value in topic.rows for v in value.splitlines())]
        out += [f"{eq_id} [{label}] {line}" for label, line in lines if shown(line)]
    return out


def card_lines(outcome, registry) -> list[str]:
    """Return the matching result cards with their disclosure Inputs, then the Torque-speed tab."""
    out = []
    for row in result_rows(outcome.analysis):
        if not (shown(row.title) or shown(row.label)):
            continue
        out.append(
            f"card {row.quantity}: title {row.title!r}, value {row.value_text} {row.unit_text}, status "
            f"{row.status.value}, {row.assumed_count} assumptions, {', '.join(row.eq_ids)}, estimate label "
            f"{row.estimate_label!r}"
        )
        for section in disclosure(row, registry):
            out += [
                f"    {section.title}: {line}"
                for line in section.lines
                if section.title.lower().startswith("input") or shown(line)
            ]
    charts = torque_speed_charts(outcome)
    if charts is None:
        return [*out, "chart tab Torque-speed: no chart (the message chart.no-dc-link)"]
    return out + [
        f"chart {c.chart_id}: title {c.title!r}, y {c.y_label} {c.y_unit}, status {c.status.value}, "
        f"{c.assumed_count} assumptions, {', '.join(c.eq_ids)}"
        for c in charts
    ]


def pdf_lines(outcome, folder: Path, stem: str) -> list[str]:
    """Return the lines of the example's PDF report that name balance, torque or efficiency."""
    pdf = folder / f"{stem}.pdf"
    written = write_report_pdf(outcome, pdf)
    if not hasattr(written, "path"):
        return [f"report refused: {written}"]
    text = "\n".join(page.extract_text() for page in pypdf.PdfReader(pdf).pages)
    return [line for line in text.splitlines() if shown(line)] or ["(no line)"]


def main() -> int:
    """Print the guide, then the result cards of each example, then each example's PDF report lines."""
    registry = load_registry()
    print(f"lg_allowlist.toml sha256 {hashlib.sha256(ALLOWLIST.read_bytes()).hexdigest()}")
    print("\n## Equation guide", *guide_lines(registry), sep="\n")
    reports: dict[str, list[str]] = {}
    with tempfile.TemporaryDirectory() as tmp:
        for path in sorted(EXAMPLES.glob("*.embodic.json")):
            stem = path.name.removesuffix(".embodic.json")
            outcome = compute_project(path)
            if isinstance(outcome, tuple):
                print(f"{stem}: refused {outcome}")
                return 1
            print(f"\n## Results table: {stem}", *card_lines(outcome, registry), sep="\n")
            reports[stem] = pdf_lines(outcome, Path(tmp), stem)
    for stem, lines in reports.items():
        print(f"\n## PDF report: {stem}", *lines, sep="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
