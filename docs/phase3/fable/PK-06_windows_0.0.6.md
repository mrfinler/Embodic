Prepared by: Fable (coordinator) - model: claude-opus-5-5

# PK-06 record on the reference laptop, release 0.0.6 (REQ-N-07)

- Date: 2026-10-22, 12:22 and 12:23 local time (UTC+8; 04:22 and 04:23 UTC). The user started
  `_campaign\run_0.0.6_pk06_v2.cmd`; nothing else ran on the laptop.
- Machine: the user's laptop, Windows 11 Home, CPython 3.11.9 from the NuGet package inside the folder (D-049f).
- Build: the release wheel `embodic-0.0.6-py3-none-any.whl`, SHA-256
  `fdb89189161d14b71433c4e35861d4e4d56fc6a7e64383f96ba13e27ba450101`, checked on the laptop before the gate run of
  D-098 (`w11_status_0.0.6.txt`). `pip list` in each run shows `embodic 0.0.6`.
- Script: `_campaign\pk06_walkthrough_v2.ps1`. It follows `docs/install/INSTALL.md` steps 2 to 6 in a new folder per
  run, with a new venv, the hashed lock file `requirements\py311.txt`, then the wheel with `--no-deps`. One deviation:
  the in-folder Python replaces `py -3.11`, because the laptop has no `py` launcher. The pip cache was the user's
  default cache (warm). Version 2 of the script records a program that never starts as `not-started`, and its helper
  is named `Invoke-EmbodicCli` (D-100a).

## Results

| Step | Run 11: `embodic-cli`, as INSTALL.md writes it | Run 12: `python -m embodic.cli` |
|---|---|---|
| 2 venv and activate | 4.95 s, exit 0 | 4.84 s, exit 0 |
| 3a lock file, `--require-hashes` | 12.19 s, exit 0 | 10.83 s, exit 0 |
| 3b wheel, `--no-deps` | 1.26 s, exit 0 | 1.25 s, exit 0 |
| 5 compute the default spiral | 3.23 s, exit 0 | 1.68 s, exit 0 |
| Time to the first computed example | 22.32 s | 19.29 s |
| 5 validate (design rule check passed) | 0.52 s, exit 0 | 0.41 s, exit 0 |
| 5 export SVG | 2.58 s, exit 0 | 2.43 s, exit 0 |
| 6 self-test | 7.54 s, exit 0, "45 tests: 45 passed, 0 failed" | 7.09 s, exit 0, "45 tests: 45 passed, 0 failed" |

The two runs gave the same `outcome.json` (SHA-256 `d1e0787a…d0fb` in both). The two `board.svg` files are 63706
bytes each and differ in one attribute only, `generated_utc` (04:22:45Z against 04:23:15Z), read with `diff`.

Logs on the laptop: `_campaign\pk06_run11.log`, `_campaign\pk06_run12.log`, and `steps.tsv` in each run folder. The
logs print the full path of the venv's Python, which holds the Windows account name, so they stay on the laptop
(order 6). The numbers above are copied from `steps.tsv`.

## Runs that do not count

- Run 8 (D-098b): Application Control blocked `embodic-cli.exe` at every call, and version 1 of the script logged exit
  0 for those steps. Not passed.
- Runs 9 and 10: the script's helper `Cli` was shadowed by the built-in PowerShell alias `cli` (Clear-Item), so no
  embodic command ran. A defect in Fable's script, not a product result.

## Verdict

- PK-06 on Windows passes on 0.0.6, both ways: 22.3 s and 19.3 s to the first computed example against the 10 minute
  bound, and the self-test 45 of 45 (`verified`, warm pip cache).
- The same runs meet the Windows cells of PK-02 (the hashed lock file and the wheel install in a clean venv) and
  PK-11 (`embodic-cli selftest` in a clean venv that holds only the lock file and the wheel prints 45 of 45), as
  `docs/phase2/architecture/test_plan.md` writes those criteria (`verified`, run 11; run 12 for the `python -m` form).
- The policy that blocked `embodic-cli.exe` in run 8 and in the release run of D-099 let it run in run 11, about 40
  minutes after the release gate ended (11:41 local, `w10_status_0.0.6.txt`). Its decisions are not uniform, and the
  cause is `inferred` (D-098b). DEF-W-16 stays open.
- PK-06 cold on Windows has no run since 0.0.2 (D-084e). `python -m embodic.ui.app` was not opened on Windows.
