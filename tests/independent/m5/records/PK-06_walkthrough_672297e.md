Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5 (unit U-V28, 2026-10-21 UTC)

# PK-06 Linux walkthrough redone for 0.0.6 on candidate main 672297e

D-061d: the record `tests/independent/m5/records/PK-06_walkthrough_6d50d0b.md` names Agent 4's wheel 5d891a26 of
6d50d0b. Its subject is the guide, the lock file and the wheel's inputs (README.md, docs/install/INSTALL.md,
requirements/py311.txt, pyproject.toml, src/embodic, resources). `git diff --stat 6d50d0b 672297e -- <those paths>`
gives `1 file changed, 2 insertions(+), 2 deletions(-)`: two rows of the guide's key table in
`src/embodic/ui/strings/results.py` (U-M9e, D-094b; `tests/independent/m7/v14_record_currency.py --target 672297e`,
entry 0). In the wheel, 3 of 274 members have other bytes: that file, the evidence file and `RECORD`
(`tests/independent/m7/v21_wheel_diff.py`, in `docs/phase3/verification/manual_records_0.0.6_672297e_currency.txt`).
The record does not stand for 672297e, and this record redoes the Linux walkthrough. The Windows walkthrough is a
person's check on the user's laptop and is not redone here.

What ran. `tests/independent/m5/pk06_walkthrough.py`, unchanged, followed `docs/install/INSTALL.md` steps 1 to 6 three
times, each in a new empty folder with a new Python 3.11 venv and a new empty `PIP_CACHE_DIR`. The raw output of every
step is in `pk06_672297e_run1.json` to `pk06_672297e_run3.json`.

Inputs (`verified`):

- Wheel `embodic-0.0.6-py3-none-any.whl`, SHA-256 `ad9e02c073c45668938621ebeea8f8ca9b42cae9036c869a0871de3da2802aaa`,
  274 members. Agent 4 built it from 672297e as U-V27 built the 6d50d0b candidate.
  `tools/record_passed_tests.py --profile=release` read the REQ report of a pytest run on `git archive 672297e`
  restricted to the release tests that carry a registry test ID (`-m "eqt and not manual and not latency"
  --ignore=tests/packaging/evidence`: 518 passed, 2 xfailed, 0 failed, 141 s). The recorder wrote "58 of 63 registry
  test IDs passed". It ran in a clone checked out at 672297e (`git_commit` 672297ecd342, `git_dirty` false), then `pip
  wheel --no-build-isolation --no-deps .`. Against wheel 5d891a26 the evidence file differs in `build_id`,
  `generated_utc`, `git_commit` and `source_sha256`; `passed_tests`, `realised_by`, `embodic_version` and
  `git_dirty` are equal. It is not Fable's release wheel. Tests without a registry test ID did not run for this wheel;
  they do not enter the evidence file.
- Lock file `requirements/py311.txt` of 672297e, equal to 6d50d0b (`git diff --stat 6d50d0b 672297e -- requirements`,
  empty).
- CPython 3.11.17 (`/usr/bin/python3.11`), Linux x86-64 container, 2 CPUs, no display. Load average at the start of
  the runs 0.52, 0.48 and 1.02 (`/proc/loadavg` in each JSON); unit U-S19 ran beside this one.

## Times per step

Wall time in seconds, `time.monotonic()` around each `bash -c` call, one sample per run (`verified`).

| Step | Command (verbatim from the guide) | run 1 | run 2 | run 3 | Exit |
|---|---|---|---|---|---|
| 2 | `python3.11 -m venv .venv` and `. .venv/bin/activate` | 3.874 | 5.054 | 4.245 | 0 |
| 3a | `python -m pip install --require-hashes -r requirements/py311.txt` | 104.250 | 106.841 | 23.137 | 0 |
| 3b | `python -m pip install --no-deps embodic-0.0.6-py3-none-any.whl` | 1.036 | 0.996 | 0.942 | 0 |
| 4 | `embodic` | 0.576 | 0.634 | 0.546 | -6 |
| 5b | `embodic-cli compute <example> --json outcome.json --timings` | 1.748 | 1.805 | 2.013 | 0 |
| 6 | `embodic-cli selftest` | 8.660 | 9.905 | 8.698 | 0 |
| total | steps 1, 2, 3a, 3b, 3c, 4, 5a, 5b | 112.003 | 115.975 | 31.499 | |

Verdict on REQ-N-07 on Linux (below 10 minutes): `passed` on this container, 31.5 s to 116.0 s over three cold runs
(`verified`). The total includes step 4, which aborts here in under 1 s without a display.

What limits the number. Step 3a takes 93 %, 92 % and 73 % of the total. pip printed the numpy (16.9 MB) and
PySide6-Essentials (80.1 MB) downloads at 0.45 and 1.8 MB/s, 1.1 and 0.98 MB/s, and 4.5 and 8.2 MB/s (`verified`,
pip's progress lines in the JSON records). The other steps of the total sum to 7.75 to 9.13 s, the range of the
6d50d0b record (8.26 to 9.23 s). So the longer totals of runs 1 and 2 are the proxy's rate, not the product
(`inferred`). A warm pip cache, a slower disk, another Python build and Windows are `not tested` here.

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
