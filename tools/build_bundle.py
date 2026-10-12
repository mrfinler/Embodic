"""Build the PyInstaller one-folder bundle of embodic at build/bundle/embodic (package_layout.md section 5.2).

Usage, with the Python 3.11+ whose lock file the bundle should use::

    python tools/build_bundle.py

The steps: create the scratch venv `.venv-bundle` when it lacks the build tools (the hashed lock file, embodic in
editable mode, PyInstaller and hatchling), run PyInstaller on `packaging/pyinstaller/embodic.spec`, add the licence
files and embodic's source distribution, then check the real folder. The check prints the licence checklist and the
Qt library listing of dependency_licences.md R10 and exits 1 when a shipped row is missing or a Qt library is not a
separate file. `build/bundle-work` is removed afterwards; `build/bundle` stays.
"""

import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / ".venv-bundle"
VENV_PYTHON = VENV / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
LOCK_FILE = ROOT / "requirements" / f"py3{sys.version_info.minor}.txt"
PYINSTALLER_VERSION = "6.22.3"
BUILD_TOOLS = (f"pyinstaller=={PYINSTALLER_VERSION}", "hatchling==1.32.4")
SPEC = ROOT / "packaging" / "pyinstaller" / "embodic.spec"
FETCHED_DIR = ROOT / "packaging" / "pyinstaller" / "licenses"
DIST = ROOT / "build" / "bundle"
WORK = ROOT / "build" / "bundle-work"
FOLDER = DIST / "embodic"
RESOURCES = "_internal/embodic/_resources"
QT_LIBRARIES = ("Core", "Gui", "Widgets", "Svg")
SDIST_MEMBERS = ("packaging/pyinstaller/embodic.spec", "tools/build_bundle.py", "src/embodic/__init__.py")


@dataclass(frozen=True, slots=True, kw_only=True)
class FetchedText:
    """A licence text committed under packaging/pyinstaller/licenses, with the URL and hash it was fetched with."""

    name: str
    url: str
    sha256: str


# Fetched 2026-10-12 16:03 UTC; both hashes equal Agent 5's in dependency_licences.md (text sources table).
FETCHED = (
    FetchedText(
        name="LGPL-3.0.txt",
        url="https://raw.githubusercontent.com/qt/qtbase/v6.11.2/LICENSES/LGPL-3.0-only.txt",
        sha256="da7eabb7bafdf7d3ae5e9f223aa5bdc1eece45ac569dc21b3b037520b4464768",
    ),
    FetchedText(
        name="GPL-3.0.txt",
        url="https://raw.githubusercontent.com/qt/qtbase/v6.11.2/LICENSES/GPL-3.0-only.txt",
        sha256="8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b165a1dcd80c7c545eb65b903",
    ),
)


@dataclass(frozen=True, slots=True, kw_only=True)
class Shipped:
    """A file, or a non-empty folder, the bundle must carry; path is relative to the bundle folder."""

    path: str
    why: str


@dataclass(frozen=True, slots=True, kw_only=True)
class Absent:
    """An item the bundle should carry but this build cannot supply."""

    item: str
    reason: str


CHECKLIST: tuple[Shipped | Absent, ...] = (
    Shipped(path="THIRD_PARTY_LICENSES.md", why="REQ-N-19 and the LGPL-3.0 4 a) notice (R2)"),
    Shipped(path="licenses/LGPL-3.0.txt", why="LGPL-3.0 4 b) (R3)"),
    Shipped(path="licenses/GPL-3.0.txt", why="LGPL-3.0 4 b) (R3)"),
    Shipped(path="licenses/numpy", why="BSD-3-Clause binary clause (Q28) and the notices of the bundled code"),
    Shipped(path="licenses/PYTHON-LICENSE.txt", why="PSF License Agreement section 2 (Q29)"),
    Shipped(path=f"{RESOURCES}/fonts/Inter/LICENSE.txt", why="OFL condition 2 beside the Inter files (Q30)"),
    Shipped(path=f"{RESOURCES}/fonts/JetBrainsMono/OFL.txt", why="OFL condition 2 beside the JetBrains Mono files"),
    Shipped(path="source", why="LGPL-3.0 4 d) 0: embodic's sdist with the spec and this script (R5, R7)"),
    Absent(
        item="written offer for the Qt 6.11.2 and PySide6 6.11.2 source",
        reason="who makes the offer is a user decision (dependency_licences.md R5, R6)",
    ),
    Absent(
        item="Qt third-party notices for the bundled modules",
        reason="https://doc.qt.io/qt-6/licenses-used-in-qt.html was refused by the proxy; the list is unresolved",
    ),
    Absent(item="embodic's own licence file", reason="the user has not chosen embodic's licence (D-015)"),
)

# Runs inside the build venv: where its NumPy licence files and its Python licence are, and the tool versions.
PROBE = """
import importlib.metadata as md, json, sys, sysconfig
from pathlib import Path
numpy = md.distribution("numpy")
candidates = [Path(sysconfig.get_path("stdlib")) / "LICENSE.txt", Path(sys.base_prefix) / "LICENSE.txt"]
print(json.dumps({
    "numpy_licences": {
        "/".join(f.parts[2:]): str(numpy.locate_file(f)) for f in numpy.files if f.parts[1:2] == ("licenses",)
    },
    "python_licence": next((str(p) for p in candidates if p.is_file()), None),
    "versions": {d: md.version(d) for d in ("pyinstaller", "pyinstaller-hooks-contrib", "PySide6-Essentials", "numpy")},
    "python": sys.version.split()[0],
}))
"""


@dataclass(frozen=True, slots=True, kw_only=True)
class BuildVenv:
    """What the build venv reports about itself."""

    numpy_licences: dict[str, Path]  # path below the dist-info's licenses/ folder -> installed file
    python_licence: Path
    versions: dict[str, str]
    python: str


def run(command: list[str | Path]) -> None:
    """Run a command from the repository root and stop the build when it fails."""
    print("$", " ".join(str(part) for part in command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def build_venv_ready() -> bool:
    """Return True when the scratch venv imports the build tools at the pinned PyInstaller version."""
    if not VENV_PYTHON.is_file():
        return False
    probe = "import PyInstaller, hatchling, PySide6, embodic; print(PyInstaller.__version__)"
    result = subprocess.run([VENV_PYTHON, "-c", probe], capture_output=True, text=True)
    return result.returncode == 0 and result.stdout.strip() == PYINSTALLER_VERSION


def ensure_build_venv() -> None:
    """Create or complete .venv-bundle; the project venv is never touched."""
    if build_venv_ready():
        return
    if not VENV_PYTHON.is_file():
        run([sys.executable, "-m", "venv", VENV])
    pip: list[str | Path] = [VENV_PYTHON, "-m", "pip", "install", "--disable-pip-version-check", "-q"]
    run([*pip, "--require-hashes", "-r", LOCK_FILE])
    run([*pip, "--no-deps", "-e", ROOT])
    run([*pip, *BUILD_TOOLS])


def probe_build_venv() -> BuildVenv:
    """Ask the build venv for its licence files and versions; stop when its Python ships no licence text."""
    raw = json.loads(subprocess.run([VENV_PYTHON, "-c", PROBE], capture_output=True, text=True, check=True).stdout)
    if raw["python_licence"] is None:
        raise SystemExit("the Python that runs PyInstaller has no LICENSE.txt in its stdlib or base folder")
    return BuildVenv(
        numpy_licences={relative: Path(path) for relative, path in raw["numpy_licences"].items()},
        python_licence=Path(raw["python_licence"]),
        versions=raw["versions"],
        python=raw["python"],
    )


def sha256_of(path: Path) -> str:
    """Return the hex SHA-256 of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_into_folder(source: Path, relative: str) -> None:
    """Copy one file to a path relative to the bundle folder."""
    target = FOLDER / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def add_licences(venv: BuildVenv) -> None:
    """Copy the licence texts into the bundle folder; a committed text whose hash drifted stops the build."""
    for text in FETCHED:
        source = FETCHED_DIR / text.name
        if sha256_of(source) != text.sha256:
            raise SystemExit(f"{source} no longer has the SHA-256 it was fetched with from {text.url}")
        copy_into_folder(source, f"licenses/{text.name}")
    for relative, source in venv.numpy_licences.items():
        copy_into_folder(source, f"licenses/numpy/{relative}")
    copy_into_folder(venv.python_licence, "licenses/PYTHON-LICENSE.txt")
    copy_into_folder(ROOT / "THIRD_PARTY_LICENSES.md", "THIRD_PARTY_LICENSES.md")


def files_below(path: Path) -> list[Path]:
    """Return the regular files at or below path, symlinks excluded so that nothing counts twice."""
    if path.is_file():
        return [path]
    return sorted(p for p in path.rglob("*") if p.is_file() and not p.is_symlink())


def checklist_ok() -> bool:
    """Print each checklist row as present, MISSING or absent from the real folder; True when nothing is missing."""
    ok = True
    for row in CHECKLIST:
        if isinstance(row, Absent):
            print(f"  absent   {row.item}: {row.reason}")
            continue
        found = files_below(FOLDER / row.path) if (FOLDER / row.path).exists() else []
        ok = ok and bool(found)
        size = sum(p.stat().st_size for p in found)
        state = "present" if found else "MISSING"
        print(f"  {state:8} {row.path} ({len(found)} files, {size} bytes): {row.why}")
    return ok


def source_ok() -> bool:
    """Print the members the source distribution must hold to rebuild this folder; True when it holds them all."""
    archives = sorted((FOLDER / "source").glob("embodic-*.tar.gz"))
    if len(archives) != 1:
        print(f"  expected one embodic sdist in source/, found {[a.name for a in archives]}")
        return False
    with tarfile.open(archives[0]) as archive:
        names = {name.split("/", 1)[1] for name in archive.getnames() if "/" in name}
    for member in SDIST_MEMBERS:
        print(f"  {archives[0].name} holds {member}: {'yes' if member in names else 'NO'}")
    return all(member in names for member in SDIST_MEMBERS)


def qt_libraries_ok() -> bool:
    """Print the Qt libraries found as separate files (R10); True when each of QT_LIBRARIES has one."""
    ok = True
    for name in QT_LIBRARIES:
        found = [p for p in FOLDER.rglob(f"*Qt6{name}.*") if p.is_file() and not p.is_symlink()]
        ok = ok and bool(found)
        for path in found or [Path(f"no file for Qt6{name}")]:
            size = path.stat().st_size if path.is_file() else 0
            print(f"  Qt6{name:8} {path.relative_to(FOLDER) if found else path} {size} bytes")
    return ok


def summarise() -> None:
    """Print the executables, the folder size and the .py files the folder holds."""
    for name in ("embodic", "embodic-cli", "embodic.exe", "embodic-cli.exe"):
        if (FOLDER / name).is_file():
            print(f"  executable {name}: {(FOLDER / name).stat().st_size} bytes")
    every = files_below(FOLDER)
    print(f"  folder: {len(every)} files, {sum(p.stat().st_size for p in every)} bytes")
    sources = [p.relative_to(FOLDER).as_posix() for p in every if p.suffix == ".py"]
    print(f"  .py files: {len(sources)} {sources[:5]}")


def main() -> int:
    """Build the folder and check it; return 0 when every shipped row and every Qt library is present."""
    ensure_build_venv()
    venv = probe_build_venv()
    print(f"build venv: Python {venv.python}, {venv.versions}")
    run([VENV_PYTHON, "-m", "PyInstaller", "--noconfirm", "--clean", "--distpath", DIST, "--workpath", WORK, SPEC])
    add_licences(venv)
    run([VENV_PYTHON, "-m", "hatchling", "build", "-t", "sdist", "-d", FOLDER / "source"])
    shutil.rmtree(WORK, ignore_errors=True)
    print(f"licence checklist for {FOLDER.relative_to(ROOT).as_posix()}:")
    rows = checklist_ok()
    sdist = source_ok()
    print("Qt libraries as separate files (dependency_licences.md R10):")
    qt = qt_libraries_ok()
    summarise()
    print(f"python licence SHA-256: {sha256_of(FOLDER / 'licenses' / 'PYTHON-LICENSE.txt')}")
    return 0 if rows and sdist and qt else 1


if __name__ == "__main__":
    sys.exit(main())
