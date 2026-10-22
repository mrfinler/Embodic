"""V3-14: independent wording, name and brand scans for the cause-C must rows REQ-T-10, REQ-T-11, REQ-L-03, REQ-L-05.

    .venv/bin/python -I tests/independent/m7/v3_14_scan.py [--src src] [--work DIR] [--wheel WHL] [--record MD]
        [--brand-dir DIR] [--brand-sha256 FILE]

The venv holds only the release wheel and its numpy pin, plus pypdf from the dev lock. Corpora: (1) every string
literal of the installed embodic package (bare string statements count as docstrings, which users never see) and
every text resource it ships, JSON walked key by key; (2) the files `embodic-cli export` writes for the five packaged
examples in every format (svg, dxf, dxf-outline, dxf-screws, pdf, readme, bundle with its members) and
`embodic-cli compute --json`; (3) with --src, main's source tree. PDF text comes from pypdf and, apart from it, from
the string operands of every zlib-inflated stream. --work keeps the exports in DIR and reuses them on a rerun.

Controls run first. Each class must find a planted hit in a synthetic file of every artefact kind and in a planted
copy of each real export of the default example, and the allow-list must not admit it (U-V30); the real PDF must
yield its own 'Key results' heading through both extractors; the brand check must find a planted copy and a planted
changed file. A control miss exits 2. A hit outside the allow-list exits 1. Personal-data tokens (git author e-mails,
Windows account names written in the docs) are read at run time and never written: the record prints only their count.

--wheel names the installed wheel in the record with its SHA-256. --record writes another file than records/V3-14.md.
--brand-dir hashes the brand originals of another folder, and --brand-sha256 adds the hashes of a `sha256sum` file for
originals that have no copy there (U-V30: the user's folder is not in the container).
"""

import argparse
import ast
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
import zlib
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RECORD = HERE / "records" / "V3-14.md"
BRAND_DIR = Path("/mnt/user-data/uploads/Desktop/Fantastic Creature/pitchdeck/resources")
EXAMPLES = (
    "serpentine_16p_example",
    "spiral_12c10p_d08",
    "spiral_12c14p",
    "spiral_12c16p_default",
    "wave_16p_example",
)
FORMATS = {
    "svg": "board.svg",
    "dxf": "board.dxf",
    "dxf-outline": "outline.dxf",
    "dxf-screws": "screws.dxf",
    "pdf": "report.pdf",
    "readme": "README.txt",
    "bundle": "bundle.zip",
}
TEXT_SUFFIXES = {".svg", ".md", ".txt", ".css", ".qss", ".toml", ".dxf", ".html", ".csv"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".ico", ".icns", ".svg", ".gif", ".bmp", ""}
BUILD_ACCOUNTS = {"claude"}

# A word starts after a non-letter (space, digit, `_`) or at a lower-to-upper change, so the scan sees words inside
# identifiers such as RANGE_MANUAL_ASSIGNMENT_UNBALANCED and isUnbalanced; `\b` treats `_` as a letter (DEF-US9-01).
START = r"(?:(?<![a-z])|(?-i:(?<=[a-z])(?=[A-Z])))"
END = r"(?-i:(?![a-z]))"
CLASSES = {
    "REQ-T-10": re.compile(START + r"measur\w*", re.IGNORECASE),
    "REQ-T-11": re.compile(START + r"(?:balanc\w*|torque\w*|efficien\w*|imbalanc\w*|unbalanc\w*)", re.IGNORECASE),
    "REQ-L-03": re.compile(r"xcoil", re.IGNORECASE),
    "REQ-L-03 other": re.compile(
        START + r"(?:kicad|kimotor|magnetless|femm|elmer|matlab|ansys|comsol|motor-?cad|pcbnew)" + END, re.IGNORECASE
    ),
}
IDENT_PLANTS = {
    "REQ-T-10": "Measured",
    "REQ-T-11": "Unbalanced",
    "REQ-L-03": "Xcoil",
    "REQ-L-03 other": "Kicad",
}
PLANT = "Planted control: Xcoil measured balanced torque MATLAB planted@example.org C:\\Users\\plantedperson\\x"
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
HOME = re.compile(r"(?:[A-Za-z]:\\+Users\\+|/home/|/Users/)(?![%$<{])([^\\/\s\"'<>`]+)")
HOME_PLACEHOLDERS = {"user", "username", "you", "name", "runner", "me"}
IDENT = re.compile(r"^[a-z0-9_.\-/#$\[\]]+$")
REGISTRY = r"_resources/evidence/(?:equations|evidence)\.v1\.json"


@dataclass(frozen=True)
class Rule:
    """One allow-list entry: class, regexes over where, kind and text, and the reason that admits the hit."""

    cls: str
    where: str
    kind: str
    text: str
    reason: str

    def admits(self, cls: str, t: "Text") -> bool:
        """Return True when every regex of the rule matches the hit."""
        return (
            cls == self.cls
            and re.search(self.where, t.where) is not None
            and re.fullmatch(self.kind, t.kind) is not None
            and re.search(self.text, t.text) is not None
        )


ALLOW = (
    Rule(
        "REQ-T-10",
        r"#/(?:input_provenance_note|assumptions_tag_rule)$|\.qss:",
        r"json-value|resource\.qss",
        r".",
        "the rule or the style of input provenance `measured` (REQ-T-06), not a computed value",
    ),
    Rule(
        "REQ-T-10",
        REGISTRY,
        r"json-value",
        r"(?i)none is a measurement|no measured oracle|measurement temperature|measured O\d|\bD\d{2}\b.*measured",
        "registry text about a paper's measurement, or a statement that no measurement exists (LG-03 allow-list "
        "'reference (paper, measured)')",
    ),
    Rule(
        "REQ-T-10",
        r"equations\.v1\.json#/equations/\[\]/reference_case/",
        r"json-key",
        r"^(?:measured_ohm|D\d{2}_measured_\w+)$",
        "a reference case's paper value (the D08 measured resistance, a D09 measured inductance); reference cases "
        "are not shown (`inferred`)",
    ),
    Rule(
        "REQ-T-10",
        r"equations\.v1\.json#/notes/\[\]$",
        r"json-value",
        r"measures nothing",
        "a registry change note that says embodic measures nothing (U-E15); the guide does not show the notes "
        "(`inferred`, as for the REQ-L-03 rule of these fields)",
    ),
    Rule(
        "REQ-T-10",
        r"passed_tests\.v1\.json",
        r"json-value",
        r"^tests/",
        "a test node id in the evidence file, not shown (see the REQ-L-03 rule for the same file)",
    ),
    Rule(
        "REQ-T-10",
        r"\.py:\d+$",
        r"literal",
        r"^INVALID_MEASURED_(?:SOURCE_EMPTY|DESIGN_FIELD)$",
        "issue codes that refuse a `measured` input provenance (D-007, REQ-T-06); U-S9 ruled them no finding "
        "(docs/phase3/design/v3_14_copy.md section 6)",
    ),
    Rule(
        "REQ-T-11",
        r"passed_tests\.v1\.json",
        r"json-value",
        r"^tests/",
        "a test node id in the evidence file, not shown (see the REQ-L-03 rule for the same file)",
    ),
    Rule(
        "REQ-T-11",
        r"embodic/selftest/catalogue\.py:\d+$",
        r"literal",
        r"^tests/\S+\.py::test_\w+$",
        "the pytest node id of a self-test's `source_test`, which no output shows (`verified`: src reads the field "
        "nowhere, grep)",
    ),
    Rule(
        "REQ-T-11",
        r"_resources/icons/ICONS\.md",
        r"resource\.md",
        r"Torque-speed",
        "icon documentation naming the torque-speed estimate's tab (REQ-F-20, `unresolved` estimate)",
    ),
    Rule(
        "REQ-T-10",
        r".",
        r"literal|resource\.\w+|json-\w+|export\.txt",
        r"(?i)mark(?:ed)? as measured|measured (?:value|entry)|Measured: \{source\}|property not measured|"
        r"input_provenance_note|assumptions_tag_rule|#/\$defs/measured|^measured$|or a measurement before",
        "input provenance `measured` (REQ-T-06: a property value the user marks as measured, with its source), or the "
        "advice to compare with a measurement; neither calls a computed value measured",
    ),
    Rule(
        "REQ-T-10",
        r".",
        r"json-\w+|resource\.json",
        r"(?i)\bD\d{2} measured|vs (?:D\d{2} )?measured|measured peak voltages|LCR measurement|"
        r"(?:mu|eps)_?0 is measured",
        "a physical measurement in a cited paper or a CODATA constant's source (LG-03 allow-list 'reference (paper, "
        "measured)')",
    ),
    Rule(
        "REQ-T-11",
        r".",
        r"literal",
        r"^(?:Torque|Torque-speed|Torque-speed envelope|Torque constant(?:, (?:star|delta)| per line current, rms)?|"
        r"Efficiency, electromagnetic only|TorqueSpeedEstimate)$|^The torque-speed estimate needs a DC-link voltage",
        "the name of a computed result, shown with unit, EQ-ID and status badge (REQ-T-01); the value comes from the "
        "equation chain with its status, not from geometry alone",
    ),
    Rule(
        "REQ-T-11",
        r".",
        r"pdf-text",
        r"^(?:Torque T|Torque constant per line current, rms Kt|Efficiency, electromagnetic only \S+) .* "
        r"(?:not tested|unresolved|inferred|verified|assumption)",
        "a report row of a computed result with its unit and status label",
    ),
    Rule(
        "REQ-T-11",
        r".",
        r"json-key|json-value",
        r"^(?:torque|efficiency|torque_n_m|torque_speed|torque_speed_\w+|torqueSpeed|balanced|balancedSectorList)$",
        "a JSON key or quantity id of a computed Traceable or a golden-data field; the object carries its own status",
    ),
    Rule(
        "REQ-T-11",
        REGISTRY + r"#/(?:equations|entries|notes|documents)",
        r"json-value",
        r".",
        "registry text: an equation's name or formula, a validity rule, or a cited paper's claim or title; not a claim "
        "embodic makes about the user's design",
    ),
    Rule(
        "REQ-L-03",
        r"passed_tests\.v1\.json",
        r"json-value",
        r".",
        "a test node id in the evidence file; the app reads it for the test state and shows neither the file nor its "
        "ids (`inferred` from ui/viewmodels/results.py equation_topic, which shows `tests` of equations.v1.json)",
    ),
    Rule(
        "REQ-L-03",
        r"equations\.v1\.json#/(?:notes|golden_tolerance_default|equations/\[\]/(?:tolerance|source_notes|changes|"
        r"constants/\[\]/basis|reference_case))",
        r"json-value|json-key",
        r".",
        "registry fields that neither the equation guide nor the 'How was this computed' disclosure shows (`inferred` "
        "from ui/viewmodels/results.py l.220-245 and l.699-750)",
    ),
    Rule(
        "REQ-L-03",
        r"evidence\.v1\.json#/(?:topology_vocabulary|entries/\[\]/applies)",
        r"json-value",
        r".",
        "evidence registry fields that the guide does not show; it shows document, location and status (`inferred`)",
    ),
    Rule(
        "REQ-L-03",
        r"_resources/examples/.*#/example/source_note",
        r"json-value",
        r".",
        "the example's `source_note`, 'never shown' (io/examples.py l.39); no export carries it (0 export hits)",
    ),
    Rule(
        "REQ-L-03",
        r"embodic/io/board_dump\.py",
        r"literal",
        r"name: 'xcoil-v3'",
        "board-dump schema text (REQ-F-40 harness format); no CLI format or UI export writes a board dump (`inferred`)",
    ),
    Rule(
        "REQ-L-03 other",
        REGISTRY,
        r"json-value",
        r".",
        "a cited tool or repository in the evidence registry; REQ-L-03 bans only Xcoil",
    ),
)


@dataclass(frozen=True)
class Text:
    """One piece of text a user or a file could show, with its corpus, location and artefact kind."""

    corpus: str
    where: str
    kind: str
    text: str


def literals(path: Path, rel: str, corpus: str):
    """Yield the string literals of one module; bare string statements (docstrings) carry kind 'docstring'."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docs = {
        id(node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.strip():
            kind = "docstring" if id(node) in docs else "literal"
            yield Text(corpus, f"{rel}:{node.lineno}", kind, node.value)


def json_texts(data: bytes, where: str, corpus: str):
    """Every key and every string value of a JSON document, with its path ([] for list items)."""

    def walk(obj, path):
        if isinstance(obj, dict):
            for key, value in obj.items():
                yield Text(corpus, f"{where}#{path}/{key}", "json-key", key)
                yield from walk(value, f"{path}/{key}")
        elif isinstance(obj, list):
            for value in obj:
                yield from walk(value, f"{path}/[]")
        elif isinstance(obj, str):
            yield Text(corpus, f"{where}#{path}", "json-value", obj)

    yield from walk(json.loads(data.decode("utf-8")), "")


def text_lines(data: bytes, where: str, corpus: str, kind: str):
    """Yield one Text per non-blank line."""
    for n, line in enumerate(data.decode("utf-8", errors="replace").splitlines(), 1):
        if line.strip():
            yield Text(corpus, f"{where}:{n}", kind, line)


def stream_strings(data: bytes, where: str, corpus: str):
    """Yield the string operands of every PDF stream, inflated when it is zlib data."""
    for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.DOTALL):
        try:
            raw = zlib.decompress(m.group(1))
        except zlib.error:
            raw = m.group(1)
        strings = re.findall(rb"\(((?:\\.|[^\\)])*)\)", raw)
        if strings:
            yield Text(corpus, f"{where}#stream@{m.start()}", "pdf-stream", b" ".join(strings).decode("latin-1"))


def pdf_texts(data: bytes, where: str, corpus: str):
    """Yield a PDF's page text and information entries (pypdf) and its raw stream strings."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    for n, page in enumerate(reader.pages, 1):
        yield from text_lines((page.extract_text() or "").encode(), f"{where}#page{n}", corpus, "pdf-text")
    for key, value in (reader.metadata or {}).items():
        yield Text(corpus, f"{where}#info{key}", "pdf-info", str(value))
    yield from stream_strings(data, where, corpus)


def blob_texts(data: bytes, name: str, where: str, corpus: str, kind_prefix: str):
    """Yield the texts of one file by its suffix: PDF, ZIP (members recursively), JSON or plain text."""
    suffix = Path(name).suffix.lower()
    if suffix == ".pdf":
        yield from pdf_texts(data, where, corpus)
    elif suffix == ".zip":
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for member in archive.namelist():
                yield from blob_texts(archive.read(member), member, f"{where}!{member}", corpus, kind_prefix)
    elif suffix == ".json":
        yield from json_texts(data, where, corpus)
    elif suffix in TEXT_SUFFIXES or name.startswith("README"):
        yield from text_lines(data, where, corpus, f"{kind_prefix}{suffix or '.txt'}")


def package_corpus(root: Path, corpus: str):
    """Yield the literals of every module and the texts of every other file under root."""
    for path in sorted(root.rglob("*")):
        if "__pycache__" in path.parts or not path.is_file():
            continue
        rel = str(path.relative_to(root.parent))
        if path.suffix == ".py":
            yield from literals(path, rel, corpus)
        else:
            yield from blob_texts(path.read_bytes(), path.name, rel, corpus, "resource")


def tree_corpus(root: Path, corpus: str):
    """Yield the texts of every file under root."""
    for path in sorted(root.rglob("*")):
        if path.is_file():
            yield from blob_texts(path.read_bytes(), path.name, str(path.relative_to(root)), corpus, "export")


def cli(venv_bin: Path, *args: str) -> subprocess.CompletedProcess:
    """Run the venv's embodic-cli."""
    return subprocess.run([str(venv_bin / "embodic-cli"), *args], capture_output=True, text=True, check=False)


def export_all(venv_bin: Path, project: Path, out: Path) -> list[str]:
    """Write every export format of one project into out; return one 'format exit-code' note per call."""
    notes = []
    out.mkdir(parents=True, exist_ok=True)
    for fmt, name in FORMATS.items():
        done = cli(venv_bin, "export", str(project), "--format", fmt, "-o", str(out / name), "--allow-drc-errors")
        notes.append(f"{fmt} {done.returncode}")
    done = cli(venv_bin, "compute", str(project), "--json", str(out / "outcome.json"))
    notes.append(f"compute {done.returncode}")
    (out / "exit_codes.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")
    return notes


def hits(texts, pattern: re.Pattern[str]):
    """Yield (text, match) for every match of pattern."""
    for t in texts:
        for m in pattern.finditer(t.text):
            yield t, m


def admitted(cls: str, t: Text) -> str | None:
    """Return the allow-list reason that admits the hit, or None."""
    if t.kind == "literal" and IDENT.match(t.text):
        return "an identifier or key literal (lower case, no space), not shown as text"
    for rule in ALLOW:
        if rule.admits(cls, t):
            return rule.reason
    return None


def personal_tokens() -> set[str]:
    """Git author e-mails and Windows account names that the docs write out (placeholders excluded)."""
    tokens = set()
    for path in (REPO / "docs").rglob("*.md"):
        for m in re.finditer(r"[A-Za-z]:\\+Users\\+(?![%$<{])([^\\/\s\"'<>`]+)", path.read_text(errors="replace")):
            if m.group(1).lower() not in HOME_PLACEHOLDERS:
                tokens.add(m.group(1))
    log = subprocess.run(["git", "-C", str(REPO), "log", "--format=%ae"], capture_output=True, text=True, check=True)
    tokens |= {e for e in log.stdout.split() if not e.startswith("noreply@")}
    return {t for t in tokens if len(t) >= 3}


def personal_hits(texts, tokens: set[str]):
    """(text, label) for each token, e-mail address or user home path; build-account paths are labelled apart."""
    lowered = {t.lower() for t in tokens}
    for t in texts:
        low = t.text.lower()
        for _ in (tok for tok in lowered if tok in low):
            yield t, "run-time token"
        for m in EMAIL.finditer(t.text):
            if m.group(0).lower() not in lowered:
                yield t, m.group(0)
        for m in HOME.finditer(t.text):
            account = m.group(1).lower()
            if account in BUILD_ACCOUNTS:
                yield t, "build-machine path"
            elif account not in HOME_PLACEHOLDERS:
                yield t, m.group(0)


def brand_check(files, brand: dict[str, str]):
    """Exact copies of a brand original (by SHA-256) and brand-named image files whose hash matches none."""
    exact, changed = [], []
    names = {Path(n).stem.lower() for n in brand.values()}
    for path in files:
        if path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest in brand:
            exact.append((path, brand[digest]))
        elif path.stem.lower() in names or re.search(r"logo|wordmark|embodic-symbol", path.stem.lower()):
            changed.append(path)
    return exact, changed


def planted_copies(tmp: Path, real: Path) -> list[tuple[str, list[Text]]]:
    """One synthetic file per artefact kind and one planted copy of each real export of the default example."""
    tmp.mkdir(parents=True)
    kinds = []
    (tmp / "plant.py").write_text(f"MESSAGE = {PLANT!r}\n", encoding="utf-8")
    kinds.append(("synthetic .py literal", list(literals(tmp / "plant.py", "plant.py", "control"))))
    for name, body in (
        ("plant.svg", f"<svg><text>{PLANT}</text></svg>\n"),
        ("plant.dxf", f"999\n{PLANT}\n0\nEOF\n"),
        ("plant.json", json.dumps({"note": PLANT, PLANT: 1})),
        ("README.txt", f"x\n{PLANT}\n"),
    ):
        kinds.append((f"synthetic {name}", list(blob_texts(body.encode(), name, name, "control", "export"))))
    content = zlib.compress(f"BT /F1 9 Tf ({PLANT}) Tj ET".encode("latin-1"))
    head = f"%PDF-1.4\n1 0 obj<</Length {len(content)}/Filter/FlateDecode>>stream\n".encode()
    kinds.append(("synthetic .pdf stream", list(stream_strings(head + content + b"\nendstream\n", "plant.pdf", "c"))))
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("inner/README.txt", f"x\n{PLANT}\n")
    kinds.append(("synthetic zip member", list(blob_texts(buffer.getvalue(), "p.zip", "p.zip", "control", "export"))))
    for name in ("board.svg", "board.dxf", "outline.dxf", "screws.dxf", "README.txt"):
        source = real / name if (real / name).exists() else sorted(real.parent.glob(f"*/{name}"))[0]
        data = source.read_text(encoding="utf-8")
        if name.endswith(".svg"):
            data = data.replace("</svg>", f"<text>{PLANT}</text></svg>")
        elif name.endswith(".dxf"):
            data = f"999\n{PLANT}\n" + data
        else:
            data += f"\n{PLANT}\n"
        kinds.append((f"planted copy of real {name}", list(blob_texts(data.encode(), name, name, "control", "export"))))
    for name in ("outcome.json",):
        doc = json.loads((real / name).read_text(encoding="utf-8"))
        doc["planted"] = PLANT
        kinds.append((f"planted copy of real {name}", list(json_texts(json.dumps(doc).encode(), name, "control"))))
    with zipfile.ZipFile(real / "bundle.zip") as source:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            for member in source.namelist():
                data = source.read(member)
                if member.endswith(".embodic.json"):
                    doc = json.loads(data)
                    doc["design"]["name"] = PLANT
                    data = json.dumps(doc).encode()
                archive.writestr(member, data)
    texts = list(blob_texts(buffer.getvalue(), "b.zip", "b.zip", "control", "export"))
    kinds.append(("planted copy of real bundle.zip (.embodic.json name)", texts))
    return kinds


def run_controls(
    tmp: Path, exports: Path, tokens: set[str], brand: dict[str, str], originals: Path
) -> tuple[list, bool]:
    """Return the control rows (class, planted artefact, hits on the plant) and whether a required one missed."""
    rows, failed = [], False
    controls = planted_copies(tmp / "control", exports / "spiral_12c16p_default")
    for cls, pattern in CLASSES.items():
        for kind, texts in controls:
            n = sum(1 for t, _ in hits(texts, pattern) if "Planted control" in t.text and not admitted(cls, t))
            rows.append((cls, kind, n))
            failed |= n == 0
    for kind, texts in controls:
        n = sum(1 for t, _ in personal_hits(texts, tokens | {"planted@example.org"}) if "Planted" in t.text)
        rows.append(("REQ-L-05 personal", kind, n))
        failed |= n == 0
    outcome = json.loads((exports / "spiral_12c16p_default" / "outcome.json").read_text(encoding="utf-8"))
    for cls, word in IDENT_PLANTS.items():
        for form, code in (("after `_`", f"PLANTED_{word.upper()}_CODE"), ("camelCase", f"planted{word}Code")):
            doc = {**outcome, "issues": [*outcome["issues"], {"code": code}]}
            texts = list(json_texts(json.dumps(doc).encode(), "outcome.json", "control"))
            n = sum(1 for t, _ in hits(texts, CLASSES[cls]) if t.text == code and not admitted(cls, t))
            rows.append((cls, f"identifier word {form}: issue code {code} in a copy of the real outcome.json", n))
            failed |= n == 0
    pdf = list(pdf_texts((exports / "spiral_12c16p_default" / "report.pdf").read_bytes(), "report.pdf", "control"))
    n = sum("Key results" in t.text for t in pdf if t.kind == "pdf-text")
    rows.append(("PDF extractor", "'Key results' in the real report.pdf via pypdf", n))
    failed |= n == 0
    n = sum("Key results" in t.text for t in pdf if t.kind == "pdf-stream")
    rows.append(("PDF extractor", "same via raw streams (embedded TrueType glyph ids: 0 expected)", n))
    if tokens:
        planted = [Text("control", "token.txt:1", "export.txt", f"x {sorted(tokens)[0]} x")]
        n = sum(1 for _ in personal_hits(planted, tokens))
        rows.append(("REQ-L-05 personal", "a run-time token planted in a text line", n))
        failed |= n == 0
    brand_dir = tmp / "brand_control"
    brand_dir.mkdir()
    first = sorted(p for p in originals.iterdir() if p.is_file())[0]
    shutil.copy(first, brand_dir / first.name)
    (brand_dir / "embodic_logo.png").write_bytes(b"x" + (originals / "embodic_logo.png").read_bytes())
    exact, changed = brand_check(sorted(brand_dir.iterdir()), brand)
    rows += [("REQ-L-05 brand", "planted exact copy", len(exact))]
    rows += [("REQ-L-05 brand", "planted changed brand-named file", len(changed))]
    failed |= len(exact) != 1 or len(changed) != 1
    return rows, failed


def classify(corpora: dict[str, list[Text]], tokens: set[str]):
    """Split every hit into findings, allow-listed counts, docstring counts and build-machine paths."""
    findings, allowed_counts, docstrings, observations = [], {}, {}, {}
    for cls, pattern in CLASSES.items():
        for corpus, texts in corpora.items():
            for t, m in hits(texts, pattern):
                if t.kind == "docstring":
                    docstrings[(cls, corpus)] = docstrings.get((cls, corpus), 0) + 1
                elif reason := admitted(cls, t):
                    allowed_counts[(cls, corpus, reason)] = allowed_counts.get((cls, corpus, reason), 0) + 1
                else:
                    findings.append((cls, t, m.group(0)))
    for corpus, texts in corpora.items():
        for t, label in personal_hits(texts, tokens):
            if t.kind == "docstring":
                continue
            if label == "build-machine path":
                observations[(corpus, t.where)] = t.text
            else:
                findings.append(("REQ-L-05 personal", t, label))
    return findings, allowed_counts, docstrings, observations


def render(header: list[str], control_rows, corpora, notes, brand_line: str, classified) -> tuple[str, dict]:
    """Return the record text and the finding count per class."""
    findings, allowed_counts, docstrings, observations = classified
    lines = [
        *header,
        "## Controls (a miss fails the run with exit 2)",
        "",
        "| Class | Planted artefact | Hits on the plant |",
        "|---|---|---|",
        *[f"| {c} | {k} | {n} |" for c, k, n in control_rows],
        "",
        "## Corpus",
        "",
        *[f"- {name}: {len(texts)} text items" for name, texts in corpora.items()],
        "- exit codes per example: " + "; ".join(f"{s}: {', '.join(n)}" for s, n in notes.items()),
        "",
        "## Brand assets (REQ-L-05)",
        "",
        brand_line,
        "",
        "## Allow-listed hits",
        "",
        "| Class | Corpus | Hits | Reason |",
        "|---|---|---|---|",
        *[f"| {c} | {k} | {n} | {r} |" for (c, k, r), n in sorted(allowed_counts.items())],
        "",
        "Docstring hits (not shown to users, not findings): "
        + (", ".join(f"{c} in {k}: {n}" for (c, k), n in sorted(docstrings.items())) or "none")
        + ".",
        "",
        "Build-machine paths (the container account, not a person; listed, not counted as findings): "
        + (", ".join(f"`{w}`" for (_, w) in sorted(observations)) or "none")
        + ".",
        "",
        "## Findings outside the allow-list",
        "",
        "| Class | Corpus | Where | Kind | Match | Text |",
        "|---|---|---|---|---|---|",
    ]
    for cls, t, word in findings:
        text = "(not printed)" if cls == "REQ-L-05 personal" else " ".join(t.text.split()).replace("|", "\\|")[:150]
        lines.append(f"| {cls} | {t.corpus} | `{t.where}` | {t.kind} | {word} | {text} |")
    by_class: dict[str, int] = {}
    for cls, *_ in findings:
        by_class[cls] = by_class.get(cls, 0) + 1
    summary = ", ".join(f"{k} {v}" for k, v in sorted(by_class.items())) or "none"
    lines += ["", f"Findings: {len(findings)} ({summary})."]
    return "\n".join(lines) + "\n", by_class


def export_examples(venv_bin: Path, examples: Path, exports: Path) -> dict[str, list[str]]:
    """Export the five examples into exports, reusing a folder whose exit_codes.txt exists."""
    notes = {}
    for stem in EXAMPLES:
        done = exports / stem / "exit_codes.txt"
        if done.exists():
            notes[stem] = done.read_text(encoding="utf-8").split("\n")[:-1]
        else:
            notes[stem] = export_all(venv_bin, examples / f"{stem}.embodic.json", exports / stem)
    return notes


def main(argv=None) -> int:
    """Run the controls, then the scans; write records/V3-14.md and return 2, 1 or 0."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--src", type=Path, help="also scan this source tree (main's src) for string literals")
    parser.add_argument("--work", type=Path, help="keep exports here and reuse them on a rerun")
    parser.add_argument("--wheel", type=Path, help="the wheel installed in this venv, named in the record")
    parser.add_argument("--record", type=Path, default=RECORD, help="the record to write")
    parser.add_argument("--brand-dir", type=Path, default=BRAND_DIR, help="folder of brand originals to hash")
    parser.add_argument("--brand-sha256", type=Path, help="sha256sum lines of originals without a copy in the folder")
    args = parser.parse_args(argv)

    from importlib.metadata import version

    import embodic

    package = Path(embodic.__file__).parent
    venv_bin = Path(sys.executable).parent
    tokens = personal_tokens()
    brand = {hashlib.sha256(p.read_bytes()).hexdigest(): p.name for p in args.brand_dir.iterdir() if p.is_file()}
    hashed_dir = len(brand)
    if args.brand_sha256:
        for line in args.brand_sha256.read_text(encoding="utf-8").splitlines():
            if m := re.fullmatch(r"([0-9a-f]{64})  (\S+)", line):
                brand.setdefault(m.group(1), m.group(2))

    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        exports = (args.work.resolve() if args.work else tmp / "work") / "exports"
        notes = export_examples(venv_bin, package / "_resources" / "examples", exports)
        control_rows, failed = run_controls(tmp, exports, tokens, brand, args.brand_dir)
        corpora = {
            "installed package": list(package_corpus(package, "installed package")),
            "exports": list(tree_corpus(exports, "exports")),
        }
        if args.src:
            corpora["main src"] = list(package_corpus(args.src.resolve() / "embodic", "main src"))
        files = [p for p in package.rglob("*") if p.is_file()] + [p for p in exports.rglob("*") if p.is_file()]
        real_exact, real_changed = brand_check(files, brand)
        export_files = sum(1 for p in exports.rglob("*") if p.is_file() and p.name != "exit_codes.txt")

    if args.wheel:
        digest = hashlib.sha256(args.wheel.read_bytes()).hexdigest()
        built = f"the wheel `{args.wheel}` (SHA-256 `{digest[:8]}…{digest[-4:]}`)"
    else:
        built = "no named wheel"
    command = " ".join(["tests/independent/m7/v3_14_scan.py", *(argv if argv is not None else sys.argv[1:])])
    header = [
        "Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5",
        "",
        "# V3-14: wording, name and brand scans (generated)",
        "",
        f"Generated by `.venv/bin/python -I {command}`."
        + f" The venv holds embodic {version('embodic')} from {built}, numpy {version('numpy')} and pypdf "
        f"{version('pypdf')} from the lock files. Do not edit by hand.",
        f"Personal-data tokens read at run time: {len(tokens)} (not printed). Export files scanned: {export_files}. "
        "Every count is `verified` by running this script; the classification of each hit is my reading, and an "
        "`inferred` reason says so.",
        "",
    ]
    extra = f", and {len(brand) - hashed_dir} more from `{args.brand_sha256}`" if args.brand_sha256 else ""
    brand_line = (
        f"{hashed_dir} brand originals hashed in `{args.brand_dir}`{extra}. Exact copies in the package or the "
        f"exports: {len(real_exact)}. Brand-named image files with another hash: {len(real_changed)}"
        + (": " + ", ".join(p.name for p in real_changed) if real_changed else "")
        + "."
    )
    classified = classify(corpora, tokens)
    text, by_class = render(header, control_rows, corpora, notes, brand_line, classified)
    record = args.record.resolve()
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(text, encoding="utf-8")
    found = sum(1 for *_, n in control_rows if n)
    print(f"controls {'FAILED' if failed else 'passed'}: {found} of {len(control_rows)} rows found their plant")
    print(f"findings {sum(by_class.values())} {by_class}; allow-listed {sum(classified[1].values())}")
    print(f"wrote {record}")
    return 2 if failed else (1 if by_class else 0)


if __name__ == "__main__":
    sys.exit(main())
