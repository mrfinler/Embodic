Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5 (unit U-V20, 2026-10-21)

# PK-06 Linux walkthrough redone for release 0.0.5

D-061d: the record `tests/independent/m5/records/PK-06_walkthrough_c25d8a9.md` names the release wheel 9bca49d8 of
c25d8a9. Its subject is the guide, the lock file and the wheel's inputs (README.md, docs/install/INSTALL.md,
requirements/py311.txt, pyproject.toml, src/embodic, resources). `git diff --stat c25d8a9 99d355d -- <those paths>`
gives `11 files changed, 43 insertions(+), 19 deletions(-)`: the wheel name and the `pip list` line of README.md and
INSTALL.md, the version lines of the five examples, `src/embodic/__init__.py`, two docstrings in `physics/` and the
test ID `DRC_SOURCE` in `selftest/catalogue.py` (`tests/independent/m7/v14_record_currency.py --target 99d355d`,
entry 0). The record does not stand for 0.0.5, and this record redoes the Linux walkthrough. The Windows walkthrough
is a person's check on the user's laptop and is not redone here.

What ran. `tests/independent/m5/pk06_walkthrough.py`, unchanged, followed `docs/install/INSTALL.md` steps 1 to 6 three
times, each in a new empty folder with a new Python 3.11 venv and a new empty `PIP_CACHE_DIR`. The guide names the
wheel `embodic-0.0.5-py3-none-any.whl` and the list entry `embodic 0.0.5`, and the lever takes the version from the
wheel's file name. The raw output of every step is in `pk06_99d355d_run1.json` to `pk06_99d355d_run3.json`.

Inputs (`verified`):

- Wheel `embodic-0.0.5-py3-none-any.whl`, SHA-256 `0dbac116f6e707907e22808ef14d72581a9a60a58e78a4e0f183fc0fb86949ec`
  (`sha256sum`). Agent 4 built it the way tools/ci.py's release steps do, from `git archive 99d355d`:
  `tools/record_passed_tests.py --profile=release` on the REQ report of U-V20's release-marker pytest run on 99d355d
  (4406 passed, 0 failed; 58 of 63 registry test IDs passed), then `pip wheel --no-build-isolation --no-deps .`. It is
  not Fable's release wheel. Its evidence file carries a build time, so the release wheel will hash differently; its
  `src/`, `resources/` and lock file are those of 99d355d, which is what D-061d compares.
- Lock file `requirements/py311.txt` of 99d355d, equal to c25d8a9 (`git diff c25d8a9 99d355d -- requirements`, empty).
- CPython 3.11.17 (`/usr/bin/python3.11`), Linux x86-64 container, 2 CPUs, no display. Load average at
  the start of the runs 0.08, 0.49 and 0.51 (`/proc/loadavg` in each JSON). Nothing else ran: U-V20's pytest run had ended before run 1.

## Times per step

Wall time in seconds, `time.monotonic()` around each `bash -c` call, one sample per run (`verified`).

| Step | Command (verbatim from the guide) | run 1 | run 2 | run 3 | Exit |
|---|---|---|---|---|---|
| 1 | `python3.11 --version` | 0.007 | 0.006 | 0.006 | 0 |
| 2 | `python3.11 -m venv .venv` and `. .venv/bin/activate` | 3.798 | 3.912 | 4.152 | 0 |
| 3a | `python -m pip install --require-hashes -r requirements/py311.txt` | 24.300 | 67.945 | 26.228 | 0 |
| 3b | `python -m pip install --no-deps embodic-0.0.5-py3-none-any.whl` | 0.963 | 0.966 | 0.888 | 0 |
| 3c | `python -m pip list` | 0.439 | 0.487 | 0.483 | 0 |
| 4 | `embodic` | 0.689 | 0.646 | 0.565 | -6 |
| 5a | `python -c "from embodic.paths import resource_root; print(resource_root() / 'examples')"` | 0.056 | 0.040 | 0.043 | 0 |
| 5b | `embodic-cli compute <examples>/spiral_12c16p_default.embodic.json --json outcome.json --timings` | 2.239 | 1.710 | 1.700 | 0 |
| | Total to the first computed example (steps 1 to 5b) | 32.491 | 75.712 | 34.065 | |
| 5c | `embodic-cli validate <examples>/spiral_12c16p_default.embodic.json` | 0.381 | 0.328 | 0.385 | 0 |
| 5d | `embodic-cli export <examples>/spiral_12c16p_default.embodic.json --format svg -o board.svg` | 3.674 | 3.036 | 2.979 | 0 |
| 6 | `embodic-cli selftest` | 9.858 | 9.038 | 8.591 | 0 |
| extra | `QT_QPA_PLATFORM=offscreen embodic --smoke` (troubleshooting entry, not a guide step) | 3.658 | 2.782 | 2.686 | 0 |

Verdict on REQ-N-07 on Linux (below 10 minutes): `passed` on this container, 32.5 s to 75.7 s over three cold runs
(`verified`). As before, the total includes step 4, which aborts here in about 0.6 s without a display.

What limits the number. Step 3a takes 75 % to 90 % of the total. pip printed the PySide6-Essentials download (80.1 MB)
at 5.0, 1.6 and 8.0 MB/s (`verified`, pip's progress lines in the JSON records). The other steps of the total sum to
7.77 to 8.19 s in all three runs, so the spread of 43 s is the download of run 2 (`verified` from the table). The
0.0.4 record's 26.5 s to 32.5 s came with 5.6 to 6.8 MB/s; the difference is the proxy's rate, not the product
(`inferred`). A warm pip cache, a slower disk, another Python build and Windows are `not tested` here.

## Output against the guide

Every step printed the guide's expected text (`missing_expected` empty in all three JSON records), except step 4:

- Step 3c. `embodic 0.0.5`, `numpy 2.4.6`, `pip 24.0`, `PySide6_Essentials 6.11.2`, `setuptools 79.0.1`, `shiboken6
  6.11.2` (`verified`).
- Step 4. Exit -6 with the Qt platform-plugin message, as the earlier records show and as INSTALL.md lists under
  Troubleshooting on Linux. The window step is `not tested` without a display; `embodic --smoke` offscreen exited 0.
- Step 5b. `Design: Spiral, 12 coils, 16 poles` / `Design hash:
  sha256:ac4fab5db06f9e8f733dc495080deeddfe0bcf58faa31ebb7ec841c1b27d9c09` / `Topology: spiral, boards: 1` / `Design
  rule check: passed`, equal to the guide (`verified`, string comparison in the script).
- Step 6. `45 tests: 45 passed, 0 failed`, exit 0, the guide's text (`verified`).

## Rerun

```
python3.11 -I tests/independent/m5/pk06_walkthrough.py --wheel <the 0.0.5 wheel> --lock requirements/py311.txt \
    --workdir <new empty folder> --out <run.json>
```
