Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5

# Phase 3 verification plan (U-V6, 2026-10-16)

This plan says what Phase 3 checks, in which order, and what must hold before Phase 4 (acceptance) starts. It has four
parts: the requirement audit of release 0.0.1, the Windows campaign on the user's laptop (D-048d), the campaigns that run
in the cloud container now, and the exit criteria. Nothing in the Windows campaign has run. Every Windows item is
`not tested` until Fable runs it and a record exists.

The build under audit is release 0.0.1, built by Fable's release gate on main 5e74acc (D-047). Main 99647cb has the same
`src/` tree: `diff -rq src /home/claude/wt/release2/src` lists only `__pycache__` folders (`verified` by running). The
installed sources hash to `cfefe405be515c4ba107c38b02a5e5dbaacc220ccc1e0e5a70033d919f78baae` (`package_source_sha256`,
interfaces.md §3.1), the value D-047 records for the evidence file (`verified` by running `checks/pk04_reference.py`).
The release wheel in `/home/claude/release_0.0.1/` has SHA-256
`f114a6e7f00d49081d61dc5090da3364fadb3f7b5b3d602a27e0c9183537dcd0` (`verified` by `sha256sum`).

Files of this unit:

- `checks/req_audit.py` writes `req_audit.md`, the audit table. `--check` exits 1 when the table is stale.
- `checks/pk04_reference.py` writes the outcome of `embodic-cli compute --json` for the five packaged examples and a
  manifest. `reference/linux/` holds its Linux output.
- `checks/pk04_compare.py` compares two such folders at 1e-9 relative. `--self-test` shows that it fails a 2e-9 change.
- `checks/lock_windows_check.py` checks that each pin of a lock file has a hashed CPython 3.11 Windows x64 wheel on PyPI.

## 1. Requirement audit of release 0.0.1

### How the audit decides

`python3 docs/phase3/verification/checks/req_audit.py` reads `requirements.md`, the two test plans, the REQ report
(`/home/claude/release_0.0.1/req_report.json`, 3125 records: 3114 passed, 11 skipped or xfailed) and the gate log of the
release run (`gate_release_5e74acc.log`), and the test sources of that run (`/home/claude/wt/release2/tests`). The
release trace matrix (`/home/claude/wt/release2/build/trace_matrix.md`) counts tests per REQ marker only. The audit also
asks whether each test ID that the row plans has evidence:

| Evidence | Meaning |
|---|---|
| gate | a PASS line of the gate log names the ID (MT-01, MT-02, MT-03, TR-01, TR-02, TR-05, PK-10) |
| name | every record with the row's REQ marker and the ID in its test name passed |
| file | no test name holds the ID, and a passing record with the row's REQ marker is in a file whose text names it |
| eqt | the test plans map the ID to an EQ-nn, and a passing record with the row's REQ marker carries an EQT-nn id |
| record | an Agent 4 record under `tests/independent` covers the ID outside pytest (PK-06 Linux, AX-05, AX-06) |
| skip, fail | the only records found were skipped or xfailed, or one failed |
| none | nothing above |

A row is `verified` when every planned ID has gate, name, file, eqt or record evidence and no ID needs another machine.
It is `partial` when some evidence exists but an ID lacks it or needs Windows, a real display or an FEA solver. It is
`not testable here` when only such IDs remain, and `not tested` otherwise. The script matches IDs by text. It does not
read whether a test checks the acceptance text as written, so a `verified` row means "a passing test names the planned
ID", and "the test checks the criterion" is `inferred`. Campaign V3-01 reads a sample to test that inference.

I checked that the rule bites (`verified` by running the audit function on edited copies of the report): REQ-T-07 drops
from `verified` to `not tested` when its records are removed or skipped, and REQ-F-15 drops to `partial` when the
`ut_io_03` records fail. The first version of the script read only three-letter UT groups and dropped UT-IO-xx from five
rows. That version was fixed before the counts below.

### Counts (run 2026-10-16, Linux container, `python3` 3.11.15)

```
109 requirements: not tested 10, partial 21, verified 62, withdrawn 16
must rows: not tested 4, partial 19, verified 50
planned-test evidence: eqt 14, file 29, gate 9, name 164, none 35, record 5, skip 1
```

No row is `not testable here`: every row that needs Windows or FEA also has evidence from Linux. The 16 withdrawn rows
are the REQ-K rows (D-009). MT-07 guards them, and the release run passed its records.

### Rows that are not `verified`, by cause

Cause A, needs Windows, a real display or FEA (7 rows, all must). REQ-N-04 (PK-04), REQ-N-05 (PK-01 Windows cells),
REQ-N-06 (PK-05, whose 6 bundle tests skipped in the release run), REQ-N-07 (PK-06 Windows half; the Linux half is the
U-V5 record), REQ-N-16 and REQ-N-24 (AX-06 Narrator), REQ-F-11 (OR-11 and OR-12, Phase 3 FEA, D-045b). Part 2 and
V3-11, V3-12 close them.

Cause B, a planned ID that no passing test names (14 rows: 12 must, REQ-F-20 could, REQ-F-29 should). REQ-F-03 (UT-GEO-24,
UT-GEO-26, UT-PHY-07), REQ-F-04 (GR-07), REQ-F-05 (UT-PHY-11, PR-01), REQ-F-06 (UT-GEO-25), REQ-F-08 (UT-PHY-09),
REQ-F-10 (UT-DRC-01, PR-13), REQ-F-12 (UT-PHY-08, GR-05), REQ-F-14 (BV-05), REQ-F-20 (UT-RES-02), REQ-F-29 (UT-EXP-05),
REQ-N-21 (UT-EXP-02), REQ-N-27 (AX-01), REQ-T-08 (UT-PHY-13, UT-PHY-21), REQ-T-15 (PR-12). Every one of these rows has
passing REQ-marked tests (1 to 303). The gap can be a test that checks the ID without naming it, or a test that does not
exist. One example of the first kind: test_plan.md §5.1 (revision U-D5) says the series-pair tests labelled UT-GEO-19
are UT-GEO-26, so UT-GEO-26 exists under another label (`verified` by reading). V3-01 settles each ID.

Cause C, no test carries the REQ marker (10 rows: 4 must, 6 should or could). The must rows are REQ-T-10 (LG-03),
REQ-T-11 (LG-04), REQ-L-03 (LG-05) and REQ-L-05 (LG-06). The others are REQ-F-30 (UI-20; test_plan.md §5.3.1 says UI-20
has no test), REQ-N-20 (UT-LOG-01), REQ-T-12 (UI-13), REQ-L-02 (LG-02), REQ-L-06 and REQ-L-09 (LG-07). No file under
`tests/` names LG-02 to LG-07, UI-13, UI-20 or UT-LOG-01 in any spelling (`verified` by a scan of the release tree). For
REQ-L-03, two UX-AC-03 tests check that example titles and exported examples name no other program, but they carry
REQ-F-25, and the second also REQ-F-38 (`tests/ui/qt_design/test_ruling_g.py` l.176-177 and
`tests/unit/embodic_io/project/test_examples.py` l.63-68, `verified` by reading). V3-14 writes independent scans for the
four must rows.

## 2. Windows campaign on the user's laptop

Context (D-048d): Windows 10 or 11 x64, the Claude desktop app, the folder `%USERPROFILE%\Desktop\embodic` is a git
checkout at bae5a26 or later, and no Python is known to be installed. Fable runs every step through the desktop app and
asks the user before W3 (installer), before W4.2 if the execution policy must change, and before any step that writes
outside the embodic folder.

Rules for every step:

- Each command comes from `docs/install/INSTALL.md`, cited by step, or is marked **new** with its reason.
- Write paths with `%USERPROFILE%` or `$env:USERPROFILE`. A record holds no Windows account name (standing order 7).
  Replace the user folder in every pasted output with `%USERPROFILE%` before the record is committed.
- A shell tool call can time out. The desktop-device shell tool in this session's tool list allows at most 45 s per
  call (`inferred` from the tool schema here; Fable's tool can differ). Run W4.3, W7, W8 and W9 detached with output to
  a log, then poll the log (**new**, reason: the timeout):
  `Start-Process -FilePath .venv\Scripts\python.exe -ArgumentList '<args>' -RedirectStandardOutput <step>.log -RedirectStandardError <step>.err -NoNewWindow`.
- Each tool call can start a new shell, so `Activate.ps1` may not carry over. After W4.2, call
  `.venv\Scripts\python.exe` in place of `python` and `.venv\Scripts\embodic-cli.exe` in place of `embodic-cli`
  (**new** form of the INSTALL commands, reason: activation is per shell). Record which form ran.

What to record per step: the command as run, start and end time (`Get-Date -Format o`, **new**, reason: timing), the
exit code (`$LASTEXITCODE`), the last 20 lines of output, and one status label. The record goes to
`docs/phase3/verification/records/windows_campaign_<date>.md`, with logs and JSON beside it in
`records/windows_<date>/`.

### W0. Prepare in the cloud (Fable)

1. Check the lock files for Windows wheels: `python3 docs/phase3/verification/checks/lock_windows_check.py
   requirements/py311.txt requirements/py311-dev.txt`. Result on 2026-10-16: every pin passes, 3 of 3 runtime and 41
   of 41 dev, each with a hashed `cp311-win_amd64`, `abi3-win_amd64`, `py3-none-win_amd64` or pure wheel (`verified` by
   running; a copy of `py311.txt` with the numpy `win_amd64` hash removed fails with exit 1). Step 3 should therefore not
   stop on a missing hash (`inferred`; pip on Windows is `not tested`).
2. Commit `docs/phase3/verification/**`, or copy `docs/phase3/verification/checks` and `reference/linux` into the
   laptop folder at the same paths.
3. Copy the release wheel to `%USERPROFILE%\Desktop\embodic\embodic-0.0.1-py3-none-any.whl`. The wheel is not in the
   checkout: INSTALL.md step 8 builds it, and that step runs after this one.

### W1. Identify the checkout (new commands, reason: the record must name what ran)

```
cd "$env:USERPROFILE\Desktop\embodic"
git rev-parse HEAD
git status --short
git config --get core.autocrlf
Get-FileHash .\embodic-0.0.1-py3-none-any.whl -Algorithm SHA256
[System.Environment]::OSVersion.VersionString
Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors
```

Expected: HEAD is bae5a26 or a later main commit, the status is empty, and the wheel hash is `F114A6E7…DCD0` (the full
value is above). `core.autocrlf` matters for W7: with `true`, git writes the `.py` files with CRLF, and the editable
install then hashes to another `source_sha256` than the wheel (`inferred` from `package_source_sha256`, which hashes
file bytes, `src/embodic/results/registry.py` l.228-243).

### W2. Look for Python

```
py --version
python --version
py -3.11 --version
```

The first two come from the brief. The third is INSTALL.md step 1. If `py -3.11 --version` prints `Python 3.11.`
followed by a patch number, skip W3. If `python` prints a Microsoft Store message, treat Python as absent (the message
text is an `assumption`; record what it printed).

### W3. Install CPython 3.11 for the current user (only if W2 found none; Fable asks the user first)

python.org gives no Windows installer for 3.11 after 3.11.9. The 3.11.17 page (released 2026-10-01) says "binary
installers are no longer provided for it", and the 3.11.9 page lists "Windows installer (64-bit)" at
`https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe`, 25.0 MB, MD5 `e8dcd502e34932eebcaf1be056d5cbcd`,
with a Sigstore file and no SHA-256 (`verified` by reading https://www.python.org/downloads/release/python-31117/ and
https://www.python.org/downloads/release/python-3119/ on 2026-10-16). The cloud proxy refused a download of the
installer from www.python.org (`curl: (56) CONNECT tunnel failed, response 403`), so its SHA-256 is `unresolved`.

```
Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe -OutFile "$env:TEMP\python-3.11.9-amd64.exe"
Get-FileHash "$env:TEMP\python-3.11.9-amd64.exe" -Algorithm MD5
[Environment]::GetEnvironmentVariable('Path', 'User')
Start-Process -Wait -FilePath "$env:TEMP\python-3.11.9-amd64.exe" -ArgumentList '/quiet','InstallAllUsers=0','Include_launcher=1','InstallLauncherAllUsers=0','PrependPath=0','AppendPath=0','AssociateFiles=0','Shortcuts=0','Include_test=0'
[Environment]::GetEnvironmentVariable('Path', 'User')
py -3.11 --version
```

All six commands are **new**. Reasons: download, integrity check against the python.org MD5, the user PATH before and
after, the silent install, and the INSTALL.md step 1 check. Expected: the MD5 equals the page, the last line prints
`Python 3.11.9`.

The switches come from "4.1.3. Installing Without UI" of https://docs.python.org/3.11/using/windows.html (`verified` by
reading on 2026-10-16):

| Switch | Page text | Why |
|---|---|---|
| `/quiet` | "To completely hide the installer UI and install Python silently, pass the /quiet option." | the desktop app cannot click |
| `InstallAllUsers=0` | "Perform a system-wide installation", default 0 | per-user |
| `Include_launcher=1` | "Install Python Launcher for Windows", default 1 | INSTALL.md uses `py -3.11` |
| `InstallLauncherAllUsers=0` | "Installs the launcher for all users", default 1 | §4.1.1 says a per-user install needs no administrator "unless … you install the Python Launcher for Windows for all users" |
| `PrependPath=0`, `AppendPath=0` | "Prepend (Append) install and Scripts directories to PATH", default 0 | no PATH change; `py` and the venv need none |
| `AssociateFiles=0` | "Create file associations if the launcher is also installed", default 1 | no file associations |
| `Shortcuts=0` | "Create shortcuts for the interpreter, documentation and IDLE", default 1 | nothing outside the user folder |
| `Include_test=0` | "Install standard library test suite", default 1 | smaller install, as the page's own examples do |

Install folder: the default for a just-for-me install is `%LocalAppData%\Programs\Python\Python311` (same page, table
row `DefaultJustForMeTargetDir`). Whether the per-user launcher adds itself to the user PATH is `unresolved`: the page
does not say. The two PATH lines above record it. §4.1.1 also says a C runtime update can still need an administrator;
if the installer asks, stop and tell the user.

### W4. PK-06 Windows half: timed walkthrough of INSTALL.md steps 1 to 6 (REQ-N-07)

Start the clock before W4.1 and stop it when step 5's `compute` prints `Design rule check: passed`. Criterion: less than
10 minutes (REQ-N-07). Record whether the pip cache was empty with `py -3.11 -m pip cache info` (**new**, reason: U-V5
found the download dominates the time, `tests/independent/m5/records/PK-06_walkthrough.md`).

1. Step 1: `py -3.11 --version`.
2. Step 2: `py -3.11 -m venv .venv`, then `.venv\Scripts\Activate.ps1`. If PowerShell refuses the script, the INSTALL.md
   Windows troubleshooting command is `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. It changes a user setting, so
   Fable asks the user first, or skips activation and uses the `.venv\Scripts\` form.
3. Step 3: `python -m pip install --require-hashes -r requirements\py311.txt`, then
   `python -m pip install --no-deps embodic-0.0.1-py3-none-any.whl`, then `python -m pip list`. Expected: `embodic 0.0.1`,
   `numpy 2.4.6`, `PySide6_Essentials 6.11.2`, `shiboken6 6.11.2`, plus pip and setuptools.
4. Step 4: `embodic --smoke` (**new** on Windows: INSTALL.md gives it under "Troubleshooting on Linux" with
   `QT_QPA_PLATFORM=offscreen`; here it runs on the real display, opens the window, computes D08 and exits 0, so the
   clock does not wait for a person to close the window). The plain `embodic` of step 4 runs in W6.
5. Step 5: `python -c "from embodic.paths import resource_root; print(resource_root() / 'examples')"`, then
   `embodic-cli compute <examples>\spiral_12c16p_default.embodic.json --json outcome.json --timings`,
   `embodic-cli validate <examples>\spiral_12c16p_default.embodic.json` and
   `embodic-cli export <examples>\spiral_12c16p_default.embodic.json --format svg -o board.svg`. Expected: the design hash
   `sha256:ac4fab5db06f9e8f733dc495080deeddfe0bcf58faa31ebb7ec841c1b27d9c09`, `Valid: Spiral, 12 coils, 16 poles` and
   `Wrote board.svg`. The Linux reference run printed the same hash on 2026-10-16 (`verified`).
6. Step 6 (after the clock stops): `embodic-cli selftest`. Expected: last line `45 tests: 45 passed, 0 failed`, exit 0.
   This is PK-11 on Windows.

### W5. PK-04: Windows outcome against the Linux reference (REQ-N-04)

No test or script implements PK-04: no file under `tests/` names it (`verified` by the scan of part 1). These two
commands are **new**, reason: PK-04 has no lever on main.

```
python docs\phase3\verification\checks\pk04_reference.py --out docs\phase3\verification\reference\windows
python docs\phase3\verification\checks\pk04_compare.py docs\phase3\verification\reference\linux docs\phase3\verification\reference\windows
```

Run them in the W4 venv, before W7 replaces the wheel with the editable install. The Linux reference files are
`docs/phase3/verification/reference/linux/{serpentine_16p_example, spiral_12c10p_d08, spiral_12c14p,
spiral_12c16p_default, wave_16p_example}.json` and `manifest.json`. They came from `pk04_reference.py` on 2026-10-16:
Linux x86-64, CPython 3.11.15, NumPy 2.4.6, source hash `cfefe405…baae`. Four examples exit 0, and the wave example exits
2 with 186 DRC violations (D-034). The comparison refuses (exit 2) when the source hash, embodic or NumPy version differ,
so it never compares two builds. It passes when every float agrees within `abs(a - b) <= 1e-9 * max(|a|, |b|)`, every
other value is equal, the exit codes are equal, and only `/versions/python` differs. Expected output on success:
`PK-04 passed at rel 1e-09`. The self-test (`--self-test`) gave exit 0 for a copy, exit 1 for a 2e-9 change and exit 0
for a 5e-10 change of one Ke value (`verified` by running). The script also prints whether each file is byte-identical.
That is information only, because REQ-N-04 asks for byte identity on one platform, not across platforms.

### W6. The app on the real display

1. INSTALL.md step 4: `embodic`. The user confirms that the window opens and then closes it. Record the window title
   and one screenshot.
2. `embodic --smoke --screenshot-dir shots` (**new**, reason: `src/embodic/ui/app.py` l.3-4 documents it; it saves
   the light and dark window at 1280 x 800 and 960 x 540 from the real display).
3. The rows of section 1 of `docs/phase3/design/ux_verification_plan.md` (U-S7, Agent 1, read in its worktree
   `/home/claude/wt/U-S7` on 2026-10-16 before Fable merged it): S01, S03, S04, S05, S07, S09, S11, S14, S17, S20, S22,
   S23, S29, S30, S36, S38, S39 and S41 of `docs/phase2/design/screenshot_checklist.md`, at native scale and at 100 %,
   in the themes of each row. In-window rows use `.venv\Scripts\python -m tests.ui.qt_shell.capture_acceptance <OUT>
   <ROW ...>` without `QT_QPA_PLATFORM`; rows marked "OS" need a whole-window screenshot. Both forms are Agent 1's
   commands, **new** to INSTALL.md (reason: screenshot capture is not an install step). Sections 2 to 4 of that plan
   give the Narrator walkthrough (AX-06), the keyboard-only walkthrough (AX-02) and the DEF-U-M5h-01 first-paint check.
   Run them here, in the W4 venv, before W7. I read only section 1 and the headings, so the list above is what the
   file said then and Agent 1's file wins on any later change.

### W7. PK-01 Windows cell: INSTALL.md step 7

```
python -m pip install --require-hashes -r requirements\py311-dev.txt
python -m pip install --no-deps -e .
python tools\ci.py --profile commit
```

Run the gate detached (see the rules). Expected: `6 of 6 gates passed`. The editable install needs the network
(INSTALL.md step 7). Record the pytest summary line and the wall time. Only Python 3.11 runs here, so the 3.12 and 3.13
Windows cells of PK-01 stay `not tested` (D-048d names 3.11 only).

### W8. INSTALL.md step 8: release profile on the laptop

`python tools\ci.py --profile release`, detached. Expected: `9 of 9 gates passed`. It also runs PF-01 to PF-05 and
writes `tests/performance/baseline.json`. REQ-N-01 says its 1.0 s threshold stays `assumption` "until run on the user's
laptop", so this is that run. The run leaves `resources\evidence\passed_tests.v1.json` in the tree (D-045f). The
release gate took 4341 s of pytest on the 2-CPU container (gate log), so it can run for more than an hour.

### W9. PK-05: INSTALL.md step 9 on Windows

```
py -3.11 tools\build_bundle.py
python -m pytest tests/bundle
build\bundle\embodic\embodic-cli.exe selftest
```

The first two commands are INSTALL.md step 9. The third is the Windows form of the frozen selftest that step 9's "What
was run" names (**new** form). Expected: the script exits 0 with the licence checklist and four Qt DLLs, `6 passed`, and
`45 tests: 45 passed, 0 failed`. The bundle test needs the venv of W7, because pytest is in the dev lock file only.

### W10. Hand back

Copy the record, the logs, `reference\windows\`, `outcome.json`, `board.svg`, the screenshots and
`tests\performance\baseline.json` to the cloud. Fable reruns `pk04_compare.py` there and commits the record.

## 3. Campaigns in the cloud (Phase 3, Agent 4 unless named)

Every campaign is `not tested` except where the Status cell names a run. Mutation campaigns apply each mutant to a
scratch copy of `src/` and never edit the worktree. "Killed" means at least one named test fails with the disagreement
the mutant predicts, not with an import error.

| ID | Campaign | Expected value source | Pass criterion | Status |
|---|---|---|---|---|
| V3-01 | Read one passing test per `verified` must row and every cause-B ID of part 1 | the row's Acceptance text in requirements.md | each sampled test asserts the criterion's value and tolerance; each cause-B ID is found under another label or filed as a missing test | not tested |
| V3-02 | Fresh mutation pass on DRC (`embodic.drc`): slack 0.004 mm, epsilon 0, a skipped arc pair, rule 2, 2b and 5 exemptions widened, half-open band flipped | D-006; interfaces.md §7; the M1 and M3 instruments | 100 % killed by `tests/unit/drc`, PR-01, PR-02, PR-13 or `tests/independent/m1`, `m3`; a survivor is a DEF row | run 2026-10-19 on 0.0.2 sources (U-V15): 9 of 11 killed, 2 boundary survivors DEF-UV15-01, -02 (`verified`, `tests/independent/m7/records/V3-02.md`) |
| V3-03 | Mutation pass on the spiral generator and geometry: a turn off by one pitch, a mirrored arc reversed, a centre via moved 1e-6 mm, a joint gap of 2e-6 mm | REQ-F-01 and REQ-N-21 bounds; `tests/independent/m2/own_spiral.py` | 100 % killed by UT-GEO tests or `tests/independent/m2/test_spiral.py` | run 2026-10-19 (U-V15): 4 of 4 judged mutants killed (`verified`, `tests/independent/m7/records/V3-03.md`) |
| V3-04 | Mutation pass on physics kernels: EQ-05 `cosh` and `sinh` swapped, EQ-06 with abs(dr), EQ-10 alpha 0.00393 to 0.0039, EQ-12 /24 to /12, a series sum that drops the last pair | Agent 2's closed forms (CF rows of `oracle_cases.json`); `tests/independent/m2/own_emf.py` | 100 % killed by UT-PHY, GR or `tests/independent/m2` | run 2026-10-19 (U-V15): 5 of 5 killed (`verified`, `tests/independent/m7/records/V3-04.md`) |
| V3-05 | Mutation pass on exporters: a quantised end point taken from its own coordinate, a DXF outline end point moved, "Key results" removed from the PDF, the design hash left out of the SVG metadata | REQ-F-16, REQ-N-21 and REQ-T-07 acceptance; `tests/independent/m4` parsers | 100 % killed by UT-EXP, UT-IO-06 or `tests/independent/m4` | run 2026-10-19 (U-V15): 3 of 4 killed; 1 survivor equivalent on the shipped examples, for Fable (`verified`, `tests/independent/m7/records/V3-05.md`) |
| V3-06 | Rerun the 27 instrument mutants: `python tests/independent/m1/mutants.py` | the mutants' own predictions | `27/27 mutants killed`; the README records only partial reruns since 69381b5 | run 2026-10-19 (U-V15): `27/27 mutants killed` (`verified`, `tests/independent/m7/records/V3-06.md`) |
| V3-07 | Longer Hypothesis: PR-01, PR-02, PR-05, PR-08, PR-13 and PR-14 under the `nightly` profile (2000 examples, `tests/conftest.py` l.25) with 10 seeds: `EMBODIC_HYPOTHESIS_PROFILE=nightly pytest tests/unit/property tests/unit/drc/test_properties.py tests/unit/api/test_compute.py tests/unit/model/test_fields.py -k test_pr --hypothesis-seed=<n>` (the six files that define `test_pr*`, `verified` by grep) | the properties as written | 0 failures over 10 seeds (20000 examples per property); a counterexample is a DEF row with its seed | run 2026-10-19 (U-V15) on the six named properties, seeds 1 to 10: 1 counterexample, PR-05 seed 5 (DEF-UV15-04); the profile lengthens PR-08 and PR-05 only (DEF-UV15-03) (`verified`, `tests/independent/m7/records/V3-07.md`) |
| V3-08 | PK-04 Linux side: references and comparison self-test | REQ-N-04 tolerance 1e-9 rel. | references written, self-test exit 0 | done 2026-10-16 (`verified`, part 2 W5) |
| V3-09 | Lock files against PyPI's Windows wheels | PyPI JSON API file digests | every pin has a hashed CPython 3.11 win_amd64 or pure wheel | done 2026-10-16: 44 of 44 pass (`verified`, W0) |
| V3-10 | Own models against the product on all five examples: own winding star and k_w, own EQ-05/EQ-06 Ke_LL, brute DRC sweep under the §7 exemptions | `tests/independent/m1` to `m3` instruments (no embodic import in the expected values) | phases equal; k_w within 1e-12; Ke_LL within 1e-4 rel. (the gap U-V2 and U-V3 measured was at most 1.02e-4, so 1e-4 can fail and the bound is an `assumption` to settle in the run); DRC violation sets equal, wave 186 | run 2026-10-19 (U-V15): pass on the modelled rows; Ke_LL within 2.46e-5 of the 181-point peak, so 1e-4 holds; serpentine and wave star and k_w `not tested` (`tests/independent/m7/records/V3-10.md`) |
| V3-11 | OR-11, EQ-05 field per layer against FEA (Elmer, set up by Agent 5 in U-S6) on Agent 2's case spec from U-E11 | the FEA result of that case, built by Agent 4 from the spec; the band and the compared quantity come from U-E11, never chosen here | the embodic value lies in U-E11's band; mesh convergence as U-E11 states it; out of band is a DEF row, the band is never widened | not tested; U-E11 and U-S6 outputs not read (they did not exist when this plan was written) |
| V3-12 | OR-12, EQ-12 eddy loss against FEA, same route | as V3-11 | as V3-11 | not tested |
| V3-13 | Release evidence still applies to main | `package_source_sha256` of main's `src/embodic` against the evidence's `source_sha256` | equal | done 2026-10-16: `cfefe405…baae` on both (`verified`) |
| V3-14 | Independent scans for the four cause-C must rows: "measured" applied to computed values (REQ-T-10), balance, torque or efficiency claimed from geometry (REQ-T-11), "Xcoil" in UI strings and every export of the five examples (REQ-L-03), personal names and brand-asset checksums (REQ-L-05) | the acceptance text of each row and the allow-lists of test_plan_draft.md LG-03 to LG-06 | 0 hits outside the allow-lists; the scan finds a planted hit in each class | not tested |
| V3-15 | Rerun `req_audit.py` on the build that Phase 4 accepts | this plan, part 1 | the counts meet part 4 | not tested |

V3-02 to V3-07 and V3-10 need CPU. They run one at a time, never beside another unit's gate, and never through
`tools/ci.py`.

## 4. Exit criteria Phase 3 to Phase 4 (acceptance)

Phase 4 starts when all of the following hold on one named build:

1. Every live must row of `req_audit.md` is `verified`, except the rows in point 3.
2. These items are `verified` by a run with a record:
   - The Windows campaign: W4 under 10 minutes and selftest 45 of 45; W5 `PK-04 passed`; W7 `6 of 6 gates passed`;
     W8 `9 of 9 gates passed` with the PF baseline recorded; W6 screenshots and Agent 1's rows.
   - V3-01 to V3-07, V3-10 and V3-14: every mutant killed, or each survivor a DEF row that Fable closes or accepts by
     name.
   - V3-11 and V3-12: each has a verdict. An out-of-band verdict is a DEF row with a cause or `unresolved`, as F-OR07
     is (D-045a), and Fable rules on it before Phase 4.
3. These items may stay `not tested`, each with its reason in the final report:
   - EQT-14-O2 and the F-OR07 closure that needs a measurement, because no board exists (D-048f).
   - The 3.12 and 3.13 Windows cells of PK-01, because D-048d names Python 3.11 only.
   - PK-05 and W9, if the build or the bundle test fails for a cause in the stretch goal (D-015), with the failure
     recorded.
   - AX-06 Narrator, if the user declines the walkthrough.
   - REQ-F-30 (could; UI-20 has no test, §5.3.1) and the should rows REQ-N-20, REQ-T-12, REQ-L-02, REQ-L-06 and
     REQ-L-09, unless V3-01 finds a test or Fable assigns one.
4. Every DEF row opened in Phase 3 is closed, accepted by name by Fable, or moved to Phase 5 with a reason.

The user receives one report: Fable's Thai summary of an English report by Agent 4. The English report holds the rerun
audit counts and table, the Windows record with times and outputs, one line per V3 campaign with its verdict and
status, the DEF list, and the list of what stays `not tested` and why.

## Open questions for Fable

- Q-1. W0 point 2: does the laptop get this plan's files by `git pull` after your commit, or by a copy through the
  desktop app? A pull also changes the checkout under test, so W1 must run after it.
- Q-2. W8 leaves `resources\evidence\passed_tests.v1.json` in the user's folder. Keep it, or delete it after the record?
- Q-3. V3-14 needs instruments under `tests/independent/`, outside this unit's scope. It needs a new brief.
- Q-4. bae5a26 does not appear in the decision log or in any document I read. W1 records HEAD, and W5 refuses a
  different build, so the campaign does not depend on it.
