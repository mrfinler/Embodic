"""Layout hash: SHA-256 over the canonical JSON of the copper, vias, pads and outline (UT-GEO-15)."""

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from embodic.geometry.layout import BoardOutline, Pad, Via
    from embodic.geometry.paths import CopperPath


def _canonical(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: _canonical(getattr(value, f.name)) for f in fields(value)} | {"$t": type(value).__name__}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_canonical(v) for v in value]
    return value


def compute_layout_hash(
    paths: Sequence["CopperPath"], vias: Sequence["Via"], pads: Sequence["Pad"], outline: "BoardOutline"
) -> str:
    """Return ``"sha256:<hex>"`` of sorted-key JSON with shortest round-trip floats; NaN or infinity raises."""
    document = _canonical({"paths": paths, "vias": vias, "pads": pads, "outline": outline})
    text = json.dumps(document, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()
