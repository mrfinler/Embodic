Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5 (unit U-V18, 2026-10-20)

# PK-06 Linux walkthrough redone for release 0.0.4

D-061d: the record `tests/independent/m5/records/PK-06_walkthrough_c0f4894.md` names the wheel cb4e51c2 of main
c0f4894. Its subject is the guide, the lock file and the wheel's inputs (README.md, docs/install/INSTALL.md,
requirements/py311.txt, pyproject.toml, src/embodic, resources). `git diff --stat c0f4894 c25d8a9 -- <those paths>`
gives `33 files changed, 635 insertions(+), 147 deletions(-)` (`tests/independent/m7/v14_record_currency.py --target
c25d8a9`, entry 0), so the record does not stand for 0.0.4 and this record redoes the Linux walkthrough. The Windows
walkthrough is a person's check on the user's laptop and is not redone here.

What ran. `tests/independent/m5/pk06_walkthrough.py` followed `docs/install/INSTALL.md` steps 1 to 6 three times, each
in a new empty folder with a new Python 3.11 venv and a new empty `PIP_CACHE_DIR`. The guide now names the wheel
`embodic-0.0.4-py3-none-any.whl` and the list entry `embodic 0.0.4` (`git diff c0f4894 c25d8a9 --
docs/install/INSTALL.md`, read; the other command lines of steps 1 to 6 are unchanged). The lever had those two strings
fixed at 0.0.1; U-V18 makes it take the version from the wheel's file name and changes nothing else. The raw output of
every step is in `pk06_c25d8a9_run1.json` to `pk06_c25d8a9_run3.json`.

Inputs (`verified`):

- Wheel `/home/claude/release_0.0.4/embodic-0.0.4-py3-none-any.whl` of Fable's release gate on c25d8a9 (tag v0.0.4),
  SHA-256 `9bca49d895aee779be71cda8b939b67f86414ef8f711d7090b9c01215a6de579` (`sha256sum`, the value of D-081).
- Lock file `requirements/py311.txt` of main 705c1cb, equal to c25d8a9 (`git diff c25d8a9 705c1cb -- requirements`,
  empty).
- CPython 3.11.17 (`/usr/bin/python3.11`), Linux x86-64 container, 2 CPUs, no display. Load average at the start of the
  runs 0.15, 0.50 and 0.70 (`/proc/loadavg` in each JSON). Nothing else of this unit ran during the walkthrough, and
  `ps` showed no other CPU user before it.

## Times per step

Wall time in seconds, `time.monotonic()` around each `bash -c` call, one sample per run (`verified`).

| Step | Command (verbatim from the guide) | run 1 | run 2 | run 3 | Exit |
|---|---|---|---|---|---|
| 1 | `python3.11 --version` | 0.005 | 0.008 | 0.005 | 0 |
| 2 | `python3.11 -m venv .venv` and `. .venv/bin/activate` | 4.093 | 4.052 | 3.658 | 0 |
| 3a | `python -m pip install --require-hashes -r requirements/py311.txt` | 22.252 | 18.140 | 24.078 | 0 |
| 3b | `python -m pip install --no-deps embodic-0.0.4-py3-none-any.whl` | 1.048 | 1.091 | 1.063 | 0 |
| 3c | `python -m pip list` | 0.623 | 0.680 | 0.549 | 0 |
| 4 | `embodic` | 0.648 | 0.649 | 0.786 | -6 |
| 5a | `python -c "from embodic.paths import resource_root; print(resource_root() / 'examples')"` | 0.047 | 0.049 | 0.050 | 0 |
| 5b | `embodic-cli compute <examples>/spiral_12c16p_default.embodic.json --json outcome.json --timings` | 1.957 | 1.844 | 2.295 | 0 |
| | Total to the first computed example (steps 1 to 5b) | 30.673 | 26.513 | 32.484 | |
| 5c | `embodic-cli validate <examples>/spiral_12c16p_default.embodic.json` | 0.467 | 0.382 | 0.548 | 0 |
| 5d | `embodic-cli export <examples>/spiral_12c16p_default.embodic.json --format svg -o board.svg` | 3.313 | 3.334 | 3.801 | 0 |
| 6 | `embodic-cli selftest` | 9.484 | 9.477 | 8.571 | 0 |
| extra | `QT_QPA_PLATFORM=offscreen embodic --smoke` (troubleshooting entry, not a guide step) | 3.309 | 3.249 | 3.221 | 0 |

Verdict on REQ-N-07 on Linux (below 10 minutes): `passed` on this container, 26.5 s to 32.5 s over three cold runs
(`verified`). As before, the total includes step 4, which aborts here in about 0.7 s without a display.

What limits the number. Step 3a takes 68 % to 74 % of the total. pip printed the PySide6-Essentials download (80.1 MB)
at 5.7, 6.8 and 5.6 MB/s (`verified`, pip's progress lines in the JSON records). The other steps of the total sum to
8.37 to 8.42 s in all three runs, so the spread of 6.0 s is the download (`verified` from the table). The 0.0.2 record's
17.4 s to 26.8 s came with download rates of 4.7 to 22.4 MB/s; the difference between the two records is the proxy's
rate, not the product (`inferred`). A warm pip cache, a slower disk, another Python build and Windows are `not tested`
here.

## Output against the guide

Every step printed the guide's expected text (`missing_expected` empty in all three JSON records), except step 4:

- Step 3c. `embodic 0.0.4`, `numpy 2.4.6`, `pip 24.0`, `PySide6_Essentials 6.11.2`, `setuptools 79.0.1`, `shiboken6
  6.11.2` (`verified`).
- Step 4. Exit -6 with the Qt platform-plugin message, as the earlier records show and as INSTALL.md lists under
  Troubleshooting on Linux. The window step is `not tested` without a display; `embodic --smoke` offscreen exited 0.
- Step 5b. `Design: Spiral, 12 coils, 16 poles` / `Design hash:
  sha256:ac4fab5db06f9e8f733dc495080deeddfe0bcf58faa31ebb7ec841c1b27d9c09` / `Topology: spiral, boards: 1` / `Design
  rule check: passed`, equal to the guide (`verified`, string comparison in the script).
- Step 6. `45 tests: 45 passed, 0 failed`, exit 0, the guide's text (`verified`).

## Rerun

```
python3.11 -I tests/independent/m5/pk06_walkthrough.py --wheel <the 0.0.4 wheel> --lock requirements/py311.txt \
    --workdir <new empty folder> --out <run.json>
```
