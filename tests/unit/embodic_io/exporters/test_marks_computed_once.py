"""DEF-U-M8o-02: the SVG writer and the PDF report build each board's coil marks once, not once per use.

`coil_marks` runs the eye search of every spiral coil, the slowest step of a drawing (D08: about 300 ms a board). A
drawing needs the marks twice, for the eye fills and for the labels, so each writer builds them once and hands them on.
"""

import sys
from collections import Counter
from collections.abc import Callable
from pathlib import Path

import pytest

from embodic.api import ComputeOutcome
from embodic.geometry import marks
from embodic.geometry.layout import Layout
from embodic.io.exporters import ExportSummary, PhaseRenderMode
from embodic.io.report import write_report_pdf
from embodic.io.svg_writer import write_svg

pytestmark = pytest.mark.req("REQ-F-16", "REQ-N-01")

WRITERS = {
    "svg": lambda outcome, folder: write_svg(
        outcome, folder / "drawing.svg", mode=PhaseRenderMode.GREYSCALE_HATCH, allow_drc_errors=True
    ),
    "pdf report": lambda outcome, folder: write_report_pdf(outcome, folder / "report.pdf"),
}


@pytest.fixture
def mark_builds(monkeypatch: pytest.MonkeyPatch) -> Counter[int]:
    """Count the calls of `coil_marks` per layout, wherever the package imported the function by name."""
    real = marks.coil_marks
    builds: Counter[int] = Counter()

    def counting(layout: Layout):
        builds[id(layout)] += 1
        return real(layout)

    for name, module in list(sys.modules.items()):
        if name.startswith("embodic.") and getattr(module, "coil_marks", None) is real:
            monkeypatch.setattr(module, "coil_marks", counting)
    return builds


@pytest.mark.parametrize("writer", WRITERS)
def test_def_u_m8o_02_each_board_has_its_marks_built_once(
    writer: str,
    example_id: str,
    outcome_of: Callable[[str], ComputeOutcome],
    mark_builds: Counter[int],
    tmp_path: Path,
) -> None:
    """Catches an export that repeats the eye search for a board, which doubles the time of a spiral drawing.

    The count is exactly one per board, so a writer that stops building marks for the eyes would fail as well.
    """
    outcome = outcome_of(example_id)
    summary = WRITERS[writer](outcome, tmp_path)
    assert isinstance(summary, ExportSummary), summary
    assert outcome.boards is not None
    assert mark_builds == Counter({id(board): 1 for board in outcome.boards.boards})
