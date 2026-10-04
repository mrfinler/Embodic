"""Independent reader for ``embodic.board-dump`` v1 (interfaces.md section 9.2, port notes section 7.5).

Parses the JSON into Agent 4's own records and collects every contract violation it finds instead of stopping at the
first. It never imports embodic.
"""

import json
import math
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from typing import Any

from records import Arc, Line, Prim, end_point, start_point

FORMAT = "embodic.board-dump"
FORMAT_VERSION = 1
ENDPOINT_TOL_MM = 1e-9

TOP_KEYS = frozenset(
    {"format", "format_version", "producer", "case_id", "params", "params_sha256", "units", "frame", "layers",
     "primitives", "objects", "vias", "pads", "outline", "circuits", "drc"}
)  # fmt: skip
LAYER_KEYS = frozenset({"index", "name", "kicad_name", "z", "copper_t", "role", "pair", "phase"})
COMMON_PRIM_KEYS = frozenset(
    {"id", "type", "layer", "start", "end", "width", "kind", "object", "seq", "net", "phase", "coil"}
)
GEOMETRY_KEYS = {"line": frozenset({"x1", "y1", "x2", "y2"}), "arc": frozenset({"cx", "cy", "r", "a1", "a2"})}
OBJECT_KEYS = frozenset({"id", "kind", "layer", "net", "phase", "coil", "primitive_ids", "touch_vias"})
VIA_KEYS = frozenset(
    {"id", "x", "y", "drill", "pad", "layer_from", "layer_to", "role", "net", "phase", "terminal", "label"}
)
PAD_KEYS = frozenset({"id", "x", "y", "shape", "w", "h", "rot", "drill", "smd", "layer", "net", "label"})
OUTLINE_KEYS = frozenset({"board", "cutouts", "holes"})
CIRCUIT_KEYS = frozenset({"elements", "terminals"})
DRC_KEYS = frozenset({"rule", "values", "pass_d006", "producer_flag"})

_NON_FINITE = {"inf": math.inf, "-inf": -math.inf, "nan": math.nan}


class DumpError(ValueError):
    """The dump breaks the v1 contract; ``problems`` lists every finding."""

    def __init__(self, problems: list[str]) -> None:
        super().__init__("; ".join(problems))
        self.problems = problems


@dataclass(frozen=True, slots=True)
class DumpPrimitive:
    """One copper primitive with the dump's bookkeeping fields."""

    id: int
    layer: int
    prim: Prim
    kind: str
    object: int
    seq: int
    net: str
    phase: int | None
    coil: int | None


@dataclass(frozen=True, slots=True)
class DumpVia:
    """One via; its copper is a disc of diameter ``pad``."""

    id: int
    x: float
    y: float
    drill: float
    pad: float
    role: str
    net: str


@dataclass(frozen=True, slots=True)
class BoardDump:
    """The parsed dump. ``raw`` keeps the decoded JSON for fields no check reads yet."""

    layers: tuple[int, ...]
    primitives: tuple[DumpPrimitive, ...]
    paths: Mapping[int, tuple[DumpPrimitive, ...]]  # object id -> primitives in ``seq`` order
    vias: tuple[DumpVia, ...]
    raw: Mapping[str, Any]


def decode_non_finite(value: Any) -> Any:
    """Replace ``{"$f": "inf" | "-inf" | "nan"}`` by the float, recursively (interfaces.md section 9.2)."""
    if isinstance(value, dict):
        if value.keys() == {"$f"} and value["$f"] in _NON_FINITE:
            return _NON_FINITE[value["$f"]]
        return {key: decode_non_finite(item) for key, item in value.items()}
    if isinstance(value, list):
        return [decode_non_finite(item) for item in value]
    return value


def read_board_dump(path: Path) -> BoardDump:
    """Read and validate a dump file."""
    return parse_board_dump(json.loads(path.read_text(encoding="utf-8")))


def parse_board_dump(document: Mapping[str, Any]) -> BoardDump:
    """Validate a decoded JSON document against v1 and return the records; raise DumpError with all problems."""
    doc = decode_non_finite(document)
    problems = _missing(doc, TOP_KEYS, "dump")
    if problems:
        raise DumpError(problems)
    if doc["format"] != FORMAT or doc["format_version"] != FORMAT_VERSION:
        problems.append(
            f"format must be {FORMAT!r} version {FORMAT_VERSION}, got {doc['format']!r} {doc['format_version']!r}"
        )
    if doc["units"] != {"length": "mm", "angle": "rad"}:
        problems.append(f"units must be mm and rad, got {doc['units']!r}")
    problems += _check_records(doc)
    layers = tuple(layer["index"] for layer in doc["layers"] if "index" in layer)
    parsed = (_primitive(rec, layers, problems) for rec in doc["primitives"] if not _missing_prim(rec))
    primitives = tuple(p for p in parsed if p is not None)
    problems += _check_membership(doc, primitives)
    if problems:
        raise DumpError(problems)
    paths = {
        obj["id"]: tuple(sorted((p for p in primitives if p.object == obj["id"]), key=lambda p: p.seq))
        for obj in doc["objects"]
    }
    vias = tuple(DumpVia(v["id"], v["x"], v["y"], v["drill"], v["pad"], v["role"], v["net"]) for v in doc["vias"])
    return BoardDump(layers, primitives, paths, vias, doc)


def path_adjacent(dump: BoardDump) -> set[frozenset[int]]:
    """Primitive id pairs that are consecutive in one object path, the only trace pairs D-006 exempts."""
    pairs: set[frozenset[int]] = set()
    for path in dump.paths.values():
        pairs.update(frozenset((a.id, b.id)) for a, b in pairwise(path))
    return pairs


def _missing(record: Any, keys: frozenset[str], where: str) -> list[str]:
    if not isinstance(record, dict):
        return [f"{where}: expected an object, got {type(record).__name__}"]
    absent = sorted(keys - record.keys())
    return [f"{where}: missing {', '.join(absent)}"] if absent else []


def _missing_prim(rec: Any) -> bool:
    if not isinstance(rec, dict) or COMMON_PRIM_KEYS - rec.keys():
        return True
    geometry = GEOMETRY_KEYS.get(rec["type"])
    return geometry is None or bool(geometry - rec.keys())


def _check_records(doc: Mapping[str, Any]) -> list[str]:
    problems: list[str] = []
    for name, keys in (("layers", LAYER_KEYS), ("objects", OBJECT_KEYS), ("vias", VIA_KEYS), ("pads", PAD_KEYS)):
        for k, rec in enumerate(doc[name]):
            problems += _missing(rec, keys, f"{name}[{k}]")
    for k, rec in enumerate(doc["primitives"]):
        problems += _missing(rec, COMMON_PRIM_KEYS, f"primitives[{k}]")
        if isinstance(rec, dict) and "type" in rec:
            geometry = GEOMETRY_KEYS.get(rec["type"])
            if geometry is None:
                problems.append(f"primitives[{k}]: type must be 'line' or 'arc', got {rec['type']!r}")
            else:
                problems += _missing(rec, geometry, f"primitives[{k}] ({rec['type']})")
    problems += _missing(doc["outline"], OUTLINE_KEYS, "outline")
    for k, rec in enumerate(doc["circuits"]):
        problems += _missing(rec, CIRCUIT_KEYS, f"circuits[{k}]")
    if doc["drc"] is not None:
        problems += _missing(doc["drc"], DRC_KEYS, "drc")
    for name in ("layers", "primitives", "objects", "vias", "pads"):
        key = "index" if name == "layers" else "id"
        counts = Counter(rec.get(key) for rec in doc[name] if isinstance(rec, dict))
        problems += [f"{name}: {key} {value!r} appears {n} times" for value, n in counts.items() if n > 1]
    return problems


def _primitive(rec: Mapping[str, Any], layers: tuple[int, ...], problems: list[str]) -> DumpPrimitive | None:
    where = f"primitive {rec['id']}"
    if rec["layer"] not in layers:
        problems.append(f"{where}: layer {rec['layer']!r} is not in layers[]")
    numbers = [rec["width"], *(rec[k] for k in GEOMETRY_KEYS[rec["type"]])]
    if not all(isinstance(x, int | float) and math.isfinite(x) for x in numbers):
        problems.append(f"{where}: geometry and width must be finite numbers")
        return None
    if rec["width"] < 0:
        problems.append(f"{where}: negative width {rec['width']!r}")
    if rec["type"] == "line":
        prim: Prim = Line(rec["x1"], rec["y1"], rec["x2"], rec["y2"], rec["width"])
    else:
        prim = Arc(rec["cx"], rec["cy"], rec["r"], rec["a1"], rec["a2"] - rec["a1"], rec["width"])
    problems += _check_ends(where, prim, rec["start"], rec["end"])
    return DumpPrimitive(rec["id"], rec["layer"], prim, rec["kind"], rec["object"], rec["seq"], rec["net"],
                         rec["phase"], rec["coil"])  # fmt: skip


def _check_ends(where: str, prim: Prim, start: Any, end: Any) -> list[str]:
    problems = []
    for label, stated, computed in (("start", start, start_point(prim)), ("end", end, end_point(prim))):
        if not _is_point(stated):
            problems.append(f"{where}: {label} must be [x, y]")
        elif not math.dist(stated, computed) <= ENDPOINT_TOL_MM:
            problems.append(
                f"{where}: stated {label} {stated} is {math.dist(stated, computed):.3g} mm from the geometry"
            )
    return problems


def _is_point(value: Any) -> bool:
    return isinstance(value, list) and len(value) == 2 and all(isinstance(x, int | float) for x in value)


def _check_membership(doc: Mapping[str, Any], primitives: tuple[DumpPrimitive, ...]) -> list[str]:
    """Every primitive belongs to exactly one object, and its ``object`` field names that object."""
    owners: dict[int, list[int]] = {}
    for obj in doc["objects"]:
        if isinstance(obj, dict) and "primitive_ids" in obj:
            for pid in obj["primitive_ids"]:
                owners.setdefault(pid, []).append(obj.get("id"))
    problems = []
    for p in primitives:
        listed = owners.get(p.id, [])
        if len(listed) != 1:
            problems.append(f"primitive {p.id}: listed by {len(listed)} objects {listed}, expected exactly one")
        elif listed[0] != p.object:
            problems.append(f"primitive {p.id}: object field {p.object} but listed by object {listed[0]}")
    known = {p.id for p in primitives}
    problems += [f"objects list unknown primitive {pid}" for pid in sorted(owners.keys() - known, key=str)]
    return problems
