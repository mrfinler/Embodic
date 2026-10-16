Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5

# D-030 lower bounds for clearance and pad: property-test specification (U-E12, 2026-10-16)

This is the test contract for Agent 3. It answers the D-047 item "D-030 lower bounds for clearance and pad"
(`engineering_verification_plan.md` §5). D-030 names a lower bound for the trace width only. D-040 d leaves the
clearance and pad bounds open. The test shows whether a positive, finite clearance or pad below the DRC rules makes a
generator fail. A found failure becomes a DEF row and a Phase 5 change (a refusal bound). This document adds no bound.

## What the code does now

Status `verified` (read in the worktree based on main f07d502).

- `src/embodic/generators/base.py` l.26 to 35 (`unusable_sizes`) refuses a size that is not finite or not above 0. It
  refuses a trace width below `DrcRules.min_trace_width_mm` as well. A clearance or pad of 5e-324 mm passes.
- The spiral guard lists `/winding/coil/clearance_mm` and `/vias/pad_mm` as positive sizes
  (`generators/spiral/generate.py` l.101 to 112). `coil_gap_mm` and `min_side_length_mm` only need to be ≥ 0 (l.113 to
  117).
- The wave guard lists `/winding/clearance_mm`, `/vias/pad_mm`, `/connection/terminal_pad_mm`,
  `/winding/bus_width_mm` and `/connection/ring_width_mm` (`generators/wave/generate.py` l.51 to 63).
- The serpentine guard lists the same sizes without the bus width (`generators/serpentine/generate.py` l.84 to 95).
- The existing UT-GEN-01 fuzz tests draw the clearance from `st.floats(-0.1, 1.0)` and the pad from
  `st.floats(0.0, 2.0)` together with the width from `st.floats(-0.1, 3.0)`, 40 examples each
  (`tests/unit/generators/test_spiral_generate.py` l.309 to 341; `wave/test_wave_generate.py` l.302 to 331;
  `serpentine/test_serpentine_inputs.py` l.68 to 92). A drawn width is often invalid, so the build stops at the
  width refusal. Few examples reach the builders with a valid width and a hostile clearance or pad.

## Probe result before the test exists

`verified` (ran, one run each, worktree U-E12, scratch script outside the repository). With the example designs and a
valid width, each generator was called with the clearance, the via pad and (wave and serpentine) the terminal pad set
in turn to 5e-324, 2.2250738585072014e-308, 1e-12, 1e-9 and 1e-6 mm. All 45 hostile calls returned a `BoardStack` with
finite coordinates and the same path count as the default (spiral 64, wave 197, serpentine 21). The tracemalloc peak
stayed at 2.2 to 3.0 MB (spiral and serpentine) and 5.0 to 5.1 MB (wave). The serpentine call with a hostile clearance
took 2.5 to 2.8 s against 1.7 s for the default.

The limiter is the turn count, not the clearance: wave and serpentine take `turns` as an input, and the spiral count is
held by the width floor (pitch ≥ w) and `MAX_TURNS_PER_LAYER = 100` (`generators/spiral/turns.py` l.25). Five points on
three fixed designs do not cover other spans, coil counts, poles or styles. That is the job of the property test.

## The property

For every drawn input, `generate_spiral`, `generate_wave` and `generate_serpentine` do all of these:

1. Return a `BoardStack` or an `Unbuildable`. They raise nothing.
2. Satisfy the existing `_check_contract` of the topology's test module (every winding path is in the circuit once or
   is interconnect; every referenced via exists).
3. For a `BoardStack`: every float field of every primitive, and `x_mm`, `y_mm` and `pad_mm` of every via, is finite.
4. For a `BoardStack`: the path count is at most the path count of the same design built at the default clearance and
   pad. A smaller clearance or pad may move geometry. With a fixed width and `turns`, it must not create paths. For the
   spiral with `turns=None`, compare against the build at clearance `DRC_EPSILON_MM` (1e-6 mm), the largest legitimate
   turn count in the range, instead (`assumption`: the loop rule admits at least as many turns at a smaller pitch).
5. Finish inside the Hypothesis deadline below. A build that grows without bound fails here instead of being killed by
   the memory cgroup (the D-030 failure mode: 6 GB RSS, "5 of 6, no FAILED line").

## Inputs and generator ranges

Hold the width valid so that the hostile clearance or pad reaches the builders.

| Input | Strategy | Why |
|---|---|---|
| clearance (`/winding/coil/clearance_mm` spiral, `/winding/clearance_mm` wave and serpentine) | `st.floats(min_value=0.0, max_value=rules.trace_clearance_mm, exclude_min=True, allow_subnormal=True)` | every positive value below the rule passes `unusable_sizes` today |
| via pad `/vias/pad_mm` | `st.floats(min_value=0.0, max_value=rules.min_drill_mm + 2 * rules.min_annular_ring_mm, exclude_min=True, allow_subnormal=True)` | the DRC-derived lower pad size a later bound would use (`model/drc_rules.py` l.13 to 19) |
| terminal pad `/connection/terminal_pad_mm` (wave, serpentine) | same as the via pad | listed as a positive size in both guards |
| which size is hostile | `st.sampled_from(["clearance", "pad", "terminal_pad", "all"])`; the others keep the example value | isolates the input that fails |
| trace width | `st.sampled_from([rules.min_trace_width_mm, example width])` | valid by construction, so the width refusal never stops the build |
| geometry | `r_inner` from `st.floats(1.0, 60.0)`, `span` from `st.floats(1.0, 40.0)`; spiral `coils` and `poles` from the UT-GEN-01 sets; wave `style` from `WaveStyle` | the DEF-M3b-03 failure needed a small span (r_inner 1, span 1) |
| turns | spiral `st.none() \| st.integers(1, 30)`; wave and serpentine `st.integers(1, 30)` | inside the range the guards accept |

Explicit `@example` rows, each with a valid width:

- clearance, via pad and terminal pad all 5e-324 mm on r_inner 1.0, span 1.0 (the DEF-M3b-03 shape with the width
  fixed);
- clearance 1e-6 mm (`DRC_EPSILON_MM`) on the default spiral with `turns=None` (the turn-cap shape of `test_spiral_generate.py` l.313);
- pad 2.2250738585072014e-308 mm (the smallest normal float) on each example design.

Settings: `max_examples=200` per generator and `deadline=10 s` per example (`assumption`: about 4 times the slowest
probe call, 2.8 s). Mark the tests `slow` if the suite has such a marker. The DRC rules are the example design's
`drc_rules`; read every bound from that object, never as a literal.

## Defects the test catches

- A division by the clearance or the pad, or an angle from `asin` or `atan2` of a ratio with that size in the
  denominator. DEF-M3b-03 was this defect for the width (`biarc` divided by zero at a denormal width, D-040 d).
- A count derived from 1/s or 1/pad without the width floor, for example vias per ring or fillet subdivisions. That
  is the unbounded-build pattern of D-030.
- Non-finite coordinates in a `BoardStack`, which the DRC and the exporters would then read.
- An exception that escapes the generator instead of an `Unbuildable` with a catalogue code.

The test does not decide whether a clearance below `trace_clearance_mm` should be refused. The DRC already reports such
a layout under D-006. Refusing at the input is a product decision for Phase 5.

## If the test fails

Agent 3 keeps the failing example as an `@example` row, records a DEF row with the shrunk input, and reports to Fable.
Agent 2 then specifies the bound (the candidates are `rules.trace_clearance_mm − DRC_EPSILON_MM` for the clearance and
`rules.min_drill_mm + 2·rules.min_annular_ring_mm` for the pads). The test is never relaxed to pass.
