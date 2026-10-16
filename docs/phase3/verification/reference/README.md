Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5

# PK-04 Linux reference (U-V10)

`linux/` is the output of `pk04_reference.py` run with the Python of `/home/claude/wheelvenv`, which has the 0.0.1
release wheel installed (embodic 0.0.1, NumPy 2.4.6, Python 3.11.15, source SHA-256 `cfefe405…baae`). All six files
are byte-identical to Fable's run in `/home/claude/pk04_linux_wheel` (`cmp`, `verified`).

## Why the earlier reference differed

The earlier files (commit 0a5a351) differ from these in 294 places over the five examples. Every one of them is a
`status` or `status_reasons` field (`verified`, counted with pk04_compare.diff). The earlier files list
"EQ-nn tests not passed in this build" for every equation. I copied the installed package, deleted
`_resources/evidence/passed_tests.v1.json` from the copy and ran `pk04_reference.py` on it: all six output files are
byte-identical to the earlier reference (`verified`). The earlier reference therefore came from the same sources
without the build's evidence file. The file is a build product (`tools/record_passed_tests.py`) and is not in git, so a
source checkout lacks it (`inferred` from `git ls-files`).

## Comparison with the Windows output (W1)

`python3 -I docs/phase3/verification/checks/pk04_compare.py docs/phase3/verification/reference/linux <pk04_windows>`
exits 1 (`verified`):

```
not compared: /boards/layout_hashes, /boards/stack_hash, /versions/python
pass serpentine_16p_example.json: 0 differences, byte-identical False
pass spiral_12c10p_d08.json: 0 differences, byte-identical False
pass spiral_12c14p.json: 0 differences, byte-identical False
pass spiral_12c16p_default.json: 0 differences, byte-identical False
FAIL wave_16p_example.json: 831 differences, byte-identical False
  /drc/0/summaries/0/pairs_checked: 3461 != 3462
  /drc/0/violations/0/at_mm/0: 14.819969569209762 != 40.723443523579945 (abs 2.590e+01 > 1e-9 x array peak 40.7234)
PK-04 failed at rel 1e-09
```

All 831 wave differences lie under `/drc`. After sorting both violation lists by (kind, layer, objects), the 186
violations agree within the rules (0 differences, 186 unique keys on both sides, `verified`). That part is DEF-W-01.

One difference is not an order effect. The `trace_trace` summary counts `pairs_checked` 3461 on Linux and 3462 on
Windows (`verified`). `pairs_checked` is the number of pairs that reach the clearance measurement
(`src/embodic/drc/engine.py` l.318-325). A canonical violation order does not change this count, so PK-04 still fails
after DEF-W-01 is fixed (`inferred`). The cause, a candidate pair at the broad-phase limit that float noise moves in or
out, is a guess (`not tested`). This is DEF-UV10-01.
