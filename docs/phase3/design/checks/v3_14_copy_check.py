r"""U-S9 lever: prove the V3-14 copy table against the tree it targets.

    python3 -I docs/phase3/design/checks/v3_14_copy_check.py [--root .]

For every fix in FIXES it prints where the current text sits (file:line, found by search, so the lines track the
tree), whether the replacement still matches one of Agent 4's V3-14 word classes, whether both strings appear verbatim
in v3_14_copy.md, and which tests and docs pin the rendered text. It then scans the registry fields the equation guide
shows on this tree, lists issue codes whose words the scan's \b-anchored patterns cannot see, applies every fix to a
copy of the touched files and re-runs the scan's own classifier on them, and measures the PDF header against its cell.
Exit 1 when a current text is missing, a replacement hits a class, the doc disagrees, or a patched file still has a
finding.
"""

import argparse
import ast
import importlib.util
import json
import py_compile
import re
import string
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

DOC = Path("docs/phase3/design/v3_14_copy.md")
SCAN = Path("tests/independent/m7/v3_14_scan.py")
REGISTRY = Path("resources/evidence/equations.v1.json")
PIN_ROOTS = (Path("tests"), Path(".claude/skills"), Path("docs/phase2/design"))
PIN_SKIP = re.compile(r"^tests/independent/m7/records/|^tests/independent/README\.md$")
GUIDE_FIELDS = {  # what ui/viewmodels/results.py equation_topic shows of each registry entry; None = the whole value
    "name": None,
    "formula": None,
    "label": None,
    "dominant_assumptions": ("text",),
    "validity_checks": ("id", "name", "rule"),
    "tests": None,
    "constants": ("name", "source"),
    "implementation": None,
}


@dataclass(frozen=True, slots=True)
class Fix:
    """One copy fix: the exact current text, where it sits, its replacement and the rendered text tests may pin."""

    id: str
    req: str
    paths: tuple[str, ...]
    old: str
    new: str
    pins: tuple[str, ...]
    code: bool = False  # a call-site edit: identifiers in it are not text, and the scan reads only literals


ENGINEERING_REGISTRY = (
    "docs/phase2/engineering/checks/build_registry.py",
    "docs/phase2/engineering/equation_registry.json",
)
REGISTRY_COPIES = (*ENGINEERING_REGISTRY, str(REGISTRY))

FIXES = (
    Fix(
        "T10-1",
        "REQ-T-10",
        ("src/embodic/ui/strings/export.py",),
        "{message} {layer}: {measured} measured, {required} required.",
        "{message} {layer}: {clearance} clearance, {required} required.",
        ("mm measured", "measured, {required}"),
    ),
    Fix(
        "T10-1a",
        "REQ-T-10",
        ("src/embodic/ui/views/dialogs.py",),
        "measured=drc_length_text(v.measured_mm),",
        "clearance=drc_length_text(v.measured_mm),",
        (),
        code=True,
    ),
    Fix(
        "T10-2",
        "REQ-T-10",
        ("src/embodic/ui/strings/results.py",),
        r'"Measured\n(mm)"',
        r'"Clearance\n(mm)"',
        ("Measured (mm)", r"Measured\n(mm)", "Measured and Required"),
    ),
    Fix(
        "T10-3",
        "REQ-T-10",
        ("src/embodic/ui/strings/results.py",),
        "Error. {code}. {message} Measured {measured}, required {required}, layer {layer}.",
        "Error. {code}. {message} Clearance {clearance}, required {required}, layer {layer}.",
        ("Measured 0.", "Measured {measured}"),
    ),
    Fix(
        "T10-3a",
        "REQ-T-10",
        ("src/embodic/ui/views/checks_view.py",),
        "measured=row.measured_text,",
        "clearance=row.measured_text,",
        (),
        code=True,
    ),
    Fix(
        "T10-4",
        "REQ-T-10",
        ("src/embodic/io/report.py",),
        '(MARGIN + 130, "Least measured")',
        '(MARGIN + 130, "Least clearance")',
        ("Least measured",),
    ),
    Fix(
        "T10-5",
        "REQ-T-10",
        ("src/embodic/selftest/catalogue.py",),
        "the check measured no track pair",
        "the check found no track pair",
        ("measured no track pair",),
    ),
    Fix(
        "T10-6",
        "REQ-T-10",
        (*REGISTRY_COPIES, "docs/phase2/engineering/equation_specification.md"),
        "DRC clearance measurement and acceptance",
        "DRC clearance computation and acceptance",
        ("clearance measurement",),
    ),
    Fix(
        "T10-7",
        "REQ-T-10",
        ("resources/fonts/FONTS.md",),
        "each SHA-256 above is the one measured with `sha256sum` after download",
        "each SHA-256 above is the one computed with `sha256sum` after download",
        (),
    ),
    Fix(
        "T10-7b",
        "REQ-T-10",
        ("resources/fonts/FONTS.md",),
        "(`verified` by measuring;",
        "(`verified` by computing each hash;",
        (),
    ),
    Fix(
        "T11-1",
        "REQ-T-11",
        ("src/embodic/ui/strings/design.py",),
        "Balanced: q = {q}, periodicity t = {t}.",
        "Symmetric 3-phase pattern: q = {q}, periodicity t = {t}.",
        ("Balanced: q",),
    ),
    Fix(
        "T11-2",
        "REQ-T-11",
        ("src/embodic/ui/strings/design.py",),
        "Not balanced for {coils} coils and {poles} poles.",
        "No symmetric 3-phase pattern for {coils} coils and {poles} poles.",
        ("Not balanced for",),
    ),
    Fix(
        "T11-3",
        "REQ-T-11",
        ("src/embodic/ui/strings/design.py",),
        '"Balanced."',
        '"Symmetric 3-phase pattern."',
        ('"Balanced."',),
    ),
    Fix(
        "T11-4",
        "REQ-T-11",
        ("src/embodic/ui/strings/design.py",),
        "Not balanced: each phase needs the same number of coils.",
        "Not a symmetric 3-phase pattern: the other two phases must repeat phase A at 120° and 240° electrical.",
        ("each phase needs the same number of coils",),
    ),
    Fix(
        "T11-5",
        "REQ-T-11",
        ("src/embodic/ui/strings/design.py",),
        "Not balanced: choose {counts} coils.",
        "No symmetric 3-phase pattern: choose {counts} coils.",
        ("Not balanced: choose",),
    ),
    Fix(
        "T11-6",
        "REQ-T-11",
        ("src/embodic/ui/strings/design.py",),
        '"Not balanced."',
        '"No symmetric 3-phase pattern."',
        ('"Not balanced."',),
    ),
    Fix(
        "T11-7",
        "REQ-T-11",
        ("src/embodic/errors/catalogue/winding.py",),
        "The star of slots gives no balanced 3-phase winding for this coil count and pole count.",
        "No symmetric 3-phase pattern exists for this coil count and pole count.",
        ("no balanced 3-phase",),
    ),
    Fix(
        "T11-8",
        "REQ-T-11",
        ("src/embodic/errors/catalogue/winding.py",),
        "The manual phase assignment is not balanced; the value is the spread of the phase EMF phasor magnitudes.",
        "The manual phase assignment is not a symmetric 3-phase pattern; the value is the relative spread of the three "
        "phase phasor sums, each coil counted as a unit phasor.",
        ("is not balanced;", "EMF phasor magnitudes"),
    ),
    Fix(
        "L03-1",
        "REQ-L-03",
        ("src/embodic/model/validate.py",),
        "Xcoil clamps to the supported range.",
        "Values outside the supported range move to the nearest limit.",
        ("Xcoil clamps",),
    ),
    Fix(
        "L03-2",
        "REQ-L-03",
        ("src/embodic/model/validate.py",),
        "Xcoil rounds up to an even count.",
        "Odd counts round up to the next even count.",
        ("Xcoil rounds",),
    ),
    Fix(
        "L03-3",
        "REQ-L-03",
        REGISTRY_COPIES,
        "(form (a) only; Xcoil's current-sheet model is not ported, D-049 d)",
        "(form (a) only; the current-sheet model is not included, D-049 d)",
        ("current-sheet model is not ported",),
    ),
    Fix(
        "L03-4",
        "REQ-L-03",
        REGISTRY_COPIES,
        "pull-in T_pi = T_po - J omega f_e (Xcoil estimate)",
        "pull-in T_pi = T_po - J omega f_e (estimate)",
        ("(Xcoil estimate)",),
    ),
    Fix(
        "L03-5",
        "REQ-L-03",
        REGISTRY_COPIES,
        "over the magnet span) (Xcoil 'kw1'); serpentine",
        "over the magnet span); serpentine",
        ("(Xcoil 'kw1')",),
    ),
)

ADDITIONS = (
    (
        "A-1",
        "src/embodic/ui/strings/design.py",
        '"phase-balance-status.tooltip"',
        "A symmetric 3-phase pattern has its three phases 120° electrical apart. The check reads only the coil count, "
        "the pole count and the phase assignment. It does not look at the copper or the layer positions.",
    ),
)


INSERTS = (  # (file, line after which to insert, inserted line) for the additions
    (
        "src/embodic/ui/strings/design.py",
        '    "phase-balance-status.unbalanced": "No symmetric 3-phase pattern.",',
        f'    "phase-balance-status.tooltip": "{ADDITIONS[0][3]}",',
    ),
    (
        "src/embodic/ui/views/phase_panel.py",
        "        self.balance.setWordWrap(True)",
        '        self.balance.setToolTip(text("phase-balance-status.tooltip"))',
    ),
)
PLACEHOLDER_CALLS = (  # (strings module, key, call-site module) whose placeholders and keywords must agree
    ("src/embodic/ui/strings/export.py", "export.confirm.row", "src/embodic/ui/views/dialogs.py"),
    ("src/embodic/ui/strings/results.py", "drc.row.description", "src/embodic/ui/views/checks_view.py"),
    ("src/embodic/ui/strings/design.py", "phase-balance-status.tooltip", "src/embodic/ui/views/phase_panel.py"),
)


def load_scan(root: Path):
    """Import Agent 4's V3-14 scan module, so its patterns, extractor and allow-list are the ones applied."""
    spec = importlib.util.spec_from_file_location("v3_14_scan", root / SCAN)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scan_classes(scan) -> dict[str, re.Pattern[str]]:
    """Return the scan's patterns of the three classes this unit covers."""
    return {k: v for k, v in scan.CLASSES.items() if k in ("REQ-T-10", "REQ-T-11", "REQ-L-03")}


def apply_fixes(root: Path, out: Path) -> list[str]:
    """Write every file a fix or an addition touches under `out`, with all of them applied; return the paths."""
    touched = sorted({rel for fix in FIXES for rel in fix.paths} | {rel for rel, _, _ in INSERTS})
    for rel in touched:
        body = (root / rel).read_text(encoding="utf-8")
        for fix in FIXES:
            if rel in fix.paths:
                body = body.replace(fix.old, fix.new)
        for target, after, line in INSERTS:
            if target == rel:
                assert body.count(after + "\n") == 1, (rel, after)
                body = body.replace(after + "\n", f"{after}\n{line}\n")
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
        (out / rel).write_text(body, encoding="utf-8")
    return touched


def scan_findings(scan, path: Path, rel: str) -> dict[str, int]:
    """Count the V3-14 findings (not docstrings, not allow-listed) of one file, as the scan classifies them."""
    if path.suffix == ".py":
        texts = list(scan.literals(path, rel, "main src"))
    else:
        numbered = enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        texts = [scan.Text("main src", f"{rel}:{n}", "resource.md", line) for n, line in numbered]
    counts: dict[str, int] = {}
    for cls, pattern in scan_classes(scan).items():
        for t, _ in scan.hits(texts, pattern):
            if t.kind != "docstring" and not scan.admitted(cls, t):
                counts[cls] = counts.get(cls, 0) + 1
    return counts


def string_value(module: Path, key: str) -> str:
    """Return the value of `key` in a strings module's catalogue dict."""
    for node in ast.walk(ast.parse(module.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values, strict=True):
                if isinstance(k, ast.Constant) and k.value == key:
                    return ast.literal_eval(v)
    raise KeyError(key)


def call_keywords(module: Path, key: str) -> set[str] | None:
    """Return the keyword names of the first call whose first argument is `key`, or None when no call has it."""
    for node in ast.walk(ast.parse(module.read_text(encoding="utf-8"))):
        first = node.args[0] if isinstance(node, ast.Call) and node.args else None
        if isinstance(first, ast.Constant) and first.value == key:
            return {k.arg for k in node.keywords}
    return None


def check_applied(root: Path, scan) -> bool:
    """Apply every fix to a copy, then require zero findings, zero guide hits and matching placeholders."""
    ok = True
    with tempfile.TemporaryDirectory(prefix="us9-") as tmp:
        out = Path(tmp)
        touched = apply_fixes(root, out)
        print("== all fixes and additions applied to a copy of the touched files")
        for rel in touched:
            if rel.endswith(".py"):
                py_compile.compile(str(out / rel), doraise=True)
            if rel.endswith((".py", ".md")) and rel.startswith(("src/", "resources/fonts/")):
                before, after = scan_findings(scan, root / rel, rel), scan_findings(scan, out / rel, rel)
                ok &= not after
                print(f"   {rel}: V3-14 findings {before or 0} -> {after or 0}")
        hits = registry_hits(out, scan_classes(scan))
        ok &= not hits
        print(f"   {REGISTRY}: guide-shown REQ-T-10 and REQ-L-03 hits after: {hits or 0}")
        for strings_rel, key, caller_rel in PLACEHOLDER_CALLS:
            fields = {f for _, f, _, _ in string.Formatter().parse(string_value(out / strings_rel, key)) if f}
            keywords = call_keywords(out / caller_rel, key)
            agree = keywords is not None and fields == keywords
            ok &= agree
            shown = f"placeholders {sorted(fields)}, call keywords {sorted(keywords or ())}"
            print(f"   {key}: {shown} at {caller_rel}: {agree}")
    return ok


def where(root: Path, rel: str, needle: str) -> list[int]:
    """Return the 1-based lines of `rel` that contain `needle`."""
    lines = (root / rel).read_text(encoding="utf-8").splitlines()
    return [n for n, line in enumerate(lines, start=1) if needle in line]


def enclosing_test(lines: list[str], index: int) -> str:
    """Return the name of the test function a line belongs to, or "" outside one."""
    for line in reversed(lines[: index + 1]):
        if found := re.match(r"\s*def (test_\w+)", line):
            return found.group(1)
    return ""


def pinned(root: Path, probes: tuple[str, ...]) -> list[str]:
    """Return file:line (and test name) of every test or design doc line that holds one of the probes."""
    out: list[str] = []
    for base in PIN_ROOTS:
        for path in sorted((root / base).rglob("*")):
            rel = path.relative_to(root).as_posix()
            if not path.is_file() or path.suffix not in {".py", ".md"} or PIN_SKIP.search(rel):
                continue
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            for i, line in enumerate(lines):
                if any(p in line for p in probes):
                    test = enclosing_test(lines, i) if path.suffix == ".py" else ""
                    out.append(f"{rel}:{i + 1}" + (f" ({test})" if test else ""))
    return out


def strings(value: object) -> list[str]:
    """Return every string leaf of a JSON value."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [t for v in value.values() for t in strings(v)]
    if isinstance(value, list):
        return [t for v in value for t in strings(v)]
    return []


def registry_hits(root: Path, classes: dict[str, re.Pattern[str]]) -> list[str]:
    """Return the REQ-T-10 and REQ-L-03 hits in the registry fields the equation guide shows."""
    out = []
    for e in json.loads((root / REGISTRY).read_text(encoding="utf-8"))["equations"]:
        for field, keys in GUIDE_FIELDS.items():
            raw = e.get(field)
            shown = raw if keys is None else [{k: item.get(k) for k in keys} for item in raw or ()]
            for value in strings(shown):
                for cls in ("REQ-T-10", "REQ-L-03"):
                    if found := classes[cls].search(value):
                        out.append(f"{cls} {e['id']} {field}: {found.group(0)!r} in {value[:100]!r}")
    return out


def hidden_codes(root: Path, classes: dict[str, re.Pattern[str]]) -> list[str]:
    """Return issue codes that hold a class word only after an underscore, where a word-boundary pattern fails."""
    out = []
    for path in sorted((root / "src/embodic/errors/catalogue").glob("*.py")):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for code in re.findall(r'"([A-Z][A-Z0-9_]+)"\s*:', line):
                words = " ".join(code.split("_"))
                for cls, pattern in classes.items():
                    if pattern.search(words) and not pattern.search(code):
                        out.append(f"{cls} {code} ({path.relative_to(root).as_posix()}:{n})")
    return out


def header_width(root: Path) -> list[str]:
    """Measure the old and new DRC headers with the bundled Inter fonts' advance widths."""
    sys.path.insert(0, str(root / "src"))
    from embodic.io.pdf_writer import parse_truetype

    inter = root / "resources/fonts/Inter"
    fonts = {w: parse_truetype((inter / f"Inter-{w}.ttf").read_bytes()) for w in ("SemiBold", "Regular")}
    cell = 240 - 130  # report.py _drc: the column starts at MARGIN + 130 and the next at MARGIN + 240
    semibold = fonts["SemiBold"]
    out = [
        f"PDF {t!r}: {semibold.width_pt(t, 8.0):.1f} pt of a {cell} pt cell"
        for t in ("Least measured", "Least clearance")
    ]
    for w, font in fonts.items():
        old, new = font.width_pt("Measured", 1.0), font.width_pt("Clearance", 1.0)
        out.append(f"DRC table header, Inter {w}: 'Clearance' is {new / old - 1:+.1%} against 'Measured'")
    return out


def main(argv: list[str] | None = None) -> int:
    """Run every check and print the report; return 1 on any failure."""
    sys.dont_write_bytecode = True  # importing src/ and the scan must not leave __pycache__ in the tree
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    root = parser.parse_args(argv).root.resolve()
    scan = load_scan(root)
    classes = scan_classes(scan)
    doc = (root / DOC).read_text(encoding="utf-8") if (root / DOC).exists() else ""
    failed = False
    for fix in FIXES:
        print(f"== {fix.id} {fix.req}")
        for rel in fix.paths:
            lines = where(root, rel, fix.old)
            failed |= not lines
            print(f"   at {rel}:{','.join(map(str, lines)) or 'MISSING'}")
        hits = [] if fix.code else [f"{cls} {m.group(0)!r}" for cls, p in classes.items() for m in p.finditer(fix.new)]
        failed |= bool(hits)
        print(f"   replacement class hits: {hits or 0}")
        in_doc = fix.old in doc and fix.new in doc
        failed |= not in_doc
        print(f"   old and new verbatim in {DOC.name}: {in_doc}")
        for pin in pinned(root, fix.pins) if fix.pins else ():
            print(f"   pinned by {pin}")
    for aid, rel, key, value in ADDITIONS:
        hits = [f"{cls} {m.group(0)!r}" for cls, p in classes.items() for m in p.finditer(value)]
        failed |= bool(hits) or value not in doc
        print(f"== {aid} new key {key} in {rel}: class hits {hits or 0}, in doc {value in doc}")
    print("== registry fields the guide shows, REQ-T-10 and REQ-L-03 hits on this tree")
    for line in registry_hits(root, classes):
        print(f"   {line}")
    print("== issue codes the \\b-anchored scan patterns miss (shown as the issue-list tooltip)")
    for line in hidden_codes(root, classes):
        print(f"   {line}")
    failed |= not check_applied(root, scan)
    print("== header widths")
    for line in header_width(root):
        print(f"   {line}")
    print("FAILED" if failed else "OK")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
