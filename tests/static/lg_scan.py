"""One scanner for LG-03 to LG-06 (test_plan.md section 5.8.1).

A `Text` is one string that a user or a file could show. An `AllowRule` admits hits of one class by place, kind and
text, and gives its reason and one status label. The rules are data in `lg_allowlist.toml`. This module does not import
Agent 4's scanner under `tests/independent`: the instruments stay independent (standing order 12).
"""

import ast
import io
import json
import re
import tomllib
import zipfile
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ALLOWLIST = Path(__file__).with_name("lg_allowlist.toml")

# A word starts after a non-letter (space, digit, `_`) or at a lower-to-upper change, so the scan finds MEASURED inside
# INVALID_MEASURED_SOURCE_EMPTY and Unbalanced inside isUnbalanced; `\b` treats `_` as a letter (DEF-US9-01).
START = r"(?:(?<![a-z])|(?-i:(?<=[a-z])(?=[A-Z])))"
END = r"(?-i:(?![a-z]))"
PROGRAM_NAMES = r"(?:kicad|kimotor|magnetless|femm|elmer|matlab|ansys|comsol|motor-?cad|pcbnew)"
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
HOME_PATH = re.compile(r"(?:[A-Za-z]:\\+Users\\+|/home/|/Users/)(?![%$<{])([^\\/\s\"'<>`]+)")
HOME_PLACEHOLDERS = frozenset({"user", "username", "you", "name", "runner", "me", "claude"})
LOWER_NO_SPACE = re.compile(r"^[a-z0-9_.\-/#$\[\]]+$")
REGISTRY_FILES = frozenset({"equations.v1.json", "evidence.v1.json"})
TEXT_SUFFIXES = frozenset({".md", ".txt", ".qss", ".toml", ".svg", ".html", ".csv", ".css", ".dxf"})


class Kind(StrEnum):
    """Where a text came from, which decides whether a lower-case word counts as a name."""

    LITERAL = "literal"
    IDENTIFIER = "identifier"
    JSON_KEY = "json-key"
    JSON_VALUE = "json-value"
    TEXT_LINE = "text-line"
    EXPORT_TEXT = "export-text"


class Corpus(StrEnum):
    """The three corpora of section 5.8.1, and the rendered registry text that stands in for two resource files."""

    SOURCE = "source"
    RESOURCES = "resources"
    EXPORTS = "exports"


@dataclass(frozen=True)
class Text:
    """One string a user or a file could show."""

    corpus: Corpus
    kind: Kind
    place: str
    text: str


@dataclass(frozen=True)
class LgClass:
    """One scan class: a pattern, and whether an identifier literal counts as an admitted name."""

    name: str
    pattern: re.Pattern[str]
    admits_identifiers: bool


MEASUR = LgClass("measur", re.compile(START + r"measur\w*", re.IGNORECASE), admits_identifiers=True)
CLAIM = LgClass(
    "claim",
    re.compile(START + r"(?:balanc\w*|torque\w*|efficien\w*|imbalanc\w*|unbalanc\w*)", re.IGNORECASE),
    admits_identifiers=True,
)
XCOIL = LgClass("xcoil", re.compile(r"xcoil", re.IGNORECASE), admits_identifiers=False)
PROGRAM = LgClass("program", re.compile(START + PROGRAM_NAMES + END, re.IGNORECASE), admits_identifiers=False)


@dataclass(frozen=True)
class AllowRule:
    """One admitted text: regular expressions over place, kind and text, with the reason and one status label."""

    cls: str
    place: re.Pattern[str]
    kind: re.Pattern[str]
    text: re.Pattern[str]
    reason: str
    status: str

    def admits(self, cls: LgClass, item: Text) -> bool:
        """Return True when the rule is of this class and all three expressions match the text."""
        return (
            self.cls == cls.name
            and self.place.search(item.place) is not None
            and self.kind.fullmatch(item.kind.value) is not None
            and self.text.search(item.text) is not None
        )


def load_allowlist(path: Path = ALLOWLIST) -> tuple[AllowRule, ...]:
    """Read the rules of one allow-list file; a rule without a reason or a status label is an error."""
    rows = tomllib.loads(path.read_text(encoding="utf-8")).get("allow", [])
    return tuple(
        AllowRule(
            cls=row["class"],
            place=re.compile(row.get("place", ".")),
            kind=re.compile(row.get("kind", ".*")),
            text=re.compile(row.get("text", ".")),
            reason=row["reason"],
            status=row["status"],
        )
        for row in rows
    )


def find_hits(cls: LgClass, texts: Iterable[Text], rules: Sequence[AllowRule]) -> list[str]:
    """Return one line per text that matches the class pattern and no rule: place, kind and the first 110 characters."""
    hits = []
    for item in texts:
        if cls.pattern.search(item.text) is None:
            continue
        if cls.admits_identifiers and item.kind is Kind.IDENTIFIER:
            continue
        if any(rule.admits(cls, item) for rule in rules):
            continue
        hits.append(f"{item.place} [{item.kind.value}] {' '.join(item.text.split())[:110]}")
    return hits


def _json_texts(corpus: Corpus, place: str, document: object, *, export: bool = False) -> Iterator[Text]:
    def walk(obj: object, pointer: str) -> Iterator[Text]:
        if isinstance(obj, dict):
            for key, value in obj.items():
                yield Text(corpus, Kind.JSON_KEY, f"{place}#{pointer}/{key}", str(key))
                yield from walk(value, f"{pointer}/{key}")
        elif isinstance(obj, list):
            for value in obj:
                yield from walk(value, f"{pointer}/[]")
        elif isinstance(obj, str):
            yield Text(corpus, Kind.JSON_VALUE, f"{place}#{pointer}", obj)

    yield from walk(document, "")


def _lines(corpus: Corpus, kind: Kind, place: str, text: str) -> Iterator[Text]:
    for number, line in enumerate(text.splitlines(), start=1):
        if line.strip():
            yield Text(corpus, kind, f"{place}:{number}", line)


def python_texts(path: Path, place: str, *, catalogue: bool) -> Iterator[Text]:
    """Yield the string constants of one module except docstrings and, in a string catalogue, the mapping keys."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = {
        id(node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)
    }
    skipped = set(docstrings)
    values = set()
    if catalogue:
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                skipped.update(id(key) for key in node.keys if key is not None)
                values.update(id(value) for value in node.values)
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, str)) or id(node) in skipped:
            continue
        if not node.value.strip():
            continue
        is_name = LOWER_NO_SPACE.match(node.value) is not None and id(node) not in values
        kind = Kind.IDENTIFIER if is_name else Kind.LITERAL
        yield Text(Corpus.SOURCE, kind, f"{place}:{node.lineno}", node.value)


def source_texts(package: Path) -> Iterator[Text]:
    """Corpus 1: every string constant of a package folder that is not a docstring or a catalogue key."""
    for path in sorted(package.rglob("*.py")):
        relative = path.relative_to(package.parent)
        catalogue = relative.parts[:3] == (package.name, "ui", "strings")
        yield from python_texts(path, relative.as_posix(), catalogue=catalogue)


def resource_texts(resources: Path) -> Iterator[Text]:
    """Corpus 2: every text file under resources/, JSON by key and by value, the rest by line.

    The two registry files are left to `registry_texts`, which renders what the views show.
    """
    for path in sorted(resources.rglob("*")):
        if not path.is_file() or path.name in REGISTRY_FILES:
            continue
        place = f"{resources.name}/{path.relative_to(resources).as_posix()}"
        if path.suffix == ".json":
            yield from _json_texts(Corpus.RESOURCES, place, json.loads(path.read_text(encoding="utf-8")))
        elif path.suffix in TEXT_SUFFIXES:
            yield from _lines(Corpus.RESOURCES, Kind.TEXT_LINE, place, path.read_text(encoding="utf-8"))


def pdf_text(data: bytes) -> str:
    """Return the page text of a PDF and its document information, one line each."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    info = [str(value) for value in (reader.metadata or {}).values()]
    return "\n".join([*info, *(page.extract_text() for page in reader.pages)])


def member_texts(corpus: Corpus, place: str, name: str, data: bytes) -> Iterator[Text]:
    """Yield the texts of one exported file by its suffix; a ZIP is opened and each member read the same way."""
    suffix = Path(name).suffix
    if suffix == ".zip":
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for member in archive.namelist():
                yield Text(corpus, Kind.EXPORT_TEXT, f"{place}!{member}", member)
                yield from member_texts(corpus, f"{place}!{member}", member, archive.read(member))
    elif suffix == ".pdf":
        yield from _lines(corpus, Kind.EXPORT_TEXT, place, pdf_text(data))
    elif suffix == ".json":
        yield from _json_texts(corpus, place, json.loads(data.decode("utf-8")))
    else:
        yield from _lines(corpus, Kind.EXPORT_TEXT, place, data.decode("utf-8", errors="replace"))


def code_files(repo: Path, folders: Sequence[str]) -> Iterator[tuple[str, str]]:
    """Yield (place, text) for each text file under the given folders of a checkout, skipping binary files."""
    for folder in folders:
        for path in sorted((repo / folder).rglob("*")):
            if path.is_file() and ".venv" not in path.parts and "__pycache__" not in path.parts:
                try:
                    yield path.relative_to(repo).as_posix(), path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue


def guide_texts(registry: object) -> Iterator[Text]:
    """Corpus 2, method (b): the register entry of every equation exactly as the equation guide shows it (UI-17)."""
    from embodic.ui.viewmodels.results import equation_topic

    for eq_id in registry.equations:  # type: ignore[attr-defined]
        topic = equation_topic(eq_id, registry)  # type: ignore[arg-type]
        yield Text(Corpus.RESOURCES, Kind.TEXT_LINE, f"guide:{eq_id}", topic.title)
        for label, value in topic.rows:
            yield from _lines(Corpus.RESOURCES, Kind.TEXT_LINE, f"guide:{eq_id}/{label}", value)


def export_texts(outcome: object, example_id: str, folder: Path) -> Iterator[Text]:
    """Corpus 3 for one example: the bundle with each member, and the outcome JSON of `outcome_to_json`.

    The bundle holds the writers that UT-EXP-01 to UT-EXP-05 call: SVG, the DXF files, PDF, project JSON and README.
    """
    from embodic.api import outcome_to_json
    from embodic.io.bundle import write_bundle
    from embodic.io.exporters import ExportKind, ExportRefused

    kinds = [kind for kind in ExportKind if kind is not ExportKind.README]
    if not any(board.outline.holes for board in outcome.boards.boards):  # type: ignore[attr-defined]
        kinds.remove(ExportKind.DXF_SCREWS)
    bundle = folder / f"{example_id}.zip"
    written = write_bundle(outcome, kinds, bundle, allow_drc_errors=True)  # type: ignore[arg-type]
    if isinstance(written, ExportRefused):
        raise AssertionError(f"{example_id}: bundle refused: {written.reason}")
    yield from member_texts(Corpus.EXPORTS, f"export:{example_id}/bundle", bundle.name, bundle.read_bytes())
    yield from _json_texts(Corpus.EXPORTS, f"export:{example_id}/outcome.json", outcome_to_json(outcome))  # type: ignore[arg-type]


def disclosure_texts(outcome: object, example_id: str, registry: object) -> Iterator[Text]:
    """Corpus 2, method (b): the 'How was this computed' lines of every result row of one example (REQ-T-13)."""
    from embodic.ui.viewmodels.results import disclosure, result_rows

    for row in result_rows(outcome.analysis):  # type: ignore[attr-defined]
        for section in disclosure(row, registry):  # type: ignore[arg-type]
            place = f"disclosure:{example_id}/{row.quantity}/{section.title}"
            for line in section.lines:
                yield Text(Corpus.RESOURCES, Kind.TEXT_LINE, place, line)


PERSONAL = LgClass("personal", EMAIL, admits_identifiers=False)
SYSTEM_ACCOUNTS = frozenset({"root", "admin", "administrator", "system"})
IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".ico", ".icns", ".svg", ".gif", ".bmp", ""})
BRAND_TABLE = Path(__file__).with_name("brand_assets.sha256")
REQUIRE_TOKENS = "EMBODIC_REQUIRE_PERSONAL_TOKENS"
BRAND_NAME_WORDS = re.compile(r"logo|wordmark|embodic-symbol")


def tokens_from(identity: Iterable[str]) -> list[str]:
    """Return the personal-data tokens of an identity: each name or address and the part of an address before the @.

    A placeholder, a system account and a string of fewer than 3 characters never become a token (standing order 7).
    """
    tokens: list[str] = []
    for value in identity:
        for candidate in (value.strip(), value.partition("@")[0].strip() if "@" in value else ""):
            usable = len(candidate) >= 3 and candidate.lower() not in HOME_PLACEHOLDERS | SYSTEM_ACCOUNTS
            if usable and candidate not in tokens:
                tokens.append(candidate)
    return tokens


def environment_tokens(repo: Path = REPO) -> list[str]:
    """Return the tokens of the run environment: the committer of the checkout and the OS account. None is stored."""
    import getpass
    import subprocess

    identity = []
    for key in ("user.name", "user.email"):
        try:
            done = subprocess.run(["git", "config", key], cwd=repo, capture_output=True, text=True, check=False)
        except OSError:
            continue
        identity.append(done.stdout.strip())
    identity.append(getpass.getuser())
    return tokens_from(identity)


def personal_tokens() -> list[str]:
    """Return the tokens of the run environment. With none, fail when the release run requires them, else skip.

    The commit, nightly and release profiles cannot be told apart in a test (tools/ci.py sets the same Hypothesis
    profile for the last two), so the release run sets EMBODIC_REQUIRE_PERSONAL_TOKENS=1 to make the skip a failure.
    """
    import os

    import pytest

    tokens = environment_tokens()
    if not tokens:
        if os.environ.get(REQUIRE_TOKENS) == "1":
            pytest.fail(f"no personal-data token in the environment and {REQUIRE_TOKENS}=1: a skip would hide the gap")
        pytest.skip(f"no committer name, address or OS account to scan for; set {REQUIRE_TOKENS}=1 to fail instead")
    return tokens


def personal_hits(texts: Iterable[Text], tokens: Sequence[str], rules: Sequence[AllowRule]) -> list[str]:
    """Return one line per text that holds an e-mail address, a home path with an account name or a token."""
    words = [re.compile(rf"(?<![A-Za-z0-9]){re.escape(token)}(?![A-Za-z0-9])", re.IGNORECASE) for token in tokens]
    hits = []
    for item in texts:
        found = (
            EMAIL.search(item.text) is not None
            or any(m.group(1).lower() not in HOME_PLACEHOLDERS for m in HOME_PATH.finditer(item.text))
            or any(word.search(item.text) for word in words)
        )
        if found and not any(rule.admits(PERSONAL, item) for rule in rules):
            hits.append(f"{item.place} [{item.kind.value}] {' '.join(item.text.split())[:110]}")
    return hits


def line_texts(repo: Path, folders: Sequence[str]) -> Iterator[Text]:
    """Yield every non-blank line of every text file under the given folders of a checkout."""
    for place, text in code_files(repo, folders):
        yield from _lines(Corpus.SOURCE, Kind.TEXT_LINE, place, text)


def load_brand_table(path: Path = BRAND_TABLE) -> dict[str, str]:
    """Read a `sha256sum` listing into {sha256: file name}; a line that starts with # is a comment."""
    table = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            digest, _, name = line.partition("  ")
            table[digest.strip()] = name.strip()
    return table


def tracked_files(repo: Path = REPO) -> list[Path]:
    """Return the files that git tracks in a checkout."""
    import subprocess

    done = subprocess.run(["git", "ls-files", "-z"], cwd=repo, capture_output=True, check=True)
    return [repo / name for name in done.stdout.decode("utf-8").split("\0") if name]


def brand_check(files: Iterable[Path], table: dict[str, str]) -> tuple[list[tuple[Path, str]], list[Path]]:
    """Split the image files into exact copies of a brand original and brand-named files with an unknown hash."""
    import hashlib

    exact, changed = [], []
    stems = {Path(name).stem.lower() for name in table.values()}
    for path in files:
        if path.suffix.lower() not in IMAGE_SUFFIXES or not path.is_file():
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest in table:
            exact.append((path, table[digest]))
        elif path.stem.lower() in stems or BRAND_NAME_WORDS.search(path.stem.lower()):
            changed.append(path)
    return exact, changed
