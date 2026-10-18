"""LG-01 and LG-08: software text is English (REQ-L-01)."""

import ast
import subprocess
import sys
from pathlib import Path

import pytest
from tests.static import lg_scan
from tests.static.lg_scan import distinct_words

THAI_FIRST, THAI_LAST = 0x0E00, 0x0E7F
ALLOWED_SYMBOLS = frozenset("°µΩ²³·−×±≤≥√")
# Symbols one module may add (D-040): the Greek letters equation_specification.md writes in the quantity symbols that
# results/labels.py shows (delta l.326, Delta T l.373, eta and P_delta,circ l.509). No other module may use them.
# U+00A0 (D-040c) joins a number and its unit in results/formatting.py, so a line never breaks there (REQ-L-07).
MODULE_SYMBOLS = {"embodic.results.labels": frozenset("ηδΔ"), "embodic.results.formatting": frozenset("\u00a0")}


def is_thai(char: str) -> bool:
    """Return True for a character of the Thai Unicode block."""
    return THAI_FIRST <= ord(char) <= THAI_LAST


def is_allowed_in_english_text(char: str, module_name: str = "") -> bool:
    """Return True for printable ASCII, tab, newline, the allowed unit symbols and the module's own symbols."""
    return (
        " " <= char <= "~"
        or char in "\t\n\r"
        or char in ALLOWED_SYMBOLS
        or char in MODULE_SYMBOLS.get(module_name, frozenset())
    )


def check_string_literals(modules) -> list[str]:
    """LG-01: return one message per string literal in src that holds a character outside English text."""
    violations = []
    for module in modules:
        for node in ast.walk(module.tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                bad = sorted({c for c in node.value if not is_allowed_in_english_text(c, module.name)})
                if bad:
                    codes = ", ".join(f"U+{ord(c):04X}" for c in bad)
                    violations.append(f"{module.where(node)}: non-English characters {codes}; software text is English")
    return violations


def check_no_thai(roots: list[Path]) -> list[str]:
    """LG-08: return one message per shipped text file line that contains a Thai character."""
    violations = []
    for root in roots:
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            violations += [
                f"{path}:{number}: Thai characters in a shipped file"
                for number, line in enumerate(text.splitlines(), start=1)
                if any(is_thai(c) for c in line)
            ]
    return violations


@pytest.mark.req("REQ-L-01")
def test_lg01_string_literals_are_english(src_modules):
    """LG-01 on every string literal of the real package, which includes the issue message catalogue."""
    assert check_string_literals(src_modules) == []


@pytest.mark.req("REQ-L-01")
def test_lg01_flags_thai_and_accented_letters_but_not_unit_symbols(planted):
    """Catches a check that passes Thai or accented text, or one that rejects the unit symbols the UI needs."""
    thai = "".join(chr(c) for c in (0x0E2A, 0x0E27, 0x0E31, 0x0E2A, 0x0E14, 0x0E35))
    module = planted(
        "embodic.errors",
        f'GOOD = "Resistance 1.9 Ω at 60 °C, 0.5 mm², ≤ 3 µm, 0.03 N·m/√W"\nTHAI = "{thai}"\nFRENCH = "Résistance"\n',
    )
    violations = check_string_literals([module])
    assert len(violations) == 2
    assert any("U+0E2A" in v for v in violations)
    assert any("U+00E9" in v for v in violations)


@pytest.mark.req("REQ-L-01")
def test_lg01_admits_the_spec_greek_letters_in_the_label_module_only(planted):
    """Catches a Greek allowance that leaked to every module, or one that also admits letters the labels do not use."""
    symbols = "η δ ΔT P_δ,circ"
    labels = planted("embodic.results.labels", f'SYMBOLS = "{symbols}"\nOTHER = "ω"\n')
    elsewhere = planted("embodic.errors", f'SYMBOLS = "{symbols}"\n')
    assert [v.split(": ", 1)[1] for v in check_string_literals([labels])] == [
        "non-English characters U+03C9; software text is English"
    ]
    assert [v.split(": ", 1)[1] for v in check_string_literals([elsewhere])] == [
        "non-English characters U+0394, U+03B4, U+03B7; software text is English"
    ]


@pytest.mark.req("REQ-L-01")
def test_lg01_admits_the_no_break_space_in_the_formatting_module_only(planted):
    """D-040c. Catches an allowance that leaked to every module, or none at all for the unit joiner."""
    source = 'JOIN = "5\u00a0mm"\n'
    formatting = planted("embodic.results.formatting", source)
    elsewhere = planted("embodic.errors", source)
    assert check_string_literals([formatting]) == []
    assert [v.split(": ", 1)[1] for v in check_string_literals([elsewhere])] == [
        "non-English characters U+00A0; software text is English"
    ]


@pytest.mark.req("REQ-L-01")
def test_lg08_shipped_files_have_no_thai(shipped_roots):
    """LG-08 over src/embodic and resources."""
    assert check_no_thai(shipped_roots) == []


@pytest.mark.req("REQ-L-01")
def test_lg08_flags_planted_thai(tmp_path):
    """Catches a scan that skips text files or reads them with the wrong encoding."""
    (tmp_path / "light.json").write_text('{"label": "' + chr(0x0E01) + '"}\n', encoding="utf-8")
    (tmp_path / "ok.svg").write_text("<svg/>\n", encoding="utf-8")
    (violation,) = check_no_thai([tmp_path])
    assert "light.json:1" in violation


WORD_FILES = ("ui/strings/shell.py", "errors/catalogue/base.py", "io/report.py", "io/readme_writer.py")


def word_package(tmp_path: Path, **sources: str) -> Path:
    """Write a package folder with one module per word-list source and return it; `sources` maps a file to its text."""
    package = tmp_path / "embodic"
    for relative in WORD_FILES:
        path = package / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(sources.get(relative, 'EMPTY = "."\n'), encoding="utf-8")
    return package


@pytest.mark.req("REQ-L-01")
@pytest.mark.parametrize("relative", WORD_FILES)
def test_lg01_word_list_holds_a_word_planted_in_every_catalogue_and_template(tmp_path, relative):
    """Catches a list that scans nothing, or that leaves out one catalogue folder or one report template."""
    package = word_package(tmp_path, **{relative: 'TEXTS = {"menu.quuxkey": "Zorgle frobnicate"}\n'})
    assert {"zorgle", "frobnicate"} <= set(distinct_words(package))


@pytest.mark.req("REQ-L-01")
def test_lg01_word_list_leaves_out_docstrings_and_catalogue_keys(tmp_path):
    """Catches a list that reads text no user sees: a docstring, or the key of a catalogue mapping."""
    source = '"""Wibblish docstring."""\nTEXTS = {"menu.quuxkey": "Zorgle"}\n'
    words = distinct_words(word_package(tmp_path, **{"ui/strings/shell.py": source}))
    assert "zorgle" in words
    assert not {"wibblish", "quuxkey"} & set(words)


@pytest.mark.req("REQ-L-01")
def test_lg01_word_list_is_sorted_distinct_lower_case_with_format_fields_dropped_and_camel_case_split(tmp_path):
    """Catches a list that repeats a word, keeps case, spells out `{value:.3g}` or reads isUnbalanced as one word."""
    source = 'TEXT = "Total {value:.3g} is Unbalanced, isUnbalanced and unbalanced twice"\n'
    words = distinct_words(word_package(tmp_path, **{"io/report.py": source}))
    assert words == ["and", "is", "total", "twice", "unbalanced"]


@pytest.mark.req("REQ-L-01")
@pytest.mark.parametrize("missing", ["io/readme_writer.py", "errors/catalogue"])
def test_lg01_word_list_fails_when_a_named_source_is_missing(tmp_path, missing):
    """Catches a rename that leaves the list shorter with no error, which the reviewer would read as complete."""
    package = word_package(tmp_path)
    target = package / missing
    for path in sorted(target.rglob("*"), reverse=True) if target.is_dir() else [target]:
        path.unlink() if path.is_file() else path.rmdir()
    with pytest.raises(FileNotFoundError):
        distinct_words(package)


@pytest.mark.req("REQ-L-01")
def test_lg01_word_list_of_the_real_package_is_sorted_distinct_and_free_of_format_debris():
    """Catches a list of the real package that is empty, unsorted, repeats a word or keeps a field, digit or `_`."""
    words = distinct_words()
    assert words
    assert words == sorted(set(words))
    assert all(word == word.lower() and not any(c.isspace() or c in "{}_0123456789" for c in word) for word in words)


@pytest.mark.req("REQ-L-01")
def test_lg01_word_command_prints_the_list_one_word_per_line():
    """Catches a command that prints nothing, prints the list in another shape or fails for a non-ASCII letter."""
    done = subprocess.run(
        [sys.executable, str(Path(lg_scan.__file__))], capture_output=True, check=False, cwd=lg_scan.REPO
    )
    assert done.returncode == 0, done.stderr.decode("utf-8", errors="replace")
    assert done.stdout.decode("utf-8").splitlines() == distinct_words()
