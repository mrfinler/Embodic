"""V3-09: check that each pin of a lock file has a hashed Windows x64 wheel that CPython 3.11 can load.

    python3 docs/phase3/verification/checks/lock_windows_check.py requirements/py311.txt requirements/py311-dev.txt

It reads the file list of each pinned release from PyPI's JSON API (https://pypi.org/pypi/<name>/<version>/json) and
accepts a wheel tagged for win_amd64 or any platform whose Python tag CPython 3.11 can load (cp311, cpXY-abi3 with
XY <= 311, py3, py2.py3). A pin with no such wheel would make pip build from the sdist on Windows; a pin whose wheel
hash is missing makes `pip install --require-hashes` stop. Exit 1 when any pin fails either way.
"""

import json
import os
import re
import ssl
import sys
import urllib.request
from pathlib import Path

PIN = re.compile(r"^([A-Za-z0-9_.-]+)==([^\s;\\]+)")
HASH = re.compile(r"--hash=sha256:([0-9a-f]{64})")


def parse_lock(text: str) -> dict[tuple[str, str], set[str]]:
    """Return (name, version) -> the SHA-256 values the lock file lists for that pin."""
    pins: dict[tuple[str, str], set[str]] = {}
    current = None
    for line in text.splitlines():
        if match := PIN.match(line):
            current = (match.group(1), match.group(2))
            pins[current] = set()
        if current is not None:
            pins[current].update(HASH.findall(line))
    return pins


def loads_on_cp311_win_amd64(filename: str) -> bool:
    """Return True for a wheel file name that pip on CPython 3.11, Windows x64, would accept."""
    if not filename.endswith(".whl"):
        return False
    python_tag, abi_tag, platform_tag = filename[:-4].split("-")[-3:]
    if not set(platform_tag.split(".")) & {"win_amd64", "any"}:
        return False
    for tag in python_tag.split("."):
        if tag in ("cp311", "py3", "py311") or (tag == "py2" and "py3" in python_tag):
            return abi_tag in ("cp311", "none", "abi3")
        if abi_tag == "abi3" and tag.startswith("cp3") and int(tag[3:]) <= 11:
            return True
    return False


def main(argv: list[str]) -> int:
    """Print one verdict per pin and return 1 when any pin fails."""
    proxy_ca = Path("/root/.ccr/ca-bundle.crt")
    cafile = os.environ.get("SSL_CERT_FILE") or (str(proxy_ca) if proxy_ca.exists() else None)
    context = ssl.create_default_context(cafile=cafile)
    failed = False
    for lock in argv:
        pins = parse_lock(Path(lock).read_text(encoding="utf-8"))
        print(f"{lock}: {len(pins)} pins")
        for (name, version), hashes in sorted(pins.items()):
            url = f"https://pypi.org/pypi/{name}/{version}/json"
            with urllib.request.urlopen(url, context=context, timeout=30) as response:
                files = json.load(response)["urls"]
            wheels = [f for f in files if loads_on_cp311_win_amd64(f["filename"])]
            hashed = [f["filename"] for f in wheels if f["digests"]["sha256"] in hashes]
            verdict = "pass" if hashed else ("FAIL no Windows wheel" if not wheels else "FAIL hash not in lock")
            failed |= not hashed
            print(f"  {verdict:<24} {name}=={version}  {hashed[0] if hashed else ''}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
