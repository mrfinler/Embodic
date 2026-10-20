Prepared by: Fable (coordinator) - model: claude-opus-5-5

# PF-01 record on the reference laptop (REQ-N-01)

- Date: 2026-10-21, about 02:50 local time.
- Machine: the user's laptop (Windows 11 Home, CPython 3.11.9 from the NuGet package inside the folder), on mains power
  (`Win32_Battery` BatteryStatus 2 and `BatteryStatus.PowerOnline` True, read right after the runs), with no other
  campaign running. The CPU load before each run is in the logs.
- Build: the editable install in `%USERPROFILE%\Desktop\embodic\.venv` at checkout bbeed84. `embodic.__version__` is
  0.0.5, imported from the checkout's `src` (logged). bbeed84's `src` equals that of 99d355d, the source of the 0.0.5
  candidate (`git diff --stat 99d355d bbeed84 -- src` is empty).
- Example: `spiral_12c16p_default`, 20 warm recomputes per set (`tests/performance/test_pf_baseline.py::timed_runs`).

## Budgets

REQ-N-01 and the PF-01 row of `docs/phase2/architecture/test_plan.md` set these budgets: full recompute p95 strictly
below 1.0 s; per-stage p95 below 0.2 s for geometry, 0.4 s for DRC and 0.3 s for physics. Their status is `assumption`
until they run on this laptop.

## Results

1. `pytest -m manual -rA -s tests/performance/test_n01_pf01_budgets.py` (log `_campaign\pf01_0.0.5.log`, CPU 35 %
   before): failed with one finding, `physics p95 0.660 s is not below 0.3 s`. The full recompute and the other two
   stages stayed below their budgets in that run.
2. Three more sets through the same helper (`_campaign\pf01_numbers.py`, log `_campaign\pf01_numbers_0.0.5.txt`, CPU
   40 % before the first):

| Set | Full recompute p95 | Geometry p95 | DRC p95 | Physics p95 |
|---|---|---|---|---|
| 1 | 0.926 s | 0.024 s | 0.284 s | 0.617 s |
| 2 | 0.913 s | 0.024 s | 0.282 s | 0.621 s |
| 3 | 1.003 s | 0.019 s | 0.302 s | 0.663 s |

## Verdict

- Geometry and DRC meet their budgets with margin (`verified`).
- Physics misses its budget in every set: 0.617 to 0.663 s against 0.3 s (`verified`).
- The full recompute is at its bound: below 1.0 s in three runs and 1.003 s in one (`verified`).
- REQ-N-01 is therefore not met on the reference laptop. The finding is DEF-W-15 (D-087).
- U-D27 measured the cause on Linux. The physics stage spends most of its time in NumPy's per-call overhead on small
  arrays, and a compiled `integrate_path` cut physics 3.3 to 6.7 times there (`verified` on Linux; not run on Windows).
