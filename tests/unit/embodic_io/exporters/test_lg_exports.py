"""LG-03 to LG-06 over the exports (scan 3 of test_plan.md 5.8.1), and the disclosure of every result row.

Corpus 3 is the bundle of each packaged example with each of its members (SVG, the DXF files, the PDF report read with
pypdf, the project JSON and README.txt) and the outcome JSON of `outcome_to_json`. The disclosure lines are the
registry text that the view shows for a result row (method (b) of 5.8.1). The scanner and its controls are in
`tests/static/lg_scan.py` and `tests/static/test_lg_wording.py`.
"""

from collections.abc import Callable
from pathlib import Path

import pytest
from tests.static.lg_scan import (
    CLAIM,
    MEASUR,
    PROGRAM,
    REPO,
    XCOIL,
    Corpus,
    Text,
    disclosure_texts,
    export_texts,
    find_hits,
    guide_texts,
    load_allowlist,
    personal_hits,
    personal_tokens,
    resource_texts,
    source_texts,
)

from embodic.api import ComputeOutcome
from embodic.results import registry as registry_module

from .conftest import EXAMPLE_IDS

KINDS_OF_FILE = (".svg", "_outline.dxf", "_report.pdf", ".embodic.json", "README.txt", "outcome.json")
_TEXTS: dict[str, list[Text]] = {}


def texts_of(example_id: str, outcome: ComputeOutcome, folder: Path) -> list[Text]:
    """Return the export texts and the disclosure lines of one example, written once per session."""
    if example_id not in _TEXTS:
        registry = registry_module.load_registry()
        _TEXTS[example_id] = [
            *export_texts(outcome, example_id, folder),
            *disclosure_texts(outcome, example_id, registry),
        ]
    return _TEXTS[example_id]


@pytest.fixture(scope="module")
def export_folder(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """One folder for every bundle of the module."""
    return tmp_path_factory.mktemp("lg_exports")


@pytest.fixture
def texts(example_id: str, outcome_of: Callable[[str], ComputeOutcome], export_folder: Path) -> list[Text]:
    """Corpus 3 and the disclosure of one packaged example."""
    return texts_of(example_id, outcome_of(example_id), export_folder)


@pytest.fixture(scope="module")
def rules():
    """Return the allow-list file of the real checkout."""
    return load_allowlist()


@pytest.mark.req("REQ-T-10", "REQ-T-11", "REQ-L-03", "REQ-L-05")
def test_lg_scan_reads_every_kind_of_file_of_a_real_export(texts, example_id):
    """Control. Catches a scanner that reads the bundle but no member of one kind and so passes on an empty corpus."""
    for suffix in KINDS_OF_FILE:
        assert any(suffix in t.place for t in texts if t.corpus is Corpus.EXPORTS), (example_id, suffix)
    pdf_lines = [t.text for t in texts if t.place.split("!")[-1].startswith(example_id) and "_report.pdf" in t.place]
    assert any(line.startswith("Torque T ") for line in pdf_lines), "pypdf read no result row of the report"
    assert any(t.place.endswith("/Sources") or "/Equation" in t.place for t in texts), "no disclosure line"


@pytest.mark.req("REQ-T-10")
def test_lg03_exports_and_disclosure_never_call_a_computed_value_measured(texts, rules):
    """LG-03 over the exports. Catches 'measured' applied to a computed value in an export or a disclosure line."""
    assert find_hits(MEASUR, texts, rules) == []


@pytest.mark.req("REQ-T-11")
def test_lg04_exports_and_disclosure_make_no_balance_torque_or_efficiency_claim(texts, rules):
    """LG-04 over the exports. Catches a balance, torque or efficiency claim in an export or a disclosure."""
    assert find_hits(CLAIM, texts, rules) == []


@pytest.mark.req("REQ-L-03")
def test_lg05_exports_and_disclosure_carry_no_program_name(texts, rules):
    """LG-05 over the exports. Catches the old product name or another program name in an export or a disclosure."""
    assert find_hits(XCOIL, texts, rules) == []
    assert find_hits(PROGRAM, texts, rules) == []


@pytest.mark.req("REQ-L-05")
def test_lg06_exports_carry_no_e_mail_address_home_path_or_personal_name(texts, rules):
    """LG-06 over the exports. Catches a user name or address written into a drawing, a report, the README or a JSON."""
    assert personal_hits(texts, personal_tokens(), rules) == []


@pytest.mark.req("REQ-T-10", "REQ-T-11", "REQ-L-03")
def test_lg_every_allow_list_rule_admits_a_text_of_the_real_corpora(outcome_of, export_folder, rules):
    """Catches a stale allow-list entry: a rule that no text needs any more still admits a future hit by its pattern."""
    registry = registry_module.load_registry()
    corpus = [
        *source_texts(REPO / "src" / "embodic"),
        *resource_texts(REPO / "resources"),
        *guide_texts(registry),
        *(t for example_id in EXAMPLE_IDS for t in texts_of(example_id, outcome_of(example_id), export_folder)),
    ]
    classes = {"measur": MEASUR, "claim": CLAIM, "xcoil": XCOIL, "program": PROGRAM}
    stale = [
        f"{rule.cls}: {rule.text.pattern[:70]}"
        for rule in rules
        if rule.cls in classes
        and not any(rule.admits(classes[rule.cls], t) and classes[rule.cls].pattern.search(t.text) for t in corpus)
    ]
    assert stale == []
