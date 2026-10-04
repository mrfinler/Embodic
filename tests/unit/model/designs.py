"""Complete designs for tests, one per topology. Every number is an example value, not a recommendation.

Spiral: spiral_generator_spec.md worked example 1 (12 coils, 16 poles). Serpentine and wave: Xcoil DEFAULTS
(engine.js l.19-97) renamed to embodic fields. Board, rotor and DRC rules not given there are example values.
"""

import math

from embodic.model.analysis_options import AnalysisOptions
from embodic.model.connection import ConnectionSpec
from embodic.model.design import DesignParameters
from embodic.model.drc_rules import DrcRules
from embodic.model.layers import LayerConfig, LayerPair
from embodic.model.operating import OperatingPoint
from embodic.model.outline import CircleOutline, OutlineSpec, PolygonOutline, ScrewFit, ScrewPattern
from embodic.model.rotor import ArcMagnet, BlockMagnet, RotorSpec, RotorType
from embodic.model.stackup import generate_even_stackup
from embodic.model.vias import ViaSpec
from embodic.model.winding_specs import (
    SerpentineWindingSpec,
    SpiralCoilSpec,
    SpiralWindingSpec,
    WaveStyle,
    WaveWindingSpec,
    WindingSpec,
)

COPPER_2OZ_MM = 2 * 0.0348

DRC = DrcRules(
    trace_clearance_mm=0.15,
    via_clearance_mm=0.15,
    edge_clearance_mm=0.3,
    hole_clearance_mm=0.3,
    min_trace_width_mm=0.15,
    min_drill_mm=0.3,
    min_annular_ring_mm=0.1,
)


def _xcoil_rotor() -> RotorSpec:
    magnet = ArcMagnet(pole_arc_ratio=0.85, r_inner_mm=22.0, r_outer_mm=40.0, thickness_mm=3.0)
    return RotorSpec(
        poles=16,
        rotor_type=RotorType.DOUBLE,
        magnet=magnet,
        remanence_t=1.3,
        recoil_permeability=1.05,
        air_gap_mm=0.8,
        back_iron_thickness_mm=3.0,
    )


def _xcoil_design(winding: WindingSpec, copper_count: int) -> DesignParameters:
    screws = (ScrewPattern(size="M3", fit=ScrewFit.NORMAL, count=8, pitch_radius_mm=44.5),)
    return DesignParameters(
        name="Xcoil defaults example",
        phases=3,
        rotor=_xcoil_rotor(),
        winding=winding,
        stackup=generate_even_stackup(copper_count, COPPER_2OZ_MM, 1.6),
        vias=ViaSpec(drill_mm=0.3, pad_mm=0.6, plating_um=25.0),
        connection=ConnectionSpec(ring_width_mm=1.0, terminal_pad_mm=2.4, terminal_drill_mm=1.2),
        outline=OutlineSpec(board=CircleOutline(radius_mm=48.0), bore=CircleOutline(radius_mm=18.7), screws=screws),
        operating=OperatingPoint(
            speed_rpm=1500.0,
            line_current_rms_a=0.8,
            winding_temperature_degc=60.0,
            ambient_temperature_degc=25.0,
            convection_h_w_m2k=30.0,
            dc_link_v=24.0,
        ),
        drc_rules=DRC,
    )


def serpentine_design() -> DesignParameters:
    """Xcoil DEFAULTS as a serpentine design: 2 layers per phase, 6 copper layers."""
    winding = SerpentineWindingSpec(
        r_inner_mm=22.0, r_outer_mm=40.0, turns=4, trace_width_mm=0.4, clearance_mm=0.2, layers_per_phase=2
    )
    return _xcoil_design(winding, copper_count=6)


def wave_design() -> DesignParameters:
    """Xcoil DEFAULTS as a wave design on 2 copper layers."""
    winding = WaveWindingSpec(
        r_inner_mm=22.0,
        r_outer_mm=40.0,
        turns=4,
        trace_width_mm=0.4,
        clearance_mm=0.2,
        wave_style=WaveStyle.INVOLUTE,
        bus_width_mm=1.0,
    )
    return _xcoil_design(winding, copper_count=2)


def spiral_design() -> DesignParameters:
    """Worked example 1 of spiral_generator_spec.md: 12 coils, 16 poles, one layer pair."""
    coil = SpiralCoilSpec(
        coil_count=12, r_inner_mm=18.0, r_outer_mm=38.0, trace_width_mm=0.5, clearance_mm=0.2, coil_gap_mm=0.2
    )
    layers = LayerConfig(pairs=(LayerPair(index=0, layer_in="L1", layer_out="L2"),), series_groups=((0,),))
    magnet = BlockMagnet(width_mm=6.0, length_mm=20.0, r_center_mm=28.0, thickness_mm=2.0)
    return DesignParameters(
        name="Spiral 12/16 example",
        phases=3,
        rotor=RotorSpec(
            poles=16,
            rotor_type=RotorType.DOUBLE,
            magnet=magnet,
            remanence_t=1.3,
            recoil_permeability=1.05,
            air_gap_mm=1.0,
            back_iron_thickness_mm=3.0,
        ),
        winding=SpiralWindingSpec(coil=coil, layers=layers),
        stackup=generate_even_stackup(2, 0.0348, 1.6),
        vias=ViaSpec(drill_mm=0.3, pad_mm=0.6, plating_um=25.0),
        connection=ConnectionSpec(ring_width_mm=1.0, terminal_pad_mm=2.4, terminal_drill_mm=1.2),
        outline=OutlineSpec(
            board=PolygonOutline(sides=12, across_flats_mm=93.0, rotation_rad=math.pi / 12),
            bore=CircleOutline(radius_mm=12.5),
        ),
        operating=OperatingPoint(
            speed_rpm=1000.0,
            line_current_rms_a=1.0,
            winding_temperature_degc=60.0,
            ambient_temperature_degc=20.0,
            convection_h_w_m2k=10.0,
        ),
        analysis=AnalysisOptions(max_segment_mm=0.25),
        drc_rules=DRC,
    )


EXAMPLES = {"spiral": spiral_design, "serpentine": serpentine_design, "wave": wave_design}
