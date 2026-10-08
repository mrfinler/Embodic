"""``embodic.board-dump`` v1: one JSON document per Layout for the golden harness and Agent 4's checks.

The format is Phase 1 port notes section 7.5, frozen by interfaces.md section 9.2. ``BOARD_DUMP_SCHEMA`` lists every
key with its meaning so a second reader can be written without this module. Numbers are JSON doubles in shortest
round-trip form; infinity and NaN are ``{"$f": "inf"}``, ``{"$f": "-inf"}``, ``{"$f": "nan"}``; negative zero is
``-0.0``. Keys are sorted. Write, read, write gives identical text.

What embodic leaves null, and why: ``params`` and ``params_sha256`` when the caller passes no ``design``; ``drc``
until interfaces.md section 13 point 4 fixes its shape; layer ``copper_t``, ``role``, ``pair`` and ``phase`` and
object ``kind``, which a Layout does not carry; circuit ``terminals``, because a PhaseCircuit names only its terminal
net. The Phase 1 layer key for the PCB-tool layer name is not written (D-009, MT-07).
"""

import json
import math
import platform
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TypeAlias

import embodic
from embodic.geometry.layout import Layout, Pad, Via, ViaRole
from embodic.geometry.paths import CopperPath
from embodic.geometry.primitives import Line, Primitive
from embodic.io.canonical import design_document, design_hash
from embodic.model.design import DesignParameters
from embodic.model.vocabulary import Phase

JsonValue: TypeAlias = bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"] | None

BOARD_DUMP_FORMAT = "embodic.board-dump"
BOARD_DUMP_VERSION = 1
NONFINITE_TAG = "$f"
PHASE_INDEX: Mapping[Phase, int] = {Phase.A: 0, Phase.B: 1, Phase.C: 2}

BOARD_DUMP_SCHEMA: Mapping[str, str] = {
    "format": '"embodic.board-dump"',
    "format_version": "1",
    "producer": "{name: 'xcoil-v3' | 'embodic', version, engine_sha256 (Xcoil only, else null), runtime}",
    "case_id": "string naming the case",
    "params": "the design in its project-file form (interfaces.md 9.1, angles in degrees), or null without a design",
    "params_sha256": "design hash: 'sha256:' + SHA-256 of the canonical params JSON, or null",
    "units": "{length: 'mm', angle: 'rad'}",
    "frame": "x right, y up, origin on the rotor axis",
    "layers[]": "{index, name, z (mm, copper centre), copper_t, role, pair, phase}",
    "primitives[]": (
        "{id, type 'line' | 'arc', layer (index), start [x, y], end [x, y] in current direction, line: x1 y1 x2 y2, "
        "arc: cx cy r a1 a2 (sweep = a2 - a1, signed, counter-clockwise positive), width, kind (embodic "
        "PrimitiveRole value), object (CopperPath id), seq (position in the object), net, phase (0 A, 1 B, 2 C or "
        "null), coil (element index or null)}"
    ),
    "objects[]": "{id, kind, layer (index), net, phase, coil, primitive_ids[], touch_vias[]}",
    "vias[]": "{id, x, y, drill, pad, layer_from, layer_to (layer indices), role, net, phase, terminal (bool), label}",
    "pads[]": "{id, x, y, shape, w, h, rot (rad), drill, smd (bool), layer (index or null = all layers), net, label}",
    "outline": "{board: [primitives, width 0], cutouts: [[primitives]], holes: [{x, y, dia}]}",
    "circuits[]": (
        "per phase {phase, elements[] in series, each {members: [{object, layer, direction +1 | -1}], vias: [ids]}, "
        "terminals: {plus, minus}}; a ParallelGroup is one element, each path of each Member one member"
    ),
    "drc": "{rule: {clearance, epsilon}, values, pass_d006, producer_flag} or null",
}


def _primitive_geometry(p: Primitive) -> dict[str, JsonValue]:
    start, end = p.start_point(), p.end_point()
    if isinstance(p, Line):
        geometry: dict[str, JsonValue] = {"type": "line", "x1": p.x1_mm, "y1": p.y1_mm, "x2": p.x2_mm, "y2": p.y2_mm}
    else:
        a2 = p.start_rad + p.sweep_rad
        geometry = {"type": "arc", "cx": p.cx_mm, "cy": p.cy_mm, "r": p.r_mm, "a1": p.start_rad, "a2": a2}
    return geometry | {"width": p.width_mm, "kind": p.role.value, "start": list(start), "end": list(end)}


def _phase(phase: Phase | None) -> int | None:
    return None if phase is None else PHASE_INDEX[phase]


def _objects_and_primitives(
    paths: tuple[CopperPath, ...], layer_index: Mapping[str, int]
) -> tuple[list[JsonValue], list[JsonValue]]:
    objects: list[JsonValue] = []
    primitives: list[JsonValue] = []
    for path in paths:
        first_id = len(primitives)
        for seq, p in enumerate(path.primitives):
            primitives.append(
                _primitive_geometry(p)
                | {"id": len(primitives), "layer": layer_index[path.layer], "object": path.id, "seq": seq}
                | {"net": path.net, "phase": _phase(path.phase), "coil": path.element}
            )
        objects.append(
            {"id": path.id, "kind": None, "layer": layer_index[path.layer], "net": path.net}
            | {"phase": _phase(path.phase), "coil": path.element, "touch_vias": []}
            | {"primitive_ids": list(range(first_id, len(primitives)))}
        )
    return objects, primitives


def _via_record(v: Via, layer_index: Mapping[str, int]) -> JsonValue:
    record: dict[str, JsonValue] = {
        "id": v.id,
        "x": v.x_mm,
        "y": v.y_mm,
        "drill": v.drill_mm,
        "pad": v.pad_mm,
        "layer_from": layer_index[v.layer_from],
        "layer_to": layer_index[v.layer_to],
        "role": v.role.value,
        "net": v.net,
        "phase": None,
        "terminal": v.role is ViaRole.TERMINAL,
        "label": "",
    }
    return record


def _pad_record(p: Pad, layer_index: Mapping[str, int]) -> JsonValue:
    record: dict[str, JsonValue] = {
        "id": p.id,
        "x": p.x_mm,
        "y": p.y_mm,
        "shape": p.shape,
        "w": p.width_mm,
        "h": p.height_mm,
        "rot": p.rotation_rad,
        "drill": p.drill_mm,
        "smd": p.drill_mm == 0,
        "layer": None if p.layer is None else layer_index[p.layer],
        "net": p.net,
        "label": p.label,
    }
    return record


def _layer_record(index: int, name: str, z_mm: float) -> JsonValue:
    record: dict[str, JsonValue] = {"index": index, "name": name, "z": z_mm}
    return record | {"copper_t": None, "role": None, "pair": None, "phase": None}


def _circuits(layout: Layout, layer_index: Mapping[str, int]) -> list[JsonValue]:
    path_by_id = {path.id: path for path in layout.paths}
    circuits: list[JsonValue] = []
    for pc in layout.circuit.phases:
        elements: list[JsonValue] = []
        for group in pc.groups:
            members: list[JsonValue] = [
                {"object": pid, "layer": layer_index[path_by_id[pid].layer], "direction": path_by_id[pid].polarity}
                for member in group.members
                for pid in member.path_ids
            ]
            vias: list[JsonValue] = [vid for member in group.members for vid in member.via_ids]
            elements.append({"members": members, "vias": vias})
        circuits.append(
            {"phase": PHASE_INDEX[pc.phase], "elements": elements, "terminals": {"plus": None, "minus": None}}
        )
    return circuits


def dump_layout(layout: Layout, *, case_id: str, design: DesignParameters | None = None) -> dict[str, JsonValue]:
    """Return the board dump of ``layout`` as plain JSON data (non-finite floats still as floats).

    With ``design``, ``params`` is the design in its project-file form and ``params_sha256`` its design hash.
    """
    layer_index = {name: i for i, name in enumerate(layout.copper_layers)}
    objects, primitives = _objects_and_primitives(layout.paths, layer_index)
    outline = layout.outline
    return {
        "format": BOARD_DUMP_FORMAT,
        "format_version": BOARD_DUMP_VERSION,
        "producer": {
            "name": "embodic",
            "version": embodic.__version__,
            "engine_sha256": None,
            "runtime": f"CPython {platform.python_version()}",
        },
        "case_id": case_id,
        "params": None if design is None else design_document(design),
        "params_sha256": None if design is None else design_hash(design),
        "units": {"length": "mm", "angle": "rad"},
        "frame": BOARD_DUMP_SCHEMA["frame"],
        "layers": [_layer_record(i, name, layout.copper_z_mm[name]) for i, name in enumerate(layout.copper_layers)],
        "primitives": primitives,
        "objects": objects,
        "vias": [_via_record(v, layer_index) for v in layout.vias],
        "pads": [_pad_record(p, layer_index) for p in layout.pads],
        "outline": {
            "board": [_primitive_geometry(p) for p in outline.outer],
            "cutouts": [[_primitive_geometry(p) for p in loop] for loop in outline.cutouts],
            "holes": [{"x": h.x_mm, "y": h.y_mm, "dia": h.diameter_mm} for h in outline.holes],
        },
        "circuits": _circuits(layout, layer_index),
        "drc": None,
    }


def _scalar(value: object) -> JsonValue:
    if value is None or isinstance(value, bool | int | float | str):
        return value
    raise TypeError(f"{type(value).__name__} has no board-dump form")


def _encode(value: Any) -> JsonValue:
    if isinstance(value, float) and not math.isfinite(value):
        return {NONFINITE_TAG: "nan" if math.isnan(value) else ("inf" if value > 0 else "-inf")}
    if isinstance(value, list | tuple):
        return [_encode(v) for v in value]
    if isinstance(value, Mapping):
        return {k: _encode(v) for k, v in value.items()}
    return _scalar(value)


def _decode(value: Any) -> JsonValue:
    if isinstance(value, list):
        return [_decode(v) for v in value]
    if isinstance(value, dict):
        if set(value) == {NONFINITE_TAG}:
            return {"inf": math.inf, "-inf": -math.inf, "nan": math.nan}[value[NONFINITE_TAG]]
        return {k: _decode(v) for k, v in value.items()}
    return _scalar(value)


def _reject_constant(token: str) -> float:
    raise ValueError(f"non-standard JSON token {token}; board dumps tag non-finite numbers with {NONFINITE_TAG!r}")


def encode_board_dump(dump: Mapping[str, JsonValue]) -> str:
    """Return the canonical text: sorted keys, one-space indent, tagged non-finite numbers, trailing newline."""
    return json.dumps(_encode(dump), sort_keys=True, indent=1, allow_nan=False) + "\n"


def decode_board_dump(text: str) -> dict[str, JsonValue]:
    """Parse board-dump text and decode non-finite tags; bare ``NaN`` or ``Infinity`` tokens are an error."""
    dump = _decode(json.loads(text, parse_constant=_reject_constant))
    if not isinstance(dump, dict) or dump.get("format") != BOARD_DUMP_FORMAT or dump.get("format_version") != 1:
        raise ValueError(f"not an {BOARD_DUMP_FORMAT} v{BOARD_DUMP_VERSION} document")
    return dump


def write_board_dump(layout: Layout, path: Path, *, case_id: str, design: DesignParameters | None = None) -> None:
    """Write the board dump of ``layout`` to ``path`` as UTF-8 (side effect: one file)."""
    path.write_text(encode_board_dump(dump_layout(layout, case_id=case_id, design=design)), encoding="utf-8")


def read_board_dump(path: Path) -> Mapping[str, JsonValue]:
    """Return the parsed JSON with non-finite numbers decoded ({"$f": "inf"} -> math.inf)."""
    return decode_board_dump(path.read_text(encoding="utf-8"))
