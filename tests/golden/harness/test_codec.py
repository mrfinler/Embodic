"""Self-tests for the non-finite codec and fixture loading."""

import json
import math
import shutil
from pathlib import Path

import pytest

from harness import DATA_DIR, dumps, load_case, loads

pytestmark = pytest.mark.req("REQ-F-40")


def _same(a: object, b: object) -> bool:
    """Structural equality that treats NaN as equal to NaN and tells -0.0 from 0.0."""
    if isinstance(a, float) and isinstance(b, float):
        if math.isnan(a) or math.isnan(b):
            return math.isnan(a) and math.isnan(b)
        return a == b and math.copysign(1.0, a) == math.copysign(1.0, b)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b, strict=True))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_same(a[k], b[k]) for k in a)
    return type(a) is type(b) and a == b


def test_codec_round_trip_preserves_nonfinite_and_signed_zero() -> None:
    """Catch an encoder that turns NaN or Infinity into null, or drops the sign of -0.0."""
    value = {
        "scalars": [math.inf, -math.inf, math.nan, -0.0, 0.0, 5e-324, 1.7976931348623157e308, -2.5],
        "nested": {"at": None, "clearance": math.inf, "points": [[math.nan, -0.0], [1, 2]]},
        "text": "side",
        "flag": True,
    }
    text = dumps(value)
    assert "NaN" not in text and "Infinity" not in text
    assert _same(loads(text), value)


def test_codec_writes_strict_json() -> None:
    """Catch fixtures that only parse with Python's non-standard NaN and Infinity tokens."""
    text = dumps([math.inf, math.nan])
    assert json.loads(text, parse_constant=lambda token: pytest.fail(f"bare token {token}")) == [
        {"$f": "inf"},
        {"$f": "nan"},
    ]


@pytest.mark.parametrize("text", ['{"x": NaN}', "[Infinity]", "[-Infinity]"])
def test_codec_rejects_bare_nonfinite_tokens(text: str) -> None:
    """Catch a dumper regression that writes bare NaN or Infinity instead of the tag."""
    with pytest.raises(ValueError, match="non-standard JSON token"):
        loads(text)


@pytest.mark.parametrize("text", ['{"$f": "infinity"}', '{"$f": "inf", "x": 1}', '{"$f": 1}'])
def test_codec_rejects_malformed_tags(text: str) -> None:
    """Catch a malformed tag being read as an ordinary object or a wrong number."""
    with pytest.raises(ValueError, match="non-finite tag"):
        loads(text)


def test_codec_decodes_nonfinite_values_written_by_node() -> None:
    """Catch a decoder that misreads the tags the Node dumper writes (swapped signs, NaN as inf)."""
    assert _same(load_case(DATA_DIR / "m1" / "primstart-arc-r-inf.json").calls[0].output, [math.inf, math.nan])
    assert load_case(DATA_DIR / "m1" / "primlength-arc-r-inf.json").calls[0].output == math.inf
    assert math.isnan(load_case(DATA_DIR / "m1" / "ptsegdist-nan-point.json").calls[0].output)
    assert load_case(DATA_DIR / "m1" / "ptsegdist-inf-point.json").calls[0].inputs["px"] == -math.inf
    assert load_case(DATA_DIR / "m1" / "padsclearance-empty.json").calls[0].output == {
        "at": None,
        "clearance": math.inf,
    }


def test_codec_keeps_signed_zero_written_by_node() -> None:
    """Catch -0 collapsing to 0 between Node and Python (it decides atan2 = -pi against +pi)."""
    start = load_case(DATA_DIR / "m1" / "primstart-line-signed-zero.json").calls[0].output
    assert [math.copysign(1.0, v) for v in start] == [-1.0, -1.0]
    call = load_case(DATA_DIR / "m1" / "tfpoint-negative-x-signed-zero.json").calls[0]
    assert math.copysign(1.0, call.inputs["y"]) == -1.0
    assert call.output[1] < 0.0


def test_load_case_rejects_fixture_under_another_name(tmp_path: Path) -> None:
    """Catch a copied or renamed fixture silently answering for a different case id."""
    copy = tmp_path / "primlength-line-zero.json"
    shutil.copy(DATA_DIR / "m1" / "primlength-line-3-4-5.json", copy)
    with pytest.raises(ValueError, match="case_id"):
        load_case(copy)


def test_load_case_rejects_unknown_format(tmp_path: Path) -> None:
    """Catch a board dump or other JSON file being loaded as a golden case."""
    path = tmp_path / "x.json"
    path.write_text('{"format": "embodic.board-dump", "format_version": 1, "case_id": "x"}')
    with pytest.raises(ValueError, match="format"):
        load_case(path)
