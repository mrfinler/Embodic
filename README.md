# embodic

embodic designs and analyses three-phase PCB stator coils for axial-flux machines: spiral coils, serpentine windings
and interleaved wave windings. It builds the copper layout of a design, checks it against design rules, estimates
electrical quantities such as the back-EMF constant and the phase resistance, and exports SVG, DXF, PDF and JSON files.
It runs as a desktop window (`embodic`) and as a command-line program (`embodic-cli`).

Every computed result carries a badge with one status word. The badge is the weakest of its equation's evidence status,
the test state of its equation in this build and any validity cap. The app's equation guide defines the words:

- `verified`: read in the source or reproduced by running something.
- `inferred`: follows from verified facts by reasoning that was not reproduced.
- `assumption`: taken as true without evidence for this design.
- `unresolved`: not known yet. A label beside the badge, such as "estimate", says why.
- `not tested`: the tests linked to the equation have not passed in this build.

No result is a measurement of a built stator.

Licence: not yet chosen; all rights reserved until the project owner chooses one.

## Requirements

- CPython 3.11, 3.12 or 3.13.
- Windows 10 or 11 (x64), or Linux (x86-64).

`docs/install/INSTALL.md` has every step below with the expected output and troubleshooting. The Windows commands are
written from the documentation of Python and pip. They are not tested on Windows in this build.

## Install

Create a virtual environment, install the pinned dependencies from the lock file of your Python version, then install
the embodic wheel. The example uses Python 3.11 and `requirements/py311.txt`.

Linux (bash):

```
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --require-hashes -r requirements/py311.txt
python -m pip install --no-deps embodic-0.0.5-py3-none-any.whl
```

Windows (PowerShell), not tested on Windows in this build:

```
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --require-hashes -r requirements\py311.txt
python -m pip install --no-deps embodic-0.0.5-py3-none-any.whl
```

## Run the app

```
embodic
```

## Run the command-line program

The examples ship inside the package. This command prints their folder:

```
python -c "from embodic.paths import resource_root; print(resource_root() / 'examples')"
```

Compute an example, check a design without building it, and export a drawing. On Windows, write the paths with `\`.

```
embodic-cli compute <examples>/spiral_12c16p_default.embodic.json --json outcome.json
embodic-cli validate <examples>/spiral_12c16p_default.embodic.json
embodic-cli export <examples>/spiral_12c16p_default.embodic.json --format svg -o board.svg
```

`--format` takes `svg`, `dxf`, `dxf-outline`, `dxf-screws`, `pdf`, `readme` or `bundle`.

## Check the installation

`embodic-cli selftest` runs 45 built-in checks against the installed package and needs no display. It prints one line
per check with the verdict word, the check ID and the duration, then a summary line. A failed check adds its message to
its line. The exit code is 0 when every check passes and 1 otherwise.

```
embodic-cli selftest
```

The last two lines of a passing run on Linux (the durations differ on your machine):

```
passed   ST-EXP-BUNDLE                         3.99 s
45 tests: 45 passed, 0 failed
```

The app runs the same checks from the Tests dialog. Open the View tab, find the group Help, and click **Self-tests**.

A self-test result never changes a result badge. Badges follow the registry and the test evidence of the build, so a
pass or a fail here moves none of them (`docs/phase2/architecture/interfaces.md` section 14).

## Run the tests

Install the development lock file and embodic in editable mode, then run the commit gate from the repository root.

Linux (bash):

```
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --require-hashes -r requirements/py311-dev.txt
python -m pip install --no-deps -e .
python tools/ci.py --profile commit
```

Windows (PowerShell), not tested on Windows in this build:

```
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --require-hashes -r requirements\py311-dev.txt
python -m pip install --no-deps -e .
python tools\ci.py --profile commit
```

## Build the wheel and record the test evidence

```
python tools/ci.py --profile release
```

The release profile runs every gate. When all of them pass, it writes the list of registry tests that passed to
`resources/evidence/passed_tests.v1.json`, builds the wheel into `build/dist/`, and checks that the wheel carries the
list. Only then can a result read anything other than `not tested`. The file is a build product and is never committed.
Add `--record-baseline` to rewrite `tests/performance/baseline.json`.

## Build the Windows folder

`python tools/build_bundle.py` builds a PyInstaller one-folder bundle. Section 9 of `docs/install/INSTALL.md` has the
command, the contents of the folder and the checks. The build was run on Linux only, and that run is a smoke test of the
PyInstaller spec. The Windows folder is not tested.

## Licences

`THIRD_PARTY_LICENSES.md` lists the licence of every runtime dependency and bundled font, with the full texts. embodic
uses Qt and PySide6 under LGPL-3.0. embodic's own licence is not yet chosen; all rights reserved until the project
owner chooses one.
