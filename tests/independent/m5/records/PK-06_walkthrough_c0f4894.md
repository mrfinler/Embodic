Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5 (unit U-V14, 2026-10-18)

# PK-06 Linux walkthrough redone on main c0f4894

D-061d: the U-V5 record `tests/independent/m5/records/PK-06_walkthrough.md` names the 0.0.1 wheel of 5e74acc, and 83 of
the files its subject depends on (the guide, the lock file and the wheel's inputs) changed before c0f4894
(`tests/independent/m7/v14_record_currency.py`, entry 0). This record redoes the Linux walkthrough. The Windows
walkthrough of `docs/phase3/fable/windows_campaign_w1.md` is a person's check on the user's laptop and is not redone
here.

What ran. `tests/independent/m5/pk06_walkthrough.py` (unchanged since U-V5) followed `docs/install/INSTALL.md` steps 1
to 6 three times, each in a new empty folder with a new Python 3.11 venv and a new empty `PIP_CACHE_DIR`. The command
lines of steps 1 to 6 in INSTALL.md are the same on c0f4894 as on 5e74acc; the diff adds the U-V5 times, a pip notice,
the selftest section and a troubleshooting entry (`git diff 5e74acc c0f4894 -- docs/install/INSTALL.md`, read). The raw
output of every step is in `pk06_c0f4894_run1.json` to `pk06_c0f4894_run3.json`.

Inputs (`verified`):

- Wheel built on c0f4894 with `pip wheel --no-build-isolation --no-deps .` (the `tools/ci.py` command), file
  `embodic-0.0.1-py3-none-any.whl`, SHA-256 `cb4e51c28889d6ee0916d95cf0a3622655eb6fea9b8b8acca2c745354e7879ba`, 272
  members, `Version: 0.0.1` in its METADATA. The version string is still 0.0.1 on c0f4894 (`src/embodic/__init__.py`
  l.3), so the guide's file name `embodic-0.0.1-py3-none-any.whl` matches.
- Lock file `requirements/py311.txt` of c0f4894, unchanged since 5e74acc (`git diff --stat`, empty).
- CPython 3.11.15 (`/usr/bin/python3.11`), Linux x86-64 container, 2 CPUs, 8 GB RAM shared with another agent's unit,
  no display. Load average at the start of the runs 0.60, 0.79 and 1.11 (`/proc/loadavg` in each JSON). No FEA, pytest
  or build of this unit ran during the walkthrough.

## Times per step

Wall time in seconds, `time.monotonic()` around each `bash -c` call, one sample per run (`verified`).

| Step | Command (verbatim from the guide) | run 1 | run 2 | run 3 | Exit |
|---|---|---|---|---|---|
| 1 | `python3.11 --version` | 0.009 | 0.005 | 0.004 | 0 |
| 2 | `python3.11 -m venv .venv` and `. .venv/bin/activate` | 3.693 | 3.897 | 3.730 | 0 |
| 3a | `python -m pip install --require-hashes -r requirements/py311.txt` | 9.767 | 11.183 | 19.411 | 0 |
| 3b | `python -m pip install --no-deps embodic-0.0.1-py3-none-any.whl` | 1.048 | 0.903 | 0.864 | 0 |
| 3c | `python -m pip list` | 0.608 | 0.486 | 0.479 | 0 |
| 4 | `embodic` | 0.590 | 0.563 | 0.639 | -6 |
| 5a | `python -c "from embodic.paths import resource_root; print(resource_root() / 'examples')"` | 0.042 | 0.049 | 0.043 | 0 |
| 5b | `embodic-cli compute <examples>/spiral_12c16p_default.embodic.json --json outcome.json --timings` | 1.614 | 1.754 | 1.668 | 0 |
| | Total to the first computed example (steps 1 to 5b) | 17.371 | 18.840 | 26.838 | |
| 5c | `embodic-cli validate <examples>/spiral_12c16p_default.embodic.json` | 0.359 | 0.402 | 0.394 | 0 |
| 5d | `embodic-cli export <examples>/spiral_12c16p_default.embodic.json --format svg -o board.svg` | 4.585 | 4.146 | 4.758 | 0 |
| 6 | `embodic-cli selftest` | 10.760 | 10.351 | 10.977 | 0 |
| extra | `QT_QPA_PLATFORM=offscreen embodic --smoke` (troubleshooting entry, not a guide step) | 2.921 | 3.155 | 2.832 | 0 |

Verdict on REQ-N-07 on Linux (below 10 minutes): `passed` on this container, 17.4 s to 26.8 s over three cold runs
(`verified`). As in U-V5, the total includes step 4, which aborts here in about 0.6 s without a display.

What limits the number. Step 3a takes 56 % to 72 % of the total. pip printed the PySide6-Essentials download (80.1 MB)
at 22.4, 10.0 and 4.7 MB/s (`verified`, pip's progress lines in the JSON records). The other steps of the total vary by
less than 0.25 s between runs, so the spread of 9.5 s is the download rate (`verified` from the table). Everything except step 3a
takes about 7.5 s. A warm pip cache, a slower disk, another Python build and Windows are `not tested` here.

## Output against the guide

Every step printed the guide's expected text (`missing_expected` empty in all three JSON records), except step 4:

- Step 3c. `embodic 0.0.1`, `numpy 2.4.6`, `pip 24.0`, `PySide6_Essentials 6.11.2`, `setuptools 79.0.1`, `shiboken6
  6.11.2` (`verified`).
- Step 4. Exit -6 with the Qt `xcb-cursor0` message, as U-V5 recorded and as INSTALL.md now lists under
  Troubleshooting on Linux. The window step is `not tested` without a display; `embodic --smoke` offscreen exited 0.
- Step 5b. `Design: Spiral, 12 coils, 16 poles` / `Design hash:
  sha256:ac4fab5db06f9e8f733dc495080deeddfe0bcf58faa31ebb7ec841c1b27d9c09` / `Topology: spiral, boards: 1` / `Design
  rule check: passed`, equal to the guide (`verified`, string comparison in the script).
- Step 6. 45 lines `passed <id> <s>`, then `45 tests: 45 passed, 0 failed`, exit 0, which is the guide's text on
  c0f4894 (`verified`). The time column now lines up for the two long IDs that DEF-UV5-04 named (read in run 1).
