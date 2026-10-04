"""Golden fixture loading and the non-finite encoding shared with ``tools/golden/dump_xcoil.mjs``.

JSON has no Infinity or NaN, so both producers write ``{"$f": "inf"}``, ``{"$f": "-inf"}`` and ``{"$f": "nan"}``
(test_plan.md section 3). Negative zero is written as the number ``-0.0``.
"""

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

JsonValue: TypeAlias = bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"] | None

NONFINITE_TAG = "$f"
FIXTURE_FORMAT = "embodic.golden-case"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"

_DECODED = {"inf": math.inf, "-inf": -math.inf, "nan": math.nan}


def decode_nonfinite(value: JsonValue) -> JsonValue:
    """Replace every ``{"$f": ...}`` tag with the float it stands for; reject malformed tags."""
    if isinstance(value, list):
        return [decode_nonfinite(v) for v in value]
    if isinstance(value, dict):
        if NONFINITE_TAG not in value:
            return {k: decode_nonfinite(v) for k, v in value.items()}
        tag = value[NONFINITE_TAG]
        if len(value) != 1 or not isinstance(tag, str) or tag not in _DECODED:
            raise ValueError(f"malformed non-finite tag {value!r}")
        return _DECODED[tag]
    return value


def encode_nonfinite(value: object) -> JsonValue:
    """Replace every infinite or NaN float with its tag; tuples become lists."""
    if isinstance(value, float) and not math.isfinite(value):
        return {NONFINITE_TAG: "nan" if math.isnan(value) else ("inf" if value > 0 else "-inf")}
    if isinstance(value, list | tuple):
        return [encode_nonfinite(v) for v in value]
    if isinstance(value, dict):
        return {str(k): encode_nonfinite(v) for k, v in value.items()}
    if value is None or isinstance(value, bool | int | float | str):
        return value
    raise TypeError(f"{type(value).__name__} has no JSON form")


def _reject_constant(token: str) -> float:
    raise ValueError(f"non-standard JSON token {token}; fixtures must use the {NONFINITE_TAG!r} tag")


def dumps(value: object) -> str:
    """Encode ``value`` as strict JSON with tagged non-finite numbers and sorted keys."""
    return json.dumps(encode_nonfinite(value), allow_nan=False, sort_keys=True)


def loads(text: str) -> JsonValue:
    """Parse strict JSON and decode non-finite tags; bare ``NaN`` or ``Infinity`` tokens are an error."""
    return decode_nonfinite(json.loads(text, parse_constant=_reject_constant))


@dataclass(frozen=True, slots=True)
class GoldenCall:
    """One Xcoil call: the inputs as passed and the decoded output."""

    inputs: Mapping[str, JsonValue]
    output: JsonValue


@dataclass(frozen=True, slots=True)
class GoldenCase:
    """One fixture file written by the dumper."""

    case_id: str
    fn: str
    eq_ids: tuple[str, ...]
    tags: frozenset[str]
    note: str
    engine_sha256: str
    calls: tuple[GoldenCall, ...]


def load_case(path: Path) -> GoldenCase:
    """Load and check one fixture; the file stem must equal its ``case_id``."""
    raw = loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("format") != FIXTURE_FORMAT or raw.get("format_version") != 1:
        raise ValueError(f"{path}: not an {FIXTURE_FORMAT} v1 file (format, format_version)")
    if raw["case_id"] != path.stem:
        raise ValueError(f"{path}: case_id {raw['case_id']!r} does not match the file name")
    return GoldenCase(
        case_id=raw["case_id"],
        fn=raw["fn"],
        eq_ids=tuple(raw["eq_ids"]),
        tags=frozenset(raw["tags"]),
        note=raw["note"],
        engine_sha256=raw["producer"]["engine_sha256"],
        calls=tuple(GoldenCall(inputs=c["inputs"], output=c["output"]) for c in raw["calls"]),
    )


def load_area(area: str, data_dir: Path = DATA_DIR) -> dict[str, GoldenCase]:
    """Load every fixture of one area (``tests/golden/data/<area>``), keyed by case id in sorted order."""
    paths = sorted((data_dir / area).glob("*.json"))
    if not paths:
        raise FileNotFoundError(f"no fixtures in {data_dir / area}")
    return {p.stem: load_case(p) for p in paths}
