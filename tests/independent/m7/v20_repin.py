"""U-V20 item 3: carry the V3-01 `checks` rulings across the test renames of U-M8y and U-M8z (release 0.0.5, 99d355d).

    python3 tests/independent/m7/v20_repin.py --write    # pin the cites of v3_01_rulings_v20.py on the target
    python3 tests/independent/m7/v20_repin.py            # classify every pinned cite on the target, print the table
    python3 tests/independent/m7/v20_repin.py --before-v20   # the same without the v20 overlay: what it re-rules

The rulings are those req_audit.py applies (v13, then the v14, v18, v19 and v20 overlays). For each `checks` ruling,
each cite that is not a gate is hashed on `git archive <target> tests` the way req_audit.py `cite_hash` hashes it:

- `holds`: the hash equals the pin, nothing to do.
- `renamed`: the cited function is gone on the target, RENAMES names the function that replaced it, and the two
  function nodes are equal once both carry the new name and the docstring edits of u_v19_id_map.TEXT_EDITS
  (`ast.dump`, so only formatting may differ). The ruling carries; v3_01_rulings_v20.py cites the new name.
- `same body`: the function keeps its name, its hash moved, and its node is equal to the pinned base once the
  TEXT_EDITS apply (a docstring the map asked for, or formatting). The ruling carries.
- anything else is `CHANGED` and needs a reading and a new ruling before any pin moves (v3_01_rulings_v20.py).

`--write` hashes every non-gate cite of the v20 rulings on the target and writes them as the v20 pins; it refuses a
cite that is missing there. The base of a pin is the commit its rulings file names (v13 260191f, v14 c0f4894, v18 and
v19 c25d8a9, v20 99d355d); a cite that already names the new function is compared with the function of its old name.
Exit 1 when a cite is `CHANGED`.
"""

import argparse
import ast
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
TARGET = "99d355d"
PIN_FILE = HERE / "records/V3-01_pins_99d355d_v20.json"


def load(path: Path):
    """Import a module by path."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUDIT = load(REPO / "docs/phase3/verification/checks/req_audit.py")
MAP = load(HERE / "u_v19_id_map.py")
# Old cite -> new function name: the renames of the ID map, which U-M8y applied and U-M8z for UT-DRC-01 (D-084b, c),
# and the UT-GEO-19 rename of e457a33 (U-D26). `--before-v20` shows that each one is on 99d355d.
RENAMES = {old: new for entry in MAP.ENTRIES for old, new in entry.rename}
LAYERS = (("v13", "260191f"), ("v14", "c0f4894"), ("v18", "c25d8a9"), ("v19", "c25d8a9"), ("v20", TARGET))


def renamed(cite: str) -> str:
    """Return the cite under its new function name, or the cite itself."""
    return f"{cite.partition('::')[0]}::{RENAMES[cite]}" if cite in RENAMES else cite


def original(cite: str) -> str:
    """Return the old cite of a new function name, or the cite itself."""
    back = {renamed(old): old for old in RENAMES}
    return back.get(cite, cite)


def tree_files(commit: str) -> dict[str, str]:
    """Return {path: text} of every .py file under tests at commit."""
    data = subprocess.run(["git", "-C", str(REPO), "archive", commit, "tests"], capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        return {m.name: tar.extractfile(m).read().decode("utf-8") for m in tar.getmembers() if m.name.endswith(".py")}


def node_of(files: dict[str, str], cite: str):
    """Return (the function node, its source segment) of a cite, or (None, None)."""
    path, _, name = cite.partition("::")
    text = files.get(path)
    if text is None:
        return None, None
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == name:
            return node, ast.get_source_segment(text, node)
    return None, None


def normal(node, segment: str, path: str, name: str) -> str:
    """ast.dump of a function after giving it `name` and applying the TEXT_EDITS of its file to its source."""
    for file, old, new in MAP.TEXT_EDITS:
        if file == path:
            segment = segment.replace(old, new)
    tree = ast.parse("\n".join(line[node.col_offset :] for line in segment.splitlines()))
    tree.body[0].name = name
    return ast.dump(tree.body[0])


def rulings_by_layer(layers=LAYERS):
    """Yield (layer, base, req, ruling, pins of req) for every `checks` ruling, in the order req_audit applies."""
    merged = {}
    for layer, base in layers:
        if not (HERE / f"v3_01_rulings_{layer}.py").is_file():
            continue
        module = load(HERE / f"v3_01_rulings_{layer}.py")
        pins = (
            json.loads((HERE / "records/V3-01_pins_260191f.json").read_text(encoding="utf-8"))
            if layer == "v13"
            else module.PINS
        )
        for req, ruling in module.RULINGS.items():
            merged[req] = (layer, base, ruling, pins.get(req, {}))
    for req, (layer, base, ruling, pins) in sorted(merged.items()):
        if ruling.ruling == "checks":
            yield layer, base, req, ruling, pins


def classify(target: str, layers=LAYERS):
    """Return one row per non-gate cite: (req, layer, cite, new cite, kind, target hash)."""
    target_files = tree_files(target)
    bases = {base: tree_files(base) for _, base in layers}
    rows = []
    for layer, base, req, ruling, pins in rulings_by_layer(layers):
        for cite in ruling.cites:
            if cite.startswith("gate:"):
                continue
            new = renamed(cite)
            if cite.startswith("record:"):
                digest = AUDIT.cite_hash(cite, REPO / "nonexistent")
                kind = "holds" if pins.get(cite) == digest else "CHANGED"
                rows.append((req, layer, cite, cite, kind, digest))
                continue
            node, segment = node_of(target_files, new)
            if node is None:
                rows.append((req, layer, cite, new, "CHANGED: missing on the target", None))
                continue
            digest = hashlib.sha256(segment.encode("utf-8")).hexdigest()
            if pins.get(cite) == digest:
                rows.append((req, layer, cite, new, "holds", digest))
                continue
            old_node, old_segment = node_of(bases[base], original(cite))
            if old_node is None:
                rows.append((req, layer, cite, new, f"CHANGED: not in {base}", digest))
                continue
            path, _, name = new.partition("::")
            same = normal(old_node, old_segment, path, name) == normal(node, segment, path, name)
            if same:
                kind = "renamed" if new != cite or original(cite) != cite else "same body"
            else:
                kind = "CHANGED: body differs"
            rows.append((req, layer, cite, new, kind, digest))
    return rows


def main(argv: list[str] | None = None) -> int:
    """Print the classification; with --write, write the v20 pins."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", default=TARGET)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--before-v20", action="store_true")
    args = parser.parse_args(argv)
    if args.write:
        target_files = tree_files(args.target)
        pins: dict[str, dict[str, str]] = {}
        for req, ruling in load(HERE / "v3_01_rulings_v20.py").RULINGS.items():
            for cite in ruling.cites:
                if cite.startswith("gate:"):
                    continue
                _, segment = node_of(target_files, cite)
                if segment is None:
                    raise SystemExit(f"{req}: {cite} is missing on {args.target}")
                pins.setdefault(req, {})[cite] = hashlib.sha256(segment.encode("utf-8")).hexdigest()
        PIN_FILE.write_text(json.dumps(pins, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {PIN_FILE.relative_to(REPO)}: {sum(len(v) for v in pins.values())} pins over {len(pins)} rows")
    rows = classify(args.target, LAYERS[:-1] if args.before_v20 else LAYERS)
    counts = {}
    for req, layer, cite, new, kind, _ in rows:
        counts[kind] = counts.get(kind, 0) + 1
        if kind != "holds":
            shown = cite if new == cite else f"{cite} -> {new.partition('::')[2]}"
            print(f"{req} ({layer}) {kind}: {shown}")
    print(", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    return 1 if any(r[4].startswith("CHANGED") for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
