"""Fix wave F2 (U-E18, Agent 2): the REQ-T-05 links of EQ-06 and EQ-22, and what the EQ-06 ruling does to badges.

Run from the repository root, with the passed-tests evidence of a release build (for example the copy inside the
0.0.1 wheel, embodic/_resources/evidence/passed_tests.v1.json):

    PYTHONPATH=src:.:tests/golden python3 docs/phase3/engineering/checks/f2_req_t05.py --evidence PATH

Part 1 lists the test functions whose decorators carry EQT-06-O2 or EQT-22-GR, and marks a carrier that also has an
xfail or skip decorator. It reads function decorators only, which is where both IDs are marked.
Part 2 applies `Registry.tests_passed` to the evidence file's `passed_tests`, the predicate of
`tools/record_passed_tests.py` (REQ-T-05, D-056 a), and prints the `verified` equations it refuses.
Part 3 reproduces the EQT-22-GR comparison: J of the three mapped m1_layout layouts against Xcoil's
`currentDensity` at rel 1e-12 (the KERNEL class of tests/golden/harness/compare.py).
Part 4 computes the D08 example with the evidence's passed IDs plus EQT-22-GR under four registry variants (V0 as
shipped, V1 the ruling, V2 the rejected alternative, V3 as shipped once OR-07 passes) and prints the badge of each
result whose chain holds EQ-06.
"""

import argparse
import ast
import dataclasses
import json
from collections.abc import Mapping
from pathlib import Path

from embodic.api import _traceables, compute
from embodic.io.project import load_project, project_provenance
from embodic.results import Registry, load_registry
from embodic.results.status import Status

REPO = Path(__file__).resolve().parents[4]
D08_EXAMPLE = REPO / "resources" / "examples" / "spiral_12c10p_d08.embodic.json"
F11_DATA = REPO / "tests" / "golden" / "data" / "mass_thermal"
F11_LAYOUTS = ("sector-default", "serpentine-default", "wave-turns-2")
KERNEL_REL = 1e-12
WATCHED = ("EQT-06-O2", "EQT-22-GR")


def _mark_name(node: ast.expr) -> str:
    target = node.func if isinstance(node, ast.Call) else node
    parts = []
    while isinstance(target, ast.Attribute):
        parts.append(target.attr)
        target = target.value
    if isinstance(target, ast.Name):
        parts.append(target.id)
    return ".".join(reversed(parts)).removeprefix("pytest.mark.")


def part1() -> None:
    """Print each decorator carrier of the watched IDs and its xfail or skip decorators."""
    print("Part 1. Decorator carriers of " + ", ".join(WATCHED))
    for path in sorted((REPO / "tests").rglob("test_*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.FunctionDef):
                continue
            names = [_mark_name(d) for d in node.decorator_list]
            ids = [
                a.value
                for d in node.decorator_list
                if isinstance(d, ast.Call) and _mark_name(d) == "eqt"
                for a in d.args
                if isinstance(a, ast.Constant)
            ]
            for test_id in set(ids).intersection(WATCHED):
                gated = sorted(set(names).intersection(("xfail", "skip", "skipif")))
                where = f"{path.relative_to(REPO)}::{node.name} l.{node.lineno}"
                print(f"  {test_id}: {where} gated by {gated or 'nothing'}")


def part2(registry: Registry, passed: frozenset[str], build_id: str) -> None:
    """Print the verified equations that REQ-T-05 refuses on the given passed IDs."""
    with_evidence = dataclasses.replace(registry, passed_tests=passed)
    refused = [
        f"{eq_id} (not passed: {sorted(set(e.tests) - passed)})"
        for eq_id, e in registry.equations.items()
        if e.status is Status.VERIFIED and not with_evidence.tests_passed(eq_id)
    ]
    print(f"Part 2. evidence {build_id}, {len(passed)} passed IDs; REQ-T-05 refuses {refused or 'none'}")


def part3(registry: Registry) -> None:
    """Compare analyse()'s current density with Xcoil's on the three mapped layouts."""
    from m2_physics.test_analyse_layouts import _design, _raw, _stack

    from embodic.physics import analyse

    print("Part 3. EQT-22-GR: J of the mapped layout against Xcoil currentDensity")
    for tag in F11_LAYOUTS:
        xcoil = json.loads((F11_DATA / f"connection-{tag}.json").read_text(encoding="utf-8"))["calls"][0]["output"]
        raw = _raw(f"layout-{tag}")
        result = analyse(_design(raw), _stack(raw), {}, registry)
        assert result is not None
        j = result.current_density_a_per_mm2.value
        rel = abs(j - xcoil["currentDensity"]) / abs(xcoil["currentDensity"])
        verdict = "pass" if rel <= KERNEL_REL else "FAIL"
        print(f"  {tag}: embodic {j!r} A/mm2, Xcoil {xcoil['currentDensity']!r} A/mm2, rel {rel:.2e} ({verdict})")


def _badges(registry: Registry) -> Mapping[str, tuple[str, tuple[str, ...]]]:
    project, issues = load_project(D08_EXAMPLE)
    assert project is not None, issues
    outcome = compute(project.design, project_provenance(project), registry=registry)
    assert outcome is not None and outcome.analysis is not None, outcome
    return {t.quantity: (str(t.status), t.eq_ids) for t in _traceables(outcome.analysis) if "EQ-06" in t.eq_ids}


def part4(registry: Registry, passed: frozenset[str]) -> None:
    """Print the badge of every EQ-06 result of the D08 example under the four registry variants."""
    eq06 = registry.equation("EQ-06")
    linked = tuple(dict.fromkeys((*eq06.tests, "EQT-06-O2")))
    unlinked = tuple(t for t in linked if t != "EQT-06-O2")
    or07 = passed | {"EQT-05-O2", "EQT-06-O2"}

    def variant(status: Status, tests: tuple[str, ...], ids: frozenset[str]) -> Registry:
        equations = {**registry.equations, "EQ-06": dataclasses.replace(eq06, status=status, tests=tests)}
        return dataclasses.replace(registry, equations=equations, passed_tests=ids)

    variants = {
        "V0 0.0.1 registry": variant(Status.VERIFIED, linked, passed),
        "V1 ruling: inferred, O2 linked": variant(Status.INFERRED, linked, passed),
        "V2 verified, O2 unlinked": variant(Status.VERIFIED, unlinked, passed),
        "V3 V0 once OR-07 passes": variant(Status.VERIFIED, linked, or07),
    }
    badges = {name: _badges(r) for name, r in variants.items()}
    all_linked = {t for e in registry.equations.values() for t in e.tests} | {"EQT-06-O2"}
    print(f"Part 4. D08 example; passed = evidence + EQT-22-GR; linked, not passed: {sorted(all_linked - passed)}")
    print("  " + " | ".join(variants))
    v0 = badges["V0 0.0.1 registry"]
    for quantity in sorted(v0):
        row = " | ".join(badges[name][quantity][0] for name in variants)
        print(f"  {quantity:24s} [{','.join(v0[quantity][1])}] {row}")
    for name in variants:
        changed = sum(badges[name][q][0] != v0[q][0] for q in v0)
        print(f"  {name}: {changed} of {len(v0)} badges differ from V0")


def main() -> None:
    """Run the four parts on the given evidence file."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--evidence", type=Path, required=True, help="a passed_tests.v1.json of a release build")
    args = parser.parse_args()
    evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
    passed = frozenset(evidence["passed_tests"])
    registry = load_registry()
    print(f"registry {registry.version}; EQ-06 tests {registry.equation('EQ-06').tests}")
    part1()
    part2(registry, passed, evidence["build_id"])
    ruled = {**registry.equations, "EQ-06": dataclasses.replace(registry.equation("EQ-06"), status=Status.INFERRED)}
    part2(dataclasses.replace(registry, equations=ruled), passed | {"EQT-22-GR"}, "same + EQT-22-GR, EQ-06 inferred")
    part3(registry)
    part4(registry, passed | {"EQT-22-GR"})


if __name__ == "__main__":
    main()
