"""Independent check of the release evidence file against req_report.json and the installed package.

Usage: python evidence_check.py --report REPORT --wheel WHEEL --site-embodic SITE_PACKAGES/embodic [--src SRC/embodic]

Rules applied, read from docs/phase2/architecture/interfaces.md §3.1 (base 1eb110d):
- A registry test ID passes when at least one report record carries it in "eqt" and every record carrying it has
  outcome "passed".
- source_sha256: SHA-256 over the *.py files below the package folder outside __pycache__, sorted by relative POSIX
  path; per file the UTF-8 path, one NUL byte, then the raw 32-byte SHA-256 of the file bytes.
- registry_version: "v1+" + first 12 hex of the equations.v1.json copy hash + "." + first 12 hex of evidence.v1.json's
  (load_registry reads them from manifest.v1.json; this script hashes the shipped files itself and also checks the
  manifest says the same).
- build_id: <embodic_version>+g<first 12 hex of git_commit>.<generated_utc as YYYYMMDDThhmmssZ>.
Exit 0 when every check holds, 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

EVIDENCE_IN_WHEEL = "embodic/_resources/evidence/passed_tests.v1.json"


def my_passed_ids(records: list[dict], registry_ids: set[str]) -> tuple[set[str], dict[str, list[str]], set[str]]:
    """Return the passed ids, their carrier node ids, and eqt ids the registry lacks."""
    carriers: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        for eqt_id in record.get("eqt", []):
            carriers[eqt_id].append(record)
    unknown = set(carriers) - registry_ids
    passed = {i for i, recs in carriers.items() if recs and all(r["outcome"] == "passed" for r in recs)}
    realised = {i: sorted(r["nodeid"] for r in carriers[i]) for i in passed}
    return passed, realised, unknown


def my_source_sha256(package_dir: Path) -> tuple[str, int]:
    """Return the §3.1 source hash of package_dir and the number of files hashed."""
    entries = []
    for path in package_dir.rglob("*.py"):
        rel = path.relative_to(package_dir)
        if "__pycache__" in rel.parts:
            continue
        entries.append((rel.as_posix(), path))
    entries.sort(key=lambda e: e[0])
    outer = hashlib.sha256()
    for rel, path in entries:
        outer.update(rel.encode("utf-8"))
        outer.update(b"\x00")
        outer.update(hashlib.sha256(path.read_bytes()).digest())
    return outer.hexdigest(), len(entries)


def main() -> int:
    """Run every evidence check and print PASS or FAIL per check."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--site-embodic", type=Path, required=True)
    parser.add_argument("--src", type=Path, default=None)
    args = parser.parse_args()

    failures: list[str] = []

    def check(name: str, ok: bool, detail: str) -> None:
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}")
        if not ok:
            failures.append(name)

    with zipfile.ZipFile(args.wheel) as wheel:
        evidence = json.loads(wheel.read(EVIDENCE_IN_WHEEL))
    installed = json.loads((args.site_embodic / "_resources/evidence/passed_tests.v1.json").read_text())
    check("installed evidence equals the wheel's", installed == evidence, f"{len(installed['passed_tests'])} ids")

    equations = json.loads((args.site_embodic / "_resources/evidence/equations.v1.json").read_text())["equations"]
    registry_ids = {t for eq in equations for t in eq["tests"]}
    print(f"INFO  registry: {len(equations)} equations, {len(registry_ids)} distinct EQT ids")

    records = json.loads(args.report.read_text())
    outcomes = defaultdict(int)
    for r in records:
        outcomes[r["outcome"]] += 1
    print(f"INFO  report: {len(records)} records, outcomes {dict(sorted(outcomes.items()))}")

    passed, realised, unknown = my_passed_ids(records, registry_ids)
    carried = {i for r in records for i in r.get("eqt", [])}
    print(
        f"INFO  my derivation: {len(passed)} passed of {len(registry_ids)}; carried by no test: "
        f"{len(registry_ids - carried)}; carried but not passed: {sorted(carried - passed)}"
    )
    check("no unknown eqt id in the report", not unknown, str(sorted(unknown)))
    wheel_ids = set(evidence["passed_tests"])
    check(
        "passed_tests equals my derivation",
        wheel_ids == passed,
        f"only in wheel {sorted(wheel_ids - passed)}, only in mine {sorted(passed - wheel_ids)}",
    )
    check("passed_tests is sorted", evidence["passed_tests"] == sorted(evidence["passed_tests"]), "")
    diff_realised = {i for i in passed if evidence["realised_by"].get(i) != realised[i]}
    check(
        "realised_by equals my carrier lists",
        not diff_realised and set(evidence["realised_by"]) == passed,
        f"differing ids {sorted(diff_realised)}",
    )

    init_text = (args.site_embodic / "__init__.py").read_text()
    version_line = next(line for line in init_text.splitlines() if line.startswith("__version__"))
    installed_version = version_line.split("=", 1)[1].strip().strip("\"'")
    check(
        "embodic_version",
        evidence["embodic_version"] == installed_version,
        f"file {evidence['embodic_version']!r}, installed __init__ {installed_version!r}",
    )

    folder = args.site_embodic / "_resources/evidence"
    manifest = json.loads((folder / "manifest.v1.json").read_text())
    own = [hashlib.sha256((folder / n).read_bytes()).hexdigest() for n in ("equations.v1.json", "evidence.v1.json")]
    listed = [manifest["files"][n]["copy_sha256"] for n in ("equations.v1.json", "evidence.v1.json")]
    check("manifest copy_sha256 equals the shipped files", own == listed, f"own {own}, manifest {listed}")
    my_registry_version = f"v1+{own[0][:12]}.{own[1][:12]}"
    check(
        "registry_version",
        evidence["registry_version"] == my_registry_version,
        f"file {evidence['registry_version']!r}, mine {my_registry_version!r}",
    )

    check("gate_profile", evidence["gate_profile"] == "release", repr(evidence["gate_profile"]))
    stamp = evidence["generated_utc"].replace("-", "").replace(":", "")
    my_build_id = f"{evidence['embodic_version']}+g{evidence['git_commit'][:12]}.{stamp}"
    check(
        "build_id format", evidence["build_id"] == my_build_id, f"file {evidence['build_id']!r}, mine {my_build_id!r}"
    )

    site_hash, site_count = my_source_sha256(args.site_embodic)
    check(
        "source_sha256 vs installed package",
        evidence["source_sha256"] == site_hash,
        f"file {evidence['source_sha256']}, mine {site_hash} over {site_count} files",
    )
    if args.src is not None:
        src_hash, src_count = my_source_sha256(args.src)
        check(
            "source_sha256 vs release source tree",
            evidence["source_sha256"] == src_hash,
            f"mine {src_hash} over {src_count} files",
        )

    print(f"{len(failures)} failed checks: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
