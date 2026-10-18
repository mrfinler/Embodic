"""Print the sorted distinct words of the string catalogues and report templates (REQ-L-01 manual review, U-V13).

    python3 tests/independent/m7/l01_words.py [--sources]

Agent 4's own lister. test_plan.md LG-01 (revision U-D20) specifies a product function and command that print this
list; neither exists on main 260191f (DEF-UV13-01), so the reviewer reads this list instead. The corpus, read with
`ast` and never imported: every string constant of the UI string catalogue (src/embodic/ui/strings), of the issue
message catalogue (src/embodic/errors/catalogue) and of the two report writers (src/embodic/io/report.py,
src/embodic/io/readme_writer.py), except docstrings and the keys of a catalogue mapping. Format fields such as
`{value}` and `{value:.3g}` are dropped. A word is a run of ASCII or non-ASCII letters; it is lowered, and a run with a
lower-to-upper change (camelCase) is split there. `--sources` adds the first file that holds each word.
"""

import ast
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CATALOGUES = ("src/embodic/ui/strings", "src/embodic/errors/catalogue")
TEMPLATES = ("src/embodic/io/report.py", "src/embodic/io/readme_writer.py")
FIELD = re.compile(r"\{[^{}]*\}")
WORD = re.compile(r"[^\W\d_]+")
CAMEL = re.compile(r"(?<=[a-z])(?=[A-Z])")


def corpus_files() -> list[Path]:
    """Return the catalogue modules and the two report writers, in path order."""
    files = [p for folder in CATALOGUES for p in sorted((REPO / folder).glob("*.py"))]
    return files + [REPO / t for t in TEMPLATES]


def docstring_nodes(tree: ast.Module) -> set[int]:
    """Return the ids of the string constants that are docstrings of the module, a class or a function."""
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                out.add(id(first.value))
    return out


def mapping_keys(tree: ast.Module) -> set[int]:
    """Return the ids of the string constants that are keys of a dict display (catalogue keys)."""
    return {id(k) for node in ast.walk(tree) if isinstance(node, ast.Dict) for k in node.keys if k is not None}


def texts(path: Path, *, catalogue: bool) -> list[str]:
    """Return the string constants of one file that a user can read."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    skip = docstring_nodes(tree) | (mapping_keys(tree) if catalogue else set())
    return [
        n.value
        for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in skip
    ]


def words(text: str) -> list[str]:
    """Return the lowered words of one text, format fields dropped and camelCase split."""
    return [w.lower() for run in WORD.findall(FIELD.sub(" ", text)) for w in CAMEL.split(run) if w]


def distinct_words() -> dict[str, str]:
    """Return word -> first file (repository-relative) that holds it, sorted by word."""
    first: dict[str, str] = {}
    for path in corpus_files():
        catalogue = any(path.is_relative_to(REPO / folder) for folder in CATALOGUES)
        for text in texts(path, catalogue=catalogue):
            for word in words(text):
                first.setdefault(word, path.relative_to(REPO).as_posix())
    return dict(sorted(first.items()))


def main(argv: list[str]) -> int:
    """Print one word per line, with its first file when --sources is given, then a count line."""
    found = distinct_words()
    for word, where in found.items():
        print(f"{word}\t{where}" if "--sources" in argv else word)
    print(f"# {len(found)} distinct words in {len(corpus_files())} files", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
