# Install and run embodic

This guide installs embodic into a virtual environment, runs the app and the command-line program, runs the tests and
builds the wheel. Each step gives the command for Linux (bash) and for Windows (PowerShell), then the output you should
see.

Two labels mark what was run for this build:

- Linux commands were run on a Linux x86-64 container with CPython 3.11.15 on 2026-10-12, unless a step says otherwise.
- Windows commands are written from the documentation of Python, venv and pip. They are not tested on Windows in this
  build.

The PK-06 walkthrough (unit U-V5) followed steps 1 to 6 of this guide on Linux on 2026-10-13. It ran four times, each in
a new folder with a new virtual environment and an empty pip cache. The machine was a Linux x86-64 container with 2
CPUs, 8 GB of RAM, CPython 3.11.15 and no display. From step 1 to the first computed example (the `compute` command in
step 5), the four cold runs took 19.2 s, 20.7 s, 26.0 s and 27.7 s. All four finished inside the 10 minutes that
REQ-N-07 allows. In all four runs, step 4 aborted after about 0.5 s with the Qt error listed under Troubleshooting on
Linux. The container has no display, so the window step is `not tested`, and the times include the abort.

The download limits the time. The dependency install in step 3 took 12.7 s to 20.1 s of each run, and pip downloaded the
80.1 MB PySide6-Essentials wheel at 5.0 MB/s to 9.7 MB/s. The spread between the runs comes from the download rate,
because no other step varies by more than 1.5 s. A machine with a warm pip cache, a slower disk or another Python build
is `not tested`. The Windows walkthrough is `not tested`.

## 1. Check the requirements

embodic needs CPython 3.11, 3.12 or 3.13, on Windows 10 or 11 (x64) or on Linux (x86-64).

Linux:

```
python3.11 --version
```

Windows, not tested on Windows in this build:

```
py -3.11 --version
```

Expected output: `Python 3.11.` followed by the patch number. If the command is not found, install CPython from your
distribution (Linux) or from the python.org installer (Windows).

## 2. Create a virtual environment

Linux:

```
python3.11 -m venv .venv
. .venv/bin/activate
```

Windows, not tested on Windows in this build:

```
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```

Expected result: the prompt starts with `(.venv)`. Every later command runs inside this environment.

## 3. Install the dependencies and the wheel

The lock file pins NumPy, PySide6-Essentials and shiboken6 with the SHA-256 of every file. Use the file of your Python
version: `py311.txt`, `py312.txt` or `py313.txt`. Then install the wheel without its dependencies, because
`--require-hashes` needs a hash for every requirement and the local wheel has none.

Linux:

```
python -m pip install --require-hashes -r requirements/py311.txt
python -m pip install --no-deps embodic-0.0.6-py3-none-any.whl
```

Windows, not tested on Windows in this build:

```
python -m pip install --require-hashes -r requirements\py311.txt
python -m pip install --no-deps embodic-0.0.6-py3-none-any.whl
```

After an install command, pip may print an upgrade notice, and the notice does not affect the install. In the PK-06 runs
it read `[notice] A new release of pip is available: 24.0 -> 26.2.1`.

Check what is installed:

```
python -m pip list
```

Expected output: the list holds `embodic 0.0.6`, `numpy 2.4.6`, `PySide6_Essentials 6.11.2` and `shiboken6 6.11.2`,
besides `pip` (and `setuptools` on Python 3.11). The test PK-02 (`tests/packaging/test_pk02_clean_install.py`) checks
exactly this list on Linux.

## 4. Run the app

```
embodic
```

Expected result: the embodic window opens. The test PF-03 opened the window on Qt's offscreen platform on Linux. A
desktop session on Linux and the Windows app were not opened in this build.

## 5. Run the command-line program

The examples ship inside the package. Print their folder:

```
python -c "from embodic.paths import resource_root; print(resource_root() / 'examples')"
```

Expected output: a path that ends in `embodic/_resources/examples` for a wheel install, or `resources/examples` for a
development checkout. In the commands below, replace `<examples>` with that path. On Windows, write the path with `\`.

Compute the default example and write the full outcome as JSON:

```
embodic-cli compute <examples>/spiral_12c16p_default.embodic.json --json outcome.json --timings
```

Expected output (the timings differ on your machine):

```
Design: Spiral, 12 coils, 16 poles
Design hash: sha256:ac4fab5db06f9e8f733dc495080deeddfe0bcf58faa31ebb7ec841c1b27d9c09
Topology: spiral, boards: 1
Design rule check: passed
Timings (s): validate 0.001, geometry 0.020, drc 0.306, physics 0.702
```

Each result in `outcome.json` carries its `status`, its `eq_ids` and its assumed inputs.

Check a design against its rules without building it:

```
embodic-cli validate <examples>/spiral_12c16p_default.embodic.json
```

Expected output: `Valid: Spiral, 12 coils, 16 poles`.

Export a drawing:

```
embodic-cli export <examples>/spiral_12c16p_default.embodic.json --format svg -o board.svg
```

Expected output: `Wrote board.svg`. `--format` also takes `dxf`, `dxf-outline`, `dxf-screws`, `pdf`, `readme` and
`bundle`.

## 6. Check the installation

The wheel carries 45 self-tests. They check that this installation reproduces the numbers of its build. Run them from
the virtual environment of step 2. The command is the same on Windows, where it is not tested in this build.

```
embodic-cli selftest
```

Expected output: one line per check with the verdict word (`passed` or `failed`), the check ID and the duration, and for
a failed check its message. The last line is the summary. These are the last two lines of a passing run on Linux (the
durations differ on your machine):

```
passed   ST-EXP-BUNDLE                         3.99 s
45 tests: 45 passed, 0 failed
```

The exit code is 0 when every check passes and 1 when a check fails. The PK-06 walkthrough ran the command four times on
Linux without a display. Each run passed, exited 0 and took 8.6 s to 8.9 s. No failing run was produced for this guide,
so the exit code 1 comes from the interface contract (`docs/phase2/architecture/interfaces.md` section 12). A failed
check points to a defect in the installation, such as a broken NumPy or a damaged resource file.

The app runs the same checks in the Tests dialog. Open the View tab, find the group Help and click **Self-tests**. Click
**Run** to start the checks. **Stop** or Esc cancels a run. The summary line reads `45 tests: 45 passed, 0 failed` after
a passing run. A desktop session did not open the dialog in this build, so the description comes from the source and
`docs/phase2/design/screens.md` section 13.

A self-test result never changes a result badge. Badges follow the registry and the test evidence of the build, so a
pass or a fail here moves none of them (`docs/phase2/architecture/interfaces.md` section 14).

## 7. Run the tests

A development install uses the `-dev` lock file, which adds the test and build tools, and installs embodic in editable
mode from a checkout of the repository. The editable install needs network access: pip builds it in an isolated
environment and downloads hatchling and `editables` there. `--no-build-isolation` fails, because hatchling's editable
build imports `editables`, which the lock file does not pin.

Linux (the two install commands ran in a fresh environment; the gate ran in the existing project environment):

```
python -m pip install --require-hashes -r requirements/py311-dev.txt
python -m pip install --no-deps -e .
python tools/ci.py --profile commit
```

Windows, not tested on Windows in this build:

```
python -m pip install --require-hashes -r requirements\py311-dev.txt
python -m pip install --no-deps -e .
python tools\ci.py --profile commit
```

Expected output: the gate prints one line per gate and ends with `6 of 6 gates passed`. The commit gate runs for tens
of minutes on a 2-CPU machine.

## 8. Build the wheel and record the test evidence

```
python tools/ci.py --profile release
```

Expected output: the summary lists the six gates, then `passed-test evidence (TR-05)`, `wheel build` and `evidence in
the wheel (PK-10)`, and ends with `9 of 9 gates passed`. The wheel is in `build/dist/`, and
`resources/evidence/passed_tests.v1.json` lists the registry tests that passed. A failed gate stops the run before the
evidence step, and no evidence file remains.

## 9. Build the Windows folder

`tools/build_bundle.py` builds a PyInstaller 6.22.3 one-folder bundle from `packaging/pyinstaller/embodic.spec`. It
installs PyInstaller in its own scratch venv, `.venv-bundle`, and leaves the venv of step 2 unchanged. The first run
downloads the packages of the lock file, PyInstaller and hatchling, so it needs the network. Run it from a source
checkout with the Python whose lock file the bundle should use.

Linux:

```
python3.11 tools/build_bundle.py
```

Windows, not tested on Windows in this build:

```
py -3.11 tools\build_bundle.py
```

The folder is `build/bundle/embodic`. It holds the desktop app `embodic` and the command line `embodic-cli`
(`embodic.exe` and `embodic-cli.exe` on Windows), `_internal/` with Python, Qt and embodic's resources,
`THIRD_PARTY_LICENSES.md`, `licenses/` (LGPL-3.0, GPL-3.0, NumPy and Python texts) and `source/` with embodic's source
distribution. The build uses one-folder mode without UPX, so each Qt library stays a separate file that a user can
replace (LGPL-3.0). The folder does not yet carry a written offer for the Qt and PySide6 source, Qt's third-party
notices or embodic's own licence; the script lists each as `absent`.

Expected output: the script ends with the licence checklist, the four Qt libraries and the folder size, then exits 0.
On Linux the Qt lines were:

```
Qt libraries as separate files (dependency_licences.md R10):
  Qt6Core     _internal/PySide6/Qt/lib/libQt6Core.so.6 7524648 bytes
  Qt6Gui      _internal/PySide6/Qt/lib/libQt6Gui.so.6 11412488 bytes
  Qt6Widgets  _internal/PySide6/Qt/lib/libQt6Widgets.so.6 8155496 bytes
  Qt6Svg      _internal/PySide6/Qt/lib/libQt6Svg.so.6 691176 bytes
```

The Linux folder held 444 files, about 232 MB, and no `.py` file. PyInstaller warned that it could not resolve
`libxcb-cursor.so.0`, which the build machine lacks; the folder's `xcb` platform plugin then needs that library on the
user's system. The offscreen platform runs without it.

Check the folder with the smoke test, from the venv of step 7:

```
python -m pytest tests/bundle
```

Expected output: `6 passed`. The tests run the frozen `embodic-cli compute` and `export --format svg` on the default
example and compare the result with the source, start the frozen app with `--smoke` on the offscreen Qt platform, run
the frozen `embodic-cli selftest`, and check the Qt libraries. Without a folder the six tests are skipped.

What was run: the build, the smoke test and `build/bundle/embodic/embodic-cli selftest`, which ended with
`45 tests: 45 passed, 0 failed`, on the Linux container named at the top of this guide. A Linux folder is a smoke test
of the spec only. The Windows folder, which the bundle test PK-05 needs, is not tested.

## Troubleshooting on Linux

- `ERROR: Hashes are required in --require-hashes mode`: the command installs a file that the lock file does not pin.
  Install the wheel in its own command with `--no-deps`, as in step 3.
- The app aborts with `qt.qpa.plugin: From 6.5.0, xcb-cursor0 or libxcb-cursor0 is needed to load the Qt xcb platform
  plugin.` followed by `Could not load the Qt platform plugin "xcb"`: the system lacks the library that Qt names. On
  Ubuntu 24.04 the package is `libxcb-cursor0` in the universe component (`apt-cache policy libxcb-cursor0` on the build
  container lists candidate 0.1.4-1build1). Install it with your package manager. Whether the window then opens on a
  desktop session is not tested. Debian and other distributions are not tested. If Qt names other libraries, install your
  distribution's packages for EGL, OpenGL, xkbcommon and fontconfig (the package names differ per distribution; not
  tested in this build).
- There is no display: set `QT_QPA_PLATFORM=offscreen` before you start `embodic`. Qt then uses its offscreen platform
  and shows no window. The command `QT_QPA_PLATFORM=offscreen embodic --smoke` opens the window, loads the D08 example,
  computes it and exits with code 0. It took 2.5 s to 3.0 s in the four PK-06 runs.
- `embodic-cli: command not found`: the virtual environment is not active. Run `. .venv/bin/activate`.

## Troubleshooting on Windows

These points are written from the Python and PowerShell documentation. They are not tested on Windows in this build,
except the first one.

- `Activate.ps1 cannot be loaded because running scripts is disabled`: allow local scripts for this PowerShell window
  only with `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`, then activate again. The setting ends
  when the window closes and leaves the policy of your user account unchanged. Run on 2026-10-18 on Windows 11 Home
  with PowerShell 5.1 and a `Restricted` policy: activation failed before the command and worked after it, and the
  `CurrentUser` policy stayed `Undefined` (D-051g, DEF-W-04).
- `Program 'embodic-cli.exe' failed to run: An Application Control policy has blocked this file` (the same can happen
  to `embodic.exe`): a Windows policy such as Smart App Control blocks the launchers that pip writes into
  `.venv\Scripts`. Start embodic through Python instead: `python -m embodic.cli` takes the same commands as
  `embodic-cli` (for example `python -m embodic.cli selftest`), and `python -m embodic.ui.app` opens the window. On
  the test laptop (Windows 11 Home) the policy blocked `embodic-cli.exe` in some runs and not in others on
  2026-10-22. In one run `python -m embodic.cli` passed steps 5 and 6, with the self-test 45 of 45 (D-098, D-100, DEF-W-16).
  `python -m embodic.ui.app` was not opened on Windows.
- `py` is not found: the python.org installer adds the `py` launcher. Run the installer again and select it.
- Paths with spaces: put the path in double quotes, for example `embodic-cli compute "$env:USERPROFILE\My designs\a.embodic.json"`.
