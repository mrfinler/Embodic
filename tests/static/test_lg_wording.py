"""LG-03, LG-04 and LG-05: wording and name scans of the source and the resources (test_plan.md 5.8.1 to 5.8.4).

Scan 1 reads the string constants of `src/embodic`. Scan 2 reads the text files of `resources/` and the equation guide
as the view renders it. The exports are scan 3, in `tests/unit/embodic_io/exporters/test_lg_exports.py`. Each class has
controls that plant a hit in every kind of text, so a scan that skips one kind cannot pass on it.
"""

import pytest
from tests.static.lg_plants import ARTEFACTS, plant, write, zip_bytes
from tests.static.lg_scan import (
    CLAIM,
    MEASUR,
    PROGRAM,
    REPO,
    XCOIL,
    Corpus,
    Text,
    find_hits,
    guide_texts,
    load_allowlist,
    member_texts,
    resource_texts,
    source_texts,
)

from embodic.results import registry as registry_module

KNOWN_STATUS = {"verified", "inferred", "assumption", "unresolved", "not tested"}
REQ_OF = {"measur": "REQ-T-10", "claim": "REQ-T-11", "xcoil": "REQ-L-03", "program": "REQ-L-03"}
PLANTED_WORD = {"measur": "Measured", "claim": "Balanced", "xcoil": "Xcoil", "program": "KiCad"}
CLASSES = {"measur": MEASUR, "claim": CLAIM, "xcoil": XCOIL, "program": PROGRAM}


CLASS_PARAMS = [pytest.param(name, marks=pytest.mark.req(REQ_OF[name]), id=name) for name in CLASSES]


@pytest.fixture(scope="session")
def rules():
    """Return the allow-list file of the real checkout."""
    return load_allowlist()


@pytest.fixture(scope="session")
def source_corpus() -> list[Text]:
    """Corpus 1: the string constants of src/embodic."""
    return list(source_texts(REPO / "src" / "embodic"))


@pytest.fixture(scope="session")
def resource_corpus() -> list[Text]:
    """Corpus 2: the resource files, with the registry files replaced by the equation guide as the view renders it."""
    return [*resource_texts(REPO / "resources"), *guide_texts(registry_module.load_registry())]


@pytest.mark.req("REQ-T-10", "REQ-T-11", "REQ-L-03", "REQ-L-05")
def test_lg_allowlist_rules_state_a_reason_and_one_status_label(rules):
    """Catches an allow-list entry with no reason beside it, or one with a status word outside standing order 2."""
    assert rules
    for rule in rules:
        assert rule.reason.strip(), rule.text.pattern
        assert rule.status in KNOWN_STATUS, rule.text.pattern
        assert rule.cls in {*CLASSES, "personal"}, rule.text.pattern


@pytest.mark.parametrize("artefact", ARTEFACTS)
@pytest.mark.parametrize("class_name", CLASS_PARAMS)
def test_lg_scan_finds_a_planted_word_in_every_kind_of_text(class_name, artefact, tmp_path):
    """Control for LG-03 to LG-05. Catches a scanner that skips one kind of file or text and so passes on it."""
    texts = plant(artefact, PLANTED_WORD[class_name], tmp_path)
    hits = find_hits(CLASSES[class_name], texts, ())
    assert len(hits) == 1, (artefact, hits)
    assert PLANTED_WORD[class_name].lower() in hits[0].lower()


@pytest.mark.parametrize("class_name", CLASS_PARAMS)
def test_lg_scan_does_not_report_a_docstring_or_a_catalogue_key(class_name, tmp_path):
    """Catches a scan that reads docstrings, which no user sees, or the mapping keys of a catalogue."""
    word = PLANTED_WORD[class_name]
    write(tmp_path / "embodic" / "mod.py", f'"""Module with {word}."""\n\ndef f():\n    """Return {word}."""\n')
    write(tmp_path / "embodic" / "ui" / "strings" / "keys.py", f'STRINGS = {{"hint.{word.lower()}": "Symmetric."}}\n')
    assert find_hits(CLASSES[class_name], source_texts(tmp_path / "embodic"), ()) == []


@pytest.mark.req("REQ-T-10")
def test_lg03_a_measured_column_in_the_catalogue_is_a_hit_and_the_provenance_word_is_not(rules, tmp_path):
    """DEF-UV8-03. Catches a computed clearance called 'Measured (mm)', and an allow-list that admits any 'Measured'."""
    strings = tmp_path / "embodic" / "ui" / "strings"
    write(
        strings / "results.py",
        'STRINGS = {"drc.col": "Measured (mm)", "results.how.reason": "property not measured"}\n',
    )
    hits = find_hits(MEASUR, source_texts(tmp_path / "embodic"), rules)
    assert [h.split("] ", 1)[1] for h in hits] == ["Measured (mm)"]


@pytest.mark.req("REQ-T-10")
def test_lg03_a_planted_measured_key_in_an_outcome_copy_is_a_hit(rules, tmp_path):
    """DEF-UV8-03. Catches an outcome JSON that keeps the DRC key `measured_min_mm` for a computed clearance."""
    document = '{"drc": {"measured_min_mm": 0.2, "least_clearance_mm": 0.2}}'
    data = zip_bytes({"outcome.json": document})
    hits = find_hits(MEASUR, member_texts(Corpus.EXPORTS, "outcome", "bundle.zip", data), rules)
    assert [h.split("] ", 1)[1] for h in hits] == ["measured_min_mm"]


@pytest.mark.req("REQ-T-11")
def test_lg04_a_balanced_claim_in_the_catalogue_is_a_hit(rules, tmp_path):
    """DEF-UV8-04. Catches the claim "Balanced." that D-051b removed, or a one-word catalogue label "efficiency"."""
    strings = tmp_path / "embodic" / "ui" / "strings"
    write(
        strings / "design.py",
        'STRINGS = {"a": "Balanced.", "b": "efficiency", "c": "Symmetric 3-phase pattern."}\nNAME = "efficiency"\n',
    )
    hits = find_hits(CLAIM, source_texts(tmp_path / "embodic"), rules)
    assert [h.split("] ", 1)[1] for h in hits] == ["Balanced.", "efficiency"]
    assert hits[1].startswith("embodic/ui/strings/design.py:1 ")


@pytest.mark.req("REQ-T-11")
def test_lg04_a_new_sentence_about_torque_is_a_hit_and_the_result_name_is_not(rules, tmp_path):
    """Catches an allow-list that matches part of a string: 'Torque' passes, 'Delivers high torque' does not."""
    write(tmp_path / "embodic" / "results" / "labels.py", 'A = "Torque"\nB = "Delivers high torque"\n')
    hits = find_hits(CLAIM, source_texts(tmp_path / "embodic"), rules)
    assert [h.split("] ", 1)[1] for h in hits] == ["Delivers high torque"]


@pytest.mark.req("REQ-L-03")
def test_lg05_the_board_dump_schema_text_is_admitted_only_in_its_own_module(rules, tmp_path):
    """Catches an allow-list that admits the old product name anywhere because one module needs it."""
    text = "{name: 'xcoil-v3' | 'embodic', version, engine_sha256 (Xcoil only, else null), runtime}"
    write(tmp_path / "embodic" / "io" / "board_dump.py", f'SCHEMA = "{text}"\n')
    write(tmp_path / "embodic" / "io" / "other.py", f'SCHEMA = "{text}"\n')
    hits = find_hits(XCOIL, source_texts(tmp_path / "embodic"), rules)
    assert len(hits) == 1
    assert hits[0].startswith("embodic/io/other.py:1 ")


@pytest.mark.req("REQ-L-03")
def test_lg05_a_program_name_is_found_but_not_inside_a_longer_word(tmp_path):
    """Catches a name class with no word end: 'femme' and 'Elmerton' are words, 'FEMM' and 'Motor-CAD' are not."""
    resources = tmp_path / "resources"
    write(resources / "notes.md", "femme\nElmerton\nUse FEMM here\nMotor-CAD and motorcad\npcbnew\n")
    hits = find_hits(PROGRAM, resource_texts(resources), ())
    assert [h.split("] ", 1)[1] for h in hits] == ["Use FEMM here", "Motor-CAD and motorcad", "pcbnew"]


@pytest.mark.req("REQ-T-10", "REQ-T-11")
def test_lg_class_patterns_find_a_word_inside_an_identifier():
    """DEF-US9-01. Catches a plain word-boundary start, which treats the underscore as a letter and misses these."""
    cases = [
        (MEASUR, "INVALID_MEASURED_SOURCE_EMPTY", True),
        (CLAIM, "RANGE_MANUAL_ASSIGNMENT_UNBALANCED", True),
        (CLAIM, "isUnbalanced", True),
        (CLAIM, "rebalancing", False),
        (MEASUR, "unmeasured", False),
    ]
    for cls, text, expected in cases:
        assert (cls.pattern.search(text) is not None) is expected, text


@pytest.mark.req("REQ-T-10")
def test_lg03_source_strings_never_call_a_computed_value_measured(source_corpus, rules):
    """LG-03 on the string constants of src/embodic. Catches 'measured' applied to a computed value in a string."""
    assert find_hits(MEASUR, source_corpus, rules) == []


@pytest.mark.req("REQ-T-10")
def test_lg03_resources_outside_the_fonts_notes_never_call_a_computed_value_measured(resource_corpus, rules):
    """LG-03 on the resources and the guide, less FONTS.md. Catches 'measured' in a resource or a register entry."""
    hits = find_hits(MEASUR, resource_corpus, rules)
    assert [h for h in hits if not h.startswith("resources/fonts/FONTS.md:")] == []


@pytest.mark.req("REQ-T-10")
@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="resources/fonts/FONTS.md l.24-25 say 'measured with sha256sum' and 'verified by measuring' "
    "(v3_contract_rulings.md section 1: 'computed ... by computing'). The owner removes this mark with the edit.",
)
def test_lg03_resources_never_call_a_computed_value_measured(resource_corpus, rules):
    """LG-03 on every resource file. Catches 'measured' for a hash that the tool computed."""
    assert find_hits(MEASUR, resource_corpus, rules) == []


@pytest.mark.req("REQ-T-11")
def test_lg04_source_strings_make_no_balance_torque_or_efficiency_claim(source_corpus, rules):
    """LG-04 on the string constants of src/embodic. Catches a sentence that claims balance, torque or efficiency."""
    assert find_hits(CLAIM, source_corpus, rules) == []


@pytest.mark.req("REQ-T-11")
def test_lg04_resources_make_no_balance_torque_or_efficiency_claim(resource_corpus, rules):
    """LG-04 on the resources and the equation guide. Catches such a sentence in a register entry or a document."""
    assert find_hits(CLAIM, resource_corpus, rules) == []


@pytest.mark.req("REQ-L-03")
def test_lg05_source_strings_carry_no_program_name_beyond_the_board_dump_format(source_corpus, rules):
    """LG-05 on the string constants of src/embodic. Catches 'xcoil' or another program name in a string."""
    assert find_hits(XCOIL, source_corpus, rules) == []
    assert find_hits(PROGRAM, source_corpus, rules) == []


@pytest.mark.req("REQ-L-03")
def test_lg05_resources_carry_no_program_name_beyond_the_unshown_source_notes(resource_corpus, rules):
    """LG-05 on the resources and the equation guide. Catches the old product name in a document or a register entry."""
    assert find_hits(XCOIL, resource_corpus, rules) == []
    assert find_hits(PROGRAM, resource_corpus, rules) == []
