Prepared by: Agent 6 — Software Architecture Specialist — model: claude-opus-5-5

# ADR-0002: One primitive geometry model (lines and arcs with width, layer, net) shared by DRC, physics and all exporters

**Status:** Proposed
**Date:** 2026-10-04
**Deciders:** Fable 5.1 — consulted: Agent 2 (geometry rules), Agent 3, Agent 4

## Context

- Coordinator constraint: keep Xcoil's proven "primitive" concept so SVG, DXF, `.kicad_pcb` and KiCad-IPC exporters share
  one geometry model; DRC measures clearance on the generated copper.
- Xcoil v3 stores copper as primitives `{t: 'L'|'A', …, w, kind}` (engine.js l.462–468, l.2289–2302) and every exporter
  walks the same lists: `exportSvg` l.2796, `exportDxf` l.2861, `exportKicad` l.2877 (`verified` code reading). Its
  export tests parse the outputs with independent libraries (ezdxf, kiutils, pypdf — `validate_exports.py`, `verified`).
- Resistance is computed from the generated primitives (A2-EQ EQ-03: "The authoritative length for resistance is the sum
  over the generated copper primitives"), and back-EMF integrates over path segments (EQ-06). Physics therefore needs
  ordered, continuous paths with current direction — not only copper shapes.
- KiCad represents tracks as segments and arcs defined by start/mid/end with a width and a layer (Xcoil writes
  `(arc (start …) (mid …) (end …) (width …))`, l.2900–2901, `verified`); kipy has `Track` and `ArcTrack` classes
  (A5-KI §3, `verified` source reading).

## Decision

- Geometry is a set of **`CopperPath`s** (ordered chains on one copper layer, in current direction, with net, phase,
  coil and pair indices) made of immutable **`Line` / `Arc` primitives** with `width_mm` and `role`; plus `PlannedVia`s,
  `Pad`s and a `BoardOutline` (architecture_draft.md §7.5). Arcs are exact (centre, radius, start, signed sweep) and expose
  start/mid/end points.
- The `Layout` additionally carries the electrical `Circuit` (series chain of parallel groups per phase, §7.4).
- A cached NumPy array view (`Layout.arrays()`) serves DRC and physics kernels; the dataclasses remain the source of truth.
- All exporters and the KiCad adapter are pure functions of `Layout` (+ metadata); none regenerates geometry.

## Options Considered

### Option A: Line/arc primitives with width + ordered paths + array view (chosen)
| Dimension | Assessment |
|---|---|
| Complexity | Medium — exact arc maths in DRC |
| Cost | Low — proven design to port |
| Scalability | High — serpentine/wave generators emit the same primitives |
| Team familiarity | High — Xcoil precedent |

**Pros:** native mapping to KiCad tracks/arcs, DXF LINE/ARC, SVG paths; exact lengths for resistance; current direction for
EMF; one DRC for all generators. **Cons:** the DRC needs exact line–arc and arc–arc distances (or conservative
discretisation).

### Option B: Filled polygons (copper outlines, e.g. via a polygon library)
| Dimension | Assessment |
|---|---|
| Complexity | Medium — boolean operations hidden in a library |
| Cost | Adds a native dependency (GEOS through Shapely — Shapely BSD-3 per PyPI, `verified`) |
| Scalability | Medium |
| Team familiarity | Medium |

**Pros:** generic clearance via polygon distance; zones/pours possible. **Cons:** loses centre-line, width and current
direction needed for EQ-03/06/10; KiCad export would become zones or approximated tracks; heavier dependency in the KiCad
venv (REQ-K-07).

### Option C: Polylines only (arcs discretised at generation)
| Dimension | Assessment |
|---|---|
| Complexity | Low |
| Cost | Low |
| Scalability | Medium — exports grow large |
| Team familiarity | High |

**Pros:** simple distance maths. **Cons:** chord error in lengths and clearances, many KiCad segments instead of arcs,
non-round traces in manufacturing data.

### Option D: Each exporter regenerates geometry from parameters
**Cons:** DRC no longer checks what is exported; violates the coordinator constraint. Rejected.

## Trade-off Analysis

A is the only option that serves geometry, resistance, EMF, DRC and every exporter from one artefact without loss. The
extra maths for exact arc distances is bounded (closed-form point–arc and segment–arc distances, `inferred`) and testable
against brute-force discretisation (PR-01).

## Consequences

- Easier: adding exporters (one function of `Layout`); guaranteeing "what you check is what you export".
- Harder: generators must emit continuous, ordered paths (tested by UT-GEO-01) and correct widths per primitive.
- Revisit: copper pours/zones (none needed for the spiral stator now) would add a polygon primitive type.

## Action Items

1. [ ] Agent 3: implement `primitives.py`, `paths.py`, `arrays.py` with tests UT-GEO-01…05 first.
2. [ ] Agent 2: confirm primitive roles needed by the spiral generator (side, end_turn, lead, fillet, ring, stub).
3. [ ] Agent 4: independent brute-force clearance checker for PR-01.
