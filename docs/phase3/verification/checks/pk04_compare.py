"""PK-04: compare the outcome files of two platforms at 1e-9 relative (REQ-N-04, D-051f).

    python docs/phase3/verification/checks/pk04_compare.py <reference folder> <candidate folder>
    python docs/phase3/verification/checks/pk04_compare.py --self-test

Both folders come from pk04_reference.py. A scalar float pair passes when abs(a - b) <= 1e-9 * max(abs(a), abs(b)).
A numeric array (a list whose leaves are all numbers, such as an EMF waveform) is compared at 1e-9 relative to its own
largest magnitude: each pair passes when abs(a - b) <= 1e-9 * peak, where peak is the largest abs value in either
array. A sample whose true value is 0 then passes on rounding noise and still fails on a real change (D-051f).
Integers, strings, booleans, null, keys and list lengths must be equal. Pointers in EXCLUDED are not compared, nor is
`pairs_checked` of a DRC summary whose kind is a pair kind (BROAD_PHASE_KINDS): that count is a broad-phase diagnostic
(D-052b), and the piece count of a 1.0 mm trace rounds either way under float noise (DEF-UV10-01, U-V20). Exit 0
when every file agrees, 1 on a difference, 2 when the two manifests name different embodic sources or NumPy versions,
so the comparison would not test the platform.
"""

import argparse
import contextlib
import io
import json
import math
import re
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

REL_TOL = 1e-9
EXCLUDED = {
    "/versions/python": "REQ-N-04 covers Python 3.11 to 3.13, so the patch level differs between the machines",
    "/boards/layout_hashes": "a same-platform identity over float bytes (D-051f, DEF-W-02)",
    "/boards/stack_hash": "a same-platform identity over float bytes (D-051f, DEF-W-02)",
}
BROAD_PHASE_KINDS = frozenset(
    {"trace_trace", "trace_via", "via_via", "pad_trace", "pad_pad", "copper_edge", "copper_hole"}
)
SUMMARY = re.compile(r"/drc/\d+/summaries/\d+")
BROAD_PHASE_COUNT = "/drc/*/summaries/*/pairs_checked of the pair kinds"


def skipped_keys(pointer: str, a: dict, b: dict) -> set[str]:
    """Keys of a DRC summary left out: pairs_checked of a pair kind (D-052b); the kind itself is still compared."""
    if SUMMARY.fullmatch(pointer) and a.get("kind") == b.get("kind") and a.get("kind") in BROAD_PHASE_KINDS:
        return {"pairs_checked"}
    return set()


def is_number(x: object) -> bool:
    """Return True for an int or float that is not a bool."""
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def leaves(x: object) -> list[float] | None:
    """Return the numeric leaves of a non-empty list of numbers or of such lists, else None."""
    if is_number(x):
        return [x]
    if not isinstance(x, list) or not x:
        return None
    out = []
    for item in x:
        sub = leaves(item)
        if sub is None:
            return None
        out += sub
    return out


def number_diff(a: float, b: float, pointer: str, peak: float | None) -> list[str]:
    """Compare two numbers: relative to their own size, or inside an array relative to the array's peak."""
    if peak is None:
        if math.isclose(a, b, rel_tol=REL_TOL, abs_tol=0.0):
            return []
        return [f"{pointer}: {a!r} != {b!r} (rel {abs(a - b) / max(abs(a), abs(b)):.3e})"]
    if abs(a - b) <= REL_TOL * peak:
        return []
    return [f"{pointer}: {a!r} != {b!r} (abs {abs(a - b):.3e} > 1e-9 x array peak {peak:.6g})"]


def diff(a: object, b: object, pointer: str = "", peak: float | None = None) -> list[str]:
    """Return one line per disagreement between two parsed JSON values; peak is set inside a numeric array."""
    if pointer in EXCLUDED:
        return []
    if isinstance(a, bool) or isinstance(b, bool) or a is None or b is None or isinstance(a, str):
        return [] if a == b and type(a) is type(b) else [f"{pointer}: {a!r} != {b!r}"]
    if isinstance(a, int) and isinstance(b, int):
        return [] if a == b else [f"{pointer}: {a} != {b}"]
    if is_number(a) and is_number(b):
        return number_diff(a, b, pointer, peak)
    if isinstance(a, dict) and isinstance(b, dict):
        out = [f"{pointer}/{k}: missing on one side" for k in sorted(set(a) ^ set(b))]
        for key in sorted((set(a) & set(b)) - skipped_keys(pointer, a, b)):
            out += diff(a[key], b[key], f"{pointer}/{key}", peak)
        return out
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [f"{pointer}: length {len(a)} != {len(b)}"]
        if peak is None and (la := leaves(a)) is not None and (lb := leaves(b)) is not None:
            peak = max(abs(x) for x in la + lb)
        return [line for i, (x, y) in enumerate(zip(a, b, strict=True)) for line in diff(x, y, f"{pointer}/{i}", peak)]
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
    print("not compared: " + ", ".join([*sorted(EXCLUDED), BROAD_PHASE_COUNT]))
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


Mutation = Callable[[dict], str]


def self_test_cases(doc: dict) -> list[tuple[str, Mutation, int]]:
    """(name, mutation of the default example's outcome that returns the pointer it changed, expected exit)."""
    emf = doc["analysis"]["emf_waveform_v"]["value"]
    i_zero = min(range(len(emf)), key=lambda i: abs(emf[i]))
    i_peak = max(range(len(emf)), key=lambda i: abs(emf[i]))
    peak = abs(emf[i_peak])

    def scale_ke(factor: float) -> Mutation:
        def mutate(d: dict) -> str:
            d["analysis"]["ke_phase_v_s_per_rad"]["value"] *= 1 + factor
            return "/analysis/ke_phase_v_s_per_rad/value"

        return mutate

    def emf_sample(i: int, new: float) -> Mutation:
        def mutate(d: dict) -> str:
            d["analysis"]["emf_waveform_v"]["value"][i] = new
            return f"/analysis/emf_waveform_v/value/{i}"

        return mutate

    def summary_count(kind: str, delta: int) -> Mutation:
        def mutate(d: dict) -> str:
            index = next(i for i, s in enumerate(d["drc"][0]["summaries"]) if s["kind"] == kind)
            d["drc"][0]["summaries"][index]["pairs_checked"] += delta
            return f"/drc/0/summaries/{index}/pairs_checked"

        return mutate

    def set_hash(path: tuple[str | int, ...]) -> Mutation:
        def mutate(d: dict) -> str:
            node = d
            for key in path[:-1]:
                node = node[key]
            node[path[-1]] = "sha256:" + "0" * 64
            return "/" + "/".join(map(str, path))

        return mutate

    return [
        ("unchanged copy", lambda d: "", 0),
        ("scalar ke changed by 2e-9 rel", scale_ke(2e-9), 1),
        ("scalar ke changed by 5e-10 rel", scale_ke(5e-10), 0),
        (
            f"near-zero EMF sample {i_zero} ({emf[i_zero]:.3e} V) moved by 1e-12 x peak",
            emf_sample(i_zero, emf[i_zero] + 1e-12 * peak),
            0,
        ),
        (
            f"EMF peak sample {i_peak} ({emf[i_peak]:.6g} V) changed by 2e-9 rel",
            emf_sample(i_peak, emf[i_peak] * (1 + 2e-9)),
            1,
        ),
        ("layout hash changed", set_hash(("boards", "layout_hashes", 0)), 0),
        ("stack hash changed", set_hash(("boards", "stack_hash")), 0),
        ("design hash changed", set_hash(("design_hash",)), 1),
        ("trace_trace pairs_checked changed by 1 (D-052b)", summary_count("trace_trace", 1), 0),
        ("min_width pairs_checked changed by 1", summary_count("min_width", 1), 1),
    ]


def self_test(reference: Path) -> int:
    """Run each case on a copy of the reference; a failing case must also name the pointer it changed."""
    name = "spiral_12c16p_default.json"
    ok = True
    for label, mutate, expect in self_test_cases(json.loads((reference / name).read_text(encoding="utf-8"))):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            for path in reference.glob("*.json"):
                (out / path.name).write_bytes(path.read_bytes())
            doc = json.loads((reference / name).read_text(encoding="utf-8"))
            pointer = mutate(doc)
            (out / name).write_text(json.dumps(doc), encoding="utf-8")
            printed = io.StringIO()
            with contextlib.redirect_stdout(printed):
                got = compare(reference, out)
        named = expect == 0 or f"  {pointer}: " in printed.getvalue()
        ok &= got == expect and named
        verdict = "ok" if got == expect and named else "WRONG"
        unnamed = "" if named else f", {pointer} not named"
        print(f"self-test {verdict}: {label}: exit {got}, expected {expect}{unnamed}")
    print("self-test " + ("passed" if ok else "FAILED"))
    return 0 if ok else 1


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
