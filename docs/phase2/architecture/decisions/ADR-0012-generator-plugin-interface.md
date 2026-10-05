Prepared by: Agent 6 - Software Architecture Specialist - model: claude-opus-5-5

# ADR-0012: Generator plug-in interface for spiral, serpentine and wave

**Status:** Proposed (implements D-013; refines Phase 1 REQ-F-19 and ADR-0002)
**Date:** 2026-10-04
**Deciders:** Fable 5.1; consulted: Agent 2 (topologies), Agent 3 (port), Agent 4 (golden and independent checks)

## Context

Phase 2 ports Xcoil's serpentine and interleaved wave generators with golden regression and adds the new spiral
generator (D-013). In Xcoil each topology has its own build function and partly its own DRC and analysis: serpentine
uses `runDrc` (engine.js l.756-850) and `analyze` (l.880-1017) in a canonical frame, while wave and sector use the generic
`drcObjects` and `analyzeElements` (l.1846) paths (Agent 3 `migration_mapping.md` §3, `verified` code reading there).
Phase 1 sketched a `WindingGenerator` protocol with `max_turns` and `build`, a winding-plan stage before geometry for all
topologies, and placeholders for serpentine and wave.

Two facts change the shape. Serpentine assigns one phase per layer group and wave puts all phases on every layer, so
the star-of-slots plan is spiral-only. And DRC and physics must not branch on topology, or every new topology grows
branches in modules that should not know it.

## Decision

1. A generator is a pure function `generate_<topology>(design, registry) -> Layout | Unbuildable`. The table
   `GENERATORS: Mapping[TopologyKind, ...]` and `build_layout()` dispatch on `design.topology`. Adding a topology means one
   package and one table entry.
2. Every generator emits the same `Layout`: copper paths in current direction, vias, pads, outline, the **electrical
   element list** (`Circuit` of phases, series groups, parallel members, interconnect paths), an optional
   `RotationalSymmetry` for the DRC shortcut, shared feasibility values and a topology-specific `detail` record
   (`SpiralDetail | SerpentineDetail | WaveDetail` in `embodic.geometry.details`).
3. DRC and physics read only `Layout` (paths, vias, pads, outline, circuit, z per layer). There is one DRC and one physics
   path for all topologies. Xcoil's serpentine canonical-frame DRC becomes the generic `RotationalSymmetry` shortcut,
   proven equal to the full check by PR-02.

   Revision 2026-10-05 (U-D3, D-016). A generator now returns `BoardStack | Unbuildable`: one `Layout` per board, and
   one board for every design except the one-board-per-phase serpentine (interfaces.md §5 gives the shape and the
   reason). Decisions 2 and 3 hold per board: DRC checks one board at a time, and physics reads every board of the
   stack plus its thickness.
4. Each generator owns its phase plan. The spiral generator calls `embodic.winding.plan_spiral_winding`; serpentine and
   wave keep Xcoil's own assignment inside their packages.
5. The import contract C1 orders `generators` above `io`, `outcome`, `physics` and `drc`, so no consumer can import a
   generator.
6. Serpentine and wave are faithful ports: private helpers named after the Xcoil functions they port, with function-level
   golden cases (GR-23), and layout-level golden regression of whole boards (GR-20, GR-21). Physics results on ported
   boards are compared with Xcoil's own analysis (GR-22); a difference caused by Xcoil's serpentine-specific `analyze`
   path is recorded, not copied (open question Q-2).

## Options considered (designed twice)

### Option A: class protocol per topology with `max_turns()` and `build()` plus a shared winding-plan stage (Phase 1)

| Dimension | Assessment |
|---|---|
| Complexity | Medium: two methods per generator plus a plan stage that only fits spirals |
| Cost | Serpentine and wave would fake a star-of-slots plan |
| Scalability | Each topology adds methods the others must stub |
| Team familiarity | High |

**Pros:** explicit max-turns hook for the UI. **Cons:** shallow (the interface mirrors the spiral's internals); the
shared plan stage is wrong for two of three topologies.

### Option B: function table, one shared Layout with electrical element list and detail union (chosen)

| Dimension | Assessment |
|---|---|
| Complexity | Low: one function per topology |
| Cost | Detail records need one union in geometry |
| Scalability | New topology = package + table row |
| Team familiarity | High |

**Pros:** deep interface (one call hides artwork, placement, vias, interconnect, phase plan); DRC, physics and exporters
are written once. Max-turns hints come from the `detail` record of the last layout. **Cons:** a hint before the first
successful build needs a generator call; acceptable because a build of the default design is budgeted at 0.2 s (Phase 1
§11, `assumption`).

### Option C: each topology keeps its own DRC and analysis, as in Xcoil

**Pros:** the most literal port; golden regression of the serpentine analysis is trivial.
**Cons:** two DRC implementations to verify against D-006 and two analysis paths to put through the equation gate;
every fix applies twice; Agent 4's brute-force soundness check must cover both.

## Trade-off analysis

B hides the most behind the smallest interface and puts verification effort where it pays: one DRC proven sound (PR-01,
PR-13), one physics path through the equation gate. The price is that the serpentine physics golden test compares the
generic path with Xcoil's separate path, which may show a real difference. That difference is information about Xcoil,
recorded in `expected_diffs/serpentine.toml` with Agent 2 and Agent 4 sign-off, and it does not justify a second
analysis implementation.

## Consequences

- Easier: one DRC and one physics to test; exporters and the board dump work for every topology; UT-GEO-20's stub
  generator proves the seam.
- Harder: the ports must express Xcoil's serpentine conductor lists as `Circuit` members; the dumper reconstructs
  circuits from Xcoil internals (Agent 3 port notes §7.5).
- Revisit: if GR-22 shows that the generic EMF path is wrong for serpentine geometry (not just different from Xcoil),
  the fix goes into the generic kernel, with Agent 2's spec update.

## Action items

1. [ ] U-M2d: `generators/__init__.py`, `base.py`, spiral package, stubs for serpentine and wave, `geometry/details.py`.
2. [ ] U-M3a, U-M3b: ports, fixtures, parameter maps, GR-20 to GR-23.
3. [ ] Agent 2: tolerance for GR-22 and the decision on Q-2.
