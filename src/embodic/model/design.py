"""The complete design: one structure whose winding variant fixes the topology (interfaces.md section 2.2)."""

from dataclasses import dataclass, field
from typing import Literal, TypeAlias

from embodic.model.analysis_options import AnalysisOptions
from embodic.model.connection import ConnectionSpec
from embodic.model.drc_rules import DrcRules
from embodic.model.materials import MaterialOverrides
from embodic.model.operating import OperatingPoint
from embodic.model.outline import OutlineSpec
from embodic.model.rotor import RotorSpec
from embodic.model.stackup import Stackup
from embodic.model.vias import ViaSpec
from embodic.model.vocabulary import TopologyKind
from embodic.model.winding_specs import WindingSpec

PhaseCount: TypeAlias = Literal[1, 2, 3]  # spiral accepts 3 only (validator); serpentine and wave keep Xcoil's 1/2/3


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
    materials: MaterialOverrides = field(default_factory=MaterialOverrides)
    analysis: AnalysisOptions = field(default_factory=AnalysisOptions)
    drc_rules: DrcRules

    @property
    def topology(self) -> TopologyKind:
        """Return the topology named by the winding variant."""
        return TopologyKind(self.winding.kind)
