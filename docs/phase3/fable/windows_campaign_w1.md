Prepared by: Fable (coordinator), model id claude-opus-5-5. Windows campaign, part 1 (W2–W5 of
docs/phase3/verification/verification_plan.md), run 2026-10-17 on the user's laptop through the Claude desktop app.

# Windows campaign W1: install, self-test and PK-04 on the 0.0.1 wheel

Machine (read-only probe, `verified`): Windows 11 Home Single Language, build 26300 (Python's platform string
`Windows-10-10.0.26300-SP0`), 18 logical CPUs, 15.4 GB RAM, PowerShell 5.1.26100, git present, no Python installed (only
the WindowsApps store aliases), no `py` launcher, execution policy `Restricted` (all scopes Undefined). The user's
network during the run delivered about 0.03 MB/s on Wi-Fi (measured over 20 s while pip downloaded PySide6).

## W2 Python inside the embodic folder (D-049f)

`https://www.nuget.org/api/v2/package/python/3.11.9` (owners CPython, steve.dower on nuget.org) downloaded in 58.1 s,
17,478,009 bytes, SHA-256 `9283876D58C017E0E846F95B490DA3BCA0FC0A6EE1134B2870677CFB7EEC3C67`, extracted to
`%USERPROFILE%\Desktop\embodic\.python` (added to `.git/info/exclude`). `.python\tools\python.exe -V` → `Python 3.11.9`;
`venv` and `ensurepip` import (`verified`).

## W3–W4 PK-06 walkthrough, run 1 (INSTALL.md steps 2–6)

Script `_campaign/pk06_walkthrough.ps1` (in the user's folder, git-excluded), run with
`powershell -ExecutionPolicy Bypass -File …` (process scope only; the user's policy is unchanged). Deviation from
INSTALL.md: `py -3.11` → the in-folder `.python\tools\python.exe` (no launcher). Times (`verified`, steps.tsv):

| Step | Seconds | Exit |
|---|---|---|
| 1 python version | 0.08 | 0 |
| 2 venv | 10.95 | 0 |
| 2 activate | 0.21 | 0 (only because the process policy was Bypass; under the user's Restricted policy Activate.ps1 is blocked — DEF-W-04) |
| 3a lock file | 4137.15 | 0 (PySide6-Essentials 76.9 MB at the user's network rate; numpy came from the user's existing pip cache) |
| 3b wheel | 1.40 | 0 |
| 3c pip list | 0.52 | 0 — embodic 0.0.1, numpy 2.4.6, pip 24.0, PySide6_Essentials 6.11.2, setuptools 65.5.0, shiboken6 6.11.2 (matches INSTALL.md §3) |
| 5 compute | 4.12 | 0 — design hash `ac4fab5d…9c09` as in the guide; timings validate 0.001, geometry 0.019, drc 0.348, physics 0.625 s |
| first computed example | 4154.54 | — |
| 5 validate | 0.46 | 0 |
| 5 export svg | 3.75 | 0 |
| 6 selftest | 9.08 | 0 — `45 tests: 45 passed, 0 failed` |

PK-06's 10-minute criterion: not met in run 1 (4154.5 s), entirely from the download (step 3a is 99.6 % of the time);
without the download the steps took about 17 s. A warm-cache run 2 is still to run (`not tested`). Step 4 (the window)
was not run in run 1.

## W5 PK-04 (REQ-N-04: 1e-9 rel. across platforms)

On Windows the installed wheel's source hash equals the evidence's (`cfefe405…baae`) and the evidence applies (52 ids,
build `0.0.1+g5e74acc4e79b.20261012T212510Z`) — the §3.1 hash rule is platform-independent (`verified`).
The repository's Linux reference (`docs/phase3/verification/reference/linux`) was produced without the evidence file, so
statuses differ from any wheel install (not a platform difference). Fable regenerated the Linux reference from the same
0.0.1 wheel (`/home/claude/wheelvenv`) and compared it with the Windows output (`verified`, pk04_compare.py plus a
per-example summary):
- Every number agrees within 1e-9 rel. except `/analysis/emf_waveform_v/value/0` of spiral_12c16p_default: 2.745e-15 V
  (Linux) vs 2.723e-15 V (Windows), a sample whose true value is 0 — rounding noise; a pure relative rule cannot pass it
  (DEF-W-03, criterion).
- `boards/layout_hashes` and `boards/stack_hash` differ on all five examples: the hashes are over float bytes, which
  differ by an ulp between the platforms' maths libraries; REQ-N-04 promises byte identity on one platform only (DEF-W-02,
  contract: the hash is a same-platform identity).
- Wave example: the 186 DRC violations are the same set with equal values on both platforms (key kind/layer/objects), but
  in a different order on Windows; on Linux the order is stable across `PYTHONHASHSEED` 1 and 2 (`verified`), so the order
  depends on float noise (DEF-W-01, product: the violation list needs a canonical order).
Verdict: PK-04 `failed` as written; numerically the platforms agree; three defects to fix (two in the criterion/contract,
one in the product).

## Run 2 (warm pip cache) and the real display

Run 2 of the same script, 2026-10-17, new folder and venv, packages from the pip cache (`verified`, steps.tsv): python
0.05 s, venv 4.77 s, activate 0.08 s, lock file 10.59 s, wheel 1.47 s, pip list 0.53 s, compute 3.97 s — first computed
example after 21.57 s (PK-06's 10 minutes met with a warm cache); validate 0.51 s, export svg 3.93 s, selftest 9.26 s
(45 of 45). Step 4 on the real display: `embodic --smoke` (Windows platform plugin, not offscreen) opened the window,
loaded D08, computed and exited 0 in 6.83 s (`verified`). Display: Intel Arc graphics, 1920 × 1200 physical, 1536 × 960
logical (125 % scaling), one screen. The interactive window and the UI rows of U-S7 wait for 0.0.2 (D-049g).
