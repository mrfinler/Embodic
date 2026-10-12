Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5 (unit U-V5, 2026-10-13)

# Independent release check of embodic 0.0.1 (release run on main 5e74acc)

Artefacts, read only (`verified` by `sha256sum` and `cmp`): the wheel `embodic-0.0.1-py3-none-any.whl` (SHA-256
`f114a6e7…dcd0`), `req_report.json` and `passed_tests.v1.json` in `/home/claude/release_0.0.1/`. The report copy equals
`/home/claude/wt/release2/build/req_report.json` byte for byte, and the evidence copy equals the member
`embodic/_resources/evidence/passed_tests.v1.json` of the wheel. Every script below is in `tests/independent/m5/`, and
its output is in `records/`. "Wheel venv" means run 1 of the PK-06 walkthrough (`PK-06_walkthrough.md`).

## 1. PK-06 on Linux

Pass: 19.2 s to 27.7 s from step 1 to the first computed example over four cold runs, against 10 minutes (`verified`).
Details, per-step times, the limiter and DEF-UV5-01 to DEF-UV5-05 are in `PK-06_walkthrough.md`.

## 2. Self-test from the wheel (PK-11)

`embodic-cli selftest` in the wheel venv printed `45 tests: 45 passed, 0 failed` and exited 0, in all four walkthrough
runs (`verified`, step 6 of `pk06_run1.json` to `pk06_run4.json`).

## 3. Evidence file against the REQ report

`python3.11 -I evidence_check.py --report req_report.json --wheel <wheel> --site-embodic <wheel venv>/site-packages/embodic
--src /home/claude/wt/release2/src/embodic` exits 0 with `0 failed checks` (`verified`, `evidence_check.txt`).

| Check | Result | Status |
|---|---|---|
| Report | 3125 records: 3114 passed, 11 skipped (6 bundle smoke, OR-03, OR-07 A and B, OR-10, one m3 independent test) | `verified` |
| Registry | 30 equations, 63 distinct EQT ids in the installed `equations.v1.json` | `verified` |
| My derivation (§3.1: carried by at least one record, every carrier passed) | 52 of 63 pass. 9 carried by no test: EQT-14-GR, EQT-14-O2, EQT-16-GR, EQT-17-GR, EQT-19-GR, EQT-22-GR, EQT-27-GR, EQT-28-GR, EQT-29-GR. 2 carried but not passed: EQT-05-O2 and EQT-06-O2, whose OR-07 carriers are the strict xfail the report writes as `skipped` (D-046c keeps them `not tested`) | `verified` |
| Wheel `passed_tests` | equal to my set: only in wheel `[]`, only in mine `[]`; sorted | `verified` |
| Wheel `realised_by` | equal to my carrier lists for all 52 ids | `verified` |
| `embodic_version` | `0.0.1`, equal to `__version__` in the installed `embodic/__init__.py` | `verified` |
| `registry_version` | `v1+a48aab13172f.c01a66176ad6`. My SHA-256 of the installed `equations.v1.json` starts `a48aab13172f` and of `evidence.v1.json` starts `c01a66176ad6`; `manifest.v1.json` lists the same full hashes | `verified` |
| `gate_profile` | `release` | `verified` |
| `build_id` | `0.0.1+g5e74acc4e79b.20261012T212510Z`, equal to the §3.1 pattern built from `git_commit` and `generated_utc` | `verified` |
| `source_sha256` | `cfefe405be515c4ba107c38b02a5e5dbaacc220ccc1e0e5a70033d919f78baae`. My own loop of the §3.1 rule (path, NUL, raw 32-byte digest, sorted POSIX paths, no `__pycache__`) gives the same over the 179 `.py` files of the installed package and over the 179 of `release2/src/embodic` | `verified` |

The instrument bites (`verified`): in a copy of the report with one EQT-01-GR carrier set to `skipped`, the script
prints `FAIL passed_tests equals my derivation: only in wheel ['EQT-01-GR', 'EQT-08-GR'], only in mine []` and exits 1.

## 4. Badges of the D08 example

`python -I badge_check.py` computes `spiral_12c10p_d08` through `embodic.api.compute_project` and predicts each badge
from the installed registry alone: an equation passes when every EQT id it lists is in `passed_tests` (interfaces.md
§3.1), a `cannot verify yet` equation adds `unresolved`, a validity flag with effect `cap` adds `unresolved`, an empty chain
reads `not tested`, and the badge is the weakest by `status_order_weakest_first` (`unresolved`, `not tested`,
`assumption`, `inferred`, `verified`) as `result_badge_rule` states. The chain (`eq_ids`) and the cap flags come from the
product's result, so the prediction is independent only in the badge derivation (`assumption` that the chains are
right; D08 chains were not re-derived here).

Equations that pass with the release evidence (`verified`): EQ-01, 02, 03, 04, 07, 08, 09, 10, 11, 12, 13, 15, 18, 20,
21, 23, 24, 25, 26, 30.

| Run | Results | Badges | Prediction | Status |
|---|---|---|---|---|
| Wheel venv, evidence present | 31 | 22 `not tested`, 5 `inferred` (R 20 °C, R operating, R line, copper loss, circulating loss), 2 `verified` (interconnect loss, skin depth), 2 `unresolved` (inductance EQ-14, IPC current EQ-15) | 31 of 31 equal | `verified` |
| Second venv, `passed_tests.v1.json` deleted from the installed package | 31 | 29 `not tested`, 2 `unresolved` (the same two) | 31 of 31 equal | `verified` |

Seven results leave `not tested` with the evidence (5 to `inferred`, 2 to `verified`); the two `unresolved` results read
`unresolved` in both runs. The 22 that stay `not tested` hold EQ-05 or EQ-06 (EQT-05-O2, EQT-06-O2 not passed),
or EQ-16, 17, 19, 22 or 27 (an EQT id no test carries). Without the evidence, `load_registry()` returned
`evidence_build_id None` and 0 passed ids. The brief says every result then reads `not tested`; the two results whose
chain holds a `cannot verify yet` equation read `unresolved`, which is what §3.1 states ("A chain that holds a `cannot
verify yet` equation stays `unresolved`") and what the registry order gives. No defect; the brief's wording is wider than
the contract.

## 5. Oracle numbers of D-045g

`python -I oracle_check.py --cases docs/phase2/engineering/oracle_cases.json` builds D08 (O1-D08 v4) and D09 (O2-D09 v2,
variants A and B) as project files from the cases' values and computes them through `embodic.api.compute_project` in the
wheel venv. Conventions I applied: coil spec radius = centre line ∓ w/2, air gap = G − board/2 for D08 (1.4 − 0.3 = 1.1
mm), dielectric = board − 2 × copper, coil gap = clearance, DRC clearance = s, D08 pole-arc ratio 0.72 (`assumption`, as
in `tests/independent/m2/or01.py`). Fields the cases do not name (lead and end style, terminal pads, vias, ring, outline)
come from the shipped D08 example (`assumption`). The reference values are the papers' numbers from the case file.
The D08 build and both D09 builds pass their DRC with 0 violations and compute returns no issue (`verified`).

| Oracle | Mine through the wheel API | Reference | Difference | Band | D-045g | Verdict |
|---|---|---|---|---|---|---|
| OR-01 D08 Ke_LL peak | 0.0308768 V·s/rad | 0.031 (D08 Table 9.1 p.98) | −0.397 % | [−8 %, +8 % + e_edge 1.74 %] | −0.40 %, in band | equal, in band (`verified`) |
| OR-02 D09 R 20 °C, A | 1.115579 Ω | 1.07 Ω (D09 Table 6 p.7) | +4.260 % | ±8 % | +4.26 % | equal, in band (`verified`) |
| OR-02 D09 R 20 °C, B | 1.011576 Ω | 1.07 Ω | −5.460 % | ±8 % | −5.46 % | equal, in band (`verified`) |
| OR-06 D08 budget current | `loss_budget_current_a(4.0, 3, 0.39)` = 1.8490007 A; my √((4/3)/0.39) is the same to 1e-12 | 1.84 A (D08 Table 4.6 p.57) | +0.49 % | print rounding: 0.39 read as [0.385, 0.395] Ω gives [1.83726, 1.86097] A, holds 1.84 | within print rounding | equal (`verified`) |
| OR-06 on embodic R at 50 °C | R 0.4851617 Ω, I 1.657777 A | 1.84 A | −9.90 % | none (characterisation) | not in D-045g; spec table 0.485162 Ω, 1.65778 A | equal to the spec table (`verified`) |
| OR-08 D09 B_z peak, mid-radius 35.5 mm, z 1.035 mm, harmonics 1 to 13 | 0.738353 T from `embodic.physics.field_harmonic` summed at the pole centre; my own EQ-05 (cosh/sinh form) gives 0.738353 T | 0.72 to 0.75 T (D09 Fig. 7 p.4, `inferred` reading) | +2.55 % / −1.55 % | [0.7125, 0.7560] T | 0.7384 T, in band | equal, in band (`verified`) |

The fundamental b1 is 0.846122 T in `LayerResult.b1_peak_mid_radius_t`, in `field_harmonic` and in my own EQ-05
(`verified`). My first OR-08 run passed `LayerResult.z_mm` (0.035 mm, measured from the board face) as the distance from
the magnet and got 0.7502 T with b1 0.8878 T. That was my error: the field needs air gap + 0.035 = 1.035 mm, and the
script now adds the gap. OR-07 and OR-08 are not independent of EC-05 (test_plan.md §4).

## 6. CLI rulings on the wave example

`python -I cli_check.py --workdir <empty>` on `wave_16p_example` (`verified`, `cli_wave.txt`, `cli_wave.json`).
`embodic-cli compute` printed `Design rule check: FAILED, 186 violations` and exited 2.

| `--format` | Without `--allow-drc-errors` | With the flag |
|---|---|---|
| `pdf` | exit 0, written; stdout `Wrote …/pdf.pdf` then `Design rule check: FAILED, 186 violations` | exit 0, written |
| `readme` | exit 0, written; the same two lines | exit 0, written |
| `svg`, `dxf`, `dxf-outline`, `dxf-screws`, `bundle` | exit 2, nothing written; stderr `DRC_EXPORT_NOT_CONFIRMED` (`value: 186`), `DRC_TRACE_TRACE`, `DRC_TRACE_VIA`, `DRC_CLI_EXPORT_REFUSED` | exit 0, written; stderr `warning DRC_CLI_EXPORT_FORCED` with `value: 186` |

All 14 cases equal interfaces.md §12 (revision U-D14) and D-045e (`verified`).

GR-19 mutant. `python tests/independent/m1/mutants.py unsplit` in a venv with the dev lock file and the release wheel
installed (not editable) printed `killed   GR-19 ic objects mapped unsplit (DEF-M1V-03): FAILED
tests/independent/m1/test_board_dump_reader.py::test_golden_layout_fixtures_map_and_parse` and `1/1 mutants killed`, in
160 s (`verified`). The unmutated copy passed first, which the runner requires. The failure is the predicted
disagreement: with the mutant applied, the test fails on `assert len(board.dump.paths) == len(raw_objects)` with
`AssertionError: assert 17 == 20` (serpentine: 17 unsplit paths against 20 split objects; `verified` by running the
single test on a mutated copy).

## 7. Linux PyInstaller folder (optional)

`python3.11 -I bundle_check.py --folder /home/claude/wt/U-M5c/build/bundle/embodic --cwd <scratch>` (`verified`,
`bundle_check.txt`). The folder holds 444 regular files, 232.4 MB, and no `.py` file, as INSTALL.md §9 states. Its
`embodic-cli selftest` (offscreen) printed `45 tests: 45 passed, 0 failed`, exit 0, and the folder's file list and sizes
were the same after the run. A first count of 464 files came from my script following the folder's 20 symlinks; it now
counts regular files only.

| package_layout.md §5.1 / §5.2 item | Folder |
|---|---|
| `THIRD_PARTY_LICENSES.md` | present, 58,509 bytes |
| `licenses/LGPL-3.0.txt`, `licenses/GPL-3.0.txt` | present, 7,651 and 35,147 bytes, SHA-256 `da7eabb7…4768` and `8ceb4b9e…b903` (the values §5.1 quotes) |
| `licenses/PYTHON-LICENSE.txt` | present, 13,936 bytes, `3b2f81fe…a3bf` |
| `licenses/numpy/` | present, 17 files, 92,518 bytes |
| fonts `Inter/LICENSE.txt`, `JetBrainsMono/OFL.txt`, `FONTS.md` under `_internal/embodic/_resources/fonts/` | present |
| `source/embodic-0.0.1.tar.gz` | present, 18,807,803 bytes |
| written offer for the Qt and PySide6 source (`SOURCE.md`) | absent, as §5.1 says (user decision) |
| Qt third-party notices | absent, as §5.1 says |
| embodic's own licence (`LICENSE`, `LICENSE.txt`) | absent, as §5.1 says (user decision) |

The Windows folder (PK-05) and every Windows step are `not tested`.

## Defects

DEF-UV5-01 to DEF-UV5-05 are in `PK-06_walkthrough.md`, all in the install documents or the selftest layout. Items 2 to
7 found no difference from the contract or from D-045g.
