"""PK-04: compare the outcome files of two platforms at 1e-9 relative (REQ-N-04).

    python docs/phase3/verification/checks/pk04_compare.py <reference folder> <candidate folder>
    python docs/phase3/verification/checks/pk04_compare.py --self-test

Both folders come from pk04_reference.py. A float pair passes when abs(a - b) <= 1e-9 * max(abs(a), abs(b)), so a
zero passes only against a zero. Integers, strings, booleans, null, keys and list lengths must be equal. The one
pointer allowed to differ is /versions/python, because REQ-N-04 covers Python 3.11 to 3.13 and the patch level differs
between the two machines. Exit 0 when every file agrees, 1 on a difference, 2 when the two manifests name different
embodic sources or NumPy versions, so the comparison would not test the platform.
"""

import argparse
import json
import math
import sys
import tempfile
from pathlib import Path

REL_TOL = 1e-9
ALLOWED = {"/versions/python"}


def diff(a: object, b: object, pointer: str = "") -> list[str]:
    """Return one line per disagreement between two parsed JSON values."""
    if pointer in ALLOWED:
        return []
    if isinstance(a, bool) or isinstance(b, bool) or a is None or b is None or isinstance(a, str):
        return [] if a == b and type(a) is type(b) else [f"{pointer}: {a!r} != {b!r}"]
    if isinstance(a, int) and isinstance(b, int):
        return [] if a == b else [f"{pointer}: {a} != {b}"]
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if math.isclose(a, b, rel_tol=REL_TOL, abs_tol=0.0):
            return []
        rel = abs(a - b) / max(abs(a), abs(b))
        return [f"{pointer}: {a!r} != {b!r} (rel {rel:.3e})"]
    if isinstance(a, dict) and isinstance(b, dict):
        out = [f"{pointer}/{k}: missing on one side" for k in sorted(set(a) ^ set(b))]
        for key in sorted(set(a) & set(b)):
            out += diff(a[key], b[key], f"{pointer}/{key}")
        return out
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [f"{pointer}: length {len(a)} != {len(b)}"]
        return [line for i, (x, y) in enumerate(zip(a, b, strict=True)) for line in diff(x, y, f"{pointer}/{i}")]
    return [f"{pointer}: type {type(a).__name__} != {type(b).__name__}"]


def compare(reference: Path, candidate: Path) -> int:
    """Print one verdict per example and return the exit code of the module docstring."""
    ref_manifest = json.loads((reference / "manifest.json").read_text(encoding="utf-8"))
    cand_manifest = json.loads((candidate / "manifest.json").read_text(encoding="utf-8"))
    for key in ("embodic_source_sha256", "numpy", "embodic"):
        if ref_manifest[key] != cand_manifest[key]:
            print(f"refused: {key} {ref_manifest[key]} != {cand_manifest[key]}")
            return 2
    print(f"reference {ref_manifest['platform']} Python {ref_manifest['python']}")
    print(f"candidate {cand_manifest['platform']} Python {cand_manifest['python']}")
    names = sorted(p.name for p in reference.glob("*.json") if p.name != "manifest.json")
    missing = [n for n in names if not (candidate / n).exists()]
    failed = bool(missing)
    for name in missing:
        print(f"FAIL {name}: missing in candidate")
    exits = {r["example"]: r["exit_code"] for r in cand_manifest["runs"]}
    for ref_run in ref_manifest["runs"]:
        if exits.get(ref_run["example"]) != ref_run["exit_code"]:
            failed = True
            print(f"FAIL {ref_run['example']}: exit {exits.get(ref_run['example'])} != {ref_run['exit_code']}")
    for name in [n for n in names if n not in missing]:
        ref_bytes, cand_bytes = (reference / name).read_bytes(), (candidate / name).read_bytes()
        lines = diff(json.loads(ref_bytes), json.loads(cand_bytes))
        failed |= bool(lines)
        verdict = "FAIL" if lines else "pass"
        print(f"{verdict} {name}: {len(lines)} differences, byte-identical {ref_bytes == cand_bytes}")
        for line in lines[:20]:
            print(f"  {line}")
    print("PK-04 " + ("failed" if failed else "passed") + f" at rel {REL_TOL:g}")
    return 1 if failed else 0


def self_test(reference: Path) -> int:
    """Show that the comparison passes a copy, fails a 2e-9 change and passes a 5e-10 change of one float."""
    name = "spiral_12c16p_default.json"
    doc = json.loads((reference / name).read_text(encoding="utf-8"))
    value = doc["analysis"]["ke_phase_v_s_per_rad"]["value"]
    verdicts = []
    for factor, expect in ((0.0, 0), (2e-9, 1), (5e-10, 0)):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            for path in reference.glob("*.json"):
                (out / path.name).write_bytes(path.read_bytes())
            doc["analysis"]["ke_phase_v_s_per_rad"]["value"] = value * (1 + factor)
            (out / name).write_text(json.dumps(doc), encoding="utf-8")
            got = compare(reference, out)
        verdicts.append(got == expect)
        print(f"self-test: change {factor:g} gives exit {got}, expected {expect}")
    return 0 if all(verdicts) else 1


def main(argv: list[str] | None = None) -> int:
    """Parse the arguments and run the comparison or the self-test."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("reference", type=Path, nargs="?", default=Path(__file__).parents[1] / "reference" / "linux")
    parser.add_argument("candidate", type=Path, nargs="?")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test(args.reference)
    if args.candidate is None:
        parser.error("candidate folder is required")
    return compare(args.reference, args.candidate)


if __name__ == "__main__":
    sys.exit(main())
