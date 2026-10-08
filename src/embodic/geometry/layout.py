"""The Layout every generator produces and every consumer reads (interfaces.md section 5)."""

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal

from embodic.errors import Severity, ValidationIssue
from embodic.geometry.arrays import LayoutArrays, layout_arrays
from embodic.geometry.circuit import Circuit
from embodic.geometry.details import TopologyDetail
from embodic.geometry.hashing import compute_layout_hash
from embodic.geometry.paths import CopperPath
from embodic.geometry.primitives import Primitive
from embodic.model.vocabulary import TopologyKind, ViaSpan
from embodic.results import Traceable


class ViaRole(StrEnum):
    """Why a via exists."""

    CENTRE = "centre"
    TRANSFER = "transfer"
    TERMINAL = "terminal"
    RING = "ring"
    STITCH = "stitch"


@dataclass(frozen=True, slots=True, kw_only=True)
class Via:
    """Plated through hole joining two copper layers."""

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
    """Terminal pad; ``rotation_rad`` turns its local axes, ``drill_mm`` 0 means SMD."""

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
    """Unplated screw clearance hole."""

    x_mm: float
    y_mm: float
    diameter_mm: float
    label: str  # e.g. "M3 normal"


@dataclass(frozen=True, slots=True, kw_only=True)
class BoardOutline:
    """Board edge, bore and other cutouts as closed loops of width-0 primitives, and the screw holes."""

    outer: tuple[Primitive, ...]  # closed loop, width 0
    cutouts: tuple[tuple[Primitive, ...], ...]  # bore and other closed loops
    holes: tuple[Hole, ...]  # screw clearance holes (DXF "screws")


@dataclass(frozen=True, slots=True, kw_only=True)
class RotationalSymmetry:
    """Lets DRC check one period plus neighbours (PR-02 proves equality with the full check)."""

    order: int  # copper of `periodic_path_ids` repeats every 2*pi/order
    periodic_path_ids: tuple[int, ...]
    canonical_path_ids: tuple[int, ...]  # one period, the reference set


@dataclass(frozen=True, slots=True, kw_only=True)
class Layout:
    """Copper, vias, pads, outline and circuit of one board, with a hash computed from them (never passed in)."""

    topology: TopologyKind
    copper_layers: tuple[str, ...]
    copper_z_mm: Mapping[str, float]
    paths: tuple[CopperPath, ...]
    vias: tuple[Via, ...]
    pads: tuple[Pad, ...]
    outline: BoardOutline
    circuit: Circuit
    symmetry: RotationalSymmetry | None
    envelope_mm: tuple[float, float]  # r_min_cu, r_max_cu
    # Defaults keep hand-built Layouts in tests valid; every generator sets both (deviation from section 5).
    detail: TopologyDetail | None = None  # generator-specific record; consumers other than the UI ignore it
    derived: tuple[Traceable[float], ...] = ()  # feasibility-rail values shared by all topologies
    layout_hash: str = field(init=False)  # "sha256:<hex>" over the canonical primitive list

    def __post_init__(self) -> None:
        """Derive ``layout_hash`` so a Layout cannot carry a hash of other copper."""
        object.__setattr__(self, "layout_hash", compute_layout_hash(self.paths, self.vias, self.pads, self.outline))

    def arrays(self) -> LayoutArrays:
        """Return the per-layer NumPy view for DRC and physics."""
        return layout_arrays(self.copper_layers, self.paths, self.vias)


@dataclass(frozen=True, slots=True, kw_only=True)
class BoardStack:
    """The boards a design produces (D-016; revision 2026-10-05, U-D3).

    One Layout per board, in phase order for ``StackMode.ONE_BOARD_PER_PHASE``; one board for every other design.
    """

    boards: tuple[Layout, ...]  # never empty; board k of a per-phase stack holds only phase k
    board_thickness_mm: float  # one board, = design.stackup.board_thickness_mm()
    board_gap_mm: float  # 0.0 when len(boards) == 1
    issues: tuple[ValidationIssue, ...] = ()  # WARNING and INFO of the build (D-035 a); an error is Unbuildable
    stack_hash: str = field(init=False)  # "sha256:<hex>" over the boards' layout_hash values in order and the gap

    def __post_init__(self) -> None:
        """Set ``stack_hash``; raise ValueError for no board, a gap other than 0.0 on a one-board stack, or an error."""
        if not self.boards:
            raise ValueError("a BoardStack needs at least one board")
        if len(self.boards) == 1 and self.board_gap_mm != 0.0:
            raise ValueError(f"a one-board stack has no board gap, got {self.board_gap_mm!r} mm")
        if errors := [i.code for i in self.issues if i.severity is Severity.ERROR]:
            raise ValueError(f"the issues of a built stack are warning or info, got errors {errors}")
        document = {"boards": [b.layout_hash for b in self.boards], "board_gap_mm": self.board_gap_mm}
        text = json.dumps(document, sort_keys=True, separators=(",", ":"), allow_nan=False)
        object.__setattr__(self, "stack_hash", "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest())

    @property
    def stack_thickness_mm(self) -> float:
        """Return n * board_thickness_mm + (n - 1) * board_gap_mm (Xcoil statorThickness, engine.js l.689)."""
        n = len(self.boards)
        return n * self.board_thickness_mm + (n - 1) * self.board_gap_mm
