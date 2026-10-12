"""Read-only check of the Linux PyInstaller folder: frozen selftest and the licence files (package_layout.md §5.1).

Usage: python3.11 -I bundle_check.py --folder /home/claude/wt/U-M5c/build/bundle/embodic --cwd SCRATCH_DIR

The folder is never written: the selftest runs with its working directory outside it, and the script compares the
folder's file list and sizes before and after.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path

EXPECTED_FILES = [
    "THIRD_PARTY_LICENSES.md",
    "licenses/LGPL-3.0.txt",
    "licenses/GPL-3.0.txt",
    "licenses/PYTHON-LICENSE.txt",
    "licenses/numpy",
    "_internal/embodic/_resources/fonts/Inter/LICENSE.txt",
    "_internal/embodic/_resources/fonts/JetBrainsMono/OFL.txt",
    "_internal/embodic/_resources/fonts/FONTS.md",
    "source/embodic-0.0.1.tar.gz",
]
EXPECTED_ABSENT = ["SOURCE.md", "LICENSE", "LICENSE.txt", "licenses/qt-third-party"]


def snapshot(folder: Path) -> dict[str, int]:
    """Map each regular file below folder (symlinks not followed) to its size."""
    return {
        str(p.relative_to(folder)): p.stat().st_size for p in folder.rglob("*") if p.is_file() and not p.is_symlink()
    }


def main() -> int:
    """List the licence files, run the frozen selftest, confirm the folder did not change."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", type=Path, required=True)
    parser.add_argument("--cwd", type=Path, required=True)
    args = parser.parse_args()
    before = snapshot(args.folder)
    print(
        f"files before: {len(before)}, {sum(before.values()) / 1e6:.1f} MB, .py files: "
        f"{sum(1 for k in before if k.endswith('.py'))}"
    )
    for rel in EXPECTED_FILES + EXPECTED_ABSENT:
        path = args.folder / rel
        if path.is_dir():
            files = [p for p in path.rglob("*") if p.is_file()]
            print(f"present  {rel}/ ({len(files)} files, {sum(p.stat().st_size for p in files)} bytes)")
        elif path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            print(f"present  {rel} ({path.stat().st_size} bytes, sha256 {digest[:8]}...{digest[-4:]})")
        else:
            print(f"absent   {rel}")
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    proc = subprocess.run(
        [str(args.folder / "embodic-cli"), "selftest"],
        cwd=args.cwd,
        capture_output=True,
        text=True,
        env=env,
        timeout=600,
    )
    lines = proc.stdout.strip().splitlines()
    failed = [line for line in lines if not line.startswith("passed")][:-1]
    print(f"frozen selftest exit {proc.returncode}: {lines[-1] if lines else proc.stderr[-300:]}")
    for line in failed:
        print(f"  {line}")
    after = snapshot(args.folder)
    print(f"folder unchanged by the run: {after == before}")
    return 0 if proc.returncode == 0 and after == before else 1


if __name__ == "__main__":
    sys.exit(main())
