Prepared by: Agent 6 — Software Architecture Specialist — model: claude-opus-5-5

# embodic — System architecture (Phase 1 draft, 2026-10-04)

Status: **draft**. Every design choice in this document is an `assumption` in the sense of PROJECT_BRIEF §3 (a design
decision without empirical evidence) until the corresponding ADR in `decisions/` is accepted. Facts taken from other
agents keep their original status label and reference. No code has been written (BRIEF §3 rule 9); the Python below
is interface sketch only (Python 3.11 syntax — no PEP 695 generics, because the user's minimum is 3.11).

Related documents: `requirements_draft.md` (REQ-IDs), `app_type_comparison.md` (front-end proposal),
`test_plan_draft.md` (test IDs), `decisions/ADR-0001 … ADR-0009`.

## 1. Goals, constraints, quality attributes

| Driver | Source | Architectural consequence |
|---|---|---|
| Python calculation and geometry engine | BRIEF §1 | Core = pure Python + NumPy packages (§3) |
| Engine shared by standalone UI and KiCad plugin | DL D-004; coordinator constraint | Ports-and-adapters layering, enforced by import contracts (ADR-0001) |
| One geometry model for SVG / DXF / .kicad_pcb / KiCad-IPC | Coordinator constraint; proven in Xcoil (`exportSvg`, `exportDxf`, `exportKicad` all walk the same primitive lists, `engine.js` l.2796–2929, `verified` code reading) | `Primitive` model (ADR-0002, §7.5) |
| DRC measured on generated copper | Coordinator constraint; Xcoil DRC test group | `embodic.drc` works on the same primitives (§8.4) |
| Traceable results | Coordinator constraint; BRIEF §3 rules 2–6 | `Traceable[T]` + EQ/EV registries (ADR-0003, §13) |
| Equation-check gate before reuse | BRIEF §1; A2-EQ gate summary | Registry stores gate verdict + status; CI enforces (REQ-T-05) |
| KiCad 9.x: SWIG deprecated (removal planned 11.0), IPC needs running GUI, per-plugin venv | A5-KI §1–§3 (`verified`) | IPC adapter, UI-less; file writer as baseline (ADR-0004) |
| Spiral coils now, serpentine/wave later | Coordinator constraint | `WindingGenerator` interface + tagged-union topology spec (§7.2, §8.3) |
| Interactive recompute < 1 s | REQ-N-01 (`assumption`) | Staged pipeline with caching, vectorised kernels (§11) |
| Windows + Python 3.11 | BRIEF §1; NumPy ≥ 2.5 needs Python ≥ 3.12 (PyPI, `verified`) | Dependency ranges per Python version (ADR-0008) |

## 2. Context (C4 level 1)

```mermaid
flowchart LR
  user(["Motor designer (Windows, Python 3.11+, KiCad 9.x)"])
  subgraph EMB["embodic"]
    ui["Standalone UI (embodic.ui)"]
    cli["CLI (embodic.cli)"]
    core[["Engine core: model, winding, geometry, drc, physics, results, io"]]
    plg["KiCad IPC plugin (embodic_kicad_plugin)"]
  end
  kicad["KiCad 9.x PCB editor with IPC API server"]
  files[("Files: .embodic.json, SVG, DXF, .kicad_pcb, PDF, JSON, CSV")]
  ci["CI / test runner"]
  js["Xcoil v3 JS engine (reference, test time only)"]
  user --> ui
  user --> kicad
  ui --> core
  cli --> core
  plg --> core
  kicad <-->|"local IPC socket (protobuf over NNG)"| plg
  ui -.->|"optional IPC client (needs T3)"| kicad
  core --> files
  kicad -->|"opens .kicad_pcb"| files
  ci --> cli
  js -->|"golden JSON dumps"| ci
```

External interfaces: the user (UI, CLI); KiCad 9.x over the IPC API (A5-KI §3: Protocol Buffers over NNG, standalone
plugin process, `verified`); the file system; at test time only, the read-only Xcoil v3 JS engine via Node.js to produce
golden JSON (ADR-0006). No network service is used (REQ-N-17).

## 3. Components (C4 level 2/3)

```mermaid
flowchart TB
  subgraph AD["Adapters (may import PySide6 / kicad-python / argparse)"]
    UI["embodic.ui"]
    CLI["embodic.cli"]
    PLG["embodic_kicad_plugin"]
  end
  API["embodic.api (compute facade, stage cache, versions)"]
  subgraph CORE["Core (pure Python + NumPy; no UI, no KiCad imports)"]
    IO["embodic.io (project JSON, SVG, DXF, .kicad_pcb, PDF, JSON/CSV)"]
    PHY["embodic.physics (field, EMF, R, losses, L estimate, thermal, mass)"]
    DRC["embodic.drc (clearance on generated copper)"]
    GEO["embodic.geometry (primitives, generators, placement, vias, interconnect, outline)"]
    WND["embodic.winding (feasibility, star of slots, factors, circuit)"]
    MOD["embodic.model (design inputs, defaults, validation, provenance)"]
    RES["embodic.results (Status, Traceable, EQ/EV registry, AnalysisResult)"]
    BASE["embodic.units, embodic.errors"]
  end
  UI --> API
  CLI --> API
  PLG --> API
  UI --> IO
  CLI --> IO
  PLG --> IO
  API --> IO
  API --> PHY
  API --> DRC
  IO --> GEO
  IO --> DRC
  PHY --> GEO
  DRC --> GEO
  GEO --> WND
  WND --> MOD
  MOD --> RES
  RES --> BASE
```

Arrows mean "may import". Transitive imports downward are allowed; upward or sideways imports are forbidden except
where drawn. `physics` and `drc` are independent of each other; `io` must not import `physics` (it only reads
`AnalysisResult`, which lives in `results`).

| Component | Responsibility | Main inputs → outputs | Key REQs |
|---|---|---|---|
| `embodic.units`, `embodic.errors` | Unit vocabulary and conversions; `ValidationIssue`, `IssueCode`, `Severity`, `IssueCategory` | — | REQ-N-21, REQ-F-14 |
| `embodic.results` | `Status`, `Traceable[T]`, `Assumption`, `InputRef`, `ValidityFlag`; EQ and EV registries (packaged JSON); `AnalysisResult`; status combination; display formatting | registry JSON → lookups | REQ-T-01…08 |
| `embodic.model` | Immutable design input dataclasses; defaults (Agent 2 §5.2, all `assumption`); provenance per field; `validate_design()` (INVALID / RANGE issues) | user/project data → `DesignParameters`, issues | REQ-F-03…09, F-14, F-21, T-06 |
| `embodic.winding` | Q/2p feasibility (q, t, balance), integer star of slots, phase belts, polarity, winding factors k_w,n (turn-averaged), phase circuit topology (series chain of parallel groups, star/delta) | rotor poles, Q, phases, layer config → `WindingPlan` | REQ-F-02, F-03, F-08 |
| `embodic.geometry` | Primitives (Line/Arc with width, layer, net, role), transforms, paths; `WindingGenerator` registry (`spiral` in P2; `serpentine`, `wave` reserved); spiral coil artwork (X/Y), placement on layer pairs with rotation, via planning, interconnect (rings, terminals), outline; `Layout` incl. electrical `Circuit`; NumPy array view | `DesignParameters`, `WindingPlan` → `Layout` | REQ-F-01, F-03…06, F-09, F-19 |
| `embodic.drc` | Clearance checks on `Layout`: broad phase (uniform grid), exact narrow phase (line/arc distances), connectivity-aware exemptions, symmetric shortcut with full-check equivalence test | `Layout`, `DrcRules` → `DrcReport` | REQ-F-10 |
| `embodic.physics` | EQ-01…EQ-22 implementations as pure functions; `analyse()` orchestration; per-layer field at z; circuit solution (EQ-07); every output wrapped in `Traceable` via the registry | `DesignParameters`, `WindingPlan`, `Layout` → `AnalysisResult` | REQ-F-07, F-11, F-12, F-20 |
| `embodic.io` | Project file load/save (typed loader + published JSON Schema, migrations, canonical JSON, design hash); writers: SVG, DXF R12, `.kicad_pcb` (own s-expression writer), results JSON/CSV, PDF report | `ComputeOutcome` → files; files → `DesignParameters` | REQ-F-15, F-16, K-01, T-07 |
| `embodic.api` | `compute()` facade: validate → winding → geometry → DRC → physics; stage cache; cancellation; version info; never raises for user input | `DesignParameters` → `ComputeOutcome` | REQ-F-14, N-01, N-04 |
| `embodic.cli` | Headless `compute`, `validate`, `export`, `registry`, `golden-compare` commands; exit codes | project file → JSON/exports | REQ-F-18 |
| `embodic.ui` | Standalone front-end (proposal: PySide6, ADR-0005); MVVM view-models, worker thread, geometry view, phase/layer/results/issues views, export dialogs, string catalogue, theme tokens | user events ↔ `api`, `io` | REQ-F-13, N-02, N-11…16, L-01…07 |
| `embodic_kicad_plugin` | KiCad 9 IPC adapter: version check, stack-up import, placing/replacing embodic items in one commit, mm→nm, layer and net mapping, item tracking; optional launcher | `Layout` → kipy items; kipy stack-up → `Stackup` | REQ-K-02…11 |

## 4. Layering rules (enforced)

Enforcement tool: import-linter (BSD licence per PyPI metadata, `verified`) contracts in `pyproject.toml`, run in CI
(MT-01). Proposed contracts (`assumption`):

1. **Layers** (top → bottom): `embodic.ui | embodic.cli` → `embodic.api` → `embodic.io` → `embodic.physics | embodic.drc`
   → `embodic.geometry` → `embodic.winding` → `embodic.model` → `embodic.results` → `embodic.units | embodic.errors`.
2. **Forbidden** in every `embodic.*` module except `embodic.ui`: `PySide6`, `shiboken6`, `wx`, `tkinter`.
3. **Forbidden** in every `embodic.*` module: `kipy`, `pcbnew` (REQ-K-05, K-11). `embodic_kicad_plugin` may import
   `kipy`, never `pcbnew`.
4. **Independence**: `embodic.physics` ⟂ `embodic.drc`; `embodic.io` must not import `embodic.physics`.
5. Core third-party allow-list: standard library + `numpy` only (ADR-0008).

## 5. Runtime flow

```mermaid
sequenceDiagram
  participant A as Adapter (UI / CLI / plugin)
  participant API as embodic.api.compute
  participant M as model.validate_design
  participant W as winding.plan_winding
  participant G as geometry.build_layout
  participant D as drc.run_drc
  participant P as physics.analyse
  A->>API: DesignParameters (+ options, cache, cancel token)
  API->>M: validate
  M-->>API: issues (INVALID stops here)
  API->>W: plan (cache key = winding inputs)
  W-->>API: WindingPlan or UNBUILDABLE issues
  API->>G: build (cache key = geometry inputs + winding key)
  G-->>API: Layout or UNBUILDABLE issues
  API->>D: check (cache key = layout hash + rules)
  D-->>API: DrcReport
  API->>P: analyse (cache key = layout hash + rotor + operating + materials + options)
  P-->>API: AnalysisResult (Traceable fields, validity flags)
  API-->>A: ComputeOutcome (issues, winding, layout, drc, analysis, timings, versions, design hash)
```

Physics runs even when DRC reports violations (the user needs both), but the outcome's `ok` is false and exports of a
layout with DRC errors require an explicit override flag (REQ-F-10, §12).

## 6. Units policy (where units are enforced)

| Rule | Where enforced |
|---|---|
| U1 All lengths in data models, geometry and file formats are **millimetres**, float64 (PCB convention; matches Xcoil and KiCad's mm UI). Field names carry the unit: `trace_width_mm`, `copper_thickness_mm`. | `embodic.model` dataclass field names; review checklist; ruff custom check for dimensional fields without suffix (MT-05) |
| U2 Angles are **radians** inside the core (`_rad`); degrees exist only in UI widgets and project-file fields named `_deg`, converted in `embodic.units`. | `embodic.units.deg_to_rad`; loader converts `_deg` fields once |
| U3 All non-length quantities are SI with explicit suffixes where ambiguous: `remanence_t`, `speed_rpm` (UI convenience, converted to rad/s), `temperature_degc`, `current_rms_a`, `h_w_m2k`. | Field names; `embodic.units` |
| U4 Physics functions convert mm → m at their boundary with `units.mm_to_m()` — no bare `1e-3` / `1e-6` literals in physics code. | ruff rule banning bare power-of-ten literals in `embodic.physics` (MT-05) |
| U5 Every `Traceable` carries a `unit` from a closed vocabulary (`Unit` enum: `mm`, `m`, `mm2`, `T`, `V`, `V_s_per_rad`, `ohm`, `W`, `A`, `A_per_mm2`, `H`, `K`, `degC`, `g`, `N_m`, `rpm`, `rad_per_V_s`, `one`, …) with a display form ("V·s/rad", "Ω", "A/mm²"). | `embodic.results.traceable`; UT-RES-04 |
| U6 KiCad internal units (nm, integer) appear only in `embodic_kicad_plugin` and `embodic.io.kicad_pcb` writer (which writes mm text). Conversion `mm_to_nm(x)` = round half away from zero of `x * 1e6`, once per coordinate — **not** Python's built-in `round()`, which rounds half to even, unlike JS `Math.round` used by Xcoil's `fmt()` (Agent 3 `calculation_flow_and_port_notes.md` §2.1, `verified (run)` there); connected end points are snapped from one shared coordinate so they round identically (REQ-K-08). | `embodic.units.mm_to_nm`; adapter; PR-04, UT-UNI-02 |
| U7 No unit library at runtime (Pint 0.26 requires Python ≥ 3.12 per PyPI, `verified`; overhead in inner loops `inferred`). Dimensional consistency is tested with scaling properties (PR-06). | ADR-0009 |

## 7. Data models

All inputs are frozen, slotted, keyword-only dataclasses; validation is a separate function so that an invalid design
can still be represented, saved and reported. Enums are `StrEnum` (Python 3.11+) whose values are the JSON strings.

### 7.1 Design inputs (`embodic.model`)

```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal

class Phase(StrEnum):
    A = "A"; B = "B"; C = "C"

class RotorType(StrEnum):
    DOUBLE = "double"              # two identical rotors, N facing S (EQ-05: G = (t_s + 2g)/2)
    SINGLE_YOKE = "single_yoke"    # single rotor, opposite back iron (G = t_s + 2g)
    SINGLE_OPEN = "single_open"    # single rotor, no opposite iron (G -> infinity)

class Magnetisation(StrEnum):
    PARALLEL = "parallel"          # P2
    HALBACH = "halbach"            # reserved (D11 eq. 8-9, A2-EQ EQ-05 change); rejected until implemented

@dataclass(frozen=True, slots=True, kw_only=True)
class ArcMagnet:                   # constant pole-arc ratio (EQ-05)
    kind: Literal["arc"] = "arc"
    pole_arc_ratio: float          # alpha_p, 0 < alpha_p <= 1
    r_inner_mm: float
    r_outer_mm: float
    thickness_mm: float            # axial l_m

@dataclass(frozen=True, slots=True, kw_only=True)
class BlockMagnet:                 # rectangular block centred on a radial line (EQ-04: alpha_p(r))
    kind: Literal["block"] = "block"
    width_mm: float                # tangential w_PM
    length_mm: float               # radial
    r_center_mm: float
    thickness_mm: float

MagnetGeometry = ArcMagnet | BlockMagnet

@dataclass(frozen=True, slots=True, kw_only=True)
class RotorSpec:
    poles: int                     # 2p, even
    rotor_type: RotorType
    magnet: MagnetGeometry
    remanence_t: float             # B_r at the reference temperature
    recoil_permeability: float     # mu_r
    remanence_temp_coeff_per_k: float | None = None   # reserved: B_r(T) (A2-EQ EQ-05 change)
    magnetisation: Magnetisation = Magnetisation.PARALLEL
    air_gap_mm: float              # per side, magnet face to board surface
    back_iron_thickness_mm: float  # used by inertia/mass; field model assumes unsaturated iron (A2-EQ EQ-05)
    magnet_offset_rad: float = 0.0 # rotor angle reference

class SideStyle(StrEnum):
    RADIAL = "radial"; PARALLEL = "parallel"          # A2-TOP §3.1 S1, S2

class EndStyle(StrEnum):
    ARC = "arc"; STRAIGHT = "straight"; STADIUM = "stadium"   # S3 = stadium

class InnerTurnMode(StrEnum):
    FIXED = "fixed"                # Xcoil behaviour (A2-REV C5)
    MOVING = "moving"              # trapezoidal + triangular turns (D08 eq. 3.25-3.26, A2-EQ EQ-02)

@dataclass(frozen=True, slots=True, kw_only=True)
class SpiralCoilSpec:
    coil_count: int                # Q per layer
    r_inner_mm: float
    r_outer_mm: float
    trace_width_mm: float
    clearance_mm: float
    coil_gap_mm: float             # between neighbouring coils
    turns: int | None = None       # None = maximum feasible
    side_style: SideStyle = SideStyle.PARALLEL
    end_style: EndStyle = EndStyle.ARC
    inner_turn_mode: InnerTurnMode = InnerTurnMode.MOVING
    corner_radius_mm: float = 0.0
    end_width_outer_mm: float | None = None   # None = trace width
    end_width_inner_mm: float | None = None
    width_profile: Literal["constant"] = "constant"   # reserved: "radius_proportional" (S5, D10)

@dataclass(frozen=True, slots=True, kw_only=True)
class SpiralWindingSpec:
    kind: Literal["spiral"] = "spiral"
    coil: SpiralCoilSpec
    layers: LayerConfig
    assignment: PhaseAssignmentInput | None = None    # None = star of slots (automatic)
    parallel_paths: int = 1        # a <= t, only between identical-phasor, identical-z groups (A2-TOP §3.4)

# Reserved, not implemented in P2 (REQ-F-19): loader accepts the kind, validator reports UNSUPPORTED_TOPOLOGY.
@dataclass(frozen=True, slots=True, kw_only=True)
class SerpentineWindingSpec:
    kind: Literal["serpentine"] = "serpentine"
    params: dict[str, object]      # to be specified when the generator is ported

@dataclass(frozen=True, slots=True, kw_only=True)
class WaveWindingSpec:
    kind: Literal["wave"] = "wave"
    params: dict[str, object]

WindingSpec = SpiralWindingSpec | SerpentineWindingSpec | WaveWindingSpec
```

Stack-up and layer configuration (Agent 2 requests: custom z, per-pair phase/rotation/connection):

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class CopperLayer:
    kind: Literal["copper"] = "copper"
    name: str                      # unique, e.g. "L1"; mapped to KiCad names by order (F.Cu, In1.Cu, ..., B.Cu)
    thickness_mm: float

@dataclass(frozen=True, slots=True, kw_only=True)
class DielectricLayer:
    kind: Literal["dielectric"] = "dielectric"
    name: str
    thickness_mm: float
    material: str                  # e.g. "FR-4"
    relative_permittivity: float | None = None
    density_g_per_cm3: float | None = None   # EQ-16; source needed (A2-EQ EQ-16)

class StackupSource(StrEnum):
    USER = "user"; GENERATED_EVEN = "generated_even"; IMPORTED_KICAD = "imported_kicad"

@dataclass(frozen=True, slots=True, kw_only=True)
class Stackup:
    layers: tuple[CopperLayer | DielectricLayer, ...]   # top to bottom; always explicit
    source: StackupSource = StackupSource.USER

    def copper_layers(self) -> tuple[CopperLayer, ...]: ...
    def copper_z_mm(self) -> dict[str, float]: ...      # centre z from the top surface (exact cumulative sum)
    def board_thickness_mm(self) -> float: ...

class PairConnection(StrEnum):
    SERIES = "series"; PARALLEL = "parallel"

@dataclass(frozen=True, slots=True, kw_only=True)
class LayerPair:
    index: int
    layer_in: str                  # copper layer name of X (spiral in)
    layer_out: str                 # copper layer name of Y (spiral out, mirrored artwork)
    rotation_rad: float = 0.0      # option M3 (A2-TOP §4.2)
    phases: tuple[Phase, ...] | None = None   # None = all phases (FSCW); one phase = option M4

@dataclass(frozen=True, slots=True, kw_only=True)
class LayerConfig:
    pairs: tuple[LayerPair, ...]
    series_groups: tuple[tuple[int, ...], ...]
    # Pair indices: inner tuples are connected in PARALLEL, the groups in SERIES (EQ-07).
    # ((0,), (1,), (2,)) = all series (M2); ((0, 1, 2),) = all parallel (M1); ((0, 1), (2, 3)) = D10 style.

@dataclass(frozen=True, slots=True, kw_only=True)
class CoilAssignmentInput:
    coil_index: int
    phase: Phase
    polarity: Literal[1, -1]

@dataclass(frozen=True, slots=True, kw_only=True)
class PhaseAssignmentInput:        # manual override of the star of slots
    coils: tuple[CoilAssignmentInput, ...]
```

Vias, connection, outline, operating point, materials, analysis options, DRC rules:

```python
class ViaSpan(StrEnum):
    THROUGH = "through"; BLIND = "blind"; BURIED = "buried"

@dataclass(frozen=True, slots=True, kw_only=True)
class ViaSpec:
    drill_mm: float
    pad_mm: float
    plating_um: float              # EQ-11 input (D05 assumed 25 um)
    vias_per_transition: int = 1   # multi-via eyes (A2-EQ EQ-11 change)
    allowed_spans: tuple[ViaSpan, ...] = (ViaSpan.THROUGH,)   # blind/buried: open question Q3

class ConnectionTopology(StrEnum):
    STAR = "star"; DELTA = "delta"; OPEN = "open"

@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionSpec:
    topology: ConnectionTopology = ConnectionTopology.STAR
    draw_interconnect: bool = True
    ring_width_mm: float
    terminal_pad_mm: float
    terminal_drill_mm: float       # 0 = SMD pad
    terminal_location: Literal["outer"] = "outer"   # A2-TOP §3.4 (hub terminals conflict with bore)
    neutral_pad: bool = False

@dataclass(frozen=True, slots=True, kw_only=True)
class OutlineSpec:
    shape: Literal["circle", "polygon"]
    sides: int | None
    across_flats_mm: float | None
    radius_mm: float | None
    corner_radius_mm: float = 0.0
    rotation_rad: float = 0.0
    bore_diameter_mm: float | None
    holes: tuple[HoleSpec, ...] = ()

@dataclass(frozen=True, slots=True, kw_only=True)
class OperatingPoint:
    speed_rpm: float
    line_current_rms_a: float
    winding_temperature_degc: float
    ambient_temperature_degc: float
    dc_link_v: float | None = None
    modulation: Literal["svpwm", "spwm", "six_step"] = "svpwm"   # EQ-20 (cannot verify yet)
    convection_h_w_m2k: float      # A2-EQ EQ-17: source disagreement 10 vs 30 W/m2K

@dataclass(frozen=True, slots=True, kw_only=True)
class MaterialConstant:            # constants with provenance (G6: rho20, alpha need a cited source)
    name: str
    value: float
    unit: str
    source_ref: str | None         # EV-ID / document reference, None = unsourced
    status: str                    # Status value

@dataclass(frozen=True, slots=True, kw_only=True)
class MaterialSet:
    copper_resistivity_20c: MaterialConstant
    copper_temp_coeff: MaterialConstant
    copper_density: MaterialConstant
    laminate_density: MaterialConstant

@dataclass(frozen=True, slots=True, kw_only=True)
class AnalysisOptions:
    harmonics: tuple[int, ...] = (1, 3, 5, 7, 9, 11, 13)   # odd only (A2-EQ EQ-05)
    max_segment_mm: float = 0.5                            # EQ-06 validity
    radial_edge_correction: Literal["none"] = "none"        # reserved (D09 p.4-5, A2-EQ EQ-05)
    inductance_model: Literal["magnetising_estimate", "current_sheet_estimate"] = "magnetising_estimate"

@dataclass(frozen=True, slots=True, kw_only=True)
class DrcRules:
    trace_clearance_mm: float
    via_clearance_mm: float
    edge_clearance_mm: float
    hole_clearance_mm: float
    min_trace_width_mm: float
    min_drill_mm: float
    min_annular_ring_mm: float

@dataclass(frozen=True, slots=True, kw_only=True)
class DesignParameters:
    schema_version: int
    name: str
    rotor: RotorSpec
    winding: WindingSpec
    stackup: Stackup
    vias: ViaSpec
    connection: ConnectionSpec
    outline: OutlineSpec
    operating: OperatingPoint
    materials: MaterialSet
    analysis: AnalysisOptions
    drc_rules: DrcRules
    phases: Literal[3] = 3         # P2 scope; the winding code is written for general m

class InputSource(StrEnum):
    USER = "user"; DEFAULT = "default"; IMPORTED_KICAD = "imported_kicad"; MIGRATED = "migrated"

@dataclass(frozen=True, slots=True, kw_only=True)
class FieldProvenance:             # per input field, keyed by JSON pointer ("/rotor/remanence_t")
    source: InputSource
    note: str = ""                 # e.g. "typical NdFeB value, source needed (A2-TOP §5.2)"

ProvenanceMap = dict[str, FieldProvenance]
```

### 7.2 Winding plan (`embodic.winding`)

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class Feasibility:
    coils: int; poles: int; phases: int
    q: Fraction                    # Q / (2p m), exact
    periodicity: int               # t = gcd(Q, p)
    balanced: bool                 # Q / (m t) integer
    max_parallel_paths: int        # = t (A2-TOP §2.2 / §3.4)

@dataclass(frozen=True, slots=True, kw_only=True)
class CoilAssignment:
    coil_index: int
    phasor_index: int              # p*k mod Q (exact integer arithmetic; fixes A2-REV Q-1)
    phase: Phase
    polarity: Literal[1, -1]

@dataclass(frozen=True, slots=True, kw_only=True)
class WindingPlan:
    feasibility: Feasibility
    assignment: tuple[CoilAssignment, ...]
    pattern: str                   # e.g. "ACBACBACBACB" / "AabBCcaABbcC" (upper = +, lower = -)
    winding_factors: dict[int, Traceable[float]]   # k_w,n textbook, turn-averaged later from geometry (EQ-08)
    layer_config: LayerConfig
    connection: ConnectionTopology
    issues: tuple[ValidationIssue, ...]
```

### 7.3 Via plan (Agent 2 request)

```python
class ViaRole(StrEnum):
    CENTRE = "centre"; TRANSFER = "transfer"; TERMINAL = "terminal"; RING = "ring"; STITCH = "stitch"

@dataclass(frozen=True, slots=True, kw_only=True)
class PlannedVia:
    id: int
    x_mm: float; y_mm: float
    role: ViaRole
    span: ViaSpan
    layer_from: str; layer_to: str # copper layer names it connects
    net: str
    coil_index: int | None
    pair_index: int | None
    group_index: int | None        # index into LayerConfig.series_groups

@dataclass(frozen=True, slots=True, kw_only=True)
class ViaPlan:
    vias: tuple[PlannedVia, ...]
    vias_per_transition: int
```

Expected winding-via count (`assumption` — planner design to be confirmed by Agent 2; used by UT-GEO-13):
- all pairs in series (M2), n pairs, v vias per transition: N = Q · (n + (n − 1)) · v (one centre via per pair and coil,
  one outer transfer via per series step and coil — A2-TOP §4.2 M2). Default design (Q = 12, n = 3, v = 1): 60.
- all pairs in parallel (M1): N = Q · (1 + 2) · v (one shared through centre via, one stitch via at each of the two outer
  coil ends joining the parallel layers). Default design: 36.
- mixed groups: computed by the planner per group; interconnect vias (rings, terminals) are counted separately.

### 7.4 Electrical circuit (output of geometry, input of physics)

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class Member:                      # one conductive route between two group nodes, in current direction
    path_ids: tuple[int, ...]      # CopperPath ids (each on one layer; EMF evaluated at that layer's z)
    via_ids: tuple[int, ...]

@dataclass(frozen=True, slots=True, kw_only=True)
class ParallelGroup:
    members: tuple[Member, ...]    # connected in parallel (EQ-07: conductance-weighted EMF, circulating loss)

@dataclass(frozen=True, slots=True, kw_only=True)
class PhaseCircuit:
    phase: Phase
    groups: tuple[ParallelGroup, ...]   # connected in series
    terminal_net: str              # "U" / "V" / "W"

@dataclass(frozen=True, slots=True, kw_only=True)
class Circuit:
    phases: tuple[PhaseCircuit, ...]
    topology: ConnectionTopology
    interconnect_path_ids: tuple[int, ...]   # rings/stubs: in R (EQ-10) and integrated by the EQ-06 kernel like any path
```

Note: interconnect copper outside the magnet span produces no EMF in the EQ-05/06 model (field clipped to the magnet
span, A2-REV §2.2 `verified` code reading); inside the span its radial parts would — the physics code integrates every
path with the same EQ-06 kernel rather than assuming zero (`assumption`, avoids a hidden special case).

### 7.5 Geometry primitives and layout (`embodic.geometry`, ADR-0002)

```python
class PrimitiveRole(StrEnum):
    SIDE = "side"; END_TURN = "end_turn"; LEAD = "lead"; FILLET = "fillet"; RING = "ring"
    STUB = "stub"; OUTLINE = "outline"

@dataclass(frozen=True, slots=True, kw_only=True)
class Line:
    x1_mm: float; y1_mm: float; x2_mm: float; y2_mm: float
    width_mm: float                # 0 for outline geometry
    role: PrimitiveRole

@dataclass(frozen=True, slots=True, kw_only=True)
class Arc:
    cx_mm: float; cy_mm: float; r_mm: float
    start_rad: float; sweep_rad: float   # signed sweep: positive = counter-clockwise (y up)
    width_mm: float
    role: PrimitiveRole
    def start_point(self) -> tuple[float, float]: ...
    def mid_point(self) -> tuple[float, float]: ...   # KiCad arcs are start/mid/end
    def end_point(self) -> tuple[float, float]: ...

Primitive = Line | Arc

@dataclass(frozen=True, slots=True, kw_only=True)
class CopperPath:                  # continuous chain on ONE copper layer, ordered in current direction
    id: int
    layer: str
    net: str
    primitives: tuple[Primitive, ...]
    phase: Phase | None            # None for neutral/interconnect
    coil_index: int | None
    pair_index: int | None
    polarity: Literal[1, -1, 0]

@dataclass(frozen=True, slots=True, kw_only=True)
class Pad:
    id: int; x_mm: float; y_mm: float
    shape: Literal["round", "square", "oblong", "rect"]
    width_mm: float; height_mm: float; rotation_rad: float
    drill_mm: float                # 0 = SMD
    layer: str | None              # SMD layer; None = all copper layers
    net: str; label: str

@dataclass(frozen=True, slots=True, kw_only=True)
class BoardOutline:
    outer: tuple[Primitive, ...]   # closed loop
    cutouts: tuple[tuple[Primitive, ...], ...]   # bore etc., closed loops
    holes: tuple[tuple[float, float, float], ...]   # (x_mm, y_mm, diameter_mm)

@dataclass(frozen=True, slots=True, kw_only=True)
class Layout:
    generator: str                 # "spiral" (P2); "serpentine" / "wave" later
    copper_layers: tuple[str, ...] # top to bottom, = Stackup copper names
    copper_z_mm: dict[str, float]
    paths: tuple[CopperPath, ...]
    vias: ViaPlan
    pads: tuple[Pad, ...]
    outline: BoardOutline
    circuit: Circuit
    turns_per_coil: Traceable[int]
    envelope_mm: tuple[float, float]   # r_min_cu, r_max_cu
    layout_hash: str               # SHA-256 of the canonical primitive list (cache key, export metadata)
    def arrays(self) -> LayoutArrays: ...   # cached NumPy view for DRC/physics (§11)
```

`LayoutArrays` (per layer): `lines: ndarray (N, 5)` [x1, y1, x2, y2, w], `arcs: ndarray (M, 6)` [cx, cy, r, start, sweep, w],
`path_index`, `prim_index` (to map violations back), `vias: ndarray (K, 4)` [x, y, pad, drill] + span mask per layer.

### 7.6 DRC report (`embodic.drc`)

```python
class DrcCheckKind(StrEnum):
    TRACE_TRACE = "trace_trace"; TRACE_VIA = "trace_via"; VIA_VIA = "via_via"; PAD_TRACE = "pad_trace"
    PAD_PAD = "pad_pad"; COPPER_EDGE = "copper_edge"; COPPER_HOLE = "copper_hole"
    MIN_WIDTH = "min_width"; MIN_DRILL = "min_drill"; ANNULAR_RING = "annular_ring"

@dataclass(frozen=True, slots=True, kw_only=True)
class DrcViolation:
    kind: DrcCheckKind
    layer: str | None
    measured_mm: float
    required_mm: float
    at_mm: tuple[float, float]
    objects: tuple[str, ...]       # e.g. ("path:17/prim:4", "via:33")

@dataclass(frozen=True, slots=True, kw_only=True)
class DrcCheckSummary:
    kind: DrcCheckKind
    measured_min_mm: float | None  # None = no pair of this kind exists
    required_mm: float
    pairs_checked: int

@dataclass(frozen=True, slots=True, kw_only=True)
class DrcReport:
    passed: bool
    summaries: tuple[DrcCheckSummary, ...]
    violations: tuple[DrcViolation, ...]     # capped list (first 1 000) + total count
    violation_count: int
    method: str                    # "grid+exact" or "symmetric+grid+exact"
    tolerance_mm: float = 1e-6
```

Connectivity-aware exemption (`inferred` from the spiral topology): turns of one spiral belong to the **same net but must
keep clearance**; only primitives adjacent in a path (sharing a joint) and a via/pad with the path ends it terminates
are exempt. Net-based exemption, as in generic PCB DRC, would hide turn-to-turn shorts.

### 7.7 Results (`embodic.results`, ADR-0003)

```python
from typing import Generic, TypeVar
T = TypeVar("T")

class Status(StrEnum):
    VERIFIED = "verified"; INFERRED = "inferred"; ASSUMPTION = "assumption"
    UNRESOLVED = "unresolved"; NOT_TESTED = "not tested"

STATUS_STRENGTH = {Status.UNRESOLVED: 0, Status.NOT_TESTED: 1, Status.ASSUMPTION: 2,
                   Status.INFERRED: 3, Status.VERIFIED: 4}   # weakest-link order: proposal, ADR-0003

@dataclass(frozen=True, slots=True, kw_only=True)
class Assumption:
    id: str                        # e.g. "AS-ROTOR-NS-ALIGNED"
    text: str
    status: Status
    source_ref: str | None = None  # EV-ID, document reference, "A2-TOP §5.2", or None

@dataclass(frozen=True, slots=True, kw_only=True)
class InputRef:
    pointer: str                   # JSON pointer into DesignParameters ("/winding/coil/trace_width_mm") or "result:<quantity>"
    value: float | int | str
    unit: str
    source: InputSource | None     # user / default / imported (provenance)
    status: Status                 # DEFAULT -> assumption; USER/IMPORTED -> neutral (verified strength)

@dataclass(frozen=True, slots=True, kw_only=True)
class ValidityFlag:
    code: str                      # "RANGE_SKIN_DEPTH"
    message: str
    eq_id: str

@dataclass(frozen=True, slots=True, kw_only=True)
class Tolerance:
    relative: float | None
    absolute: float | None
    against: str                   # "measured DC resistance at known temperature (D09, D10)"
    source_ref: str                # "A2-EQ EQ-10"

@dataclass(frozen=True, slots=True, kw_only=True)
class Traceable(Generic[T]):
    quantity: str                  # machine name, e.g. "phase_resistance_operating"
    value: T
    unit: Unit
    eq_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]  # filled from the registry for the eq_ids
    assumptions: tuple[Assumption, ...]
    inputs: tuple[InputRef, ...]
    validity: tuple[ValidityFlag, ...]
    tolerance: Tolerance | None
    status: Status                 # = combine_status(...), never set by hand
    status_reasons: tuple[str, ...]   # human-readable contributors to the status

def traced(quantity: str, value: T, unit: Unit, *, eq_ids: Sequence[str],
           inputs: Sequence[InputRef], assumptions: Sequence[Assumption] = (),
           validity: Sequence[ValidityFlag] = (), registry: Registry) -> Traceable[T]:
    """Build a Traceable: pulls evidence IDs, base status and tolerance from the registry, combines statuses."""

@dataclass(frozen=True, slots=True, kw_only=True)
class LayerResult:
    layer: str; z_mm: Traceable[float]; b1_peak_mid_radius_t: Traceable[float]

@dataclass(frozen=True, slots=True, kw_only=True)
class PhaseResult:
    phase: Phase
    ke_peak_v_s_per_rad: Traceable[float]
    resistance_20c_ohm: Traceable[float]
    resistance_operating_ohm: Traceable[float]
    circulating_loss_w: Traceable[float]

@dataclass(frozen=True, slots=True, kw_only=True)
class AnalysisResult:
    ke_phase: Traceable[float]          # EQ-06, EQ-09
    ke_line: Traceable[float]           # EQ-09
    kt_per_line_a_rms: Traceable[float] # EQ-09
    kv_rpm_per_v: Traceable[float]      # EQ-09
    winding_factor_1: Traceable[float]  # EQ-08 textbook (turn-averaged)
    utilisation_factor: Traceable[float]   # Xcoil "kw1 (num)" renamed (A2-REV §1)
    resistance_phase_20c: Traceable[float]       # EQ-10, EQ-11
    resistance_phase_operating: Traceable[float]
    resistance_line: Traceable[float]
    emf_phase_rms: Traceable[float]
    torque: Traceable[float]
    loss_copper: Traceable[float]       # EQ-10 with operating current
    loss_eddy: Traceable[float]         # EQ-12
    loss_circulating: Traceable[float]  # EQ-07
    loss_delta_circulating: Traceable[float]   # EQ-19
    thd_phase: Traceable[float]; thd_line: Traceable[float]   # EQ-18 (both, A2-EQ)
    current_density: Traceable[float]   # EQ-22
    skin_depth: Traceable[float]        # EQ-13
    inductance_estimate: Traceable[float]      # EQ-14 -> status unresolved, "estimate"
    ipc_guideline_current: Traceable[float]    # EQ-15 -> status unresolved, "guideline (unverified)"
    mass_copper: Traceable[float]; mass_laminate: Traceable[float]   # EQ-16
    temperature_rise: Traceable[float]  # EQ-17
    layers: tuple[LayerResult, ...]
    phases: tuple[PhaseResult, ...]
    emf_waveform: Traceable[tuple[float, ...]]   # EQ-18 samples over one electrical period
    registry_version: str
```

### 7.8 Outcome and issues (`embodic.api`, `embodic.errors`)

```python
class Severity(StrEnum):
    ERROR = "error"; WARNING = "warning"; INFO = "info"

class IssueCategory(StrEnum):
    INVALID = "invalid"; UNSUPPORTED_RANGE = "unsupported_range"; UNBUILDABLE = "unbuildable"
    DRC = "drc"; INTERNAL = "internal"

@dataclass(frozen=True, slots=True, kw_only=True)
class ValidationIssue:
    code: str                      # stable, e.g. "INVALID_ORDER", "RANGE_SKIN_DEPTH", "UNBUILDABLE_ZERO_TURNS"
    category: IssueCategory
    severity: Severity
    message: str                   # English, from the message catalogue
    pointers: tuple[str, ...]      # JSON pointers of the parameters involved
    value: float | int | str | None = None
    limit: float | int | str | None = None
    hint: str = ""
    eq_ids: tuple[str, ...] = ()

@dataclass(frozen=True, slots=True, kw_only=True)
class VersionInfo:
    embodic: str; schema: int; registry: str; python: str; numpy: str

@dataclass(frozen=True, slots=True, kw_only=True)
class ComputeOutcome:
    design_hash: str
    issues: tuple[ValidationIssue, ...]
    winding: WindingPlan | None
    layout: Layout | None
    drc: DrcReport | None
    analysis: AnalysisResult | None
    timings_s: dict[str, float]
    versions: VersionInfo
    @property
    def ok(self) -> bool: ...      # no ERROR issue and drc.passed
```

## 8. Component interfaces (public functions)

Naming: functions are verbs, dataclasses nouns (§15.2). Every function below is pure (no I/O, no global state) unless
stated; all raise only on programming errors (wrong types), never on user input.

### 8.1 `embodic.api`

```python
def compute(design: DesignParameters, *, options: ComputeOptions | None = None,
            cache: StageCache | None = None, cancel: CancelToken | None = None) -> ComputeOutcome: ...
def default_design() -> tuple[DesignParameters, ProvenanceMap]: ...
def version_info() -> VersionInfo: ...
```

### 8.2 `embodic.model` and `embodic.winding`

```python
def validate_design(design: DesignParameters) -> tuple[ValidationIssue, ...]: ...
def generate_even_stackup(copper_count: int, copper_thickness_mm: float,
                          board_thickness_mm: float, material: str = "FR-4") -> Stackup: ...

def check_feasibility(coil_count: int, poles: int, phases: int = 3) -> Feasibility: ...
def assign_phases(coil_count: int, poles: int, phases: int = 3) -> tuple[CoilAssignment, ...]: ...
def compute_winding_factors(assignment: Sequence[CoilAssignment], poles: int, coil_count: int,
                            spans_rad: Sequence[float], harmonics: Sequence[int],
                            registry: Registry) -> dict[int, Traceable[float]]: ...
def plan_winding(design: DesignParameters, registry: Registry) -> WindingPlan: ...
```

### 8.3 `embodic.geometry`

```python
class WindingGenerator(Protocol):
    """Builds the winding copper for one topology. Implementations: SpiralGenerator (P2);
    SerpentineGenerator, WaveGenerator (Later, REQ-F-19)."""
    kind: ClassVar[str]
    def max_turns(self, design: DesignParameters, winding: WindingPlan) -> Traceable[int]: ...
    def build(self, design: DesignParameters, winding: WindingPlan) -> WindingArtwork | tuple[ValidationIssue, ...]: ...

def register_generator(generator: WindingGenerator) -> None: ...
def build_layout(design: DesignParameters, winding: WindingPlan,
                 registry: Registry) -> Layout | tuple[ValidationIssue, ...]: ...

# spiral generator building blocks (embodic.geometry.generators.spiral)
def generate_spiral_artwork(coil: SpiralCoilSpec, eye: EyeRequirement) -> SpiralArtwork: ...   # X (in) and Y (out)
def place_coils(artwork: SpiralArtwork, winding: WindingPlan, layers: LayerConfig) -> tuple[CopperPath, ...]: ...
def plan_vias(design: DesignParameters, winding: WindingPlan, paths: Sequence[CopperPath]) -> ViaPlan: ...
def build_interconnect(design: DesignParameters, winding: WindingPlan, paths: Sequence[CopperPath],
                       vias: ViaPlan) -> Interconnect: ...
def build_outline(spec: OutlineSpec, envelope_mm: tuple[float, float]) -> BoardOutline: ...

# primitive utilities (embodic.geometry.primitives / transforms)
def primitive_length_mm(p: Primitive) -> float: ...
def reverse_path(prims: Sequence[Primitive]) -> tuple[Primitive, ...]: ...
def rotate(prims: Sequence[Primitive], angle_rad: float) -> tuple[Primitive, ...]: ...
def mirror(prims: Sequence[Primitive], axis_angle_rad: float) -> tuple[Primitive, ...]: ...
```

### 8.4 `embodic.drc`

```python
def run_drc(layout: Layout, rules: DrcRules, *, use_symmetry: bool = True,
            cancel: CancelToken | None = None) -> DrcReport: ...
def min_distance_line_line(a: ndarray, b: ndarray) -> ndarray: ...   # vectorised, exact
def min_distance_line_arc(a: ndarray, b: ndarray) -> ndarray: ...
def min_distance_arc_arc(a: ndarray, b: ndarray) -> ndarray: ...
```

### 8.5 `embodic.physics`

One module per concern; each function cites its EQ-ID in the docstring and returns plain numbers/arrays; only
`analyse()` wraps values into `Traceable` (keeps kernels testable against closed forms).

```python
def pole_arc_ratio_block(width_mm: float, radius_mm: ndarray, poles: int) -> ndarray: ...       # EQ-04
def field_harmonic(n: int, radius_mm: ndarray, z_mm: ndarray, rotor: RotorSpec,
                   symmetry_plane_mm: float, alpha_p: ndarray) -> tuple[ndarray, ndarray]: ...  # EQ-05 (Bz, Bt peak)
def symmetry_plane_mm(rotor: RotorSpec, board_thickness_mm: float) -> float: ...                 # EQ-05 G
def flux_linkage_harmonics(paths: LayoutArrays, z_by_layer: Mapping[str, float], rotor: RotorSpec,
                           harmonics: Sequence[int]) -> ndarray: ...                             # EQ-06 (complex, per path)
def solve_phase_circuit(circuit: Circuit, path_emf: ndarray, path_r_ohm: ndarray) -> CircuitSolution: ...   # EQ-07
def phase_constants(ke_phase: float, topology: ConnectionTopology, phases: int) -> MotorConstants: ...      # EQ-09
def copper_resistivity(temperature_degc: float, materials: MaterialSet) -> float: ...           # EQ-10
def path_resistance_ohm(arrays: LayoutArrays, thickness_mm_by_layer: Mapping[str, float],
                        resistivity_ohm_m: float) -> ndarray: ...                               # EQ-10
def via_resistance_ohm(drill_mm: float, plating_um: float, length_mm: float,
                       resistivity_ohm_m: float, count: int) -> float: ...                       # EQ-11
def eddy_loss_w(...) -> float: ...                                                               # EQ-12
def skin_depth_mm(frequency_hz: float, resistivity_ohm_m: float) -> float: ...                   # EQ-13
def inductance_estimate_h(...) -> float: ...                                                     # EQ-14 (estimate)
def ipc2221_current_a(...) -> float: ...                                                         # EQ-15 (guideline)
def mass_g(...) -> MassBreakdown: ...                                                            # EQ-16
def temperature_rise_k(...) -> float: ...                                                        # EQ-17
def emf_waveform(...) -> ndarray: ...; def thd(...) -> float: ...                                # EQ-18
def delta_circulating_loss_w(...) -> float: ...                                                  # EQ-19
def analyse(design: DesignParameters, winding: WindingPlan, layout: Layout,
            registry: Registry) -> AnalysisResult: ...
```

### 8.6 `embodic.results` and `embodic.io`

```python
def load_registry(version: str | None = None) -> Registry: ...
def combine_status(*statuses: Status) -> Status: ...
def format_value(t: Traceable[float], *, significant: int = 4) -> str: ...   # locale-independent, SI prefixes

def load_project(path: Path) -> tuple[DesignParameters | None, ProvenanceMap, tuple[ValidationIssue, ...]]: ...
def save_project(path: Path, design: DesignParameters, provenance: ProvenanceMap, ui_state: Mapping[str, object]) -> str: ...  # returns hash
def canonical_json(design: DesignParameters) -> bytes: ...
def design_hash(design: DesignParameters) -> str: ...                     # "sha256:<hex>"
def write_svg(outcome: ComputeOutcome, path: Path) -> ExportSummary: ...
def write_dxf(outcome: ComputeOutcome, path: Path, part: Literal["full", "outline", "holes"]) -> ExportSummary: ...
def write_kicad_pcb(outcome: ComputeOutcome, path: Path, origin_mm: tuple[float, float] = (150.0, 100.0)) -> ExportSummary: ...
def write_results_json(outcome: ComputeOutcome, path: Path) -> None: ...
def write_results_csv(outcome: ComputeOutcome, path: Path) -> None: ...
def write_report_pdf(outcome: ComputeOutcome, path: Path) -> ExportSummary: ...
```

`ExportSummary` returns entity counts (segments, arcs, vias, pads, edges) so tests compare them with the layout (KX-01).
The `(150, 100)` mm origin mirrors Xcoil `exportKicad` (`OX = 150, OY = 100`, engine.js l.2878, `verified` code reading).

### 8.7 `embodic.cli`

```
embodic-cli compute  <project.embodic.json> [--json out.json] [--no-drc] [--timings]
embodic-cli validate <project.embodic.json>
embodic-cli export   <project.embodic.json> --format {svg,dxf,dxf-outline,dxf-holes,kicad_pcb,pdf,json,csv} -o <path> [--allow-drc-errors]
embodic-cli registry {list,show EQ-xx,check}
embodic-cli golden-compare <golden.json> [--tolerance 1e-9]        # test tooling, ADR-0006
embodic [project.embodic.json]                                     # standalone UI (extra "desktop")
```
Exit codes: 0 ok, 1 validation errors, 2 DRC errors, 3 internal error (REQ-F-18). Entry-point names follow Agent 3's
proposal (`dependency_and_tooling_draft.md` §4.1).

## 9. KiCad integration (ADR-0004)

### 9.1 Routes

| Route | When | Status of evidence |
|---|---|---|
| R1 `.kicad_pcb` file writer (`embodic.io.kicad_pcb`) | Always; no KiCad process needed | Writer pattern `verified` in Xcoil with kiutils parsing (`validate_exports.py`); KiCad 9.x acceptance of the written format version `unresolved` → KS-01 |
| R2 IPC plugin (`embodic_kicad_plugin`, KiCad's bundled Python, per-plugin venv) | User invokes action in the PCB editor | API capabilities `verified` from kipy 0.8.0 source (A5-KI §3); behaviour on the user's 9.0.x `unresolved` → T2/T4 |
| R3 Standalone app as IPC client | Optional; launched by R2 (inherits `KICAD_API_SOCKET` / `KICAD_API_TOKEN`, Agent 3 `kicad_plugin_feasibility.md` §4, `verified (doc extract)` there) or by the user | connection from a child or independent process on Windows `unresolved` → T3 |
| R4 `kicad-cli pcb drc --format json` on an exported board | Optional complementary check (REQ-K-12) | documented in the 9.0 CLI manual (Agent 3 §2, `verified (doc extract)`); `not tested` (T5) |
| SWIG `pcbnew` | Not used | Deprecated 9.0, removal planned 11.0 (A5-KI §2, `verified`) |

Route-label mapping between documents: R1 = Agent 3 route C; R2 = Agent 3 route A (A1 toolbar plugin) = Agent 5
route B (IPC); R3 = Agent 3 A2 "external control"; SWIG = Agent 3 route B = Agent 5 route A.

### 9.2 Plugin package

```
embodic_kicad_plugin/                 # PCM archive content: plugins/ (A5-KI §1: runtime "ipc", 9.0.1+)
  plugin.json                         # schema go.kicad.org/api/schemas/v1 (A5-KI §3); actions below
  requirements.txt                    # kicad-python==<pin from T4>, numpy<range>, embodic==<version> (or vendored core)
  main.py                             # entry: parse action id, configure logging, call adapter
  embodic_kicad_plugin/
    connection.py                     # KiCad(), check_version(), get_board(); error mapping
    board_items.py                    # Layout -> kipy Track/ArcTrack/Via/shapes; mm->nm; y-axis flip; layer map
    stackup_import.py                 # Board.get_stackup()/get_copper_layer_count() -> embodic Stackup
    tracking.py                       # identify previously placed embodic items (UUID list in project file + net prefix)
    apply_project.py                  # action "Apply embodic project"
    launcher.py                       # action "Open embodic" (could, T3)
  resources/icon.png                  # 64x64 (A5-REG EV-K3)
```

Apply sequence (one undo step, REQ-K-02/04): connect → `check_version` → read stack-up → load project file
(convention: `<board-stem>.embodic.json` beside the board, or the path recorded by the standalone app) →
`embodic.api.compute()` → refuse if errors (unless the user chose override in the standalone app) → `begin_commit()` →
`remove_items(previous embodic items)` → `create_items(new items)` → `push_commit()`; on any exception `drop_commit()`.
Method names are those of kipy 0.8.0 `board.py` l.609–912 (A5-KI §3, `verified` source reading); their presence in the
kipy version matching the user's 9.0.x is `unresolved` (T2/T4).

Core distribution into KiCad's venv — two options, decided after T2 (`unresolved`): (a) publish `embodic` core as a
wheel and list it in `requirements.txt`; (b) vendor the pure-Python core package into the plugin archive and list only
`kicad-python` and `numpy`. Option (b) avoids a public package index dependency for the core (`inferred`).

### 9.3 Mapping rules

- Coordinates: KiCad y axis points down; Xcoil writes `Y = OY − y` (engine.js l.2880, `verified`) → the adapter flips y
  and offsets to the chosen origin. Arc orientation must be preserved by passing start/mid/end points.
- Layers: copper layer *i* of *n* → `F.Cu` (i = 0), `B.Cu` (i = n − 1), `In<i>.Cu` otherwise — mirrors Xcoil `layerName`
  usage in `exportKicad` (l.2882, `verified` code reading); KiCad's naming for inner layers in 9.x `inferred`, checked in
  KS-01.
- Nets: one net per phase terminal (U, V, W) plus N when drawn; with an on-board star/delta interconnect Xcoil used a
  single "WINDING" net (l.2886–2889); embodic proposes per-phase nets until the interconnect joins them, then a single
  net per electrical node (`assumption`, REQ-K-09).
- Units: mm float → nm int at one place (§6 U6).

## 10. Standalone UI architecture (proposal: PySide6, ADR-0005)

```
embodic/ui/
  app.py                 # QApplication setup, theme, logging, crash handler (REQ-N-18)
  strings.py             # English string catalogue (REQ-L-01/02)
  theme.py               # palette tokens from Agent 1 (white/grey/black), contrast-checked (AX-01)
  workers.py             # ComputeWorker (QRunnable), debounce 150 ms, latest-wins, CancelToken
  viewmodels/
    design_vm.py         # current DesignParameters + ProvenanceMap; edit -> dataclasses.replace -> undo stack
    outcome_vm.py        # latest ComputeOutcome; derived display rows (value, unit, status, EQ links)
  views/
    main_window.py       # layout per Agent 1 (input panel, geometry view, results, issues)
    geometry_view.py     # QGraphicsView; items per (layer, phase, width run); keyboard zoom/pan/fit
    phase_view.py        # coil -> phase/polarity table + diagram (text alternative to the drawing)
    layer_view.py        # stack-up table, pairs, series/parallel groups, vias
    results_view.py      # Traceable table + details pane (EQ, EV, assumptions, inputs, validity, tolerance)
    issues_view.py       # ValidationIssue list; click/Enter focuses the offending field
    export_dialog.py
```

Pattern: MVVM — views never call the engine; view-models call `embodic.api.compute` through `workers.py` and expose
immutable outcomes. The engine is thread-safe by construction (pure functions, frozen dataclasses); the stage cache is
guarded by a lock (`assumption`). All widget texts and accessible names come from `strings.py`.

UI behaviours carried over from Agent 1's analysis (`docs/phase1/design/ux_analysis.md`): `outcome_vm` keeps the last
valid layout and shows it marked "outdated" while the current input is invalid (Xcoil strength W1, REQ-F-27); the
view-model never rewrites a user value — feasibility suggestions are separate hint objects applied only by an explicit
command (Xcoil defect C2, REQ-F-23); exports with DRC errors go through a pre-flight confirmation (Xcoil defect C14,
§12); phases are encoded by label + line pattern + grey level, colour only if the user approves (REQ-L-04, N-14).

## 11. Performance design (REQ-N-01…03)

Evidence for the budget: the Xcoil JS engine needs 0.10–0.19 s for a comparable 12/16 sector design with 584 025 DRC pairs
on the agent container (requirements_draft.md §7, `verified (measured)` JS only). Agent 3 measured the DRC distance kernel
on the same container: 10⁶ calls take 40 ms in Node, 1 813 ms as a literal CPython port (≈ 45×) and 543 ms NumPy-vectorised
over all pairs (`calculation_flow_and_port_notes.md` §4, `verified (run)` there). Applied naively to all 584 025 pairs, the
vectorised kernel alone would take ≈ 0.32 s (`inferred`, linear scaling) — most of the 0.4 s DRC budget — so pair
reduction (symmetry, broad phase) is required, not optional. Measures:

1. **Stage cache** keyed by sub-model hashes (§5): changing speed or current recomputes physics only; changing B_r skips
   geometry and DRC.
2. **Symmetry reuse**: generate one coil artwork per (pair, polarity) and rotate; DRC of the rotationally periodic winding
   checks one period plus neighbours in canonical coordinates (Xcoil `buildCanonical`/`drcLayer`, engine.js l.406–650,
   `verified` code reading), while interconnect and outline are checked fully. Property test PR-02 asserts the symmetric
   result equals the full check on random designs.
3. **Vectorised kernels**: NumPy arrays per layer (§7.5); uniform-grid broad phase; exact line/arc distance formulas in
   the narrow phase (no discretisation error → conservative by construction, `inferred`).
4. **Field/EMF**: evaluate B_z,n for all segments × harmonics as one array operation per layer z.
5. **Rendering**: one graphics item per (layer, phase, width run), as Xcoil's `widthRuns` (engine.js l.2787), not per
   primitive.
6. **Budgets** (`assumption`): geometry ≤ 0.2 s, DRC ≤ 0.4 s, physics ≤ 0.3 s, UI update ≤ 0.1 s for the default design on
   the reference laptop; CI asserts 3× budget to catch regressions on slower runners (PF-04).

## 12. Error and validation model (REQ-F-14)

| Category | Severity | Pipeline effect | Example codes |
|---|---|---|---|
| **invalid** — input violates a hard constraint or type | error | stop before winding/geometry; no results | `INVALID_TYPE`, `INVALID_NON_POSITIVE` (trace width ≤ 0), `INVALID_ORDER` (r_outer ≤ r_inner), `INVALID_POLE_COUNT_ODD`, `INVALID_PAIR_LAYER_UNKNOWN`, `INVALID_SCHEMA_VERSION_NEWER`, `INVALID_TOO_LARGE` (resource limits, e.g. > 64 copper layers) |
| **unsupported range** — valid input outside an equation's validity or the validated domain | warning | results computed; affected `Traceable`s get a `ValidityFlag` and status capped at `unresolved` | `RANGE_SKIN_DEPTH` (w or t > δ/3, EQ-13), `RANGE_LOW_SPIRAL_UTILISATION` (Q/2p > 1, A2-TOP §2.4), `RANGE_MAGNET_EDGE` (copper within one gap of magnet radial ends, EQ-05), `RANGE_DELTA_TRIPLEN` (delta with k_w3 ≠ 0, EQ-19), `RANGE_PARALLEL_UNEQUAL_Z` (EQ-07), `RANGE_TRIANGULAR_TURN_FORMULA` (EQ-02 −w_d/2 discrepancy) |
| **unbuildable** — valid input but no layout can be produced | error | stop; no layout; analysis skipped | `UNBUILDABLE_UNBALANCED_WINDING`, `UNBUILDABLE_ZERO_TURNS`, `UNBUILDABLE_VIA_DOES_NOT_FIT`, `UNBUILDABLE_ODD_PAIR_LAYERS`, `UNBUILDABLE_PARALLEL_PATHS_EXCEED_T`, `UNSUPPORTED_TOPOLOGY` (serpentine/wave in P2), `UNSUPPORTED_MAGNETISATION` (Halbach) |
| **drc** — layout produced, clearance/manufacturing rule violated | error or warning | analysis still shown; exports need `--allow-drc-errors` / confirmation | `DRC_TRACE_TRACE`, `DRC_TRACE_VIA`, `DRC_PAD_PAD`, `DRC_COPPER_EDGE`, `DRC_MIN_WIDTH` |
| **internal** — bug | exception caught at adapter | logged with correlation ID; English message; offer to save project | `INTERNAL_ERROR` |

Validation order: types (loader) → single-field ranges → cross-field relations → winding feasibility → geometry
feasibility → DRC. Messages are English sentences from a catalogue keyed by code (REQ-L-01); codes never change meaning.

## 13. Traceability chain (REQ-T-01…09)

```mermaid
flowchart LR
  REQ["REQ-ID (requirements_draft.md)"] --> TEST["Test ID (pytest marker req=...)"]
  TEST --> EQR["EQ registry entry (gate, status, tolerance, linked tests)"]
  RESULT["Traceable result in UI/report"] --> INP["InputRefs: JSON pointers + provenance (user/default/imported)"]
  RESULT --> EQR
  RESULT --> ASM["Assumptions (AS-IDs)"]
  EQR --> EVR["EV registry entry (claim, document D-ID, page, status)"]
  EVR --> DOC["Source document page / URL"]
  ART["Export / report"] --> HASH["design hash + versions"] --> PROJ["Project file (.embodic.json)"]
  RESULT --> HASH
```

Worked example (illustrative, values not computed): `resistance_phase_operating` → inputs `/winding/coil/trace_width_mm`
(user), `/stackup/layers/0/thickness_mm` (default → `assumption`), `/operating/winding_temperature_degc` (default) and
`result:path_length_sum` → EQ-10, EQ-11 → EV-08, EV-28, EV-29, EV-44, EV-37 → D08 p.45 eq. 3.37–3.38, D05 p.6–8 →
constants ρ₂₀, α (`assumption: standard value, source needed`, A2-EQ EQ-10) → status = weakest = `assumption`, reasons
listed; tolerance ±8 % vs measured DC resistance (A2-EQ EQ-10) shown next to the value.

Registry files (packaged data, versioned with the app): `embodic/results/data/equations.v1.json`,
`evidence.v1.json`. Proposed entry format (statuses are **placeholders** — Agent 2/4 own the values):

```json
{
  "id": "EQ-10",
  "title": "DC resistance with temperature",
  "gate": "reuse",
  "status": "<set by Agent 2/4>",
  "evidence": ["EV-08", "EV-28", "EV-29", "EV-44"],
  "references": [{"doc": "D08", "location": "p.45 eq. 3.37-3.38"}, {"doc": "D10", "location": "p.4 eq. 8"}],
  "validity": ["w and t much smaller than skin depth (EQ-13)"],
  "tolerance": {"relative": 0.08, "against": "measured DC resistance at known temperature", "source": "A2-EQ EQ-10"},
  "constants": [{"name": "rho20", "value": 1.724e-8, "unit": "ohm_m", "status": "assumption", "note": "source needed (G6)"}],
  "tests": ["UT-PHY-10", "GR-02", "OR-02", "OR-03"]
}
```

CI checks (TR-01…TR-04): every EQ-ID used in code exists in the registry; every registry EQ with status `verified` links ≥ 1
passing test; every test carries ≥ 1 REQ marker; every must-REQ has ≥ 1 test.

## 14. Project file format (ADR-0007)

- File name `<name>.embodic.json`, UTF-8, JSON (RFC 8259). Top level:

```json
{
  "format": "embodic-project",
  "schema_version": 1,
  "app_version": "0.1.0",
  "saved_utc": "2026-10-04T12:00:00Z",
  "design_hash": "sha256:…",
  "design": {
    "name": "default 12/16",
    "phases": 3,
    "rotor": {"poles": 16, "rotor_type": "double", "remanence_t": 1.3, "recoil_permeability": 1.05,
              "air_gap_mm": 1.0, "back_iron_thickness_mm": 3.0,
              "magnet": {"kind": "block", "width_mm": 6.0, "length_mm": 20.0, "r_center_mm": 28.0, "thickness_mm": 2.0}},
    "winding": {"kind": "spiral",
                "coil": {"coil_count": 12, "r_inner_mm": 18.0, "r_outer_mm": 38.0, "trace_width_mm": 0.5,
                         "clearance_mm": 0.2, "coil_gap_mm": 0.2, "turns": null, "side_style": "parallel",
                         "end_style": "arc", "inner_turn_mode": "moving"},
                "layers": {"pairs": [{"index": 0, "layer_in": "L1", "layer_out": "L2", "rotation_deg": 0.0},
                                     {"index": 1, "layer_in": "L3", "layer_out": "L4", "rotation_deg": 0.0},
                                     {"index": 2, "layer_in": "L5", "layer_out": "L6", "rotation_deg": 0.0}],
                           "series_groups": [[0], [1], [2]]},
                "assignment": null},
    "stackup": {"source": "user", "layers": [{"kind": "copper", "name": "L1", "thickness_mm": 0.0348},
                                             {"kind": "dielectric", "name": "D1", "thickness_mm": 0.071, "material": "FR-4"}]},
    "vias": {"drill_mm": 0.3, "pad_mm": 0.5, "plating_um": 25.0, "vias_per_transition": 1, "allowed_spans": ["through"]},
    "connection": {"topology": "star", "draw_interconnect": true},
    "outline": {"shape": "polygon", "sides": 12, "across_flats_mm": 93.0, "bore_diameter_mm": 25.0},
    "operating": {"speed_rpm": 1000.0, "line_current_rms_a": 1.0, "winding_temperature_degc": 60.0,
                  "ambient_temperature_degc": 20.0, "convection_h_w_m2k": 10.0},
    "materials": {"…": "…"},
    "analysis": {"harmonics": [1, 3, 5, 7, 9, 11, 13], "max_segment_mm": 0.5},
    "drc_rules": {"trace_clearance_mm": 0.2, "…": "…"}
  },
  "provenance": {"/rotor/remanence_t": {"source": "default", "note": "typical NdFeB value, source needed (A2-TOP §5.2)"}},
  "kicad": {"placed_item_ids": [], "board_file_hint": null},
  "ui": {"view": {"zoom": 1.0}}
}
```

All numbers above are illustrative examples (`assumption`, mostly Agent 2 §5.2 defaults; the stack-up list is truncated).

- Angles are stored in degrees in the file (`_deg` fields) for human readability and converted once by the loader (§6 U2).
- **Hash**: SHA-256 over the canonical form of `design` only (keys sorted, no insignificant whitespace, floats in Python's
  shortest round-trip `repr`, UTF-8). `provenance`, `kicad` and `ui` are excluded so that view changes do not alter the
  design identity.
- **Versioning**: integer `schema_version`; loader applies `migrate_v<n>_to_v<n+1>` functions in sequence and reports
  `INFO_MIGRATED`; a newer-than-supported version is refused (`INVALID_SCHEMA_VERSION_NEWER`). Files are never rewritten
  without an explicit save.
- **Schema**: published JSON Schema (Draft 2020-12) `embodic/io/schema/project.v1.schema.json`; the runtime loader is
  hand-written and typed (precise messages with JSON pointers, no extra runtime dependency); a test validates all example
  files against the schema with `jsonschema` (test-only, MIT) to keep both in step (UT-IO-03).

## 15. Code organisation and conventions

### 15.1 Repository structure

```
embodic/                                   repository root (Fable: mirrored to C:\Users\<user>\Desktop\embodic)
├─ pyproject.toml                          PEP 621 metadata; extras: desktop, kicad, dev; tool configs (ruff, mypy, import-linter, pytest)
├─ README.md  LICENSE  THIRD_PARTY_LICENSES.md  CHANGELOG.md
├─ requirements/                           lock files with hashes: py311.txt, py312.txt, py313.txt (+ -dev variants)
├─ src/
│  ├─ embodic/
│  │  ├─ __init__.py                       __version__ only
│  │  ├─ api.py  units.py  errors.py
│  │  ├─ model/      design.py rotor.py winding_spec.py stackup.py layers.py vias.py connection.py outline.py
│  │  │              operating.py materials.py analysis_options.py drc_rules.py provenance.py defaults.py validate.py
│  │  ├─ winding/    feasibility.py star_of_slots.py winding_factors.py circuit_topology.py
│  │  ├─ geometry/   primitives.py transforms.py paths.py layout.py arrays.py vias.py interconnect.py outline.py
│  │  │              generators/__init__.py generators/base.py generators/spiral.py
│  │  ├─ drc/        rules.py distance.py broad_phase.py symmetry.py check.py
│  │  ├─ physics/    magnets.py field.py emf.py circuit_solution.py constants.py resistance.py losses.py
│  │  │              inductance.py thermal.py mass.py drive.py analyse.py
│  │  ├─ results/    status.py traceable.py registry.py analysis_result.py formatting.py
│  │  │              data/equations.v1.json data/evidence.v1.json
│  │  ├─ io/         project.py canonical.py migrations.py schema/project.v1.schema.json
│  │  │              svg_writer.py dxf_writer.py sexpr.py kicad_pcb_writer.py pdf_writer.py report.py results_export.py
│  │  ├─ cli/        __main__.py commands.py
│  │  └─ ui/         (extra "desktop"; see §10)
│  └─ embodic_kicad_plugin/                (see §9.2)
├─ tests/   unit/ golden/ oracle/ property/ boundary/ ui/ kicad/ language/ accessibility/ performance/ packaging/
│           conftest.py (markers: req, eq, slow, manual)
├─ tools/   golden_js/dump_reference.mjs   (Node; reads /serpentine read-only; writes JSON + engine SHA-256)
│           trace_matrix.py  check_strings.py  contrast_check.py  build_bundle.py
├─ examples/ default.embodic.json  o1_d08.embodic.json  o2_d09.embodic.json
└─ docs/     (phase documents)
```

### 15.2 Naming conventions

| Element | Rule | Examples |
|---|---|---|
| Packages / modules | snake_case **nouns** | `star_of_slots.py`, `kicad_pcb_writer.py` |
| Functions | snake_case **verbs** | `generate_spiral_artwork`, `assign_phases`, `run_drc`, `write_svg` |
| Dataclasses / classes | PascalCase **nouns** | `SpiralCoilSpec`, `Layout`, `DrcReport`, `Traceable` |
| Enums | PascalCase class, UPPER members, lower-case string values (serialised) | `SideStyle.PARALLEL = "parallel"` |
| Dimensional fields/args | unit suffix (§6) | `trace_width_mm`, `rotation_rad`, `speed_rpm` |
| Booleans | `is_`, `has_`, `use_`, `allow_` | `allow_drc_errors` |
| Constants | UPPER_SNAKE with unit | `MU0_H_PER_M` |
| Issue codes | UPPER_SNAKE with category prefix | `RANGE_SKIN_DEPTH` |
| Tests | `test_<unit>_<behaviour>` + `@pytest.mark.req("REQ-F-02")` | `test_star_of_slots_12_14_is_balanced` |
| Private | leading underscore; no cross-module use | `_grid_cells` |

### 15.3 Docstring and comment policy (REQ-N-09)

- NumPy-style docstrings on every public function/class with sections **Parameters** (each with unit), **Returns**
  (unit), **Assumptions**, **Validity**, **References** (EQ-IDs, EV-IDs, ADR) and **Notes** (why this approach).
- Comments explain *why* (reason, source, limitation), never restate code. Every non-obvious constant cites its source or
  is marked `assumption`. No commented-out code; `TODO` only with an issue ID.
- Example of the expected form (illustrative):

```python
def copper_resistivity(temperature_degc: float, materials: MaterialSet) -> float:
    """Return the copper resistivity at a temperature.

    Parameters
    ----------
    temperature_degc : float
        Conductor temperature in °C.
    materials : MaterialSet
        Supplies rho20 [Ω·m] and alpha [1/K] with their provenance.

    Returns
    -------
    float
        Resistivity in Ω·m.

    Assumptions
    -----------
    Linear temperature law; constants are 'assumption: standard value, source needed' (A5 gap G6).

    Validity
    --------
    Typical PCB operating range; electrodeposited copper may differ from annealed copper.

    References
    ----------
    EQ-10 (D08 eq. 3.37, EV-08).
    """
```

### 15.4 Numerical conventions (from Agent 3's JS↔Python measurements)

Source: `docs/phase1/software/calculation_flow_and_port_notes.md` §2 (measurements `verified (run)` by Agent 3).
- No built-in `sum()` over floats in `embodic.physics`/`embodic.drc` (its algorithm changed to Neumaier summation in
  Python 3.12 → results differ between 3.11 and 3.12); use `math.fsum`, explicit loops or NumPy consistently (MT-06).
- No built-in `round()` for coordinates or quantisation (half-to-even); use the helpers in `embodic.units`.
- Explicit `math.inf` where Xcoil relied on `Infinity` (e.g. initial minimum clearances); guard every division that can
  be zero; JSON writers encode non-finite numbers explicitly (no non-standard `Infinity` tokens).
- Float `%` vs `math.fmod`: use `math.fmod` where Xcoil's JS `%` semantics are ported.
- Group layers by tolerance-based z comparison, not by formatted-string keys (Xcoil `toFixed(6)` keys).
- Threshold decisions on continuous values (discretisation counts, magnet-span membership, turn limits, DRC pass/fail)
  expose their margin so that tests can classify near-threshold cases (test plan §3).

### 15.5 Logging

- Standard library `logging`; one logger per module (`logging.getLogger(__name__)`); the core never configures handlers.
- Adapters configure: UI → rotating file in the per-user log directory (`%LOCALAPPDATA%\embodic\logs` on Windows,
  via `platformdirs`, MIT per PyPI, `verified`; 1 MB × 5 files, `assumption`) + in-app issues view; CLI → stderr with
  `--log-level`; plugin → file in the same directory (KiCad's own plugin log location `unresolved`, T2).
- Session header: embodic version, Python, NumPy, OS, design hash; no user names, no full home paths, no project content
  beyond the hash (REQ-N-20). Levels: DEBUG stage timings, INFO stage completion, WARNING range issues, ERROR internal.

## 16. How Agent 2's data-model requests are met

| Request (source) | Where in the model | Status |
|---|---|---|
| Magnet shape arc / block with dimensions; α_p(r) for blocks (A2-EQ EQ-04, A2-REV Q-4) | `RotorSpec.magnet` = `ArcMagnet` or `BlockMagnet` (tagged union, §7.1); `physics.magnets.pole_arc_ratio_block` | designed (`assumption`) |
| Per-layer-pair phase set, rotation and connection (A2-TOP §4.2 M1–M4; EQ-07) | `LayerPair.phases`, `LayerPair.rotation_rad`, `LayerConfig.series_groups` (§7.1) | designed |
| Via plan: centre vias per series pair, transfer vias, multi-via, plating, spans (A2-TOP §4.3; EQ-11) | `ViaSpec` (inputs) + `ViaPlan`/`PlannedVia` (output) (§7.1, §7.3); count formula §7.3 | designed; formula `assumption` for Agent 2 to confirm |
| Coil side style and end style; triangular inner turns; corner radius; width profile (A2-TOP §3.1, EQ-02) | `SpiralCoilSpec.side_style`, `end_style`, `inner_turn_mode`, `corner_radius_mm`, `width_profile` (reserved) | designed |
| Custom stack-up z as the default (A2-REV `stackupFor`) | `Stackup` is always an explicit layer list; `generate_even_stackup()` only produces such a list; `copper_z_mm()` | designed |
| Status label + EQ-ID on every result (A2-EQ intro; coordinator) | `Traceable[T]` on every `AnalysisResult` field; `traced()` pulls EV-IDs/status/tolerance from the registry | designed |
| Halbach option (EQ-05 change) | `Magnetisation.HALBACH` reserved → `UNSUPPORTED_MAGNETISATION` until implemented | reserved |
| B_r temperature dependence (EQ-05 change) | `RotorSpec.remanence_temp_coeff_per_k` (optional) | reserved |
| Configurable harmonic set (A2-REV constants row) | `AnalysisOptions.harmonics` | designed |
| Radial edge correction (EQ-05, D09 p.4–5) | `AnalysisOptions.radial_edge_correction` (reserved) + `RANGE_MAGNET_EDGE` flag now | reserved / flag designed |
| Rename numeric "kw1" → utilisation factor, report textbook k_w separately (A2-REV §1) | `AnalysisResult.utilisation_factor` and `winding_factor_1` | designed |
| Phase and line THD (EQ-18) | `thd_phase`, `thd_line` | designed |
| Convection coefficient with source (EQ-17) | `OperatingPoint.convection_h_w_m2k` + provenance note | designed |
| Material constants with sources (EQ-10, EQ-16; G6) | `MaterialConstant(source_ref, status)` in `MaterialSet` | designed |
| Re-run checks C1–C9 as regression tests with the same tolerances (A2-REV §4 note) | test_plan_draft.md GR-xx / OR-xx / UT-PHY-xx | planned |
| Single-rotor model consistency (field vs inductance vs inertia, A2-REV Q-3) | One `RotorType` drives all models; UT-PHY-14 checks consistency | planned |

## 17. Risks and open architectural items

| # | Item | Impact | Next step | Status |
|---|---|---|---|---|
| R1 | CPython performance of DRC/EMF kernels | REQ-N-01 | P2 spike with vectorised DRC on the default layout; measure PF-01 | unresolved |
| R2 | KiCad 9.x acceptance of the `.kicad_pcb` format version; inner-layer names | REQ-K-01 | KS-01 on the user's machine | unresolved |
| R3 | IPC capabilities on the user's 9.0.x (commit, arcs, stack-up, groups, messages) and kipy version | REQ-K-02…06 | T2, T4 (A5-KI §4) | unresolved |
| R4 | External/child-process IPC connection on Windows | REQ-K-10 | T3 | unresolved |
| R5 | Offline installation of the plugin venv dependencies | REQ-K-07 | T2 with a local wheel directory | unresolved |
| R6 | Status combination order (ADR-0003) needs agreement with Fable/Agent 4 | REQ-T-03 | review | assumption |
| R7 | Spiral generator details (moving inner end-turn, eye/via room, stadium ends) are Agent 2's domain | REQ-F-06 | Agent 2 specification before coding | unresolved |
| R8 | Golden comparison is only meaningful at equation/function level, because the Python spiral generator intentionally differs from Xcoil's sector generator (EQ-02 `replace`) | ADR-0006 | function-level golden harness (test plan §4) | inferred |
| R9 | kiutils (GPL-3.0, last release 1.4.8 on 2024-02-02 per PyPI, `verified`) may not parse KiCad 9 files | KX tests | add an independent minimal s-expression parser in tests; KiCad itself in KS-01 | inferred |
| R10 | Python floor: the sketches use 3.10/3.11 features (`StrEnum`, dataclass `slots`/`kw_only`, `X or Y` union types at runtime). KiCad 9's bundled Python version is `unresolved` (A5-KI T1); if it is older than 3.11 the core cannot be vendored into the plugin venv unchanged | REQ-K-02, K-07 | decide after T1/T2: lower the floor (replace `StrEnum` by `str, Enum`, drop `slots`/`kw_only`) or route the plugin through the user's Python (R3) | unresolved |
| R11 | Phase encoding without colour in a white/grey/black UI | REQ-L-04, N-14 | Agent 1 design + user decision on a muted phase palette | unresolved |

## 18. Reconciliation with Agents 1 and 3 (status at the end of this draft)

Agent 3 explicitly marked its package names as placeholders for Agent 6 (`migration_mapping.md` preamble;
`calculation_flow_and_port_notes.md` §6.1). Mapping to this architecture (coordinator-specified names):

| Agent 3 placeholder | This architecture | Note |
|---|---|---|
| `embodic_core` / `core.params` | `embodic.model` | design inputs, defaults, validation |
| `core.geometry`, `core.topology.spiral` | `embodic.geometry` (+ `generators/spiral.py`) | |
| `core.topology.spiral` (star of slots) | `embodic.winding` | separate package so serpentine/wave can reuse it |
| `core.analysis.*` | `embodic.physics` | |
| `core.drc` | `embodic.drc` | |
| `core.mech` | `embodic.geometry.outline` (+ fasteners) | |
| `core.equations` | `embodic.results.registry` | |
| `embodic_io`, `io.export`, `io.project` | `embodic.io` | |
| `embodic_app`, `app.*` | `embodic.ui` | |
| `embodic_kicad`, `kicad.*` | `embodic_kicad_plugin` | |
| `Board` (geometry model) | `Layout` | renamed to avoid confusion with kipy's `Board` class |
| `CopperObject`, `touch_vias` | `CopperPath` + connectivity in `Circuit`/`ViaPlan` | |
| `board_to_items()` + `apply()` | `board_items.py` (pure mapping) + `apply_project.py` | same two-layer split |
| electrical element list (`phase → series → parallel members`) | `Circuit` → `PhaseCircuit` → `ParallelGroup` → `Member` (§7.4) | same shape as Xcoil `analyzeElements` |

Agreements (no change needed): stdlib + NumPy core; own writers; IPC as plugin route, SWIG not planned, file writer first;
core vendored into the plugin package as preferred option; staged recompute and NumPy kernels; serpentine/wave deferred
behind a generator interface ("D" in `migration_mapping.md` §3); KiCad DRC cannot see same-net clearance → embodic DRC is
the authority; pytest replaces the in-app test runner; reference view generated from the EQ registry.

Adopted from Agent 3 into this draft: entry points `embodic` / `embodic-cli`; rounding, summation and non-finite
conventions (§15.4); measured performance evidence (§11); `KICAD_API_SOCKET`/`KICAD_API_TOKEN` and `kicad-cli` DRC (§9.1);
smoke tests T0/T6 (test plan KS-01/KS-02); a plain-Python reference port as an intermediate golden tier (test plan §3).

Adopted from Agent 1: last-valid-figure, no silent rewrite, export pre-flight, non-colour phase encoding, keyboard-operable
figure, offline fonts (§10; REQ-F-23, F-27, F-28, N-12, N-17).

Open reconciliation items:
1. **Python floor** (R10): Agent 3 suggests keeping the core free of newer syntax until T2; this draft proposes 3.11 —
   decide after T1/T2.
2. **NumPy lower bound**: Agent 3 proposes `numpy>=1.26,<2.5` provisionally; ADR-0008 adopts it until T1/T2.
3. **Import-rule enforcement**: Agent 3 proposes an `ast`-based test (no dependency); this draft proposes import-linter
   contracts (layers + forbidden imports). Either satisfies MT-01; Agent 3 to choose in P2.
4. **Phase colours** (R11): Agents 1 and 3 propose a muted, CVD-checked phase palette with greyscale fallback; needs the
   user's approval (REQ-L-04).
5. **Responsive targets**: Agent 1 analysed phone/tablet layouts; with the desktop proposal (ADR-0005) these are out of
   scope unless the user chooses C-B1.
6. **Agent 1's `design_spec_draft.md`** (referenced in `ux_analysis.md` §6) was not available yet; screen-to-view mapping
   in §10 must be checked against it.
7. **Xcoil v3 parameter import** (Agent 3 N-10) and **autosave** (F-04) are `could`/open in the requirements — confirm
   scope with Fable.
