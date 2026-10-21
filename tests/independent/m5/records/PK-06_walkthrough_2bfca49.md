Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5 (unit U-V29, 2026-10-22 UTC)

# PK-06 Linux walkthrough redone for the 0.0.6 release wheel (tag v0.0.6, 2bfca49)

D-096 rule: a record made on a candidate wheel stands for the release wheel when the two wheels differ only in `RECORD`
and in the evidence file's `build_id`, `generated_utc` and `git_commit`, and the evidence lists the same passed test
IDs. The record `tests/independent/m5/records/PK-06_walkthrough_672297e.md` names the candidate wheel ad9e02c0 of
672297e. `tests/independent/m7/v21_wheel_diff.py` finds 3 of 274 members with other bytes: `RECORD`, the evidence file
(only `build_id`, `generated_utc` and `git_commit`; `passed_tests` equal) and `embodic/_resources/icons/ICONS.md` (one
table row, D-094b). The third member breaks the first clause of the rule. The git subject of the record (README.md,
docs/install/INSTALL.md, requirements/py311.txt, pyproject.toml, src/embodic, resources) changes in the same file
between 672297e and 2bfca49 (`git diff --stat`: `resources/icons/ICONS.md | 2 +-`; `v14_record_currency.py --target
2bfca49`, entry 0). The record does not stand for the release, and this record redoes the Linux walkthrough. The
Windows walkthrough is a person's check on the user's laptop and is not redone here.

What ran. `tests/independent/m5/pk06_walkthrough.py`, unchanged, followed `docs/install/INSTALL.md` steps 1 to 6 three
times, each in a new empty folder with a new Python 3.11 venv and a new empty `PIP_CACHE_DIR`. The raw output of every
step is in `pk06_2bfca49_run1.json` to `pk06_2bfca49_run3.json`.

Inputs (`verified`):

- Wheel: Fable's release `embodic-0.0.6-py3-none-any.whl` from `/home/claude/release_0.0.6/`, SHA-256
  `fdb89189161d14b71433c4e35861d4e4d56fc6a7e64383f96ba13e27ba450101`, the value D-096 records. The copy in each run
  folder has that hash (`sha256sum`), and the evidence file each run installed is byte-identical to
  `/home/claude/release_0.0.6/passed_tests.v1.json` (`cmp`).
- Lock file `requirements/py311.txt` of 079d471, equal to 672297e and 2bfca49 (`git diff --stat 672297e 2bfca49 --
  requirements`, empty).
- CPython 3.11.17 (`/usr/bin/python3.11`), Linux x86-64 container, 2 CPUs, no display. Load average at the start of
  the runs 0.33, 0.48 and 0.70 (`/proc/loadavg` in each JSON). During run 1 I also ran the OR-11/OR-12 reference
  script (1.6 s) and the currency lever (a few seconds of imports); the brief says nothing else runs on the machine
  (`assumption` for work outside this unit).

## Times per step

Wall time in seconds, `time.monotonic()` around each `bash -c` call, one sample per run (`verified`).

| Step | Command (verbatim from the guide) | run 1 | run 2 | run 3 | Exit |
|---|---|---|---|---|---|
| 2 | `python3.11 -m venv .venv` and `. .venv/bin/activate` | 4.102 | 3.878 | 3.875 | 0 |
| 3a | `python -m pip install --require-hashes -r requirements/py311.txt` | 39.476 | 43.402 | 15.023 | 0 |
| 3b | `python -m pip install --no-deps embodic-0.0.6-py3-none-any.whl` | 1.124 | 0.898 | 0.995 | 0 |
| 4 | `embodic` | 0.615 | 0.611 | 0.618 | -6 |
| 5b | `embodic-cli compute <example> --json outcome.json --timings` | 1.934 | 1.594 | 1.760 | 0 |
| 6 | `embodic-cli selftest` | 8.545 | 8.846 | 8.489 | 0 |
| total | steps 1, 2, 3a, 3b, 3c, 4, 5a, 5b | 47.860 | 50.890 | 22.854 | |

Verdict on REQ-N-07 on Linux (below 10 minutes): `passed` on this container, 22.9 s to 50.9 s over three cold runs
(`verified`). The total includes step 4, which aborts here in under 1 s without a display.

What limits the number. Step 3a takes 82 %, 85 % and 66 % of the total. pip printed the numpy (16.9 MB) and
PySide6-Essentials (80.1 MB) downloads at 2.6 and 2.1 MB/s, 1.9 and 1.7 MB/s, and 11.0 and 5.3 MB/s (`verified`,
pip's progress lines in the JSON records). The other steps of the total sum to 7.49 to 8.38 s, inside the range of
the 672297e record (7.75 to 9.13 s). So the spread of the totals is the proxy's rate, not the product (`inferred`). A
warm pip cache, a slower disk, another Python build and Windows are `not tested` here.

## Output against the guide

Every step printed the guide's expected text (`missing_expected` empty for every step in all three JSON records):

- Step 3c. `embodic 0.0.6`, `numpy 2.4.6`, `pip 24.0`, `PySide6_Essentials 6.11.2`, `setuptools 79.0.1`, `shiboken6
  6.11.2` (`verified`).
- Step 4. Exit -6 without a display ("Available platform plugins are: ..."), as the earlier records show and as
  INSTALL.md lists under Troubleshooting on Linux. The window step is `not tested` without a display; `embodic --smoke`
  offscreen exited 0 in all three runs.
- Step 5b. `Design: Spiral, 12 coils, 16 poles`, `Design hash: sha256:ac4fab5d…9c09`, `Topology: spiral, boards: 1`,
  `Design rule check: passed` and `Timings (s): validate`, equal to the guide (`verified`, string comparison in the
  script).
- Step 6. `45 tests: 45 passed, 0 failed`, exit 0, the guide's text (`verified`).

The redo gave the result of the 672297e record. It is what the D-096 rule asks when a wheel member outside its two
allowed differences changed, not a claim that `ICONS.md` could change the walkthrough.

## Rerun

```
python3.11 -I tests/independent/m5/pk06_walkthrough.py --wheel <the 0.0.6 release wheel> --lock requirements/py311.txt \
    --workdir <new folder that does not exist yet> --out <run.json>
```
