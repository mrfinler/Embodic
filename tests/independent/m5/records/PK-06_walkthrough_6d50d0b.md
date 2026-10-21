Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5 (unit U-V27, 2026-10-21 UTC)

# PK-06 Linux walkthrough redone for 0.0.6 (candidate main 6d50d0b)

D-061d: the record `tests/independent/m5/records/PK-06_walkthrough_42074f2.md` names the release wheel a56eaebb of
42074f2 (0.0.5). Its subject is the guide, the lock file and the wheel's inputs (README.md, docs/install/INSTALL.md,
requirements/py311.txt, pyproject.toml, src/embodic, resources). `git diff --stat 42074f2 6d50d0b -- <those paths>`
gives `14 files changed, 69 insertions(+), 41 deletions(-)`: the wheel name and the `pip list` line of README.md and
INSTALL.md, the version lines of the five examples, `src/embodic/__init__.py`, and six files under `src/embodic/ui`
(`tests/independent/m7/v14_record_currency.py --target 6d50d0b`, entry 0). In the wheel, 13 of 269 shared members
have other bytes, among them the evidence file (`tests/independent/m7/v21_wheel_diff.py`, in
`docs/phase3/verification/manual_records_0.0.6_currency.txt`). The record does not stand for 0.0.6, and this record
redoes the Linux walkthrough. The Windows walkthrough is a person's check on the user's laptop and is not redone here.

What ran. `tests/independent/m5/pk06_walkthrough.py`, unchanged, followed `docs/install/INSTALL.md` steps 1 to 6 three
times, each in a new empty folder with a new Python 3.11 venv and a new empty `PIP_CACHE_DIR`. The raw output of every
step is in `pk06_6d50d0b_run1.json` to `pk06_6d50d0b_run3.json`.

Inputs (`verified`):

- Wheel `embodic-0.0.6-py3-none-any.whl`, SHA-256 `5d891a268323fed9ce3414db3b042d27e51e5a27e33bba44df3cdc262d3ddec8`,
  274 members. Agent 4 built it from 6d50d0b as U-V20 built the 0.0.5 candidate, with one difference in the evidence
  run. `tools/record_passed_tests.py --profile=release` read the REQ report of a pytest run on `git archive 6d50d0b`
  restricted to the release tests that carry a registry test ID (`-m "eqt and not manual and not latency"
  --ignore=tests/packaging/evidence`: 518 passed, 2 xfailed, 0 failed, 138 s), because the whole release-marker run
  takes about 1 h 51 min on this container (gate log of 0.0.5) and does not fit the unit. The recorder wrote "58 of 63
  registry test IDs passed", and `passed_tests` and `realised_by` equal those of the 0.0.5 release evidence. It ran in
  a clone checked out at 6d50d0b (`git_commit` 6d50d0b8d752, `git_dirty` false), then `pip wheel --no-build-isolation
  --no-deps .`. It is not Fable's release wheel. Tests without a registry test ID did not run for this wheel; they do not
  enter the evidence file.
- Lock file `requirements/py311.txt` of 6d50d0b, equal to 42074f2 (`git diff --stat 42074f2 6d50d0b -- requirements`,
  empty).
- CPython 3.11.17 (`/usr/bin/python3.11`), Linux x86-64 container, 2 CPUs, no display. Load average at the start of
  the runs 1.60, 1.61 and 1.60 (`/proc/loadavg` in each JSON): another unit's pytest of `tests/ui` held one CPU.

## Times per step

Wall time in seconds, `time.monotonic()` around each `bash -c` call, one sample per run (`verified`).

| Step | Command (verbatim from the guide) | run 1 | run 2 | run 3 | Exit |
|---|---|---|---|---|---|
| 2 | `python3.11 -m venv .venv` and `. .venv/bin/activate` | 4.181 | 4.743 | 3.836 | 0 |
| 3a | `python -m pip install --require-hashes -r requirements/py311.txt` | 19.421 | 45.716 | 55.925 | 0 |
| 3b | `python -m pip install --no-deps embodic-0.0.6-py3-none-any.whl` | 1.336 | 1.056 | 0.884 | 0 |
| 4 | `embodic` | 0.880 | 0.638 | 0.599 | -6 |
| 5b | `embodic-cli compute <example> --json outcome.json --timings` | 2.003 | 1.923 | 2.377 | 0 |
| 6 | `embodic-cli selftest` | 9.896 | 9.263 | 8.728 | 0 |
| total | steps 1, 2, 3a, 3b, 3c, 4, 5a, 5b | 28.648 | 54.643 | 64.189 | |

Verdict on REQ-N-07 on Linux (below 10 minutes): `passed` on this container, 28.6 s to 64.2 s over three cold runs
(`verified`). The total includes step 4, which aborts here in under 1 s without a display.

What limits the number. Step 3a takes 68 %, 84 % and 87 % of the total. pip printed the numpy (16.9 MB) and
PySide6-Essentials (80.1 MB) downloads at 7.4 and 5.8 MB/s, 2.9 and 3.4 MB/s, and 2.5 and 1.7 MB/s (`verified`, pip's
progress lines in the JSON records). The other steps of the total sum to 8.26 to 9.23 s. The 0.0.5 release record's
15.7 to 19.9 s came with 12.8 to 21.7 MB/s, so the slower totals here are the proxy's rate and the shared CPU, not the
product (`inferred`). A warm pip cache, a slower disk, another Python build and Windows are `not tested` here.

## Output against the guide

Every step printed the guide's expected text (`missing_expected` empty in all three JSON records):

- Step 3c. `embodic 0.0.6`, `numpy 2.4.6`, `pip 24.0`, `PySide6_Essentials 6.11.2`, `setuptools 79.0.1`, `shiboken6
  6.11.2` (`verified`).
- Step 4. Exit -6 without a display ("Available platform plugins are: ..."), as the earlier records show and as
  INSTALL.md lists under Troubleshooting on Linux. The window step is `not tested` without a display; `embodic --smoke`
  offscreen exited 0 in all three runs.
- Step 5b. `Design: Spiral, 12 coils, 16 poles`, `Design hash: sha256:ac4fab5d…9c09`, `Topology: spiral, boards: 1`,
  `Design rule check: passed` and `Timings (s): validate`, equal to the guide (`verified`, string comparison in the
  script).
- Step 6. `45 tests: 45 passed, 0 failed`, exit 0, the guide's text (`verified`).

## Rerun

```
python3.11 -I tests/independent/m5/pk06_walkthrough.py --wheel <the 0.0.6 wheel> --lock requirements/py311.txt \
    --workdir <new folder that does not exist yet> --out <run.json>
```
