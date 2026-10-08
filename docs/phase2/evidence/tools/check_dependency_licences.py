"""Query PyPI for every planned dependency and regenerate the table in dependency_licences.md.

Rerun: python3 docs/phase2/evidence/tools/check_dependency_licences.py
Fails before any network call when pyproject.toml declares a requirement that PACKAGES lacks; `--coverage` runs only that check.
Writes dependency_licences.snapshot.json and rewrites the block between the GENERATED markers.
"""

from __future__ import annotations

import datetime as dt
import io
import json
import re
import sys
import tomllib
import urllib.request
import zipfile
from pathlib import Path

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import InvalidVersion, Version

HERE = Path(__file__).resolve().parent.parent
PYPROJECT = HERE.parents[2] / "pyproject.toml"
SNAPSHOT = HERE / "dependency_licences.snapshot.json"
DOC = HERE / "dependency_licences.md"
PYTHON_FLOOR = "3.11.0"
BEGIN = "<!-- BEGIN GENERATED: tools/check_dependency_licences.py -->"
END = "<!-- END GENERATED -->"

# (pypi name, scope, shipped with embodic?)
# scope: runtime = imported by the app; build = makes the one-folder bundle; test/dev = never shipped.
PACKAGES: list[tuple[str, str, str]] = [
    ("numpy", "runtime (core)", "yes"),
    ("PySide6-Essentials", "runtime (desktop extra)", "yes"),
    ("shiboken6", "runtime (required by PySide6-Essentials)", "yes"),
    ("pyinstaller", "build (D-015 stretch goal)", "bootloader only"),
    ("pyinstaller-hooks-contrib", "build (required by pyinstaller)", "no"),
    ("pytest", "test", "no"),
    ("pytest-qt", "test (desktop)", "no"),
    ("pytest-cov", "test (ADR-0008)", "no"),
    ("pytest-timeout", "test (pyproject dev, hang guard)", "no"),
    ("hypothesis", "test (ADR-0008)", "no"),
    ("jsonschema", "test (ADR-0008)", "no"),
    ("ezdxf", "test (ADR-0008, DXF parser)", "no"),
    ("pypdf", "test (ADR-0008, PDF parser)", "no"),
    ("fonttools", "test (pyproject dev, U-M4f font reader oracle)", "no"),
    ("ruff", "dev", "no"),
    ("import-linter", "dev", "no"),
    ("mypy", "dev (ADR-0008)", "no"),
    ("hatchling", "build backend (pyproject build-system and dev)", "no"),
    ("pip-licenses", "dev (ADR-0008 licence gate)", "no"),
    ("pip-audit", "dev (ADR-0008 CVE gate)", "no"),
]


def norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def pyproject_requirements() -> dict[str, SpecifierSet]:
    """Version range pyproject.toml gives each requirement (build, runtime and every extra), by normalised name."""
    data = tomllib.loads(PYPROJECT.read_text())
    specs = [*data["build-system"]["requires"], *data["project"].get("dependencies", [])]
    for extra in data["project"].get("optional-dependencies", {}).values():
        specs.extend(extra)
    parsed = [Requirement(spec) for spec in specs]
    return {norm(r.name): r.specifier for r in parsed}


def undocumented_requirements() -> list[str]:
    """Requirements in pyproject.toml that PACKAGES does not list. The `embodic` self-reference is skipped."""
    listed = {norm(name) for name, _, _ in PACKAGES}
    return sorted(set(pyproject_requirements()) - listed - {"embodic"})


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as resp:
        return json.load(resp)


def get_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=60) as resp:
        return resp.read().decode("utf-8", "replace")


def admits_floor(requires_python: str | None) -> bool:
    if not requires_python:
        return True
    try:
        return SpecifierSet(requires_python).contains(PYTHON_FLOOR)
    except Exception:
        return False


def newest_for_floor(project: dict, allowed: SpecifierSet) -> tuple[str, str]:
    """Return (newest final version admitting the floor and inside the pyproject range, newest final overall)."""
    finals: list[tuple[Version, str, str | None]] = []
    for ver, files in project["releases"].items():
        try:
            v = Version(ver)
        except InvalidVersion:
            continue
        live = [f for f in files if not f.get("yanked")]
        if v.is_prerelease or v.is_devrelease or not live:
            continue
        finals.append((v, ver, live[0].get("requires_python")))
    finals.sort()
    newest = finals[-1][1]
    for v, ver, req in reversed(finals):
        if admits_floor(req) and allowed.contains(v):
            return ver, newest
    return "none", newest


class HttpRangeFile(io.RawIOBase):
    """Seekable read-only view of a remote file, so zipfile can list a wheel without downloading it."""

    def __init__(self, url: str) -> None:
        self.url, self.pos = url, 0
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=60) as resp:
            self.size = int(resp.headers["Content-Length"])

    def seekable(self) -> bool:
        return True

    def readable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.pos

    def seek(self, offset: int, whence: int = 0) -> int:
        self.pos = {0: offset, 1: self.pos + offset, 2: self.size + offset}[whence]
        return self.pos

    def read(self, n: int = -1) -> bytes:
        end = self.size if n < 0 else min(self.size, self.pos + n)
        if end <= self.pos:
            return b""
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-{end - 1}"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
        self.pos += len(data)
        return data


def pick_wheel(release: dict) -> dict | None:
    """Prefer the Windows CPython 3.11 wheel (primary target), then a pure wheel, then any wheel."""
    wheels = [u for u in release["urls"] if u["packagetype"] == "bdist_wheel"]
    for want in ("cp311-win_amd64", "abi3-win_amd64", "py3-none-any", "win_amd64"):
        hit = [w for w in wheels if want in w["filename"]]
        if hit:
            return hit[0]
    return wheels[0] if wheels else None


def shipped_notice_files(wheel_url: str) -> list[str]:
    names = zipfile.ZipFile(HttpRangeFile(wheel_url)).namelist()
    pattern = re.compile(r"(licen[cs]e|copying|notice|third.?party|lgpl|gpl)", re.I)
    binary = (".dll", ".pyd", ".so", ".dylib", ".exe")
    return sorted(n for n in names if pattern.search(n.rsplit("/", 1)[-1]) and not n.lower().endswith(binary))


def wheel_member_text(wheel_url: str, suffix: str) -> str:
    zf = zipfile.ZipFile(HttpRangeFile(wheel_url))
    name = next(n for n in zf.namelist() if n.endswith(suffix))
    return zf.read(name).decode("utf-8", "replace")


def wheel_metadata(release: dict) -> dict:
    """License-Expression and License-File lines from the PEP 658 .metadata of the chosen wheel."""
    wheel = pick_wheel(release)
    if wheel is None:
        return {"wheel": None, "metadata_url": None, "license_expression": None, "license_files": []}
    url = wheel["url"] + ".metadata"
    try:
        text = get_text(url)
    except Exception as exc:  # recorded, not hidden: the row then says "not accessed"
        return {"metadata_url": url, "error": str(exc), "license_expression": None, "license_files": []}
    headers = text.replace("\r", "").split("\n\n", 1)[0]
    expr = re.findall(r"^License-Expression: (.+)$", headers, re.M)
    files = re.findall(r"^License-File: (.+)$", headers, re.M)
    return {"wheel": wheel["filename"], "wheel_url": wheel["url"], "metadata_url": url,
            "license_expression": expr[0] if expr else None, "license_files": files}


def allowed_range(name: str, earlier: list[dict]) -> SpecifierSet:
    """The pyproject range, else the range an already-checked package pins it to (shiboken6 follows PySide6)."""
    declared = pyproject_requirements()
    if norm(name) in declared:
        return declared[norm(name)]
    for row in earlier:
        for dist in row["requires_dist"]:
            req = Requirement(dist)
            if norm(req.name) == norm(name) and req.marker is None:
                return req.specifier
    return SpecifierSet()


def check(name: str, earlier: list[dict]) -> dict:
    project = get_json(f"https://pypi.org/pypi/{name}/json")
    pin, newest = newest_for_floor(project, allowed_range(name, earlier))
    release = get_json(f"https://pypi.org/pypi/{name}/{pin}/json")
    info = release["info"]
    licence_classifiers = [c.split(" :: ", 2)[-1] for c in info.get("classifiers", []) if c.startswith("License ::")]
    return {
        "name": info["name"],
        "pin": pin,
        "newest_overall": newest,
        "requires_python": info.get("requires_python"),
        "license_expression_json": info.get("license_expression"),
        "license_field": (info.get("license") or "")[:200] or None,
        "license_classifiers": licence_classifiers,
        "requires_dist": info.get("requires_dist") or [],
        "pypi_url": f"https://pypi.org/project/{info['name']}/{pin}/",
        **wheel_metadata(release),
    }


def declared_licence(row: dict) -> str:
    for key in ("license_expression", "license_expression_json"):
        if row.get(key):
            return row[key]
    if row["license_field"] and len(row["license_field"]) < 80:
        return row["license_field"]
    return "; ".join(row["license_classifiers"]) or "not stated"


def table(rows: list[dict], scopes: dict[str, tuple[str, str]], accessed: str) -> str:
    lines = [
        f"PyPI JSON API and wheel `.metadata` files, accessed {accessed}. Pin = newest final release whose "
        f"`Requires-Python` admits {PYTHON_FLOOR} (the user's minimum) and that lies inside the version range "
        f"`pyproject.toml` declares.",
        "",
        "| Package | Pin (3.11 floor) | Newest overall | Declared licence (PyPI metadata) | `License-File` entries | Scope | Shipped | Status |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        scope, shipped = scopes[r["name"].lower()]
        files = f"{len(r['license_files'])} files (snapshot JSON)" if len(r["license_files"]) > 3 else (
            ", ".join(f"`{f}`" for f in r["license_files"]) or "none declared")
        status = "verified (PyPI metadata)" if "error" not in r else "verified (PyPI JSON); wheel metadata not accessed"
        lines.append(
            f"| [{r['name']}]({r['pypi_url']}) | {r['pin']} | {r['newest_overall']} | {declared_licence(r)} | "
            f"{files} | {scope} | {shipped} | {status} |"
        )
    return "\n".join(lines)


def main() -> None:
    missing = undocumented_requirements()
    if missing:
        raise SystemExit(f"pyproject.toml requirements missing from PACKAGES: {missing}")
    if "--coverage" in sys.argv:
        print("every pyproject.toml requirement is listed in PACKAGES")
        return
    accessed = dt.date.today().isoformat()
    rows: list[dict] = []
    for name, _, _ in PACKAGES:
        rows.append(check(name, rows))
    scopes = {name.lower(): (scope, shipped) for name, scope, shipped in PACKAGES}
    for r in rows:
        if scopes[r["name"].lower()][1] != "no" and r.get("wheel_url"):
            r["notice_files_in_wheel"] = shipped_notice_files(r["wheel_url"])
        if r["name"].lower() == "pyinstaller":
            text = wheel_member_text(r["wheel_url"], ".dist-info/licenses/COPYING.txt")
            r["bootloader_exception_excerpt"] = re.search(
                r"Bootloader Exception.{0,900}", text, re.S).group(0) if "Bootloader Exception" in text else None
    SNAPSHOT.write_text(json.dumps({"accessed": accessed, "python_floor": PYTHON_FLOOR, "packages": rows},
                                   indent=2, ensure_ascii=True) + "\n")
    doc = DOC.read_text()
    start, stop = doc.index(BEGIN) + len(BEGIN), doc.index(END)
    DOC.write_text(doc[:start] + "\n" + table(rows, scopes, accessed) + "\n" + doc[stop:])
    for r in rows:
        print(f"{r['name']:28} pin={r['pin']:10} newest={r['newest_overall']:10} licence={declared_licence(r)} "
              f"files={r['license_files']}")


if __name__ == "__main__":
    main()
