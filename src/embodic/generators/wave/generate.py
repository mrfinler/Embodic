"""Wave stator of T/B track pairs (engine.js l.1449-2230): ``generate_wave``, a faithful port of Xcoil's wave builders.

Styles ``involute``, ``jog`` and ``chord`` share ``build_wave`` (tracks on the odd layers, mirrored tracks on the even
layers, group links on layer 0); ``overlap`` has its own builder. Both return the objects in Xcoil's order and
``assemble_layout`` writes them as an embodic Layout.

The design supplies what Xcoil reads from its flat parameter set: poles (rotor), phases, copper layer count (stack-up),
via drill and pad, connection and the winding spec. The start angle is 0, as in Xcoil's defaults.
"""

import itertools
import math

from embodic.errors import IssueCategory, Severity, Unbuildable, ValidationIssue, message_for
from embodic.generators.wave.assemble import Obj, SeriesElement, WaveBuild, assemble_layout, build_in_layer_order
from embodic.generators.wave.build import Track, WaveGeometry, build_wave
from embodic.generators.wave.derive import WaveFrame, WaveParams, WaveRefusal, derive_wave, max_wave_turns
from embodic.generators.wave.interconnect import IcPad, PadSpec, build_interconnect
from embodic.generators.wave.overlap import build_overlap
from embodic.geometry.layout import BoardStack
from embodic.model.design import DesignParameters
from embodic.model.validate import WAVE_LAYERS_MAX
from embodic.model.vocabulary import ConnectionTopology
from embodic.model.winding_specs import CornerStyle, WaveWindingSpec
from embodic.results import Registry

MAX_POLES = 200  # Xcoil normalizeParams ranges (l.114-120)
MAX_TURNS = 200
MAX_SLOTS = 2400  # assumption: no wave winding approaches it (Xcoil's defaults use 96); bounds time and memory
_REFUSAL_CODES = {
    "WAVE_MIN_POLES": ("UNBUILDABLE_WAVE_MIN_POLES", "/rotor/poles"),
    "WAVE_SLOT_PITCH": ("UNBUILDABLE_WAVE_SLOT_PITCH", "/winding/turns"),
    "WAVE_OUTER_TIGHT": ("UNBUILDABLE_WAVE_OUTER_TIGHT", "/winding/end_width_outer_mm"),
    "WAVE_INNER_TIGHT": ("UNBUILDABLE_WAVE_INNER_TIGHT", "/winding/turns"),
}


def _issue(code: str, pointers: tuple[str, ...], limit: int | None = None) -> ValidationIssue:
    return ValidationIssue(
        code=code, category=IssueCategory.UNBUILDABLE, severity=Severity.ERROR, message=message_for(code),
        pointers=pointers, limit=limit,
    )  # fmt: skip


def _unbuildable(code: str, pointers: tuple[str, ...], limit: int | None = None) -> Unbuildable:
    return Unbuildable(issues=(_issue(code, pointers, limit),))


def _out_of_range(design: DesignParameters, spec: WaveWindingSpec) -> tuple[str, ...]:
    """Pointers of inputs the geometry cannot use: non-finite or non-positive sizes, counts outside Xcoil's ranges."""
    positive = {
        "/winding/r_inner_mm": spec.r_inner_mm,
        "/winding/trace_width_mm": spec.trace_width_mm,
        "/winding/clearance_mm": spec.clearance_mm,
        "/winding/bus_width_mm": spec.bus_width_mm,
        "/winding/end_width_outer_mm": spec.end_width_outer_mm or spec.trace_width_mm,
        "/winding/end_width_inner_mm": spec.end_width_inner_mm or spec.trace_width_mm,
        "/vias/pad_mm": design.vias.pad_mm,
        "/connection/ring_width_mm": design.connection.ring_width_mm,
        "/connection/terminal_pad_mm": design.connection.terminal_pad_mm,
    }
    bad = [pointer for pointer, v in positive.items() if not (math.isfinite(v) and v > 0)]
    if not (math.isfinite(spec.r_outer_mm) and spec.r_outer_mm > spec.r_inner_mm):
        bad.append("/winding/r_outer_mm")
    if not (math.isfinite(spec.fillet_radius_mm) and spec.fillet_radius_mm >= 0):
        bad.append("/winding/fillet_radius_mm")
    if not 1 <= spec.turns <= MAX_TURNS:
        bad.append("/winding/turns")
    if not (2 <= design.rotor.poles <= MAX_POLES and design.rotor.poles % 2 == 0):
        bad.append("/rotor/poles")
    elif design.rotor.poles * design.phases * spec.turns > MAX_SLOTS:
        bad.append("/winding/turns")
    return tuple(bad)


def wave_params(design: DesignParameters, spec: WaveWindingSpec, start_angle_deg: float = 0.0) -> WaveParams:
    """Xcoil's flat parameter names for the wave builders, read from the design."""
    return WaveParams(
        start_angle_deg=start_angle_deg,
        poles=design.rotor.poles, phases=design.phases, turns=spec.turns, r_in=spec.r_inner_mm, r_out=spec.r_outer_mm,
        trace_width_mm=spec.trace_width_mm, clearance_mm=spec.clearance_mm,
        end_width_outer_mm=spec.end_width_outer_mm or 0.0, end_width_inner_mm=spec.end_width_inner_mm or 0.0,
        via_pad=design.vias.pad_mm, via_drill_mm=design.vias.drill_mm, wave_layers=len(design.stackup.copper_layers()),
        wave_style=spec.wave_style.value, rounded=spec.corner_style is CornerStyle.ROUND,
        fillet_radius_mm=spec.fillet_radius_mm, bus_width_mm=spec.bus_width_mm,
    )  # fmt: skip


def _refusals(refusals: tuple[WaveRefusal, ...], params: WaveParams) -> Unbuildable:
    issues = []
    for r in refusals:
        code, pointer = _REFUSAL_CODES[r.code]
        limit = max_wave_turns(params) if r.field == "turns" and r.code != "WAVE_MIN_POLES" else None
        issues.append(_issue(code, (pointer,), limit or None))
    return Unbuildable(issues=tuple(issues))


def _wants_interconnect(design: DesignParameters) -> bool:
    conn = design.connection
    return conn.draw_interconnect and design.phases == 3 and conn.topology is not ConnectionTopology.OPEN


def _external_interconnect(design: DesignParameters, frame: WaveFrame) -> tuple[ValidationIssue, ...]:
    """Xcoil's INTERCONNECT_EXTERNAL warning (engine.js l.2190): the overlap winding cannot carry a delta connection.

    Xcoil's ``else if (wantIc)`` branch sits after ``if (wantIc || conn === 'open')`` and never runs; the condition
    here is the one its message states (D-036 d).
    """
    if (
        frame.style != "overlap"
        or not _wants_interconnect(design)
        or design.connection.topology is not ConnectionTopology.DELTA
    ):
        return ()
    code = "RANGE_WAVE_INTERCONNECT_EXTERNAL"
    return (
        ValidationIssue(
            code=code,
            category=IssueCategory.UNSUPPORTED_RANGE,
            severity=Severity.WARNING,
            message=message_for(code),
            pointers=("/connection/draw_interconnect", "/connection/topology"),
            value=ConnectionTopology.DELTA.value,
        ),
    )


def _end_via(t: Track) -> int:
    """Via ring index of the via a track ends on in current direction (outer via 2k, inner via 2k + 1)."""
    if t.kind == "T":
        return 2 * t.via_out if t.sign > 0 else 2 * t.via_in + 1
    return 2 * t.via_in + 1 if t.sign < 0 else 2 * t.via_out


def _track_objects(frame: WaveFrame, geometry: WaveGeometry) -> tuple[list[Obj], dict[tuple[str, int], list[int]]]:
    """Tracks of every layer (T on even layers, B on odd ones) and the group links on layer 0, in Xcoil's order."""
    objects: list[Obj] = []
    by_slot: dict[tuple[str, int], list[int]] = {}
    for layer in range(frame.layers):
        kind = "T" if layer % 2 == 0 else "B"
        for t in geometry.tracks_t if kind == "T" else geometry.tracks_b:
            by_slot.setdefault((kind, t.slot), []).append(len(objects))
            objects.append(Obj(layer=layer, kind="track", prims=t.prims, phase=t.phase, element=t.slot,
                               polarity=1 if t.sign > 0 else -1, end_via=_end_via(t)))  # fmt: skip
        if layer == 0:
            objects.extend(Obj(layer=0, kind="link", prims=lk.prims, phase=lk.phase) for lk in geometry.links)
    return objects, by_slot


def _series_elements(
    frame: WaveFrame, geometry: WaveGeometry, objects: list[Obj], by_slot: dict[tuple[str, int], list[int]]
) -> list[SeriesElement]:  # fmt: skip
    """Series elements per phase as Xcoil analyzeWave counts them: belts F (+) and G (-), q slots, pp pole pairs."""
    elements: list[SeriesElement] = []
    for z in geometry.zones:
        for beta in (z.beta_f, z.beta_g):
            for i, n in itertools.product(range(frame.q), range(frame.pp)):
                k_t = (beta * frame.q + i + 2 * frame.mq * n) % frame.n_slots
                k_b = (k_t + frame.mq) % frame.n_slots
                if geometry.special.get(k_t) != "removed":
                    elements.append(SeriesElement(phase=z.phase, objects=tuple(by_slot[("T", k_t)])))
                elements.append(SeriesElement(phase=z.phase, objects=tuple(by_slot[("B", k_b)])))
    for lk in geometry.links:
        link = next(i for i, o in enumerate(objects) if o.kind == "link" and o.phase == lk.phase)
        elements.append(SeriesElement(phase=lk.phase, objects=(link,)))
    return elements


def _build_standard(design: DesignParameters, frame: WaveFrame) -> WaveBuild | Unbuildable:
    """Xcoil computeWave for involute, jog and chord: tracks, group links, interconnect."""
    geometry = build_wave(frame)
    if geometry.r_link - geometry.link_width_mm / 2 < 0.5 or not geometry.link_room:
        return _unbuildable("UNBUILDABLE_WAVE_LINK_ROOM", ("/winding/r_inner_mm",))
    objects, by_slot = _track_objects(frame, geometry)
    r_min_cu = geometry.r_link - geometry.link_width_mm / 2
    r_max_cu = frame.r_vo + max(frame.pad, frame.w_out, frame.w if frame.style == "chord" else 0.0) / 2
    r_max_all = r_max_cu
    pads: tuple[IcPad, ...] = ()
    if _wants_interconnect(design):
        conn = design.connection
        ic = build_interconnect(
            geometry.terms, connection="star" if conn.topology is ConnectionTopology.STAR else "delta", base=r_max_cu,
            bus_width_mm=conn.ring_width_mm, clearance_mm=frame.s, via_pad=frame.pad,
            pad=PadSpec(size=conn.terminal_pad_mm, drill_mm=conn.terminal_drill_mm),
            link_layers=list(range(frame.layers - 1, 0, -1)), line_layer=0,
        )  # fmt: skip
        if ic.unroutable:
            return _unbuildable("UNBUILDABLE_WAVE_INTERCONNECT_CROSSING", ("/connection/topology",))
        objects.extend(
            Obj(layer=item.layer, kind="ic", prims=part.prims, phase=None, net=item.net, ic=part)
            for item in ic.items
            for part in item.parts
        )
        pads, r_max_all = ic.pads, max(r_max_cu, ic.r_edge)
    elements = _series_elements(frame, geometry, objects, by_slot)
    return build_in_layer_order(
        objects, elements, geometry.vias, pads, r_min_cu=r_min_cu, r_max_cu=r_max_cu, r_max_all=r_max_all
    )


def generate_wave(design: DesignParameters, registry: Registry) -> BoardStack | Unbuildable:
    """Faithful port of Xcoil buildWave/buildWaveOverlap, one board; a winding other than wave raises TypeError.

    The start angle is 0, Xcoil's default: ``WaveWindingSpec`` has no start angle (open question Q-1).
    """
    return generate_wave_rotated(design, registry, 0.0)


def generate_wave_rotated(
    design: DesignParameters, registry: Registry, start_angle_deg: float
) -> BoardStack | Unbuildable:  # fmt: skip
    """``generate_wave`` with Xcoil's ``startAngleDeg``: the whole winding turns rigidly by that angle (PR-14)."""
    spec = design.winding
    if not isinstance(spec, WaveWindingSpec):
        raise TypeError(f"generate_wave needs a wave winding, got {type(spec).__name__}")
    if pointers := _out_of_range(design, spec):
        return _unbuildable("UNBUILDABLE_WAVE_INPUT_OUT_OF_RANGE", pointers)
    layers = len(design.stackup.copper_layers())
    if layers < 2 or layers % 2 != 0 or layers > WAVE_LAYERS_MAX:
        return _unbuildable("UNBUILDABLE_WAVE_LAYER_COUNT", ("/stackup/layers",))
    params = wave_params(design, spec, start_angle_deg)
    frame = derive_wave(params)
    if isinstance(frame, tuple):
        return _refusals(frame, params)
    build = build_overlap(design, frame) if frame.style == "overlap" else _build_standard(design, frame)
    if isinstance(build, Unbuildable):
        return build
    layout = assemble_layout(design, build, registry)
    return BoardStack(
        boards=(layout,),
        board_thickness_mm=design.stackup.board_thickness_mm(),
        board_gap_mm=0.0,
        issues=_external_interconnect(design, frame),
    )
