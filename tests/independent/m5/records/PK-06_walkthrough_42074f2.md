Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5 (unit U-V21, 2026-10-21)

# PK-06 Linux walkthrough redone on the release 0.0.5 wheel

D-061d: the record `tests/independent/m5/records/PK-06_walkthrough_99d355d.md` names the wheel 0dbac116 that Agent 4
built from the candidate 99d355d. Its git subject (README.md, docs/install/INSTALL.md, requirements/py311.txt,
pyproject.toml, src/embodic, resources) is unchanged between 99d355d and 42074f2 (`v14_record_currency.py --target
42074f2`, entry 0: no change). The release wheel is another build of the same sources, and git cannot see its build
product. `tests/independent/m7/v21_wheel_diff.py` compares the two wheels: 274 members each, and two differ,
`embodic-0.0.5.dist-info/RECORD` and `embodic/_resources/evidence/passed_tests.v1.json`. In the evidence file
`build_id`, `generated_utc` and `git_commit` differ, and the 58 passed test IDs and `source_sha256` are equal. The
walkthrough reads that file: step 5b computes through `load_registry` (`api.py` l.246), and step 6 reports its
`build_id` as `evidence_build_id` (`selftest/runner.py` l.103). So the record does not stand for the release wheel,
and this record redoes the Linux walkthrough on it. The Windows walkthrough is a person's check on the user's laptop
and is not redone here.

What ran. `tests/independent/m5/pk06_walkthrough.py`, unchanged, followed `docs/install/INSTALL.md` steps 1 to 6 three
times, each in a new empty folder with a new Python 3.11 venv and a new empty `PIP_CACHE_DIR`. The raw output of every
step is in `pk06_42074f2_run1.json` to `pk06_42074f2_run3.json`.

Inputs (`verified`):

- Wheel `/home/claude/release_0.0.5/embodic-0.0.5-py3-none-any.whl`, SHA-256
  `a56eaebb9f3e2d7c62b87dda9f8baabd1980451157914c2a0431550f80946096` (`sha256sum`), the value D-089 records, built by
  Fable's release gate on 42074f2 (tag v0.0.5).
- Lock file `requirements/py311.txt` of 42074f2, equal to 99d355d.
- CPython 3.11.17 (`/usr/bin/python3.11`), Linux x86-64 container, 2 CPUs, no display. Load average at the start of
  the runs 0.23, 0.46 and 0.83 (`/proc/loadavg` in each JSON). No other campaign ran.

## Times per step

Wall time in seconds, `time.monotonic()` around each `bash -c` call, one sample per run (`verified`).

| Step | Command (verbatim from the guide) | run 1 | run 2 | run 3 | Exit |
|---|---|---|---|---|---|
| 1 | `python3.11 --version` | 0.005 | 0.005 | 0.004 | 0 |
| 2 | `python3.11 -m venv .venv` and `. .venv/bin/activate` | 3.813 | 3.546 | 3.434 | 0 |
| 3a | `python -m pip install --require-hashes -r requirements/py311.txt` | 12.464 | 8.684 | 9.846 | 0 |
| 3b | `python -m pip install --no-deps embodic-0.0.5-py3-none-any.whl` | 0.873 | 0.838 | 0.760 | 0 |
| 3c | `python -m pip list` | 0.446 | 0.464 | 0.409 | 0 |
| 4 | `embodic` | 0.658 | 0.531 | 0.539 | -6 |
| 5a | `python -c "from embodic.paths import resource_root; print(resource_root() / 'examples')"` | 0.042 | 0.040 | 0.042 | 0 |
| 5b | `embodic-cli compute <examples>/spiral_12c16p_default.embodic.json --json outcome.json --timings` | 1.603 | 1.548 | 1.709 | 0 |
| | Total to the first computed example (steps 1 to 5b) | 19.904 | 15.656 | 16.743 | |
| 5c | `embodic-cli validate <examples>/spiral_12c16p_default.embodic.json` | 0.331 | 0.335 | 0.338 | 0 |
| 5d | `embodic-cli export <examples>/spiral_12c16p_default.embodic.json --format svg -o board.svg` | 2.974 | 2.897 | 2.874 | 0 |
| 6 | `embodic-cli selftest` | 8.390 | 7.925 | 8.018 | 0 |
| extra | `QT_QPA_PLATFORM=offscreen embodic --smoke` (troubleshooting entry, not a guide step) | 2.673 | 2.799 | 2.555 | 0 |

Verdict on REQ-N-07 on Linux (below 10 minutes): `passed` on this container, 15.7 s to 19.9 s over three cold runs
(`verified`). As before, the total includes step 4, which aborts here in about 0.6 s without a display.

What limits the number. Step 3a takes 55 % to 63 % of the total. pip printed the numpy (16.9 MB) and
PySide6-Essentials (80.1 MB) downloads at 17.0 and 12.8 MB/s, 18.6 and 21.7 MB/s, and 19.4 and 21.4 MB/s
(`verified`, pip's progress lines in the JSON records). The other steps of the total sum to 6.90 to 7.44 s in all three
runs. The candidate record's 32.5 s to 75.7 s came with 1.6 to 8.0 MB/s, so the faster totals here are the proxy's
rate, not the product (`inferred`). A warm pip cache, a slower disk, another Python build and Windows are `not tested`
here.

## Output against the guide

Every step printed the guide's expected text (`missing_expected` empty in all three JSON records), except step 4:

- Step 3c. `embodic 0.0.5`, `numpy 2.4.6`, `pip 24.0`, `PySide6_Essentials 6.11.2`, `setuptools 79.0.1`, `shiboken6
  6.11.2` (`verified`).
- Step 4. Exit -6 without a display, as the earlier records show and as INSTALL.md lists under Troubleshooting on
  Linux. The window step is `not tested` without a display; `embodic --smoke` offscreen exited 0.
- Step 5b. `Design: Spiral, 12 coils, 16 poles` / `Design hash:
  sha256:ac4fab5db06f9e8f733dc495080deeddfe0bcf58faa31ebb7ec841c1b27d9c09` / `Topology: spiral, boards: 1` / `Design
  rule check: passed`, equal to the guide (`verified`, string comparison in the script).
- Step 6. `45 tests: 45 passed, 0 failed`, exit 0, the guide's text (`verified`).

## Rerun

```
python3.11 -I tests/independent/m5/pk06_walkthrough.py --wheel <the 0.0.5 release wheel> --lock requirements/py311.txt \
    --workdir <new folder that does not exist yet> --out <run.json>
```
