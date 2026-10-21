"""U-V26: trace the D08 Ke badge of the 0.0.5 wheel through the registry, the gate report and the evidence file.

Run, with the wheel unpacked into <unpacked> (python -m zipfile -e <wheel> <unpacked>):
    PYTHONPATH=<unpacked> python -P -s uv26_ke_badge_trace.py <release_dir>
Read-only. -I would drop PYTHONPATH and import the venv's editable checkout, whose resources hold no evidence file.
"""

import json
import sys
from collections import defaultdict
from importlib import resources
from pathlib import Path

import embodic
from embodic.api import compute_project
from embodic.results.registry import load_registry

CARD = "ke_line_peak_v_s_per_rad"
D08_MEASURED_KE = 0.031


def gate_records(report_path: Path) -> tuple[dict[str, list[tuple[str, str]]], int, int]:
    """Return the (node ID, outcome) pairs per registry test ID, the record count and the failed count."""
    report = json.loads(report_path.read_text())
    carried: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for record in report:
        for eqt in record.get("eqt", ()):
            carried[eqt].append((record["nodeid"], record["outcome"]))
    return carried, len(report), sum(r["outcome"] == "failed" for r in report)


def main(release: Path) -> None:
    """Print the D08 card badge, then gate admission against evidence for every linked ID of its chain."""
    root = resources.files("embodic") / "_resources"
    evidence = json.loads((root / "evidence" / "passed_tests.v1.json").read_text())
    loose = json.loads((release / "passed_tests.v1.json").read_text())
    print(f"embodic {embodic.__version__} from {Path(embodic.__file__).parent}")
    print(f"wheel evidence == release-dir evidence: {evidence == loose}")
    print(f"evidence build {evidence['build_id']}, {len(evidence['passed_tests'])} passed IDs")

    registry = load_registry()
    print(f"load_registry: evidence_build_id {registry.evidence_build_id}, {len(registry.passed_tests)} passed IDs")

    outcome = compute_project(root / "examples" / "spiral_12c10p_d08.embodic.json")
    card = getattr(outcome.analysis, CARD)
    print(f"\nD08 card {CARD}: {card.value:.6f} V*s/rad, off D08 measured by {card.value / D08_MEASURED_KE - 1:+.2%}")
    print(f"  badge {card.status.value!r}, chain {card.eq_ids}")
    print(f"  reasons: {'; '.join(card.status_reasons)}")

    carried, n_records, n_failed = gate_records(release / "req_report.json")
    print(f"\ngate report: {n_records} records, {n_failed} failed")
    chain = [part.split()[0] for part in card.status_reasons if part.startswith("EQ-")]
    for eq_id in dict.fromkeys(chain):
        entry = registry.equation(eq_id)
        print(f"\n{eq_id} status {entry.status.value!r}, tests_passed {registry.tests_passed(eq_id)}")
        for eqt in entry.tests:
            rows = carried.get(eqt, [])
            gate_admits = bool(rows) and all(o == "passed" for _, o in rows)
            in_evidence = eqt in evidence["passed_tests"]
            flag = "" if gate_admits == in_evidence else "  MISMATCH gate vs evidence"
            print(
                f"  {eqt}: {len(rows)} records {sorted({o for _, o in rows})}, gate admits {gate_admits}, "
                f"in evidence {in_evidence}{flag}"
            )
            if not gate_admits:
                for nodeid, outcome_text in rows:
                    print(f"      {outcome_text}: {nodeid}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
