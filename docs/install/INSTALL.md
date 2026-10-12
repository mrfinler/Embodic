# Install and run embodic

This guide installs embodic into a virtual environment, runs the app and the command-line program, runs the tests and
builds the wheel. Each step gives the command for Linux (bash) and for Windows (PowerShell), then the output you should
see.

Two labels mark what was run for this build:

- Linux commands were run on a Linux x86-64 container with CPython 3.11.15 on 2026-10-12, unless a step says otherwise.
- Windows commands are written from the documentation of Python, venv and pip. They are not tested on Windows in this
  build.

The time of each step comes from the PK-06 walkthrough (unit U-V5), which has not run yet. This guide gives no times.

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
python -m pip install --no-deps embodic-0.0.1-py3-none-any.whl
```

Windows, not tested on Windows in this build:

```
python -m pip install --require-hashes -r requirements\py311.txt
python -m pip install --no-deps embodic-0.0.1-py3-none-any.whl
```

Check what is installed:

```
python -m pip list
```

Expected output: the list holds `embodic 0.0.1`, `numpy 2.4.6`, `PySide6_Essentials 6.11.2` and `shiboken6 6.11.2`,
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

`embodic-cli selftest` and the Tests dialog arrive with unit U-M5d. This build does not have them.

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

The PyInstaller one-folder build (`python tools/build_bundle.py`) arrives with unit U-M5c. This build does not have it.

## Troubleshooting on Linux

- `ERROR: Hashes are required in --require-hashes mode`: the command installs a file that the lock file does not pin.
  Install the wheel in its own command with `--no-deps`, as in step 3.
- The app fails with a message about the Qt platform plugin `xcb`: the system lacks a library that Qt needs. Install
  your distribution's packages for EGL, OpenGL, xkbcommon and fontconfig (the package names differ per distribution;
  not tested in this build). Without a display, set `QT_QPA_PLATFORM=offscreen` to run the tests.
- `embodic-cli: command not found`: the virtual environment is not active. Run `. .venv/bin/activate`.

## Troubleshooting on Windows

These points are written from the Python and PowerShell documentation. They are not tested on Windows in this build.

- `Activate.ps1 cannot be loaded because running scripts is disabled`: allow local scripts for your user with
  `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then activate again.
- `py` is not found: the python.org installer adds the `py` launcher. Run the installer again and select it.
- Paths with spaces: put the path in double quotes, for example `embodic-cli compute "$env:USERPROFILE\My designs\a.embodic.json"`.
