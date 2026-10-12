# PyInstaller 6.22 spec: one folder holding the desktop app `embodic` and the command line `embodic-cli`.
# Build with `python tools/build_bundle.py`, which also adds the licence files (package_layout.md section 5.2).
# One-folder mode and no UPX keep every Qt library a separate, replaceable file (dependency_licences.md R10).
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

HERE = Path(SPECPATH)
ROOT = HERE.parents[1]

# The same tree the wheel carries as embodic/_resources, so resource_root() finds it next to the frozen package.
# passed_tests.v1.json is git-ignored and enters only when the release gate wrote it.
DATAS = [(str(ROOT / "resources"), "embodic/_resources"), *collect_data_files("embodic")]
# errors/__init__.py finds the catalogue modules with pkgutil.iter_modules, so no import statement names them.
CATALOGUE = collect_submodules("embodic.errors.catalogue")

gui = Analysis(
    [str(HERE / "launch_gui.py")],
    datas=DATAS,
    hiddenimports=[*CATALOGUE, *collect_submodules("embodic.ui.strings")],
)
cli = Analysis(
    [str(HERE / "launch_cli.py")],
    datas=DATAS,
    hiddenimports=CATALOGUE,
    # The command line imports no Qt (import-linter contract C2); a Qt import there fails instead of growing the CLI.
    excludes=["PySide6", "shiboken6"],
)

gui_exe = EXE(
    PYZ(gui.pure),
    gui.scripts,
    exclude_binaries=True,
    name="embodic",
    console=False,
    upx=False,
)
cli_exe = EXE(
    PYZ(cli.pure),
    cli.scripts,
    exclude_binaries=True,
    name="embodic-cli",
    console=True,
    upx=False,
)

COLLECT(
    gui_exe,
    gui.binaries,
    gui.datas,
    cli_exe,
    cli.binaries,
    cli.datas,
    strip=False,
    upx=False,
    name="embodic",
)
