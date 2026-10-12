"""Check that every quote in dependency_licences.md section "M5 distribution" occurs in the source it names.

Rerun from the repository root: python3 docs/phase2/evidence/tools/check_m5_licence_quotes.py [--wheels]

Reads the table rows `| Q<n> | <source id> | <section> | "<quote>" |` of the section "Quoted requirements". Each source is
fetched or read and checked against its SHA-256. A quote matches when its fragments, split at `...`, occur in order after
whitespace and quotation marks are normalised. The script then lists every backticked `.venv/` and `resources/` path of the
section "Text sources for THIRD_PARTY_LICENSES.md" with its size and SHA-256 and fails on a missing path.
`--wheels` also reads two members of the Windows wheels on PyPI with HTTP range requests (slower, can time out).
Environment: EMBODIC_VENV names the virtual environment that holds the `.venv/` paths (default /home/claude/embodic/.venv).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from check_dependency_licences import HttpRangeFile  # noqa: E402

ROOT = HERE.parents[3]
DOC = HERE.parent / "dependency_licences.md"
SNAPSHOT = HERE.parent / "dependency_licences.snapshot.json"
VENV = Path(os.environ.get("EMBODIC_VENV", "/home/claude/embodic/.venv"))
SITE = VENV / "lib/python3.11/site-packages"
SPDX = "https://raw.githubusercontent.com/spdx/license-list-data/main/text/"
QT = "https://raw.githubusercontent.com/qt/qtbase/v6.11.2/LICENSES/"

# id -> (location, expected SHA-256). A location starting with http is fetched, anything else is a file path.
SOURCES: dict[str, tuple[str, str]] = {
    "lgpl3-qtbase": (QT + "LGPL-3.0-only.txt", "da7eabb7bafdf7d3ae5e9f223aa5bdc1eece45ac569dc21b3b037520b4464768"),
    "lgpl3-spdx": (SPDX + "LGPL-3.0-only.txt", "996af0513df21f7496288951c41428a03c174e9e4a9d63665c57d670f845ccb1"),
    "gpl3-spdx": (SPDX + "GPL-3.0-only.txt", "fb981668c18a279e285fc4d83fba1e836cc84dd4daa73c9697d3cfd2d8aca6e0"),
    "mit-spdx": (SPDX + "MIT.txt", "b05785f9f18e6716bab63424b11454513b9943a222595b70411009202fc592b5"),
    "apache2-spdx": (SPDX + "Apache-2.0.txt", "074e6e32c86a4c0ef8b3ed25b721ca23aca83df277cd88106ef7177c354615ff"),
    "pyside-metadata": (str(SITE / "pyside6_essentials-6.11.2.dist-info/METADATA"),
                        "a4e0d97dfc9aeb7f65f42c05281fdc0372297a95d1a3e498df14806729644677"),
    "pyside-qtcore-pyi": (str(SITE / "PySide6/QtCore.pyi"),
                          "439e2bd3f6f8576faf7ef86d6ec008a14fa2c2e7be66ed355d15d5f80f28c52e"),
    "numpy-licence-linux": (str(SITE / "numpy-2.4.6.dist-info/licenses/LICENSE.txt"),
                            "4860083caa0de2ac3292ca98bd074bd8f45d8b32624e37b1e70a240bff61e488"),
    "psf-cpython-linux": ("/usr/lib/python3.11/LICENSE.txt",
                          "3b2f81fe21d181c499c59a256c8e1968455d6689d269aa85373bfb6af41da3bf"),
    "ofl-inter": (str(ROOT / "resources/fonts/Inter/LICENSE.txt"),
                  "262481e844521b326f5ecd053e59b98c8b2da78c8ee1bdbb6e8174305e54935a"),
    "qt-qglobal-h": ("https://raw.githubusercontent.com/qt/qtbase/v6.11.2/src/corelib/global/qglobal.h",
                     "701afb76d34526593d7bd128219f2db5abccd029cdba7b9e115305c3cd558aac"),
}
# id -> (wheel name in the snapshot, member, expected SHA-256); read only with --wheels.
WHEEL_SOURCES: dict[str, tuple[str, str, str]] = {
    "qt-commercial-win": ("PySide6-Essentials", "pyside6_essentials-6.11.2.dist-info/licenses/LicenseRef-Qt-Commercial.txt",
                          "4f54763ac0fe2abd8f7f8d8fe370a94a08ebf84786aa0b91045bd6628deb08a3"),
    "numpy-licence-win": ("numpy", "numpy-2.4.6.dist-info/licenses/LICENSE.txt",
                          "a804dff0ead9fadc5293456410bcbfc32bf024be9c4513459663fb7b442d2341"),
}


def normalise(text: str) -> str:
    table = str.maketrans({"\u201c": '"', "\u201d": '"', "\u2018": "'", "\u2019": "'", "\u00a9": "(c)"})
    return re.sub(r"\s+", " ", text.translate(table)).strip()


def fetch(url: str) -> bytes:
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                return resp.read()
        except Exception as exc:  # network flake: retry, then fail loudly
            if attempt == 3:
                raise SystemExit(f"cannot fetch {url}: {exc}") from exc
            time.sleep(2)
    raise AssertionError("unreachable")


def load_sources(with_wheels: bool) -> dict[str, str]:
    texts: dict[str, str] = {}
    for sid, (loc, want) in SOURCES.items():
        data = fetch(loc) if loc.startswith("http") else Path(loc).read_bytes()
        got = hashlib.sha256(data).hexdigest()
        if got != want:
            raise SystemExit(f"{sid}: SHA-256 {got} differs from the recorded {want} ({loc})")
        texts[sid] = normalise(data.decode("utf-8", "replace"))
        print(f"source {sid}: {len(data)} bytes, sha256 matches, {loc}")
    if with_wheels:
        snap = {r["name"]: r for r in json.loads(SNAPSHOT.read_text())["packages"]}
        for sid, (pkg, member, want) in WHEEL_SOURCES.items():
            for attempt in range(4):
                try:
                    data = zipfile.ZipFile(HttpRangeFile(snap[pkg]["wheel_url"])).read(member)
                    break
                except Exception as exc:
                    if attempt == 3:
                        raise SystemExit(f"cannot read {member} from the {pkg} wheel: {exc}") from exc
                    time.sleep(2)
            got = hashlib.sha256(data).hexdigest()
            if got != want:
                raise SystemExit(f"{sid}: SHA-256 {got} differs from the recorded {want}")
            texts[sid] = normalise(data.decode("utf-8", "replace"))
            print(f"source {sid}: {len(data)} bytes, sha256 matches, {snap[pkg]['wheel']}:{member}")
    return texts


def section(md: str, heading: str) -> str:
    match = re.search(rf"^#+ {re.escape(heading)}\n(.*?)(?=^#+ |\Z)", md, re.M | re.S)
    if not match:
        raise SystemExit(f"heading not found in {DOC.name}: {heading}")
    return match.group(1)


def check_quotes(md: str, texts: dict[str, str]) -> int:
    rows = re.findall(r'^\| (Q\d+) \| (\S+) \| ([^|]+) \| "(.*)" \|$', section(md, "Quoted requirements"), re.M)
    if not rows:
        raise SystemExit("no quote rows found")
    failures = 0
    for qid, sid, where, quote in rows:
        if sid not in texts:
            print(f"{qid}: skipped, source {sid} needs --wheels")
            continue
        pos, ok = 0, True
        for fragment in (normalise(f) for f in quote.split("...")):
            hit = texts[sid].find(fragment, pos)
            if hit < 0:
                ok = False
                print(f"{qid}: FAIL, fragment not found after offset {pos} in {sid}: {fragment[:90]!r}")
                break
            pos = hit + len(fragment)
        failures += not ok
        if ok:
            print(f"{qid}: ok, {sid} {where.strip()}")
    print(f"{len(rows)} quote rows, {failures} failed")
    return failures


def check_paths(md: str) -> int:
    body = section(md, "Text sources for THIRD_PARTY_LICENSES.md")
    paths = sorted(set(re.findall(r"`((?:\.venv|resources)/[^`\s]+)`", body)))
    missing, shown = 0, 0
    for rel in paths:
        path = VENV / rel.removeprefix(".venv/") if rel.startswith(".venv/") else ROOT / rel
        if path.is_dir():
            files = sorted(f for f in path.rglob("*") if f.is_file())
            missing += not files
        elif path.is_file():
            files = [path]
        else:
            missing += 1
            print(f"MISSING {rel}")
            continue
        for f in files:
            shown += 1
            label = rel if f == path else rel + str(f.relative_to(path))
            print(f"{f.stat().st_size:>8} {hashlib.sha256(f.read_bytes()).hexdigest()[:16]} {label}")
    print(f"{len(paths)} paths ({shown} files), {missing} missing")
    return missing


def main() -> None:
    md = DOC.read_text()
    texts = load_sources("--wheels" in sys.argv)
    bad = check_quotes(md, texts) + check_paths(md)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
