Prepared by: Agent 6 - Software Architecture Specialist - model: claude-opus-5-5

# embodic Phase 2 interfaces (build contract v1, 2026-10-04)

This file is the binding interface contract for Phase 2. It is written as Python stubs: every `python` block parses with
`ast.parse`, and all blocks run in order as one module (`checks/check_contract.py`). Bodies are `...`. Phase 1 types that
survive unchanged are restated here only where Phase 2 code must match them; the rationale stays in
`docs/phase1/architecture/architecture_draft.md` §7 and §8.

Revision 2026-10-04 (U-D1, corrections from the W0 pilot): §1 replaces `round_half_away_from_zero` with `js_round` and
`quantise` (JS `Math.round` semantics, DEF-M1a-02), adds the U-M1a conversions and `MM_PER_COPPER_OZ`, and splits the
issue catalogue per owning unit. §2.4 adds `default` provenance (D-019). §9.1 states how a blank-origin file stores
it. §9.2 ratifies the U-M1d number encoding and says what the Node dumper emits for GR-19.

Revision 2026-10-05 (U-D2, corrections from the W1 and W2 reports; the merged code on main a138975 was read for every
item): §1 adds the five units of DEF-M2a-01. §2.1 adds `validate_drc_rules`. §2.3 restates `FieldSpec` as merged and
names the constants that are not fields. §5 restates `Layout` with its derived hash, adds `Segment`, `discretise_path`,
`Transform`, the Xcoil distance and grid ports, and fixes the continuity tolerance at 1e-6 mm. §7 rewrites the
exemptions, fixes the clearance rule per check kind, ratifies the pad-to-pad rule and states what `measured_min_mm`
covers. §9.1 decides that the project file stores degrees. §9.2 removes the PCB-tool layer key, names the circuit phase
key and states the interim `write_board_dump` signature. §13 records D-016 and the board dump v2 needs.

## 0. Rules for every public boundary

- Lengths are millimetres (`_mm`), angles radians (`_rad`) inside the core, temperature °C (`_degc`), current A (`_a`),
  voltage V (`_v`), resistance Ω (`_ohm`), field T (`_t`), power W (`_w`), temperature rise K (`_k`). Degrees exist only in
  the project file (`_deg`) and UI widgets.
- Data crossing a module seam is a frozen, slotted, keyword-only dataclass or a `StrEnum`. Closed choices are enums or
  tagged unions, never free strings or flag pairs.
- Functions are pure unless the docstring says otherwise. User input never raises. A failure the user can cause returns a
  value (`Unbuildable`, `DraftIncomplete`, issue tuples). Exceptions mean programming errors.
- Status vocabulary, badge rule and assumed-inputs tag follow D-007 and ADR-0003 unchanged.
- The core (`embodic.*` except `embodic.ui.views`, `embodic.ui.app`, `embodic.ui.workers`) imports no Qt
  (`package_layout.md` §3).

Deltas against the Phase 1 sketch (`architecture_draft.md` §7, §8):

| Area | Phase 1 | Phase 2 contract | Reason |
|---|---|---|---|
| KiCad | `io.kicad_items`, `.kicad_pcb` writer, plugin, `IMPORTED_KICAD` sources, nm conversion | removed | D-009 |
| Generators | `WindingGenerator` protocol with spiral only; serpentine/wave as `dict` placeholders | `generate_spiral/serpentine/wave(DesignParameters) -> Layout or Unbuildable`; full serpentine and wave specs | D-013, ADR-0012 |
| Winding plan | `plan_winding()` stage before geometry for every topology | spiral-only (`plan_spiral_winding`); each generator owns its phase plan and emits the shared `Circuit` | serpentine/wave assign phases per layer or per track, not by star of slots |
| Provenance | `default / user / imported_kicad / migrated / measured`, stored per field | `user / example / default / measured` as a tagged union, derived from the origin (example or blank) and the measurement list | D-014, D-007, D-019 |
| Design entry | app opens on the default design | blank `DesignDraft`; `parse_draft()` returns `DesignParameters` only when every required field is present | D-014 |
| Outline | one class with optional fields per shape | `CircleOutline` or `PolygonOutline` | shape-dependent fields cannot be half set |
| Materials | `MaterialConstant` inputs carrying a free `status` string | registry constants; optional user overrides as `PropertyValue` | constants and their EV status live in the registry |
| EC-05 | `ValidityFlag(metric, one_sided_addon)` | adds `metric_bound`, `calibration_status`, `transfer_status`, `threshold_status` | closes DEF-23 |
| View-models | Qt view-models | Qt-free view-models in `embodic.ui.viewmodels` behind `Observable` | testable without a display |
| Exports | SVG, DXF full/outline/holes, `.kicad_pcb`, JSON/CSV results, PDF | SVG, DXF complete/outline/screws, project JSON, PDF report, README, bundle ZIP | D-009 |

## 1. `embodic.units` and `embodic.errors`

```python
from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from fractions import Fraction
from pathlib import Path
from typing import ClassVar, Generic, Literal, Protocol, TypeAlias, TypeVar

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]


class Unit(StrEnum):
    """Closed unit vocabulary of every Traceable. The value is the canonical code; `display()` gives the UI form."""

    MM = "mm"
    MM2 = "mm2"
    M = "m"
    UM = "um"  # display "µm"; via plating (DEF-M2a-01)
    RAD = "rad"
    T = "T"
    V = "V"
    V_S_PER_RAD = "V_s_per_rad"
    N_M_PER_A = "N_m_per_A"
    RPM_PER_V = "rpm_per_V"
    OHM = "ohm"
    OHM_M = "ohm_m"  # display "Ω·m"; resistivity
    H = "H"
    W = "W"
    W_PER_M2_K = "W_per_m2_K"  # display "W/(m²·K)"; convection coefficient
    A = "A"
    A_PER_MM2 = "A_per_mm2"
    K = "K"
    PER_K = "per_K"  # display "1/K"; temperature coefficient
    DEGC = "degC"
    G = "g"
    G_PER_CM3 = "g_per_cm3"  # display "g/cm³"; density
    N_M = "N_m"
    RPM = "rpm"
    HZ = "Hz"
    ONE = "one"
    COUNT = "count"

    def display(self) -> str: ...


MM_PER_COPPER_OZ: float = 0.0348  # status assumption; Xcoil engine.js l.14 OZ_TO_MM


def deg_to_rad(angle_deg: float) -> float: ...
def rad_to_deg(angle_rad: float) -> float: ...
def mm_to_m(length_mm: float) -> float: ...
def rpm_to_rad_per_s(speed_rpm: float) -> float: ...
def copper_oz_to_mm(copper_oz: float) -> float: ...
def mm2_to_mil2(area_mm2: float) -> float: ...
def mil2_to_mm2(area_mil2: float) -> float: ...
def js_round(value: float) -> float:
    """ECMAScript Math.round: the nearest integer, ties toward +inf (js_round(-2.5) == -2.0). Never returns -0.0."""
def quantise(value: float, scale: float) -> float:
    """Xcoil fmt(): js_round(value * scale) / scale, multiplied by scale, not divided by a step. Never returns -0.0.

    Writers that emit fixed decimals use scale = 1e5 (0.00001 mm). Built-in round() is banned on coordinates (MT-06).
    """


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class IssueCategory(StrEnum):
    INVALID = "invalid"
    MISSING = "missing"  # new-design flow: a required field has no value yet (D-014)
    UNSUPPORTED_RANGE = "unsupported_range"
    UNBUILDABLE = "unbuildable"
    DRC = "drc"
    INTERNAL = "internal"


@dataclass(frozen=True, slots=True, kw_only=True)
class Suggestion:
    """The engine proposes, never applies (REQ-F-23)."""

    pointer: str
    proposed_value: float | int | str
    reason: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidationIssue:
    code: str  # stable UPPER_SNAKE code with category prefix, e.g. "RANGE_SKIN_DEPTH"
    category: IssueCategory
    severity: Severity
    message: str  # English sentence from the message catalogue
    pointers: tuple[str, ...]  # JSON pointers into the design
    value: float | int | str | None = None
    limit: float | int | str | None = None
    hint: str = ""
    eq_ids: tuple[str, ...] = ()
    suggestion: Suggestion | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class Unbuildable:
    """Returned instead of a Layout when valid input cannot produce copper."""

    issues: tuple[ValidationIssue, ...]  # at least one ERROR with category UNBUILDABLE


MESSAGES: Mapping[str, str]  # merged from every module of embodic.errors.catalogue; a duplicate code fails the import


def message_for(code: str) -> str:
    """English message template for an issue code; raises KeyError for an unknown code (programming error)."""
```

Revision 2026-10-04 (U-D1). Four changes to this section.

Rounding (DEF-M1a-02). Phase 1 `architecture_draft.md` §6 U6 says JS `Math.round` rounds half away from zero. It does
not: ECMAScript `Math.round` rounds ties toward +∞. `node -e` printed `3 -2 1 0 -1 0 0` for `Math.round` of 2.5, -2.5,
0.5, -0.5, -1.5, 0.49999999999999994 and -0.49999999999999994 (`verified (run)`, Node v22.22.2, 2026-10-04; Agent 3
measured the same values in Phase 1 `calculation_flow_and_port_notes.md` §2.1). Half away from zero gives -3, -1 and -2
for the three negative ties. Xcoil's `fmt()` (`engine.js` l.2762) is
`(Math.round(v * 1e5) / 1e5).toString()` with `"-0"` replaced by `"0"`. A port with half away from zero would therefore
write a different last digit for every negative coordinate that sits exactly on a half quantum (for example
`fmt(-0.000025)` is `-0.00002` in Xcoil and would be `-0.00003`). Decision: embodic's quantiser uses JS semantics, so
SVG and DXF numbers match Xcoil's exports digit for digit. `round_half_away_from_zero` (U-M1a) is replaced by `js_round`
and `quantise`. The obvious port `math.floor(x + 0.5)` is wrong as well: it returns 1 for 0.49999999999999994, where
`Math.round` returns 0 (`verified (run)`, same session). `js_round` takes `n = floor(x)` and adds 1 when `x - n >= 0.5`.
The subtraction cannot move a value across 0.5 for any finite double (`inferred` from Sterbenz's lemma; UT-UNI-01 tests
the ties). `-0.000025 * 1e5` is exactly -2.5 in both Python and Node (`verified (run)`), so the example above is a true
tie. The Phase 1 file is outside Agent 6's Phase 2 write scope; this section supersedes its U6 sentence.

Number text in writers. The quantised value alone does not give Xcoil's text. JS `Number.prototype.toString` writes
`0.00001` and `0`, while Python `repr` writes `1e-05` and `0.0` (`verified (run)` on the values above). Writers that must
match Xcoil format numbers like JS `toString`; U-M4a owns that formatter (UT-EXP-01, UT-EXP-02).

Copper weight. `MM_PER_COPPER_OZ = 0.0348` stays `assumption`. Xcoil `engine.js` l.14 is
`var OZ_TO_MM = 0.0348; // 1 oz/ft^2 copper = 34.8 um` (`verified` by reading, 2026-10-04). That is a copy of Xcoil's
value, not a standard. Agent 5's evidence register has no IPC-4562 entry, so no standard backs the nominal thickness yet.

Issue catalogue. `MESSAGES` is the merge of one module per owning unit under `embodic.errors.catalogue`
(`work_breakdown.md` §4). Each module exports `MESSAGES: Mapping[str, str]`. `embodic/errors/__init__.py` finds the
modules with `pkgutil.iter_modules`, so a new module needs no edit to a shared file. A code defined twice raises at
import, which fails every test run.

Revision 2026-10-05 (U-D2). DEF-M2a-01: `Unit` had no member for via plating, convection coefficient, resistivity,
temperature coefficient or density, so U-M2a left those fields without a unit. The five members above are the names
U-M1z implements (commit `eb7a2f1` on branch `unit/U-M1z`, read on 2026-10-05, not yet merged). The field table gives
`/vias/plating_um`, `/operating/convection_h_w_m2k` and the material override values these units in the U-M2a fix round
(`work_breakdown.md` §5).

## 2. `embodic.model`: design inputs, draft, provenance

### 2.1 Shared vocabulary and sub-models

```python
class TopologyKind(StrEnum):
    SPIRAL = "spiral"
    SERPENTINE = "serpentine"
    WAVE = "wave"


class Phase(StrEnum):
    A = "A"
    B = "B"
    C = "C"


PhaseCount: TypeAlias = Literal[1, 2, 3]  # spiral accepts 3 only (validator); serpentine and wave keep Xcoil's 1/2/3


class RotorType(StrEnum):
    DOUBLE = "double"
    SINGLE_YOKE = "single_yoke"
    SINGLE_OPEN = "single_open"


@dataclass(frozen=True, slots=True, kw_only=True)
class ArcMagnet:
    kind: Literal["arc"] = "arc"
    pole_arc_ratio: float
    r_inner_mm: float
    r_outer_mm: float
    thickness_mm: float


@dataclass(frozen=True, slots=True, kw_only=True)
class BlockMagnet:
    kind: Literal["block"] = "block"
    width_mm: float
    length_mm: float
    r_center_mm: float
    thickness_mm: float


MagnetGeometry: TypeAlias = ArcMagnet | BlockMagnet


@dataclass(frozen=True, slots=True, kw_only=True)
class RotorSpec:
    poles: int  # 2p, even
    rotor_type: RotorType
    magnet: MagnetGeometry
    remanence_t: float  # property input
    recoil_permeability: float  # property input
    air_gap_mm: float  # per side, magnet face to board surface
    back_iron_thickness_mm: float
    magnet_offset_rad: float = 0.0


@dataclass(frozen=True, slots=True, kw_only=True)
class CopperLayer:
    kind: Literal["copper"] = "copper"
    name: str  # unique, e.g. "L1"
    thickness_mm: float  # property input (finished copper)


@dataclass(frozen=True, slots=True, kw_only=True)
class DielectricLayer:
    kind: Literal["dielectric"] = "dielectric"
    name: str
    thickness_mm: float
    material: str


StackLayer: TypeAlias = CopperLayer | DielectricLayer


@dataclass(frozen=True, slots=True, kw_only=True)
class Stackup:
    layers: tuple[StackLayer, ...]  # top to bottom, always explicit (REQ-F-04)

    def copper_layers(self) -> tuple[CopperLayer, ...]: ...
    def copper_z_mm(self) -> dict[str, float]:
        """Centre z of each copper layer from the top surface; exact cumulative sum (math.fsum)."""
    def board_thickness_mm(self) -> float: ...


def generate_even_stackup(copper_count: int, copper_thickness_mm: float, board_thickness_mm: float,
                          material: str = "FR-4") -> Stackup:
    """Helper only; its output is an ordinary Stackup (GR-07 compares it with Xcoil stackupFor auto mode)."""


class ViaSpan(StrEnum):
    THROUGH = "through"  # Phase 2 builds through vias only (D-015)


@dataclass(frozen=True, slots=True, kw_only=True)
class ViaSpec:
    drill_mm: float
    pad_mm: float
    plating_um: float  # property input (EQ-11)
    vias_per_transition: int = 1


class ConnectionTopology(StrEnum):
    STAR = "star"
    DELTA = "delta"
    OPEN = "open"


@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionSpec:
    topology: ConnectionTopology = ConnectionTopology.STAR  # D-015 default
    draw_interconnect: bool = True
    ring_width_mm: float
    terminal_pad_mm: float
    terminal_drill_mm: float  # 0 = SMD pad
    neutral_pad: bool = False


class ScrewFit(StrEnum):
    CLOSE = "close"
    NORMAL = "normal"
    LOOSE = "loose"


@dataclass(frozen=True, slots=True, kw_only=True)
class ScrewPattern:
    """Clearance holes from a fastener table (REQ-F-24). Table values need a cited source (Agent 3 F-20)."""

    size: str  # e.g. "M3"
    fit: ScrewFit
    count: int
    pitch_radius_mm: float
    angle_offset_rad: float = 0.0


@dataclass(frozen=True, slots=True, kw_only=True)
class CircleOutline:
    shape: Literal["circle"] = "circle"
    radius_mm: float


@dataclass(frozen=True, slots=True, kw_only=True)
class PolygonOutline:
    shape: Literal["polygon"] = "polygon"
    sides: int
    across_flats_mm: float
    corner_radius_mm: float = 0.0
    rotation_rad: float = 0.0


@dataclass(frozen=True, slots=True, kw_only=True)
class OutlineSpec:
    board: CircleOutline | PolygonOutline
    bore: CircleOutline | PolygonOutline | None
    screws: tuple[ScrewPattern, ...] = ()


class Modulation(StrEnum):
    SVPWM = "svpwm"
    SPWM = "spwm"
    SIX_STEP = "six_step"


@dataclass(frozen=True, slots=True, kw_only=True)
class OperatingPoint:
    speed_rpm: float
    line_current_rms_a: float
    winding_temperature_degc: float
    ambient_temperature_degc: float
    convection_h_w_m2k: float  # property input (EQ-17 source disagreement)
    dc_link_v: float | None = None  # None: no torque-speed estimate (EQ-20)
    modulation: Modulation = Modulation.SVPWM


@dataclass(frozen=True, slots=True, kw_only=True)
class PropertyValue:
    """A user override of a registry constant. Without an override the registry constant and its EV status apply."""

    value: float
    unit: Unit


@dataclass(frozen=True, slots=True, kw_only=True)
class MaterialOverrides:
    copper_resistivity_20c_ohm_m: PropertyValue | None = None
    copper_temp_coeff_per_k: PropertyValue | None = None
    copper_density_g_per_cm3: PropertyValue | None = None
    laminate_density_g_per_cm3: PropertyValue | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class AnalysisOptions:
    harmonics: tuple[int, ...] = (1, 3, 5, 7, 9, 11, 13)  # odd only
    max_segment_mm: float = 0.5
    edge_correction: Literal["off"] = "off"  # EC-05 optional correction stays off in Phase 2


@dataclass(frozen=True, slots=True, kw_only=True)
class DrcRules:
    trace_clearance_mm: float
    via_clearance_mm: float
    edge_clearance_mm: float
    hole_clearance_mm: float
    min_trace_width_mm: float
    min_drill_mm: float
    min_annular_ring_mm: float


def validate_drc_rules(rules: DrcRules, pointer: str = "/drc_rules") -> tuple[ValidationIssue, ...]:
    """One INVALID issue per rule that is not a finite number >= 0 (INVALID_DRC_RULE_NOT_FINITE or _NEGATIVE).

    A NaN or negative rule would make every comparison pass, so callers run this before run_drc (U-M1c addition)."""
```

### 2.2 Winding specs, one per topology

The spiral spec keeps the Phase 1 fields (`architecture_draft.md` §7.1, Agent 2 `answers_to_agents.md` §3.2). Serpentine
and wave specs carry exactly the inputs Xcoil's builders read (`/home/claude/serpentine/src/engine.js` l.163-753 for
serpentine, l.1449-2230 for wave; `verified` by reading the parameter references on 2026-10-04), renamed to embodic
conventions. The golden harness maps each field to its Xcoil name (`tools/golden/param_map/<topology>.json`, units U-M3a and U-M3b).

```python
class SideStyle(StrEnum):
    RADIAL = "radial"
    PARALLEL = "parallel"


class EndStyle(StrEnum):
    ARC = "arc"
    STRAIGHT = "straight"
    STADIUM = "stadium"


class InnerTurnMode(StrEnum):
    FIXED = "fixed"
    MOVING = "moving"


class Sense(StrEnum):
    CW = "cw"
    CCW = "ccw"


class LeadStyle(StrEnum):
    RADIAL_THEN_ARC = "radial_then_arc"
    STRAIGHT = "straight"


class PhaseSequence(StrEnum):
    ABC = "abc"
    ACB = "acb"


class PairConnection(StrEnum):
    SERIES = "series"
    PARALLEL = "parallel"


@dataclass(frozen=True, slots=True, kw_only=True)
class LayerPair:
    index: int
    layer_in: str  # copper layer name of X (spiral in)
    layer_out: str  # copper layer name of Y (spiral out, mirrored)
    rotation_rad: float = 0.0  # option M3
    phases: tuple[Phase, ...] | None = None  # None = all phases (FSCW); one phase = option M4


@dataclass(frozen=True, slots=True, kw_only=True)
class LayerConfig:
    pairs: tuple[LayerPair, ...]
    series_groups: tuple[tuple[int, ...], ...]  # inner tuples in parallel, groups in series (EQ-07)


@dataclass(frozen=True, slots=True, kw_only=True)
class CoilAssignmentInput:
    coil_index: int
    phase: Phase
    polarity: Literal[1, -1]


@dataclass(frozen=True, slots=True, kw_only=True)
class SpiralCoilSpec:
    coil_count: int
    r_inner_mm: float  # copper-edge radius
    r_outer_mm: float  # copper-edge radius
    trace_width_mm: float
    clearance_mm: float
    coil_gap_mm: float
    turns: int | None = None  # None = maximum feasible
    side_style: SideStyle = SideStyle.PARALLEL
    end_style: EndStyle = EndStyle.ARC
    inner_turn_mode: InnerTurnMode = InnerTurnMode.MOVING
    corner_radius_mm: float = 0.0
    end_width_outer_mm: float | None = None
    end_width_inner_mm: float | None = None
    first_coil_angle_rad: float = math.pi / 2
    x_inward_sense: Sense = Sense.CW
    lead_style: LeadStyle = LeadStyle.RADIAL_THEN_ARC
    terminal_offset_mm: float | None = None
    min_side_length_mm: float | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class SpiralWindingSpec:
    kind: Literal["spiral"] = "spiral"
    coil: SpiralCoilSpec
    layers: LayerConfig
    assignment: tuple[CoilAssignmentInput, ...] | None = None  # None = star of slots
    phase_sequence: PhaseSequence = PhaseSequence.ABC
    parallel_paths: int = 1


class CornerStyle(StrEnum):
    ROUND = "round"
    SHARP = "sharp"


class TerminalSide(StrEnum):
    OUTER = "outer"
    INNER = "inner"


class LayerOrder(StrEnum):
    GROUPED = "grouped"
    INTERLEAVED = "interleaved"


@dataclass(frozen=True, slots=True, kw_only=True)
class SerpentineWindingSpec:
    """Xcoil 'serpentine': one phase per layer group. Xcoil's stackMode 'perPhase' (one board per phase) is not ported:
    a Layout is one board (open question Q-3 in requirements.md)."""

    kind: Literal["serpentine"] = "serpentine"
    r_inner_mm: float  # Xcoil rIn
    r_outer_mm: float  # Xcoil rOut
    turns: int  # Xcoil turns (traces per pole)
    strands: int = 1  # Xcoil strands
    trace_width_mm: float  # Xcoil traceWidth
    clearance_mm: float  # Xcoil clearance
    end_width_outer_mm: float | None = None  # Xcoil endWidthOuter (0 there = None here)
    end_width_inner_mm: float | None = None  # Xcoil endWidthInner
    side_style: SideStyle = SideStyle.PARALLEL  # Xcoil style
    corner_style: CornerStyle = CornerStyle.ROUND  # Xcoil cornerStyle
    fillet_radius_mm: float = 0.4  # Xcoil filletRadius
    fillet_max: bool = False  # Xcoil filletMax
    terminal_side: TerminalSide = TerminalSide.OUTER  # Xcoil terminalSide
    start_angle_rad: float = 0.0  # Xcoil startAngleDeg
    layers_per_phase: int  # Xcoil layersPerPhase: 1 or even
    pair_connection: PairConnection = PairConnection.SERIES  # Xcoil pairConnection
    layer_order: LayerOrder = LayerOrder.GROUPED  # Xcoil layerOrder


class WaveStyle(StrEnum):
    INVOLUTE = "involute"
    JOG = "jog"
    CHORD = "chord"
    OVERLAP = "overlap"


@dataclass(frozen=True, slots=True, kw_only=True)
class WaveWindingSpec:
    """Xcoil 'wave': all phases on every layer, via-stitched T/B track pairs."""

    kind: Literal["wave"] = "wave"
    r_inner_mm: float
    r_outer_mm: float
    turns: int  # Xcoil turns (tracks per phase and pole pair)
    trace_width_mm: float
    clearance_mm: float
    end_width_outer_mm: float | None = None
    end_width_inner_mm: float | None = None
    corner_style: CornerStyle = CornerStyle.ROUND
    fillet_radius_mm: float = 0.4
    wave_style: WaveStyle = WaveStyle.INVOLUTE  # Xcoil waveStyle
    bus_width_mm: float  # Xcoil busWidth


WindingSpec: TypeAlias = SpiralWindingSpec | SerpentineWindingSpec | WaveWindingSpec


@dataclass(frozen=True, slots=True, kw_only=True)
class DesignParameters:
    """A complete design. Only parse_draft() and load_project() construct it from user data."""

    schema_version: Literal[1] = 1
    name: str
    phases: PhaseCount
    rotor: RotorSpec
    winding: WindingSpec
    stackup: Stackup
    vias: ViaSpec
    connection: ConnectionSpec
    outline: OutlineSpec
    operating: OperatingPoint
    materials: MaterialOverrides = MaterialOverrides()
    analysis: AnalysisOptions = AnalysisOptions()
    drc_rules: DrcRules

    @property
    def topology(self) -> TopologyKind: ...


def validate_design(design: DesignParameters) -> tuple[ValidationIssue, ...]:
    """Single-field ranges and cross-field relations (INVALID, UNSUPPORTED_RANGE). Winding and geometry feasibility are
    the generators' job (UNBUILDABLE)."""
```

### 2.3 Field table, draft and the new-design flow (ADR-0010)

One table drives required-field checks, form generation, units shown next to inputs, applicability (REQ-F-32) and the
field kind that decides whether an input can be marked measured.

```python
class FieldKind(StrEnum):
    DESIGN = "design"  # geometry, layer configuration, operating point
    PROPERTY = "property"  # B_r, mu_r, finished copper thickness, plating, h, material overrides


JsonValue: TypeAlias = "None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]"
Choice: TypeAlias = str | int


class ValueType(StrEnum):  # embodic.model.schema; GROUP and LIST leaves exist while their container is None or []
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    TEXT = "text"
    CHOICE = "choice"
    INT_LIST = "int_list"
    INT_GROUPS = "int_groups"
    CHOICE_LIST = "choice_list"
    GROUP = "group"
    LIST = "list"


class FieldGroup(StrEnum):  # form group, in form order (screens.md sections 1 to 5)
    DESIGN = "design"
    COIL = "coil"
    PHASES = "phases"
    LAYERS = "layers"
    OUTLINE = "outline"
    FASTENERS = "fasteners"
    STACKUP = "stackup"
    ROTOR = "rotor"
    OPERATING = "operating"
    DRIVE = "drive"
    COOLING = "cooling"
    MATERIALS = "materials"
    ANALYSIS = "analysis"
    MANUFACTURING = "manufacturing"


class Sign(StrEnum):  # physical validity; breaking it is INVALID
    ANY = "any"
    POSITIVE = "positive"
    NON_NEGATIVE = "non_negative"


@dataclass(frozen=True, slots=True, kw_only=True)
class Limits:
    """`sign` is validity (INVALID); `low` to `high` is the supported range (UNSUPPORTED_RANGE, Xcoil clamps to it)."""

    sign: Sign = Sign.ANY
    low: float | None = None
    high: float | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class FieldSpec:
    pointer: str  # JSON pointer into the "design" object, list items as "/stackup/layers/*/thickness_mm"
    kind: FieldKind
    unit: Unit | None  # None for enums, names and booleans
    required: bool  # required while its container exists; a blank draft leaves it empty
    topologies: frozenset[TopologyKind]  # where the field applies
    neutral_value: JsonValue = None  # optional fields only; written into a blank design (ADR-0010 decision 2)
    value_type: ValueType
    choices: tuple[Choice, ...] = ()
    nullable: bool = False
    variant: Choice | None = None  # tagged-union member owning the field ("circle", "arc", ...); None if all have it
    group: FieldGroup
    widget_id: str | None  # objectName in screens.md; the join key between form and model
    limits: Limits = Limits()
    step: float | None = None  # Up and Down increment in the form


FIELDS: tuple[FieldSpec, ...]  # every field of every topology; built at import from the type hints plus one row each


def field_specs(topology: TopologyKind) -> tuple[FieldSpec, ...]: ...
def field_for(pointer: str, values: Mapping[str, JsonValue]) -> FieldSpec:
    """The field of a concrete pointer; the sibling `kind` or `shape` value in `values` picks the union member."""


@dataclass(frozen=True, slots=True, kw_only=True)
class DesignDraft:
    """What the form edits. Values may be missing; nothing is computed from a draft (D-014)."""

    topology: TopologyKind
    values: Mapping[str, JsonValue]  # pointer -> value; absent pointer = missing


@dataclass(frozen=True, slots=True, kw_only=True)
class DraftIncomplete:
    missing: tuple[str, ...]  # pointers of required fields without a value, in form order
    issues: tuple[ValidationIssue, ...]  # INVALID issues of the fields that do have values


def blank_draft(topology: TopologyKind) -> DesignDraft:
    """Required fields absent; optional fields at their neutral value."""


def parse_draft(draft: DesignDraft) -> DesignParameters | DraftIncomplete: ...


def draft_from_design(design: DesignParameters) -> DesignDraft: ...
```

Revision 2026-10-05 (U-D2, U-M2a report). The names `field_specs`, `parse_draft` and `validate_design` stay as written.
U-M2a's additions are ratified and restated above.

- `FieldSpec` gains `value_type`, `choices`, `nullable`, `variant`, `group`, `widget_id`, `limits` and `step`. The
  type hints decide `required`, `neutral_value`, `value_type`, `choices` and `topologies`; one row per field adds the
  rest (`src/embodic/model/fields.py` `_ROWS`). The import fails when a leaf has no row or a row has no leaf, so the
  table cannot drift from the dataclasses.
- `widget_id` is the only join between a form widget and a field. The UI binds through it, never through the binding
  keys written in screens.md (`screen_model_reconciliation.md`).
- `embodic.model.schema` is a new module: one walk over the dataclass annotations gives the leaves, JSON conversion
  (`to_json`, `from_json`, `design_from_json`) and pointer helpers (`flatten`, `unflatten`, `field_key`, `pattern_of`).
- A field of one tagged-union member is keyed `<pointer>#<tag>` (for example `/outline/board/radius_mm#circle`).

Constants are not fields. `/schema_version` (`Literal[1]`), `/winding/kind` (the topology tag) and
`/analysis/edge_correction` (`Literal["off"]`) are one-value literals. They appear in the project file and in
`design_hash`, but not in `FIELDS`, a draft or the provenance map. `DesignDraft.topology` sets `/winding/kind`.

### 2.4 Provenance (D-007, D-014, D-019)

Provenance is derived, not typed by hand. A design has one origin: an example, or a blank design. The first matching
rule gives a field's provenance.

1. `measured` for a property field the user marked with a named source.
2. `example` while the value equals the value in the origin example.
3. `default` while the design has a blank origin and the value equals the field's `FieldSpec.neutral_value` (the
   documented default of an optional field, D-019). Required fields have no neutral value, so they never get `default`.
4. `user` otherwise.

Re-entering the current value changes nothing. Setting a changed field back to the origin's value makes it `example` or
`default` again (value-based, keystroke independent, consistent with Phase 1 PR-12 and DEF-21).

Revision 2026-10-04 (U-D1): `DEFAULT` and `DefaultValue` added and rule 3 written, per D-019 (provenance values `user`,
`example`, `default`, `measured`). `EXAMPLE` was already present. D-019's "`InputSource` gains `example`" is met by
`InputRef.provenance` (§3), which uses this enum.

```python
class Provenance(StrEnum):
    USER = "user"
    EXAMPLE = "example"
    DEFAULT = "default"
    MEASURED = "measured"


@dataclass(frozen=True, slots=True, kw_only=True)
class UserValue:
    provenance: Literal[Provenance.USER] = Provenance.USER


@dataclass(frozen=True, slots=True, kw_only=True)
class ExampleValue:
    provenance: Literal[Provenance.EXAMPLE] = Provenance.EXAMPLE
    example_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class DefaultValue:
    provenance: Literal[Provenance.DEFAULT] = Provenance.DEFAULT


@dataclass(frozen=True, slots=True, kw_only=True)
class MeasuredValue:
    provenance: Literal[Provenance.MEASURED] = Provenance.MEASURED
    source: str  # datasheet, coupon or LCR record; never empty (mark_measured refuses an empty source)


FieldProvenance: TypeAlias = UserValue | ExampleValue | DefaultValue | MeasuredValue
ProvenanceMap: TypeAlias = Mapping[str, FieldProvenance]  # concrete pointers ("/stackup/layers/0/thickness_mm")


@dataclass(frozen=True, slots=True, kw_only=True)
class ExampleRef:
    example_id: str  # file stem in resources/examples
    example_sha256: str  # of the example's canonical design JSON


@dataclass(frozen=True, slots=True, kw_only=True)
class Measurement:
    pointer: str
    source: str


def derive_provenance(design: DesignParameters, origin: tuple[ExampleRef, DesignParameters] | None,
                      measurements: Sequence[Measurement]) -> dict[str, FieldProvenance]:
    """origin None means a blank design: rule 3 compares with field_specs(design.topology) neutral values."""


def mark_measured(design: DesignParameters, measurements: Sequence[Measurement], pointer: str,
                  source: str) -> tuple[Measurement, ...] | ValidationIssue:
    """Refuses (INVALID_MEASURED_SOURCE_EMPTY, INVALID_MEASURED_DESIGN_FIELD) instead of raising."""


def drop_stale_measurements(old: DesignParameters, new: DesignParameters,
                            measurements: Sequence[Measurement]) -> tuple[Measurement, ...]:
    """A measurement no longer applies once its field's value changes."""
```

## 3. `embodic.results`: Traceable, registry, analysis result

`Status`, the weakest-link order, `Assumption`, `AssumedInput`, `Tolerance` and `Traceable` keep their Phase 1 meaning.
`InputRef.provenance` now uses `Provenance`. `ValidityFlag` gains the DEF-23 fields.

```python
T = TypeVar("T")


class Status(StrEnum):
    VERIFIED = "verified"
    INFERRED = "inferred"
    ASSUMPTION = "assumption"
    UNRESOLVED = "unresolved"
    NOT_TESTED = "not tested"


STATUS_ORDER_WEAKEST_FIRST: tuple[Status, ...] = (
    Status.UNRESOLVED, Status.NOT_TESTED, Status.ASSUMPTION, Status.INFERRED, Status.VERIFIED,
)


class GateVerdict(StrEnum):
    REUSE = "reuse"
    REUSE_WITH_CHANGE = "reuse with change"
    REPLACE = "replace"
    ADD = "add"
    CANNOT_VERIFY_YET = "cannot verify yet"


@dataclass(frozen=True, slots=True, kw_only=True)
class Assumption:
    id: str
    text: str
    status: Status
    source_ref: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class InputRef:
    pointer: str  # JSON pointer or "result:<quantity>" or "constant:<name>"
    value: float | int | str
    unit: Unit | None
    provenance: Provenance | None  # None for result references and registry constants
    kind: FieldKind | None
    label: Status | None  # ASSUMPTION for unmeasured property inputs; constant's EV status for registry constants


@dataclass(frozen=True, slots=True, kw_only=True)
class AssumedInput:
    item: str
    value_text: str
    reason: Literal["example", "unmeasured_property", "registry_constant", "equation_assumption"]
    label: Status
    dominant: bool


class ValidityEffect(StrEnum):
    CAP = "cap"  # badge capped at unresolved
    LIMITATION = "limitation"  # badge unchanged; limitation listed, optional one-sided tolerance add-on


class MetricBound(StrEnum):
    ESTIMATE = "estimate"
    LOWER_BOUND = "lower_bound"  # true value is at least the metric (EC-05: |B| proxy for B_z, DEF-23 a)
    UPPER_BOUND = "upper_bound"


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidityFlag:
    code: str  # "RANGE_SKIN_DEPTH", "EC-05"
    message: str
    eq_id: str
    effect: ValidityEffect
    metric: float | None = None
    metric_bound: MetricBound = MetricBound.ESTIMATE
    one_sided_addon: float | None = None
    calibration_status: Status | None = None  # EC-05: inferred (one D09 case)
    transfer_status: Status | None = None  # EC-05: assumption (calibration applied to this rotor)
    threshold_status: Status | None = None  # EC-05: assumption (10 % cap)


@dataclass(frozen=True, slots=True, kw_only=True)
class Tolerance:
    relative: float | None
    absolute: float | None
    against: str
    source_ref: str


@dataclass(frozen=True, slots=True, kw_only=True)
class Traceable(Generic[T]):
    quantity: str
    value: T
    unit: Unit
    eq_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    kind_tag: Literal["computed", "input", "derived", "count"] = "computed"
    assumptions: tuple[Assumption, ...] = ()
    inputs: tuple[InputRef, ...] = ()
    assumed_inputs: tuple[AssumedInput, ...] = ()
    validity: tuple[ValidityFlag, ...] = ()
    tolerance: Tolerance | None = None
    status: Status
    status_reasons: tuple[str, ...] = ()
    label: str | None = None  # "estimate" / "guideline (unverified)"


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidityCheckSpec:
    """Registry `validity_checks` entry (Agent 2 owns the content). DEF-23 adds the four status/bound fields."""

    id: str
    name: str
    metric: str
    parameters: Mapping[str, float | str]
    basis: str
    rule: str
    threshold: float
    metric_bound: MetricBound
    calibration_status: Status
    transfer_status: Status
    threshold_status: Status
    independent_oracles: tuple[str, ...]  # e.g. ("OR-01",)
    dependent_oracles: tuple[str, ...]  # share the calibration source, e.g. ("OR-07", "OR-08")


@dataclass(frozen=True, slots=True, kw_only=True)
class RegistryConstant:
    name: str
    value: float
    unit: Unit
    source: str | None  # EV-ID
    status: Status


@dataclass(frozen=True, slots=True, kw_only=True)
class EquationEntry:
    id: str
    name: str
    formula: str
    gate: GateVerdict
    status: Status  # evidence status of the equation
    sources: tuple[str, ...]
    tolerance: Tolerance | None
    dominant_assumptions: tuple[str, ...]
    validity_checks: tuple[ValidityCheckSpec, ...]
    tests: tuple[str, ...]
    implementation: str | None
    constants: tuple[RegistryConstant, ...]
    label: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class EvidenceEntry:
    id: str
    claim: str
    document: str
    location: str
    status: Status


@dataclass(frozen=True, slots=True, kw_only=True)
class Registry:
    version: str
    equations: Mapping[str, EquationEntry]
    evidence: Mapping[str, EvidenceEntry]
    passed_tests: frozenset[str]  # test IDs that passed in this build (tests/results.json); empty in a fresh install

    def equation(self, eq_id: str) -> EquationEntry: ...
    def constant(self, name: str) -> RegistryConstant: ...
    def test_state(self, eq_id: str) -> Status:
        """NOT_TESTED until every linked test passed in this build, else the equation status."""


def load_registry(root: Path | None = None) -> Registry:
    """Reads resources/evidence/equations.v1.json and evidence.v1.json (packaged copies, tools/sync_registry.py)."""


def combine_status(*statuses: Status) -> Status: ...


def traced(quantity: str, value: T, unit: Unit, *, eq_ids: Sequence[str], inputs: Sequence[InputRef],
           registry: Registry, validity: Sequence[ValidityFlag] = (), kind_tag: Literal["computed", "input", "derived",
           "count"] = "computed") -> Traceable[T]:
    """Badge = weakest(equation status, test state, validity cap). Inputs build the tag only (D-007)."""


def format_value(t: Traceable[float], *, significant: int = 3) -> str:
    """Locale-independent, SI prefixes, U+2212 minus, space before the unit (REQ-L-07)."""
```

Result containers. Phase 1 `AnalysisResult` fields are kept; topology-specific geometry values move to the generator's
detail record (§6).

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class LayerResult:
    layer: str
    z_mm: Traceable[float]
    b1_peak_mid_radius_t: Traceable[float]


@dataclass(frozen=True, slots=True, kw_only=True)
class PhaseResult:
    phase: Phase
    ke_peak_v_s_per_rad: Traceable[float]
    resistance_20c_ohm: Traceable[float]
    resistance_operating_ohm: Traceable[float]
    circulating_loss_w: Traceable[float]


@dataclass(frozen=True, slots=True, kw_only=True)
class TorqueSpeedEstimate:
    speed_rpm: Traceable[tuple[float, ...]]
    torque_n_m: Traceable[tuple[float, ...]]
    power_w: Traceable[tuple[float, ...]]
    no_load_speed_rpm: Traceable[float]
    base_speed_rpm: Traceable[float]


@dataclass(frozen=True, slots=True, kw_only=True)
class AnalysisResult:
    ke_phase_v_s_per_rad: Traceable[float]  # EQ-06, EQ-09
    ke_line_v_s_per_rad: Traceable[float]  # EQ-09
    kt_n_m_per_a: Traceable[float]  # EQ-09
    kv_rpm_per_v: Traceable[float]  # EQ-09
    winding_factor_1: Traceable[float]  # EQ-08 (spiral); kind_tag "derived" from the generator for serpentine/wave
    resistance_phase_20c_ohm: Traceable[float]  # EQ-10, EQ-11
    resistance_phase_operating_ohm: Traceable[float]
    resistance_line_ohm: Traceable[float]
    emf_phase_rms_v: Traceable[float]
    torque_n_m: Traceable[float]
    loss_copper_w: Traceable[float]
    loss_eddy_w: Traceable[float]  # EQ-12
    loss_circulating_w: Traceable[float]  # EQ-07
    loss_delta_circulating_w: Traceable[float]  # EQ-19
    thd_phase: Traceable[float]  # EQ-18
    thd_line: Traceable[float]
    current_density_a_per_mm2: Traceable[float]  # EQ-22
    skin_depth_mm: Traceable[float]  # EQ-13
    inductance_estimate_h: Traceable[float]  # EQ-14, badge unresolved, label "estimate"
    ipc_guideline_current_a: Traceable[float]  # EQ-15, badge unresolved, label "guideline (unverified)"
    mass_copper_g: Traceable[float]  # EQ-16
    mass_laminate_g: Traceable[float]
    temperature_rise_k: Traceable[float]  # EQ-17
    edge_leakage_fraction: Traceable[float]  # EC-05 metric e_edge; status assumption (transfer, DEF-23)
    layers: tuple[LayerResult, ...]
    phases: tuple[PhaseResult, ...]
    emf_waveform_v: Traceable[tuple[float, ...]]  # EQ-18, one electrical period
    torque_speed: TorqueSpeedEstimate | None  # EQ-20; None without dc_link_v
    registry_version: str
```

## 4. `embodic.winding`: spiral phase plan

Used by the spiral generator only. Exact integer arithmetic (EQ-08 `replace`).

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class Feasibility:
    coils: int
    poles: int
    phases: int
    q: Fraction
    periodicity: int  # t = gcd(Q, p)
    balanced: bool
    max_parallel_paths: int


@dataclass(frozen=True, slots=True, kw_only=True)
class CoilAssignment:
    coil_index: int
    phasor_index: int
    phase: Phase
    polarity: Literal[1, -1]


@dataclass(frozen=True, slots=True, kw_only=True)
class SpiralWindingPlan:
    feasibility: Feasibility
    assignment: tuple[CoilAssignment, ...]
    pattern: str  # "AabBCcaABbcC", upper = +, lower = -
    winding_factors: Mapping[int, Traceable[float]]  # harmonic order -> k_w,n


def check_feasibility(coil_count: int, poles: int, phases: int = 3, *, phase_per_pair: bool = False) -> Feasibility: ...
def balanced_coil_counts(poles: int, phases: int = 3, max_coils: int = 96) -> tuple[int, ...]: ...
def assign_phases(coil_count: int, poles: int, phases: int = 3,
                  sequence: PhaseSequence = PhaseSequence.ABC) -> tuple[CoilAssignment, ...]: ...
def compute_winding_factors(assignment: Sequence[CoilAssignment], poles: int, coil_count: int,
                            spans_rad: Sequence[float], harmonics: Sequence[int],
                            registry: Registry) -> dict[int, Traceable[float]]: ...
def plan_spiral_winding(design: DesignParameters, spec: SpiralWindingSpec,
                        registry: Registry) -> SpiralWindingPlan | Unbuildable: ...
```

## 5. `embodic.geometry`: primitives, electrical element list, Layout

`Layout` is the one shape every generator produces and every consumer (DRC, physics, exporters, UI, board dump) reads.
No consumer imports a generator: the layer order of contract C1 (`package_layout.md` §3) puts `embodic.generators`
above `io`, `outcome`, `physics` and `drc`. The generator-specific records live in `embodic.geometry.details`, so
`Layout.detail` is typed without an upward import.

```python
from dataclasses import field


class PrimitiveRole(StrEnum):
    SIDE = "side"
    END_TURN = "end_turn"
    LEAD = "lead"
    FILLET = "fillet"
    TAPER = "taper"
    LEG = "leg"
    RING = "ring"
    STUB = "stub"
    BUS = "bus"
    LINK = "link"
    OUTLINE = "outline"


@dataclass(frozen=True, slots=True, kw_only=True)
class Line:
    x1_mm: float
    y1_mm: float
    x2_mm: float
    y2_mm: float
    width_mm: float  # 0 for outline geometry
    role: PrimitiveRole

    def start_point(self) -> tuple[float, float]: ...
    def end_point(self) -> tuple[float, float]: ...


@dataclass(frozen=True, slots=True, kw_only=True)
class Arc:
    cx_mm: float
    cy_mm: float
    r_mm: float
    start_rad: float
    sweep_rad: float  # signed, positive = counter-clockwise, y up
    width_mm: float
    role: PrimitiveRole

    def start_point(self) -> tuple[float, float]: ...
    def mid_point(self) -> tuple[float, float]: ...
    def end_point(self) -> tuple[float, float]: ...


Primitive: TypeAlias = Line | Arc


@dataclass(frozen=True, slots=True, kw_only=True)
class CopperPath:
    """Continuous chain on one copper layer, ordered in current direction."""

    id: int
    layer: str
    net: str
    primitives: tuple[Primitive, ...]
    phase: Phase | None  # None for neutral and interconnect copper
    element: int | None  # coil index (spiral), track or strand index (serpentine, wave)
    polarity: Literal[1, -1, 0]


class ViaRole(StrEnum):
    CENTRE = "centre"
    TRANSFER = "transfer"
    TERMINAL = "terminal"
    RING = "ring"
    STITCH = "stitch"


@dataclass(frozen=True, slots=True, kw_only=True)
class Via:
    id: int
    x_mm: float
    y_mm: float
    drill_mm: float
    pad_mm: float
    role: ViaRole
    span: ViaSpan
    layer_from: str
    layer_to: str
    net: str


@dataclass(frozen=True, slots=True, kw_only=True)
class Pad:
    id: int
    x_mm: float
    y_mm: float
    shape: Literal["round", "square", "oblong", "rect"]
    width_mm: float
    height_mm: float
    rotation_rad: float
    drill_mm: float  # 0 = SMD
    layer: str | None  # SMD layer; None = all copper layers
    net: str
    label: str  # "U", "V", "W", "N"


@dataclass(frozen=True, slots=True, kw_only=True)
class Hole:
    x_mm: float
    y_mm: float
    diameter_mm: float
    label: str  # e.g. "M3 normal"


@dataclass(frozen=True, slots=True, kw_only=True)
class BoardOutline:
    outer: tuple[Primitive, ...]  # closed loop, width 0
    cutouts: tuple[tuple[Primitive, ...], ...]  # bore and other closed loops
    holes: tuple[Hole, ...]  # screw clearance holes (DXF "screws")


@dataclass(frozen=True, slots=True, kw_only=True)
class Member:
    """One conductive route between two group nodes, in current direction (electrical element list)."""

    path_ids: tuple[int, ...]
    via_ids: tuple[int, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class ParallelGroup:
    members: tuple[Member, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class PhaseCircuit:
    phase: Phase
    groups: tuple[ParallelGroup, ...]  # in series
    terminal_net: str


@dataclass(frozen=True, slots=True, kw_only=True)
class Circuit:
    phases: tuple[PhaseCircuit, ...]
    topology: ConnectionTopology
    interconnect_path_ids: tuple[int, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class RotationalSymmetry:
    """Lets DRC check one period plus neighbours (PR-02 proves equality with the full check)."""

    order: int  # copper of `periodic_path_ids` repeats every 2*pi/order
    periodic_path_ids: tuple[int, ...]
    canonical_path_ids: tuple[int, ...]  # one period, the reference set


@dataclass(frozen=True, slots=True, kw_only=True)
class LayoutArrays:
    """Per-layer NumPy view for DRC and physics. Rows map back through path_index and prim_index."""

    lines: Mapping[str, FloatArray]  # (N, 5): x1, y1, x2, y2, width
    arcs: Mapping[str, FloatArray]  # (M, 6): cx, cy, r, start, sweep, width
    path_index: Mapping[str, NDArray[np.int64]]
    prim_index: Mapping[str, NDArray[np.int64]]
    vias: FloatArray  # (K, 4): x, y, pad, drill


# embodic.geometry.details: generator-specific records carried by Layout.detail


class TurnLimitReason(StrEnum):
    RADIAL = "radial"
    LATERAL = "lateral"
    EYE = "eye"
    USER = "user"


@dataclass(frozen=True, slots=True, kw_only=True)
class TurnLimit:
    radial_bound: float
    loops_trapezoidal: int
    loops_triangular: int
    eye_limit: int | None
    limiting_reason: TurnLimitReason


@dataclass(frozen=True, slots=True, kw_only=True)
class SpiralDetail:
    kind: Literal["spiral"] = "spiral"
    plan: SpiralWindingPlan
    turns_achieved: int
    turn_limit: TurnLimit
    track_length_per_coil_layer_mm: Mapping[str, float]  # "X", "Y"


@dataclass(frozen=True, slots=True, kw_only=True)
class SerpentineDetail:
    kind: Literal["serpentine"] = "serpentine"
    max_turns_that_fit: int  # Xcoil F-10
    layer_phase: Mapping[str, Phase]  # one phase per copper layer
    canonical_frame_rad: float


@dataclass(frozen=True, slots=True, kw_only=True)
class WaveDetail:
    kind: Literal["wave"] = "wave"
    tracks_per_layer: int
    stitch_vias_per_stack: int


TopologyDetail: TypeAlias = SpiralDetail | SerpentineDetail | WaveDetail


@dataclass(frozen=True, slots=True, kw_only=True)
class Layout:
    topology: TopologyKind
    copper_layers: tuple[str, ...]
    copper_z_mm: Mapping[str, float]
    paths: tuple[CopperPath, ...]
    vias: tuple[Via, ...]
    pads: tuple[Pad, ...]
    outline: BoardOutline
    circuit: Circuit
    symmetry: RotationalSymmetry | None
    detail: TopologyDetail  # generator-specific record; consumers other than the UI ignore it
    derived: tuple[Traceable[float], ...]  # feasibility-rail values shared by all topologies (track length, turns, ...)
    envelope_mm: tuple[float, float]  # r_min_cu, r_max_cu
    layout_hash: str = field(init=False)  # "sha256:<hex>"; never passed in

    def __post_init__(self) -> None:
        """Sets layout_hash = compute_layout_hash(paths, vias, pads, outline), so no Layout carries a foreign hash."""

    def arrays(self) -> LayoutArrays: ...


COINCIDENCE_MM: float = 1e-6  # embodic.geometry.paths; the one continuity tolerance (REQ-N-21, UT-GEO-01, IT-21)


def joint_gaps_mm(prims: Sequence[Primitive]) -> tuple[float, ...]: ...
def is_continuous(prims: Sequence[Primitive], tolerance_mm: float = COINCIDENCE_MM) -> bool: ...
def hypot_mm(dx: float, dy: float) -> float:
    """Xcoil's own hypot, sqrt(dx*dx + dy*dy) (engine.js l.77). Faithful ports use it, not math.hypot."""
def primitive_length_mm(p: Primitive) -> float: ...
def path_length_mm(prims: Sequence[Primitive]) -> float:
    """Xcoil primsLength: a left-to-right sum, so the last bit matches Xcoil."""


@dataclass(frozen=True, slots=True, kw_only=True)
class Segment:
    """One chord of a discretised chain (Xcoil keys x1, y1, x2, y2, s, len, w, kind, pi)."""

    x1_mm: float
    y1_mm: float
    x2_mm: float
    y2_mm: float
    s_mm: float  # path position of the chord midpoint
    length_mm: float  # primitive length / piece count, not the chord length
    width_mm: float
    role: PrimitiveRole
    prim_index: int


def discretise_path(prims: Sequence[Primitive], max_segment_mm: float = 0.5,
                    max_angle_rad: float = 5 * math.pi / 180, max_sagitta_mm: float = 0.001) -> tuple[Segment, ...]:
    """Chords of a chain with their path positions; port of Xcoil discretize with its three limits (GR-17)."""
def discretise(p: Primitive, max_segment_mm: float, max_angle_rad: float = 5 * math.pi / 180,
               max_sagitta_mm: float = 0.001) -> FloatArray:
    """Polyline points (K, 2) of one primitive: the chord end points of discretise_path."""


@dataclass(frozen=True, slots=True, kw_only=True)
class Transform:
    """Mirror about the line through the origin at mirror_axis_rad (when set), then rotate (Xcoil tf and thetaG)."""

    rotation_rad: float = 0.0
    mirror_axis_rad: float | None = None


def transform(prims: Sequence[Primitive], tf: Transform) -> tuple[Primitive, ...]:
    """Xcoil tfPrim on every primitive, in polar form as Xcoil computes it."""
def reverse_path(prims: Sequence[Primitive]) -> tuple[Primitive, ...]: ...
def rotate(prims: Sequence[Primitive], angle_rad: float) -> tuple[Primitive, ...]: ...
def mirror(prims: Sequence[Primitive], axis_angle_rad: float) -> tuple[Primitive, ...]: ...
def build_outline(spec: OutlineSpec, envelope_mm: tuple[float, float]) -> BoardOutline: ...
def compute_layout_hash(paths: Sequence[CopperPath], vias: Sequence[Via], pads: Sequence[Pad],
                        outline: BoardOutline) -> str: ...


# embodic.geometry.distance and embodic.geometry.grid: Xcoil ptSegDist, segSegDist, makeGrid, gridQuery (l.563-596)
class Chord(Protocol):
    x1_mm: float
    y1_mm: float
    x2_mm: float
    y2_mm: float


@dataclass(frozen=True, slots=True, kw_only=True)
class ChordGrid:
    cell_mm: float
    cells: Mapping[tuple[int, int], tuple[int, ...]]  # chords binned by midpoint, in Xcoil's first-use order


def point_segment_distance_mm(px_mm: float, py_mm: float, s: Chord) -> float: ...
def segment_segment_distance_mm(a: Chord, b: Chord) -> float: ...
def make_grid(chords: Sequence[Chord], cell_mm: float) -> ChordGrid: ...
def grid_query(grid: ChordGrid, x_mm: float, y_mm: float, radius_mm: float) -> tuple[int, ...]: ...
```

Revision 2026-10-05 (U-D2, U-M1b and U-V1 reports).

- `Layout` computes `layout_hash` in `__post_init__` from its own copper (`src/embodic/geometry/layout.py`). A caller
  cannot pass a hash, so a Layout cannot carry the hash of other copper. `derived` and `detail` arrive with U-M2d, as
  planned.
- `Segment`, `discretise_path`, `Transform`, `transform`, `hypot_mm` and `path_length_mm` are U-M1b additions. Physics
  (U-M2e) integrates over `discretise_path` chords, and the serpentine and wave ports (U-M3a, U-M3b) need `Transform`
  and `hypot_mm` to reproduce Xcoil bit for bit.
- The Xcoil distance and grid ports live in `embodic.geometry.distance` and `embodic.geometry.grid`, not in `drc`.
  The DRC uses its own exact kernels (§7) and imports neither. Generators that port Xcoil code which calls
  `segSegDist` or `gridQuery` import them from `geometry`.
- Continuity tolerance. `COINCIDENCE_MM = 1e-6` mm is the only continuity tolerance: UT-GEO-01, REQ-F-01, REQ-N-21,
  the DRC node rule in §7 and Agent 4's IT-21 use it. Xcoil's own GEO-01 test uses the same bound
  (`/home/claude/serpentine/TEST_PLAN.md` l.41, `src/tests.js` l.36; `verified` by reading, 2026-10-05). The 1e-9 mm
  in Phase 1 port notes §6 and in `tests/independent/m1/continuity.py` (`CONTINUITY_TOL_MM`) is stricter than the
  requirement, so a gap between 1e-9 mm and 1e-6 mm would be reported there and accepted here. Agent 4 aligns the
  instrument to 1e-6 mm and may log the largest gap as information (request through Fable). The mirror and centre-via
  criteria of REQ-F-01 (1e-9 mm) are separate checks and stay.


## 6. `embodic.generators`: plug-in interface (ADR-0012)

```python
class Generator(Protocol):
    """A topology generator. Pure; never raises for user input; deterministic (same design -> same layout_hash)."""

    kind: ClassVar[TopologyKind]

    def generate(self, design: DesignParameters, registry: Registry) -> Layout | Unbuildable: ...


def generate_spiral(design: DesignParameters, registry: Registry) -> Layout | Unbuildable:
    """Requires design.winding to be SpiralWindingSpec (TypeError otherwise: a dispatch bug, not user input)."""


def generate_serpentine(design: DesignParameters, registry: Registry) -> Layout | Unbuildable:
    """Faithful port of Xcoil buildCanonical/buildLayout (single board). Layout-level golden regression GR-20."""


def generate_wave(design: DesignParameters, registry: Registry) -> Layout | Unbuildable:
    """Faithful port of Xcoil buildWave/buildWaveOverlap. Layout-level golden regression GR-21."""


GENERATORS: Mapping[TopologyKind, Callable[[DesignParameters, Registry], Layout | Unbuildable]] = {
    TopologyKind.SPIRAL: generate_spiral,
    TopologyKind.SERPENTINE: generate_serpentine,
    TopologyKind.WAVE: generate_wave,
}


def build_layout(design: DesignParameters, registry: Registry) -> Layout | Unbuildable:
    """Dispatch on design.topology through GENERATORS. Adding a topology = one module + one table entry."""
```

## 7. `embodic.drc`

Rule D-006: violation when measured clearance < rule - `DRC_EPSILON_MM`. Turns of one spiral share a net and still keep
clearance. Connectivity exempts exactly the pairs below (revision 2026-10-05, U-M1c report; implemented in
`src/embodic/drc/items.py` `exempt_pairs` and `src/embodic/drc/engine.py` `_check`). Every other pair is checked,
including same-net pairs.

1. Neighbours in one path. Each primitive that is not a fillet or a taper starts a new main index; a fillet or taper
   takes the main index of the primitive before it (Xcoil `mi`, `engine.js` `drcObjects` l.1697). Two primitives of one
   path are exempt when their main indices differ by at most 1. A corner's fillets and tapers are therefore exempt
   from both primitives the corner joins. Xcoil's wider exemption of pairs closer than `1.6 * (wMax + s)` along the
   path is not adopted (`tests/independent/README.md`, known limits).
2. A path end on a land. A via and the end group of a path whose end point lies within `pad_mm / 2` of the via
   centre. A pad and the end group of a path whose end point lies inside the pad outline, when the pad is on the
   path's layer or on all layers. The end group is the terminating main primitive with its fillets and tapers.
3. Path ends meeting at a node. The end groups of two different paths on one layer whose end points lie on one via,
   on one pad, or within `COINCIDENCE_MM` of each other.
4. A pad and a via whose centre lies inside the pad.

Rules 2 to 4 apply only when both objects carry the same net. Rule 1 needs no net test, because a path has one net.

```python
DRC_EPSILON_MM: float = 1e-6


class DrcCheckKind(StrEnum):
    TRACE_TRACE = "trace_trace"
    TRACE_VIA = "trace_via"
    VIA_VIA = "via_via"
    PAD_TRACE = "pad_trace"
    PAD_PAD = "pad_pad"
    COPPER_EDGE = "copper_edge"
    COPPER_HOLE = "copper_hole"
    MIN_WIDTH = "min_width"
    MIN_DRILL = "min_drill"
    ANNULAR_RING = "annular_ring"

    @property
    def issue_code(self) -> str:
        """Catalogue code of the kind, f"DRC_{name}" (DRC_TRACE_TRACE ...); U-M1c addition."""


@dataclass(frozen=True, slots=True, kw_only=True)
class DrcViolation:
    kind: DrcCheckKind
    layer: str | None
    measured_mm: float
    required_mm: float
    at_mm: tuple[float, float]
    objects: tuple[str, ...]  # "path:17/prim:4", "via:33"


@dataclass(frozen=True, slots=True, kw_only=True)
class DrcCheckSummary:
    kind: DrcCheckKind
    measured_min_mm: float | None
    required_mm: float
    pairs_checked: int


@dataclass(frozen=True, slots=True, kw_only=True)
class DrcReport:
    passed: bool
    summaries: tuple[DrcCheckSummary, ...]
    violations: tuple[DrcViolation, ...]  # first 1000
    violation_count: int
    method: Literal["grid+exact", "symmetric+grid+exact"]
    epsilon_mm: float = DRC_EPSILON_MM


class CancelToken:
    """Cooperative cancellation, checked between stages and inside chunked kernels. Thread-safe flag."""

    def cancel(self) -> None: ...

    @property
    def cancelled(self) -> bool: ...


def run_drc(layout: Layout, rules: DrcRules, *, use_symmetry: bool = True,
            cancel: CancelToken | None = None) -> DrcReport | None:
    """None only when cancelled."""


def min_distance_line_line(a: FloatArray, b: FloatArray) -> FloatArray: ...
def min_distance_line_arc(a: FloatArray, b: FloatArray) -> FloatArray: ...
def min_distance_arc_arc(a: FloatArray, b: FloatArray) -> FloatArray: ...
```

Clearance rule per check kind (decided 2026-10-05, U-D2; `REQUIRED_MM` in `src/embodic/drc/report.py`). A pair that
contains a via uses `via_clearance_mm`, and so does a pair of two pads. Trace to trace and pad to trace use
`trace_clearance_mm`.

| Kind | Pair | Rule field |
|---|---|---|
| TRACE_TRACE | trace and trace | `trace_clearance_mm` |
| PAD_TRACE | pad and trace | `trace_clearance_mm` |
| TRACE_VIA | trace and via | `via_clearance_mm` |
| VIA_VIA | via and via | `via_clearance_mm` |
| PAD_PAD | pad and pad, pad and via | `via_clearance_mm` |
| COPPER_EDGE | trace, via or pad and a board edge or cutout | `edge_clearance_mm` |
| COPPER_HOLE | trace, via or pad and a screw hole | `hole_clearance_mm` |
| MIN_WIDTH, MIN_DRILL, ANNULAR_RING | one object | `min_trace_width_mm`, `min_drill_mm`, `min_annular_ring_mm` |

The split is an `assumption`. Xcoil compares every pair with one clearance `p.clearance` (`engine.js` `runDrc`
l.756-775; `verified` by reading, 2026-10-05), and no fabrication source for separate values is cited yet. Golden runs
set both clearances to Xcoil's value, so the split cannot change a golden verdict. The comment above `REQUIRED_MM` does
not mention TRACE_VIA; the table is the authority.

Pad to pad and pad to via (ratified). The clearance is the centre distance minus the circumscribed radius of each land
(Xcoil `padRadius` and `padsClearance`, `engine.js` l.1818). The result is exact for round lands and smaller than the
true clearance for square, rectangular and oblong pads, so it never under-reports. It can report a pair whose true
clearance passes. PR-01's no-false-positive clause excludes these pairs (test_plan.md §5.2).

What `DrcCheckSummary` covers. `measured_min_mm` is the least clearance over the pairs the narrow phase measured.
The broad phase keeps every pair that can lie closer than the largest pair rule plus `DRC_EPSILON_MM` (`verified` by
reading `candidate_pairs` in `src/embodic/drc/engine.py`; UT-DRC-08 compares it with an exhaustive check), so below that
bound the value is the true minimum of that kind. Above it, the value is an upper bound of the true minimum and the true
minimum still exceeds the bound, so no verdict depends on it. `None` means no pair of that kind came within the bound.
`pairs_checked` counts measured pairs and depends on `use_symmetry`. Golden comparisons of summary values apply only
below the bound. For MIN_WIDTH, MIN_DRILL and ANNULAR_RING the summary covers every object.

## 8. `embodic.physics`

Kernels return plain floats or arrays and cite their EQ-ID in the docstring; only `analyse()` wraps values into
`Traceable`. Argument lists follow the Phase 1 registry variables; Agent 2's `docs/phase2/engineering/equation_registry.json`
is the authority for formulas. A kernel signature change after M2 starts is a contract change (Fable approves).

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class CircuitSolution:
    phase_emf_phasor_v_s_per_rad: Mapping[Phase, complex]  # per harmonic 1, peak flux-linkage derivative
    phase_resistance_ohm: Mapping[Phase, float]
    circulating_loss_w: Mapping[Phase, float]


@dataclass(frozen=True, slots=True, kw_only=True)
class MotorConstants:
    ke_line_v_s_per_rad: float
    kt_n_m_per_a: float
    kv_rpm_per_v: float


@dataclass(frozen=True, slots=True, kw_only=True)
class MassBreakdown:
    copper_g: float
    laminate_g: float


def pole_arc_ratio_block(width_mm: float, radius_mm: FloatArray, poles: int) -> FloatArray: ...  # EQ-04
def symmetry_plane_mm(rotor: RotorSpec, board_thickness_mm: float) -> float: ...  # EQ-05 G
def field_harmonic(n: int, radius_mm: FloatArray, z_mm: FloatArray, rotor: RotorSpec, symmetry_plane_mm: float,
                   alpha_p: FloatArray) -> tuple[FloatArray, FloatArray]: ...  # EQ-05, (Bz, Bt) peak in T
def edge_leakage_fraction(layout: Layout, rotor: RotorSpec, check: ValidityCheckSpec) -> float: ...  # EC-05 e_edge
def flux_linkage_harmonics(arrays: LayoutArrays, z_by_layer_mm: Mapping[str, float], rotor: RotorSpec,
                           harmonics: Sequence[int], max_segment_mm: float) -> NDArray[np.complex128]: ...  # EQ-06
def solve_phase_circuit(circuit: Circuit, path_emf: NDArray[np.complex128], path_r_ohm: FloatArray,
                        via_r_ohm: FloatArray) -> CircuitSolution: ...  # EQ-07
def phase_constants(ke_phase_v_s_per_rad: float, topology: ConnectionTopology, phases: int,
                    poles: int) -> MotorConstants: ...  # EQ-09
def copper_resistivity_ohm_m(temperature_degc: float, rho20_ohm_m: float, alpha_per_k: float) -> float: ...  # EQ-10
def path_resistance_ohm(arrays: LayoutArrays, thickness_mm_by_layer: Mapping[str, float],
                        resistivity_ohm_m: float) -> FloatArray: ...  # EQ-10
def via_resistance_ohm(drill_mm: float, plating_um: float, length_mm: float, resistivity_ohm_m: float,
                       count: int) -> float: ...  # EQ-11
def eddy_loss_w(arrays: LayoutArrays, b_peak_t: Mapping[int, tuple[FloatArray, FloatArray]],
                thickness_mm_by_layer: Mapping[str, float], electrical_speed_rad_per_s: float,
                resistivity_ohm_m: float) -> float: ...  # EQ-12
def skin_depth_mm(frequency_hz: float, resistivity_ohm_m: float) -> float: ...  # EQ-13
def inductance_estimate_h(series_turns: int, winding_factor_1: float, r_outer_mm: float, r_inner_mm: float,
                          pole_pairs: int, effective_gap_mm: float) -> float: ...  # EQ-14 (estimate)
def ipc2221_current_a(cross_section_mm2: float, temperature_rise_k: float, internal: bool) -> float: ...  # EQ-15
def mass_g(copper_area_mm2_by_layer: Mapping[str, float], thickness_mm_by_layer: Mapping[str, float],
           board_area_mm2: float, board_thickness_mm: float, copper_density_g_per_cm3: float,
           laminate_density_g_per_cm3: float) -> MassBreakdown: ...  # EQ-16
def temperature_rise_k(loss_w: float, board_area_mm2: float, convection_h_w_m2k: float) -> float: ...  # EQ-17
def emf_waveform_v(phasors_v: Mapping[int, complex], samples: int) -> FloatArray: ...  # EQ-18
def thd(harmonic_amplitudes: Mapping[int, float]) -> float: ...  # EQ-18
def delta_circulating_loss_w(triplen_emf_v: Mapping[int, complex], loop_resistance_ohm: float) -> float: ...  # EQ-19
def torque_speed_envelope(resistance_ohm: float, inductance_h: float, ke_v_s_per_rad: float, dc_link_v: float,
                          modulation: Modulation, current_limit_a: float, poles: int,
                          points: int) -> tuple[FloatArray, FloatArray]: ...  # EQ-20 (estimate)
def loss_budget_current_a(copper_loss_w: float, phases: int, phase_resistance_ohm: float) -> float: ...  # EQ-21
def current_density_a_per_mm2(phase_current_a: float, parallel_paths: int, width_mm: float,
                              thickness_mm: float) -> float: ...  # EQ-22


def analyse(design: DesignParameters, layout: Layout, provenance: ProvenanceMap, registry: Registry,
            *, cancel: CancelToken | None = None) -> AnalysisResult | None:
    """Topology-agnostic: reads Layout.paths, vias, circuit and copper_z_mm only. None only when cancelled."""
```

## 9. `embodic.io`: project file v1, examples, board dump, exporters

### 9.1 Project file schema v1

File name `<name>.embodic.json`, UTF-8 JSON. Top level (values are examples, `assumption`):

```json
{
  "format": "embodic-project",
  "schema_version": 1,
  "app_version": "0.2.0",
  "saved_utc": "2026-10-04T12:00:00Z",
  "design_hash": "sha256:...",
  "origin_example": {"example_id": "spiral_12c16p_default", "example_sha256": "sha256:..."},
  "design": {
    "name": "my stator",
    "phases": 3,
    "rotor": {"poles": 16, "rotor_type": "double", "remanence_t": 1.3, "recoil_permeability": 1.05,
              "air_gap_mm": 1.0, "back_iron_thickness_mm": 3.0, "magnet_offset_deg": 0.0,
              "magnet": {"kind": "block", "width_mm": 6.0, "length_mm": 20.0, "r_center_mm": 28.0, "thickness_mm": 2.0}},
    "winding": {"kind": "spiral", "coil": {"coil_count": 12, "r_inner_mm": 18.0, "r_outer_mm": 38.0, "...": "..."},
                "layers": {"pairs": [{"index": 0, "layer_in": "L1", "layer_out": "L2", "rotation_deg": 0.0, "phases": null}],
                           "series_groups": [[0]]},
                "assignment": null, "phase_sequence": "abc", "parallel_paths": 1},
    "stackup": {"layers": [{"kind": "copper", "name": "L1", "thickness_mm": 0.0348},
                           {"kind": "dielectric", "name": "D1", "thickness_mm": 0.071, "material": "FR-4"}]},
    "vias": {"drill_mm": 0.3, "pad_mm": 0.5, "plating_um": 25.0, "vias_per_transition": 1},
    "connection": {"topology": "star", "draw_interconnect": true, "ring_width_mm": 1.0, "terminal_pad_mm": 2.4,
                   "terminal_drill_mm": 1.2, "neutral_pad": false},
    "outline": {"board": {"shape": "polygon", "sides": 12, "across_flats_mm": 93.0, "corner_radius_mm": 0.0,
                          "rotation_deg": 0.0},
                "bore": {"shape": "circle", "radius_mm": 12.5}, "screws": []},
    "operating": {"speed_rpm": 1000.0, "line_current_rms_a": 1.0, "winding_temperature_degc": 60.0,
                  "ambient_temperature_degc": 20.0, "convection_h_w_m2k": 10.0, "dc_link_v": null, "modulation": "svpwm"},
    "materials": {},
    "analysis": {"harmonics": [1, 3, 5, 7, 9, 11, 13], "max_segment_mm": 0.5, "edge_correction": "off"},
    "drc_rules": {"trace_clearance_mm": 0.2, "...": "..."}
  },
  "provenance": {
    "/rotor/remanence_t": {"provenance": "measured", "source": "magnet datasheet rev C, grade N42"},
    "/rotor/poles": {"provenance": "example", "example_id": "spiral_12c16p_default"},
    "/winding/coil/trace_width_mm": {"provenance": "user"}
  },
  "ui": {"theme": "system", "phase_render_mode": "colour", "view": {"zoom": 1.0}}
}
```

Rules:
- `provenance` lists every concrete pointer of the design. `save_project` writes `derive_provenance()` output; on load the
  stored map is checked against the derivation when the referenced example is packaged with the same SHA-256, and kept
  as stored otherwise (`INFO_EXAMPLE_NOT_PACKAGED`). A `measured` entry without `source`, or on a design field, is
  `INVALID_PROVENANCE`. A file with no `origin_example` stores `{"provenance": "default"}` for optional fields still at
  their neutral value (§2.4 rule 3; revision 2026-10-04, D-019).
- `design_hash` = SHA-256 over the canonical JSON of `design` only (sorted keys, no whitespace, shortest round-trip float
  `repr`, UTF-8). `origin_example`, `provenance` and `ui` do not change the hash.
- Integer `schema_version`; migrations `migrate_v<n>_to_v<n+1>` run in sequence with `INFO_MIGRATED`; newer versions are
  refused (`INVALID_SCHEMA_VERSION_NEWER`). Phase 1 drafts never shipped a v1 file, so no Phase 1 migration exists.
- The published JSON Schema `src/embodic/io/schema/project.v1.schema.json` (Draft 2020-12) is validated against every
  example and fixture in tests (UT-IO-03); the runtime loader is hand-written and typed.

Angles (decided 2026-10-05, U-D2, U-M2a report). The file stores degrees under `_deg` names, as §0 says and as the
example above shows. The model stores radians under `_rad` names (`src/embodic/model/fields.py`). `embodic.io` converts
value and name together at the boundary: every field whose `unit` is `Unit.RAD` maps `<stem>_rad` to `<stem>_deg`, and
the file's provenance map uses the file names. The map comes from `FIELDS`, not from a hand list. U-M2f owns the
converter with `embodic.units.deg_to_rad` and `rad_to_deg`. `canonical_json` writes the file form, so `design_hash`
hashes the degrees the file stores.

The reasons for degrees are readability (`15.0`, not `0.2617993877991494`) and Xcoil, whose parameters are degrees
(`startAngleDeg`, `outlineRotationDeg`, `engine.js` l.31 and l.57). `checks/angle_round_trip.py` measured the cost on
the 72,001 values from -360 to 360 in steps of 0.01 and on 200,000 random values (`verified (run)`, CPython 3.11.15,
2026-10-05):

- Save, load, save changed no saved value in either set, so REQ-F-15's byte-identical round trip and the hash hold.
- The first save of a typed value prints a longer decimal for 8,496 of the 72,001 grid values. For example, -359.7
  typed in the UI is saved as -359.70000000000005. That is cosmetic, and the next round trip keeps it unchanged.
- `math.radians(d)` differs from Xcoil's `d * Math.PI / 180` (`engine.js` l.171, l.1507) by 1 ulp for 20,170 of the
  grid values. The units module keeps `math.radians`: the difference is far inside the 1e-6 mm path tolerance of
  GR-20 and GR-21, and Xcoil's expressions would print a longer decimal on first save twice as often (17,734 values).

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectFile:
    design: DesignParameters
    origin: ExampleRef | None
    measurements: tuple[Measurement, ...]
    ui_state: Mapping[str, JsonValue]


@dataclass(frozen=True, slots=True, kw_only=True)
class LoadedDraft:
    """A project file whose design is incomplete (saved mid-entry). Loads into the new-design form."""

    draft: DesignDraft
    origin: ExampleRef | None
    measurements: tuple[Measurement, ...]
    ui_state: Mapping[str, JsonValue]


def load_project(path: Path) -> tuple[ProjectFile | LoadedDraft | None, tuple[ValidationIssue, ...]]: ...
def save_project(path: Path, project: ProjectFile | LoadedDraft) -> str:
    """Writes atomically (temp file + os.replace). Returns the design hash ('' for a draft)."""
def canonical_json(design: DesignParameters) -> bytes: ...
def design_hash(design: DesignParameters) -> str: ...


@dataclass(frozen=True, slots=True, kw_only=True)
class ExampleInfo:
    example_id: str
    title: str  # English, shown in the Examples gallery with the word "Example"
    topology: TopologyKind
    source_note: str  # e.g. "Agent 2 default 12/16 (assumption)", "D08 thesis configuration (oracle O1)"


def list_examples() -> tuple[ExampleInfo, ...]: ...
def load_example(example_id: str) -> tuple[ExampleRef, DesignParameters]: ...
```

### 9.2 Board dump (Agent 3 format, frozen here as v1)

The format of `docs/phase1/software/calculation_flow_and_port_notes.md` §7.5 is adopted as `embodic.board-dump` v1
with the two changes below. Agent 4's independent checks and the golden harness read it. `BOARD_DUMP_SCHEMA` in
`src/embodic/io/board_dump.py` lists every key with its meaning, so a second reader needs nothing else.

Revision 2026-10-05 (U-D2, U-M1b and U-V1 reports):

- `layers[]` has no PCB-tool layer-name key. Phase 1 §7.5 listed one; MT-07 forbids the tool's name in shipped files
  (D-009), and U-M1b's writer omits the key (DEF-M1b-02). A layer record is `{index, name, z, copper_t, role, pair,
  phase}`.
- Each `circuits[]` record names its phase in the key `phase`, an integer with the encoding of `primitives[].phase`
  (0 = A, 1 = B, 2 = C). Phase 1 §7.5 said "per phase" without naming the key (DEF-V1-02).
- Interim content, as U-M1b wrote it: embodic writes `params`, `params_sha256` and `drc` as null, layer `copper_t`,
  `role`, `pair` and `phase` as null, object `kind` as null, via `phase` as null and `label` as "", and circuit
  `terminals` as `{plus: null, minus: null}`. A Layout does not carry these values yet. A reader treats null as
  "not provided", never as zero.
- `write_board_dump(layout, path, *, case_id)` is U-M1b's interim signature. U-M2f adds the keyword `design`
  to fill `params` and `params_sha256` (`work_breakdown.md` §1). `drc` stays null until §13 point 4 fixes its shape for
  per-kind rules.

Number encoding, shared by board dumps and golden fixtures (revision 2026-10-04, U-M1d deviations ratified):

- Infinity and NaN are written as `{"$f": "inf"}`, `{"$f": "-inf"}` and `{"$f": "nan"}`. JSON has no literal for
  them, and Python's `json` would otherwise write the non-standard `Infinity`.
- Negative zero is written `-0.0`. A reader that sees `-0` gets the integer 0 and loses the sign, and the sign changes
  `atan2` results (`tools/golden/README.md`, case `tfpoint-negative-x-signed-zero`).
- Comparators treat `-0.0` and `0.0` as equal (test_plan.md §3). The sign is kept for functions that read it, not for
  value comparison.

Xcoil's side of GR-19. The Node dumper does not write board dumps. For each Xcoil topology it writes the raw layout
that Xcoil's builder returns (see test_plan.md §3, "Layout dumps"). The mapping from that raw layout to
`embodic.board-dump` v1 is Python code owned by U-M1b, so the mapping is tested where the reader lives.

```python
BOARD_DUMP_SCHEMA: Mapping[str, str]  # key -> meaning, for writers and second readers


def dump_layout(layout: Layout, *, case_id: str, design: DesignParameters | None = None) -> dict[str, JsonValue]:
    """Board dump as plain JSON data. `design` arrives with U-M2f; without it params and params_sha256 are null."""
def encode_board_dump(dump: Mapping[str, JsonValue]) -> str:
    """Canonical text: sorted keys, one-space indent, tagged non-finite numbers, trailing newline."""
def decode_board_dump(text: str) -> dict[str, JsonValue]:
    """Parses and decodes non-finite tags; a bare NaN or Infinity token or another format raises ValueError."""
def write_board_dump(layout: Layout, path: Path, *, case_id: str, design: DesignParameters | None = None) -> None: ...
def read_board_dump(path: Path) -> Mapping[str, JsonValue]:
    """Returns the parsed JSON with non-finite numbers decoded ({"$f": "inf"} -> math.inf)."""
```

### 9.3 Exporters (D-009 list)

```python
class ExportKind(StrEnum):
    SVG = "svg"
    DXF_COMPLETE = "dxf_complete"
    DXF_OUTLINE = "dxf_outline"  # board outline and bore only
    DXF_SCREWS = "dxf_screws"  # screw clearance holes only
    PROJECT_JSON = "project_json"
    PDF_REPORT = "pdf_report"
    README = "readme"


class PhaseRenderMode(StrEnum):
    COLOUR = "colour"  # red / blue / green plus labels and line style (D-011)
    GREYSCALE_HATCH = "greyscale_hatch"  # lightness + hatch + labels (REQ-N-23)


@dataclass(frozen=True, slots=True, kw_only=True)
class ExportMetadata:
    embodic_version: str
    engine_version: str
    registry_version: str
    design_hash: str
    generated_utc: str
    drc_passed: bool


@dataclass(frozen=True, slots=True, kw_only=True)
class ExportSummary:
    kind: ExportKind
    path: Path
    lines: int
    arcs: int
    circles: int
    vias: int
    pads: int
    holes: int
    pages: int  # PDF only, else 0


@dataclass(frozen=True, slots=True, kw_only=True)
class ExportRefused:
    reason: Literal["drc_errors_not_confirmed", "no_layout", "no_screws"]
    issues: tuple[ValidationIssue, ...]


def write_svg(outcome: ComputeOutcome, path: Path, *, mode: PhaseRenderMode = PhaseRenderMode.COLOUR,
              allow_drc_errors: bool = False) -> ExportSummary | ExportRefused: ...
def write_dxf(outcome: ComputeOutcome, path: Path, part: Literal["complete", "outline", "screws"],
              *, allow_drc_errors: bool = False) -> ExportSummary | ExportRefused: ...
def write_report_pdf(outcome: ComputeOutcome, path: Path, *,
                     mode: PhaseRenderMode = PhaseRenderMode.GREYSCALE_HATCH) -> ExportSummary | ExportRefused:
    """Own dependency-free writer (port of Xcoil report.js, team's own code). Every value with unit and status."""
def write_readme(outcome: ComputeOutcome, files: Sequence[ExportSummary], path: Path) -> ExportSummary:
    """Plain-text README.txt describing every exported file, units, frame and the estimate caveats (Xcoil ui-main.js l.37)."""
def write_bundle(outcome: ComputeOutcome, kinds: Sequence[ExportKind], path: Path, *,
                 allow_drc_errors: bool = False) -> tuple[ExportSummary, ...] | ExportRefused:
    """ZIP of the selected exports plus README.txt (stdlib zipfile)."""
```

## 10. `embodic.outcome` and `embodic.api`: the compute facade

`VersionInfo`, `ComputeOptions` and `ComputeOutcome` live in `embodic.outcome` so that `embodic.io` can take an outcome
without importing `embodic.api` (layer rule, `package_layout.md` §3); `embodic.api` re-exports them.

```python
# embodic.outcome


@dataclass(frozen=True, slots=True, kw_only=True)
class VersionInfo:
    embodic: str
    schema: int
    registry: str
    python: str
    numpy: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ComputeOptions:
    run_drc: bool = True
    use_symmetry: bool = True


@dataclass(frozen=True, slots=True, kw_only=True)
class ComputeOutcome:
    design: DesignParameters
    design_hash: str
    provenance: ProvenanceMap
    issues: tuple[ValidationIssue, ...]
    layout: Layout | None
    drc: DrcReport | None
    analysis: AnalysisResult | None
    timings_s: Mapping[str, float]
    versions: VersionInfo

    @property
    def ok(self) -> bool:
        """No ERROR issue and DRC passed."""


# embodic.api


class StageCache:
    """Per-stage LRU (8 entries per stage). Keys: SHA-256 of the stage inputs (Phase 1 §8.1 table, with 'winding' merged
    into 'geometry'). One instance per worker thread; never shared between threads (no lock needed)."""

    def get(self, stage: Literal["geometry", "drc", "physics"], key: str) -> object | None: ...
    def put(self, stage: Literal["geometry", "drc", "physics"], key: str, value: object) -> None: ...


def compute(design: DesignParameters, provenance: ProvenanceMap, *, options: ComputeOptions = ComputeOptions(),
            cache: StageCache | None = None, cancel: CancelToken | None = None,
            registry: Registry | None = None) -> ComputeOutcome | None:
    """validate -> build_layout -> run_drc -> analyse. Physics runs even with DRC violations. None only when cancelled."""


def compute_project(path: Path) -> ComputeOutcome | tuple[ValidationIssue, ...]:
    """Load + compute. Returns the issues when the file is missing, unreadable or holds an incomplete draft."""


def outcome_to_json(outcome: ComputeOutcome) -> dict[str, JsonValue]:
    """Results JSON of embodic-cli compute --json; non-finite numbers encoded as {"$f": "inf"}."""


def version_info() -> VersionInfo: ...
```

## 11. `embodic.ui`: theme, toolstrip and view-model contracts

View-models live in `embodic.ui.viewmodels` and import no Qt (import contracts C2 and C3). Qt views subscribe through
`Observable` and call view-model commands; the worker in `embodic.ui.workers` runs `compute` off the GUI thread with a
`CancelToken` per request (latest wins, REQ-N-02).

```python
class ThemeName(StrEnum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


@dataclass(frozen=True, slots=True, kw_only=True)
class PhaseStyle:
    phase: Phase
    colour_hex: str  # red / blue / green per theme (D-011), from resources/themes/<theme>.json
    grey_hex: str  # greyscale ladder value
    hatch_deg: Literal[0, 45, 135]  # 0 = no hatch; hatch only inside the coil eye (REQ-N-23)
    dash: Literal["solid", "dash", "dot"]
    label: str  # "A", "B", "C"


@dataclass(frozen=True, slots=True, kw_only=True)
class ThemeTokens:
    name: Literal["light", "dark"]
    colours: Mapping[str, str]  # chrome tokens, white / grey / black only (REQ-L-04)
    phases: tuple[PhaseStyle, PhaseStyle, PhaseStyle]
    focus_ring_px: int
    control_height_px: int


def load_theme(name: Literal["light", "dark"]) -> ThemeTokens:
    """Reads resources/themes/<name>.json (Agent 1). Raises on a missing token: the build ships both themes."""


def resolve_theme(choice: ThemeName, os_prefers_dark: bool) -> Literal["light", "dark"]: ...


class ToolstripTab(StrEnum):
    HOME = "home"
    DESIGN = "design"
    ANALYSIS = "analysis"
    EXPORT = "export"
    VIEW = "view"


@dataclass(frozen=True, slots=True, kw_only=True)
class ToolstripAction:
    id: str  # also the Qt objectName and the string-catalogue key prefix
    tab: ToolstripTab
    icon: str  # file stem in resources/icons, monochrome SVG drawn with currentColor
    shortcut: str | None
    command: str  # name of a view-model command, resolved at startup (unknown name = startup error)
    group: str  # toolstrip group label key


TOOLSTRIP: tuple[ToolstripAction, ...] = (
    ToolstripAction(id="act-new", tab=ToolstripTab.HOME, icon="new", shortcut="Ctrl+N", command="new_design", group="file"),
    ToolstripAction(id="act-open", tab=ToolstripTab.HOME, icon="open", shortcut="Ctrl+O", command="open_project", group="file"),
    ToolstripAction(id="act-save", tab=ToolstripTab.HOME, icon="save", shortcut="Ctrl+S", command="save_project", group="file"),
    ToolstripAction(id="act-examples", tab=ToolstripTab.HOME, icon="examples", shortcut=None, command="show_examples", group="file"),
    ToolstripAction(id="act-undo", tab=ToolstripTab.HOME, icon="undo", shortcut="Ctrl+Z", command="undo", group="edit"),
    ToolstripAction(id="act-redo", tab=ToolstripTab.HOME, icon="redo", shortcut="Ctrl+Y", command="redo", group="edit"),
    ToolstripAction(id="act-topo-spiral", tab=ToolstripTab.DESIGN, icon="topology-spiral", shortcut=None, command="set_topology_spiral", group="topology"),
    ToolstripAction(id="act-topo-serpentine", tab=ToolstripTab.DESIGN, icon="topology-serpentine", shortcut=None, command="set_topology_serpentine", group="topology"),
    ToolstripAction(id="act-topo-wave", tab=ToolstripTab.DESIGN, icon="topology-wave", shortcut=None, command="set_topology_wave", group="topology"),
    ToolstripAction(id="act-conn-star", tab=ToolstripTab.DESIGN, icon="connection-star", shortcut=None, command="set_connection_star", group="connection"),
    ToolstripAction(id="act-conn-delta", tab=ToolstripTab.DESIGN, icon="connection-delta", shortcut=None, command="set_connection_delta", group="connection"),
    ToolstripAction(id="act-compute", tab=ToolstripTab.ANALYSIS, icon="compute", shortcut="F5", command="compute_now", group="run"),
    ToolstripAction(id="act-drc", tab=ToolstripTab.ANALYSIS, icon="drc", shortcut=None, command="show_checks", group="run"),
    ToolstripAction(id="act-equations", tab=ToolstripTab.ANALYSIS, icon="equations", shortcut=None, command="show_equations", group="reference"),
    ToolstripAction(id="act-export-svg", tab=ToolstripTab.EXPORT, icon="export-svg", shortcut=None, command="export_svg", group="drawings"),
    ToolstripAction(id="act-export-dxf", tab=ToolstripTab.EXPORT, icon="export-dxf", shortcut=None, command="export_dxf", group="drawings"),
    ToolstripAction(id="act-export-pdf", tab=ToolstripTab.EXPORT, icon="export-pdf", shortcut=None, command="export_pdf", group="report"),
    ToolstripAction(id="act-export-all", tab=ToolstripTab.EXPORT, icon="export-all", shortcut="Ctrl+E", command="export_bundle", group="report"),
    ToolstripAction(id="act-theme", tab=ToolstripTab.VIEW, icon="theme", shortcut=None, command="cycle_theme", group="appearance"),
    ToolstripAction(id="act-greyscale", tab=ToolstripTab.VIEW, icon="greyscale", shortcut=None, command="toggle_phase_render_mode", group="appearance"),
    ToolstripAction(id="act-fit", tab=ToolstripTab.VIEW, icon="zoom-fit", shortcut="F", command="fit_view", group="view"),
)


class Observable(Generic[T]):
    """Minimal pure-Python observable value for view-models; Qt views subscribe, tests call value directly."""

    @property
    def value(self) -> T: ...
    def subscribe(self, callback: Callable[[T], None]) -> Callable[[], None]: ...


@dataclass(frozen=True, slots=True, kw_only=True)
class SessionEmpty:
    """App start: no design open. The New design dialog and the Examples gallery are offered (D-014)."""

    state: Literal["empty"] = "empty"


@dataclass(frozen=True, slots=True, kw_only=True)
class SessionDrafting:
    """Required fields missing: form editable, nothing computed, results area shows the missing list."""

    state: Literal["drafting"] = "drafting"
    draft: DesignDraft
    missing: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class SessionComputed:
    """A complete design. `outcome` is None while the first compute runs; `stale` marks a kept last valid layout."""

    state: Literal["computed"] = "computed"
    design: DesignParameters
    provenance: ProvenanceMap
    outcome: ComputeOutcome | None
    stale: bool
    computing: bool


SessionState: TypeAlias = SessionEmpty | SessionDrafting | SessionComputed


class DesignSessionViewModel(Protocol):
    """State machine of one open design. Every command returns at once; computes run in the worker."""

    state: Observable[SessionState]
    can_undo: Observable[bool]
    can_redo: Observable[bool]

    def new_design(self, topology: TopologyKind) -> None: ...
    def load_example(self, example_id: str) -> None: ...
    def open_project(self, path: Path) -> tuple[ValidationIssue, ...]: ...
    def save_project(self, path: Path) -> str: ...
    def edit(self, pointer: str, value: JsonValue) -> None:
        """Re-entering the current value is a no-op (no undo entry, no recompute, PR-12)."""
    def mark_measured(self, pointer: str, source: str) -> ValidationIssue | None: ...
    def apply_suggestion(self, suggestion: Suggestion) -> None:
        """Applies with an inline notice 'Changed from X to Y: reason' and an Undo entry (REQ-F-23)."""
    def undo(self) -> None: ...
    def redo(self) -> None: ...
    def compute_now(self) -> None: ...


@dataclass(frozen=True, slots=True, kw_only=True)
class ResultRow:
    """One displayed number (REQ-T-01): everything the row and its 'How was this computed' disclosure need."""

    quantity: str
    label: str
    value_text: str
    unit_text: str
    status: Status
    assumed_count: int
    eq_ids: tuple[str, ...]
    estimate_label: str | None
    traceable: Traceable[float]


class ResultsViewModel(Protocol):
    rows: Observable[tuple[ResultRow, ...]]
    status_filter: Observable[frozenset[Status]]

    def set_status_filter(self, statuses: frozenset[Status]) -> None: ...
    def copy_trace(self, quantity: str) -> str: ...


@dataclass(frozen=True, slots=True, kw_only=True)
class ExportPreflight:
    drc_passed: bool
    failures: tuple[DrcViolation, ...]
    needs_confirmation: bool  # True when DRC failed: confirmation dialog, focus on Cancel (REQ-F-33)


class ExportViewModel(Protocol):
    def preflight(self) -> ExportPreflight: ...
    def export(self, kinds: Sequence[ExportKind], folder: Path, *,
               confirmed_drc_errors: bool) -> tuple[ExportSummary, ...] | ExportRefused: ...


class AppearanceViewModel(Protocol):
    theme: Observable[ThemeName]
    phase_render_mode: Observable[PhaseRenderMode]

    def cycle_theme(self) -> None: ...
    def toggle_phase_render_mode(self) -> None: ...
```

## 12. `embodic.cli`

```python
class ExitCode(IntEnum):
    OK = 0
    VALIDATION_ERRORS = 1  # also: incomplete draft, unreadable file
    DRC_ERRORS = 2
    INTERNAL_ERROR = 3


def main(argv: Sequence[str] | None = None) -> int:
    """embodic-cli compute <project.embodic.json> [--json OUT] [--no-drc] [--timings]
    embodic-cli validate <project.embodic.json>
    embodic-cli export <project.embodic.json> --format {svg,dxf,dxf-outline,dxf-screws,pdf,readme,bundle} -o PATH
                [--allow-drc-errors]
    The desktop app entry point is `embodic` (embodic.ui.app:main)."""
```

## 13. Open interface points

1. `SerpentineWindingSpec` omits Xcoil `stackMode = perPhase` and `boardGap` (multi-board stacks). Decided since: D-016
   ports the multi-board option (revision 2026-10-05). The contract change is still open: the two fields, and how a
   Layout represents one board per phase. Agent 6 writes it before U-M3a starts; screens.md already has
   `param-stack-mode` and `param-board-gap` for it (`screen_model_reconciliation.md`).
2. Physics kernel argument lists for EQ-12, EQ-14, EQ-16, EQ-17, EQ-20 follow the Phase 1 registry variables. Agent 2's
   v1 specification (U-S2) may change them before M2; the change goes through Fable and updates this file.
3. Whether Xcoil's serpentine analysis path (`engine.js` `analyze`, l.880-1017) and the generic element path
   (`analyzeElements`, l.1846) give the same EMF for the same copper is `unresolved`; GR-22 measures it (test_plan.md).
4. Board dump v2 (added 2026-10-05, U-M1b report). v1 cannot say three things: a Member with several paths (v1 writes
   one `members[]` entry per path, so the grouping of paths into one route is lost), the polarity of a path (the
   GR-19 mapper writes `polarity=0` because Xcoil does not return it), and the DRC record for per-kind rules (v1 `drc`
   has one `rule.clearance`). Agent 4's readers and the golden harness need all three before M3 compares ported
   boards. Agent 6 specifies v2 with Agent 4 before U-V3; until then embodic writes v1.
