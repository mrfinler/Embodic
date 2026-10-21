Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5. Unit U-V29, 2026-10-22 UTC, worktree U-V29 on main 079d471 (release 0.0.6 is tag v0.0.6 on 2bfca49).

# OR-11 and OR-12 redone on the 0.0.6 release wheel: every embodic comparator value equal to the 672297e run

D-096 rule: a record made on a candidate wheel stands for the release wheel when the two wheels differ only in `RECORD`
and in the evidence file's `build_id`, `generated_utc` and `git_commit`, and the evidence lists the same passed test
IDs. The record `tests/independent/m6/records/OR-11_OR-12_672297e.md` names the candidate wheel ad9e02c0 of 672297e.
`tests/independent/m7/v21_wheel_diff.py` finds 3 of 274 members with other bytes: `RECORD`, the evidence file (only
`build_id`, `generated_utc` and `git_commit`; `passed_tests` equal) and `embodic/_resources/icons/ICONS.md` (one table
row: the `settings.svg` use now reads "Not used; no settings window is in scope (D-094b)"). The third member breaks
the first clause of the rule, so the record does not stand for the release wheel, and the embodic half is redone. The
git subject of the record (`resources/evidence/equations.v1.json`, `docs/phase2/engineering/oracle_cases.json` and the
120 modules that its five modules import) does not change between 672297e and 2bfca49
(`tests/independent/m7/v14_record_currency.py --target 2bfca49`, entries 2 and 3). The case specification and the
scripts are unchanged.

## What ran

- Wheel: Fable's release `embodic-0.0.6-py3-none-any.whl`, SHA-256
  `fdb89189161d14b71433c4e35861d4e4d56fc6a7e64383f96ba13e27ba450101` (D-096), installed in a fresh venv
  `/home/claude/wheelvenv-0.0.6` by the two commands of `requirements/README.md` (`pip freeze --all`: embodic 0.0.6
  from that wheel, numpy 2.4.6, PySide6_Essentials 6.11.2, shiboken6 6.11.2, pip 24.0, setuptools 79.0.1). The
  installed evidence file is byte-identical to `/home/claude/release_0.0.6/passed_tests.v1.json` (`cmp`).
- `/home/claude/wheelvenv-0.0.6/bin/python -I tests/independent/m6/fea/embodic_reference.py --repo <worktree> --out
  tests/independent/m6/fea/results/embodic_reference.json`, the first step of `run.sh`. It rewrote the committed file in
  place (exit 0, 1.6 s).
- The FEA half of `run.sh` (gmsh, GetDP and scikit-fem on `or11.py` and `or12.py`) did not run again, as in the
  earlier records: its inputs are unchanged since the c25d8a9 run, and `or11.py` and `or12.py` import no embodic
  module.

## Result

`git diff --stat tests/independent/m6/fea/results` after the run shows one changed line, `embodic_file` (the venv
path). A leaf-by-leaf comparison of the new file against the 672297e run's (`git show 079d471:<file>`, every JSON leaf
compared for equality and type) gives 310 leaves on both sides, none on one side only, and one that differs,
`embodic_file` (`verified` by running it). So every comparator value (b1 and the harmonics 1 to 13 at the three radii
and both z for the three magnet permeabilities, and the four OR-12 losses with their skin depths) and
`embodic_version` are bit-identical to the 672297e run.

The FEA side is the c25d8a9 run's (`results/or11/`, `results/or12/`, unchanged in git). Its comparison with embodic
holds for the release because every embodic comparator value is equal; that conclusion is `inferred` from equal
inputs. A fresh GetDP run on 0.0.6 is `not tested`.

Verdict: OR-11 and OR-12 `passed` on the 0.0.6 release wheel, with the values and bands of the earlier records (±5 %
and ±20 %, as in U-V7). The limits of the U-V7 record stay: 2-D model only, OR-11c (3-D, EC-05) `not tested`,
F-UV7-01 and F-UV7-02 open. The redo is what the D-096 rule asks when a wheel member outside its two allowed
differences changed. It is not a claim that `ICONS.md` could change these values: no file under `src/embodic` names it
(`grep -rn ICONS.md src/embodic`, no match), and the values are bit-identical.

## Rerun

```
<venv with the 0.0.6 release wheel>/bin/python -I tests/independent/m6/fea/embodic_reference.py --repo . \
    --out tests/independent/m6/fea/results/embodic_reference.json
git diff tests/independent/m6/fea/results    # one line: embodic_file
```
