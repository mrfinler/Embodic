Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5 (unit U-V5, 2026-10-13)

# PK-06 Linux walkthrough of embodic 0.0.1

What ran. `tests/independent/m5/pk06_walkthrough.py` followed `README.md` and `docs/install/INSTALL.md` steps 1 to 6 in
a new empty folder with a new Python 3.11 venv, four times (run 1 to run 4). The guide text is the same on the release
commit 5e74acc and on this branch's base 1eb110d (`git diff --stat 5e74acc 1eb110d` lists only three files under
`docs/phase2/architecture/`, `verified`). The raw output of every step is in `pk06_run1.json` to `pk06_run4.json`.

Inputs (`verified`):

- Wheel `/home/claude/release_0.0.1/embodic-0.0.1-py3-none-any.whl`, SHA-256
  `f114a6e7f00d49081d61dc5090da3364fadb3f7b5b3d602a27e0c9183537dcd0`, the same bytes as
  `/home/claude/wt/release2/build/dist/embodic-0.0.1-py3-none-any.whl` (`sha256sum` on both).
- Lock file `requirements/py311.txt` of this worktree, copied to `<new folder>/requirements/py311.txt`. The wheel was
  copied beside it, so the guide's relative paths work as written.
- `PIP_CACHE_DIR` pointed at a new empty folder for each run, so step 3 downloaded every package as a first install
  does. The run-1 cache held 94 MB afterwards (`du -sh`), which matches the three downloads pip printed.
- CPython 3.11.15 (`/usr/bin/python3.11`), Linux x86-64 container, 2 CPUs, 8 GB RAM. No `DISPLAY`, no Wayland.

Other load (`verified` by `ps aux --sort=-%cpu` before run 1 and after run 3, and `/proc/loadavg` per step): only this
session's own Claude Code process (2.8 % CPU average since boot) and the environment manager. Load average at the start
of the runs: 0.11, 0.28, 0.54 and 0.35. No gate, pytest or build ran during the walkthrough. Runs 2 and 3 followed run 1
directly; run 4 followed the evidence, badge, oracle and CLI checks.

## Times per step

Wall time in seconds, measured with `time.monotonic()` around each `bash -c` call (`verified`, one sample per run).

| Step | Command (verbatim from the guide) | run 1 | run 2 | run 3 | run 4 | Exit |
|---|---|---|---|---|---|---|
| 1 | `python3.11 --version` | 0.007 | 0.004 | 0.004 | 0.004 | 0 |
| 2 | `python3.11 -m venv .venv` and `. .venv/bin/activate` | 4.504 | 3.105 | 3.220 | 3.116 | 0 |
| 3a | `python -m pip install --require-hashes -r requirements/py311.txt` | 20.058 | 19.669 | 12.658 | 14.534 | 0 |
| 3b | `python -m pip install --no-deps embodic-0.0.1-py3-none-any.whl` | 0.749 | 0.774 | 0.750 | 0.745 | 0 |
| 3c | `python -m pip list` | 0.404 | 0.454 | 0.396 | 0.416 | 0 |
| 4 | `embodic` | 0.539 | 0.495 | 0.538 | 0.549 | -6 |
| 5a | `python -c "from embodic.paths import resource_root; print(resource_root() / 'examples')"` | 0.046 | 0.054 | 0.049 | 0.062 | 0 |
| 5b | `embodic-cli compute <examples>/spiral_12c16p_default.embodic.json --json outcome.json --timings` | 1.431 | 1.454 | 1.545 | 1.306 | 0 |
| | Total to the first computed example (steps 1 to 5b) | 27.738 | 26.009 | 19.160 | 20.732 | |
| 5c | `embodic-cli validate <examples>/spiral_12c16p_default.embodic.json` | 0.371 | 0.354 | 0.403 | 0.353 | 0 |
| 5d | `embodic-cli export <examples>/spiral_12c16p_default.embodic.json --format svg -o board.svg` | 3.512 | 3.616 | 3.263 | 3.408 | 0 |
| 6 | `embodic-cli selftest` | 8.879 | 8.604 | 8.694 | 8.765 | 0 |
| extra | `QT_QPA_PLATFORM=offscreen embodic --smoke` (troubleshooting entry, not a guide step) | 2.534 | 2.553 | 2.973 | 2.502 | 0 |

Verdict on REQ-N-07 (below 10 minutes on Linux): pass on this container, 19.2 s to 27.7 s over four runs (`verified`).
The total includes step 4, which fails here in 0.5 s; a working window would add the user's own time to look at it.

What limits the number. Step 3a takes 66 % to 72 % of the total. pip printed its download rates: PySide6-Essentials
(80.1 MB) at 5.0, 5.0, 9.7 and 5.2 MB/s, numpy (16.9 MB) at 10.2 to 17.5 MB/s (`verified`, pip's progress lines in the
JSON records). The run-to-run spread of 8.6 s is network rate, because the other steps vary by less than 1.5 s
(`verified` from the table). Everything except the download takes about 7 s. The 10-minute budget therefore holds down to
a download rate near 0.17 MB/s for the 97.3 MB of wheels (`inferred`: 97.3 MB / (600 s - 7 s)). A machine with a warm pip
cache, a slower disk or another Python build is `not tested`. Windows is `not tested`.

## Output against the guide, step by step

- Step 1. `Python 3.11.15`. Matches "`Python 3.11.` followed by the patch number" (`verified`).
- Step 2. `VIRTUAL_ENV=<new folder>/.venv` and `command -v python` gave `<new folder>/.venv/bin/python` (`verified`).
  The guide's "the prompt starts with `(.venv)`" needs an interactive shell and is `not tested`.
- Step 3a. pip downloaded `numpy-2.4.6-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl (16.9 MB)`,
  `pyside6_essentials-6.11.2-cp310-abi3-manylinux_2_34_x86_64.whl (80.1 MB)` and
  `shiboken6-6.11.2-cp310-abi3-manylinux_2_34_x86_64.whl (272 kB)` and printed
  `Successfully installed numpy-2.4.6 pyside6-essentials-6.11.2 shiboken6-6.11.2` (`verified`). The guide gives no
  expected output here. On stderr pip printed `[notice] A new release of pip is available: 24.0 -> 26.2.1` (DEF-UV5-05).
- Step 3b. `Successfully installed embodic-0.0.1` (`verified`). The same pip notice followed.
- Step 3c. `embodic 0.0.1`, `numpy 2.4.6`, `pip 24.0`, `PySide6_Essentials 6.11.2`, `setuptools 79.0.1`,
  `shiboken6 6.11.2`. Matches the guide's list exactly (`verified`).
- Step 4. Exit -6 (SIGABRT) in 0.5 s. stderr, verbatim:
  `qt.qpa.plugin: From 6.5.0, xcb-cursor0 or libxcb-cursor0 is needed to load the Qt xcb platform plugin.` /
  `qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in "" even though it was found.` /
  `This application failed to start because no Qt platform plugin could be initialized. Reinstalling the application may fix this problem.`
  The guide expects "the embodic window opens" and says a Linux desktop was not opened in this build. This container
  has no display, so the window step is `not tested`; the message names a library that the troubleshooting section does
  not (DEF-UV5-03). With `QT_QPA_PLATFORM=offscreen`, `embodic --smoke` exited 0 in 2.5 s (`verified`).
- Step 5a. `<new folder>/.venv/lib/python3.11/site-packages/embodic/_resources/examples`. Ends in
  `embodic/_resources/examples` as the guide says (`verified`).
- Step 5b. Output, verbatim from run 1:
  `Design: Spiral, 12 coils, 16 poles` / `Design hash: sha256:ac4fab5db06f9e8f733dc495080deeddfe0bcf58faa31ebb7ec841c1b27d9c09` /
  `Topology: spiral, boards: 1` / `Design rule check: passed` /
  `Timings (s): validate 0.001, geometry 0.020, drc 0.283, physics 0.639`.
  The first four lines equal the guide's, the design hash included (`verified`, string comparison in the script). The
  timings differ, which the guide announces. `outcome.json` (338,866 bytes) holds 31 results, each with `status`,
  `eq_ids` and `assumed_inputs` (`verified` by reading the file).
- Step 5c. `Valid: Spiral, 12 coils, 16 poles`. Matches (`verified`).
- Step 5d. `Wrote board.svg`, 63,706 bytes, an SVG document (`verified`). Matches.
- Step 6. The guide says "`embodic-cli selftest` and the Tests dialog arrive with unit U-M5d. This build does not have
  them." The release wheel has the command: 45 lines `passed <id> <s>`, then `45 tests: 45 passed, 0 failed`, exit 0
  in 8.6 s to 8.9 s (`verified`, all four runs). The guide and README.md are out of date (DEF-UV5-01). The lines of the
  two longest IDs push the time column right (DEF-UV5-04).

## Defects

| ID | Severity | Where | Reproduce | Expected (guide or contract) | Got |
|---|---|---|---|---|---|
| DEF-UV5-01 | medium (doc) | `docs/install/INSTALL.md` §6 l.139; `README.md` "Check the installation" l.78 | Steps 1 to 3 of INSTALL.md, then `embodic-cli selftest` | "`embodic-cli selftest` and the Tests dialog arrive with unit U-M5d. This build does not have them." | `45 tests: 45 passed, 0 failed`, exit 0. package_layout.md §5.2 lists "Check the installation: `embodic-cli selftest`, and the Tests dialog" as a README section |
| DEF-UV5-02 | low (doc) | `README.md` "Build the Windows folder" l.117 | Read README.md l.115-117 against INSTALL.md §9; `ls tools/build_bundle.py` on 5e74acc | README: "The PyInstaller one-folder build (`python tools/build_bundle.py`) arrives with unit U-M5c. This build does not have it." | `tools/build_bundle.py` exists on 5e74acc, INSTALL.md §9 documents it, and U-M5c's folder runs its selftest 45 of 45 (release_check.md item 7) |
| DEF-UV5-03 | low (doc) | `docs/install/INSTALL.md` "Troubleshooting on Linux", second entry | Steps 1 to 3 on a Linux machine without `libxcb-cursor0` (here: this container), then `embodic` | The entry names "EGL, OpenGL, xkbcommon and fontconfig" | Qt aborts with `From 6.5.0, xcb-cursor0 or libxcb-cursor0 is needed to load the Qt xcb platform plugin.`; the entry does not name that library. INSTALL.md §9 names `libxcb-cursor.so.0` only for the frozen folder. Whether installing it opens the window on a desktop is `not tested` |
| DEF-UV5-04 | low (cosmetic) | `embodic-cli selftest` output | `embodic-cli selftest` | One column per field (interfaces.md §12: verdict word, check ID, duration) | `passed   ST-EX-spiral_12c16p_default-COMPUTES    0.00 s` and `passed   ST-EX-serpentine_16p_example-COMPUTES    0.00 s` start their time 2 and 3 characters right of the other 43 lines (column 49 and 50 against 47), because the ID is longer than the column |
| DEF-UV5-05 | info (doc) | `docs/install/INSTALL.md` §3 | Step 3 with the venv's bundled pip 24.0 and network access | No output shown | stderr `[notice] A new release of pip is available: 24.0 -> 26.2.1` / `[notice] To update, run: pip install --upgrade pip` after each pip command. Harmless; the guide could say so |

Follow-up, not a defect: INSTALL.md l.13 says the PK-06 walkthrough "has not run
yet. This guide gives no times." The times above can now go into the guide (package_layout.md §5.2 asks for them).
