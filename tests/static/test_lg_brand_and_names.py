"""LG-06 (REQ-L-05): brand asset checksums and a personal-data scan of 0 hits (test_plan.md 5.8.5, D-053d).

Brand assets. `brand_assets.sha256` lists hashes only. Every tracked image either has a recorded hash or does not look
like a brand asset. Personal data. The tokens come from the run environment and are never written to the repository
(standing order 7). The exports half of the scan is in `tests/unit/embodic_io/exporters/test_lg_exports.py`.
"""

import hashlib
import re

import pytest
from tests.static.lg_plants import ARTEFACTS, plant
from tests.static.lg_scan import (
    BRAND_TABLE,
    PERSONAL,
    REPO,
    Kind,
    Text,
    brand_check,
    line_texts,
    load_allowlist,
    load_brand_table,
    personal_hits,
    personal_tokens,
    tokens_from,
    tracked_files,
)

CODE_FOLDERS = ["src", "tools", "tests", "packaging", "resources"]
PLANTED_ADDRESS = "planted_person" + "@" + "example.org"
PLANTED_HOME = "C:" + "\\Users\\" + "plantedperson" + "\\x"
PLANTED_TOKEN = "Zorbaxia Quuxington"
BRAND_BYTES = b"brand original, version 1"
# A key, an identifier or a member name cannot hold an address, a path or a name with a space.
NAME_ARTEFACTS = {"json-key", "identifier-after-underscore", "identifier-camel-case", "zip-member-name"}


@pytest.fixture(scope="module")
def rules():
    """Return the allow-list file of the real checkout."""
    return load_allowlist()


@pytest.fixture(scope="module")
def table() -> dict[str, str]:
    """Return the recorded brand hashes."""
    return load_brand_table()


@pytest.mark.req("REQ-L-05")
def test_lg06_brand_table_lists_a_sha256_and_a_name_per_original(table):
    """Catches a table with a malformed digest, a repeated hash or a repeated file name, which a check would misread."""
    assert table
    assert all(re.fullmatch(r"[0-9a-f]{64}", digest) for digest in table)
    assert len(set(table.values())) == len(table)
    assert BRAND_TABLE.read_text(encoding="utf-8").count("\n") >= len(table)


@pytest.mark.req("REQ-L-05")
def test_lg06_every_tracked_brand_named_image_has_a_recorded_hash(table):
    """LG-06, brand half. Catches an edited logo, wordmark or symbol, or a brand-named file that is not the original."""
    exact, changed = brand_check(tracked_files(), table)
    assert changed == []
    copies = {path.name for path, _ in exact}
    assert {"embodic_logo.png", "embodic-symbol-white.png", "embodic-wordmark-white.png"} <= copies, copies


@pytest.mark.req("REQ-L-05")
def test_lg06_brand_check_passes_an_exact_copy_and_fails_a_modified_copy(tmp_path):
    """Control. Catches a check that cannot fail: the exact copy passes, a modified file of the same name does not."""
    table = {hashlib.sha256(BRAND_BYTES).hexdigest(): "embodic_logo.png"}
    exact = tmp_path / "copy" / "banner.png"
    exact.parent.mkdir()
    exact.write_bytes(BRAND_BYTES)
    modified = tmp_path / "modified" / "embodic_logo.png"
    modified.parent.mkdir()
    modified.write_bytes(BRAND_BYTES + b"\x00")
    renamed = tmp_path / "renamed" / "my-wordmark.svg"
    renamed.parent.mkdir()
    renamed.write_bytes(b"<svg/>")
    unrelated = tmp_path / "unrelated" / "board.png"
    unrelated.parent.mkdir()
    unrelated.write_bytes(b"not a brand file")
    found, changed = brand_check([exact, modified, renamed, unrelated], table)
    assert [(path.name, name) for path, name in found] == [("banner.png", "embodic_logo.png")]
    assert sorted(path.name for path in changed) == ["embodic_logo.png", "my-wordmark.svg"]


@pytest.mark.req("REQ-L-05")
def test_lg06_tokens_come_from_names_and_addresses_without_placeholders_or_short_strings():
    """Catches a token set that holds a placeholder, a system account or a 2-character string, which hit everywhere."""
    identity = ["Ada Lovelace", "ada" + "@" + "example.org", "root", "me", "ab", "Runner", "Ada Lovelace"]
    assert tokens_from(identity) == ["Ada Lovelace", "ada" + "@" + "example.org", "ada"]


@pytest.mark.req("REQ-L-05")
def test_lg06_personal_scan_flags_an_address_a_home_path_and_a_token_but_not_a_placeholder():
    """Control. Catches a pattern that misses an account name in a path, or flags %USERPROFILE% or the build account."""
    texts = [
        Text(corpus=None, kind=Kind.TEXT_LINE, place=f"p:{n}", text=t)  # type: ignore[arg-type]
        for n, t in enumerate(
            [
                f"contact {PLANTED_ADDRESS}",
                f"path {PLANTED_HOME}",
                f"written by {PLANTED_TOKEN.lower()} today",
                "by Zorbaxia Quuxington3",
                "path %USERPROFILE%\\x",
                "path C:\\Users\\<user>\\x and /home/you/x and /Users/username/x",
                "path /home/claude/embodic-ref/x and /home/runner/x",
            ]
        )
    ]
    hits = personal_hits(texts, [PLANTED_TOKEN], ())
    assert [h.split(" ", 1)[0] for h in hits] == ["p:0", "p:1", "p:2"]


VALUE_ARTEFACTS = tuple(a for a in ARTEFACTS if a not in NAME_ARTEFACTS)


@pytest.mark.req("REQ-L-05")
@pytest.mark.parametrize("artefact", VALUE_ARTEFACTS)
@pytest.mark.parametrize("what", ["address", "home path", "token"])
def test_lg06_personal_scan_finds_a_planted_value_in_every_kind_of_text(what, artefact, tmp_path):
    """Control. Catches a scan that skips one kind of file or text, so a user name written there passes."""
    planted = {"address": PLANTED_ADDRESS, "home path": PLANTED_HOME, "token": PLANTED_TOKEN}[what]
    texts = plant(artefact, planted, tmp_path)
    assert len(personal_hits(texts, [PLANTED_TOKEN], ())) == 1, (artefact, what)


@pytest.mark.req("REQ-L-05")
def test_lg06_code_and_resources_carry_no_e_mail_address_home_path_or_personal_name(rules):
    """LG-06, personal half. Catches a user name or address in src, tools, tests, packaging or resources."""
    tokens = personal_tokens()
    texts = list(line_texts(REPO, CODE_FOLDERS))
    assert texts
    assert personal_hits(texts, tokens, rules) == []


@pytest.mark.req("REQ-L-05")
def test_lg06_the_scan_of_the_checkout_finds_a_name_that_it_is_given():
    """Control on the real corpus. Catches a code scan that reads no file: the project name must hit."""
    texts = list(line_texts(REPO, CODE_FOLDERS))
    assert personal_hits(texts, ["embodic"], [])


@pytest.mark.req("REQ-L-05")
def test_lg06_every_personal_rule_admits_a_line_of_the_checkout(rules):
    """Catches a stale personal-data rule: one that no line needs any more still admits a future hit."""
    texts = list(line_texts(REPO, CODE_FOLDERS))
    stale = [
        rule.text.pattern
        for rule in rules
        if rule.cls == "personal" and not any(rule.admits(PERSONAL, t) for t in texts)
    ]
    assert stale == []
