"""REQ-F-15: a negative zero in any float field leaves the design hash and the saved bytes as the positive zero has them.

Catches a canonical form that writes "-0.0" for a design that compares equal to one with "0.0" (0.0 == -0.0 in Python).
"""

import dataclasses
import re
from pathlib import Path

import pytest

from embodic.io.canonical import design_hash, dumps_canonical
from embodic.io.examples import list_examples, load_example
from embodic.io.project import ProjectFile, load_project, save_project
from embodic.model.design import DesignParameters
from embodic.model.schema import ValueType, design_from_json, design_values, leaves, pattern_of, unflatten
from tests.unit.property.strategies import cf11

STAMP = "2026-10-08T12:00:00Z"
EXAMPLE_IDS = [info.example_id for info in list_examples()]
NEGATIVE_ZERO = re.compile(r"(?<![0-9.eE+-])-0\.0(?![0-9eE.])")
ANGLE = "/winding/coil/first_coil_angle_rad"


def _float_pointers(design: DesignParameters) -> list[str]:
    """Return the pointer of every float field of a design, a float field that holds None included."""
    kinds = {leaf.pattern: leaf.value_type for leaf in leaves(design.topology)}
    return [
        pointer
        for pointer, value in design_values(design).items()
        if isinstance(value, float) or (value is None and kinds[pattern_of(pointer)] is ValueType.FLOAT)
    ]


def _with_value(design: DesignParameters, pointer: str, value: float) -> DesignParameters:
    values = design_values(design)
    values[pointer] = value
    return design_from_json(design.topology, unflatten(values))


def _with_first_coil_angle(angle_rad: float) -> DesignParameters:
    return _with_value(cf11(), ANGLE, angle_rad)


@pytest.mark.req("REQ-F-15")
@pytest.mark.parametrize("example_id", EXAMPLE_IDS)
def test_f15_negative_zero_in_any_float_field_leaves_the_design_hash_unchanged(example_id: str) -> None:
    """Catches a float field whose -0.0 reaches the canonical bytes: its design equals the 0.0 design, its hash not."""
    design = load_example(example_id)[1]
    assert design_from_json(design.topology, unflatten(design_values(design))) == design
    pointers = _float_pointers(design)
    assert pointers != []
    moved = []
    for pointer in pointers:
        positive, negative = _with_value(design, pointer, 0.0), _with_value(design, pointer, -0.0)
        assert positive == negative
        if design_hash(positive) != design_hash(negative):
            moved.append(pointer)
    assert moved == []


@pytest.mark.req("REQ-F-15")
def test_f15_the_canonical_bytes_write_every_negative_zero_as_zero() -> None:
    """Catches a canonical encoder that keeps the sign of a zero, in a dict, a list or a list of dicts."""
    data = {"a": -0.0, "b": [-0.0, {"c": -0.0}], "d": -1e-300, "e": 0, "f": 0.0, "g": False}
    assert dumps_canonical(data) == b'{"a":0.0,"b":[0.0,{"c":0.0}],"d":-1e-300,"e":0,"f":0.0,"g":false}'


@pytest.mark.req("REQ-F-15")
def test_f15_equal_designs_save_equal_bytes_and_a_saved_file_has_no_negative_zero(tmp_path: Path) -> None:
    """Catches a project file that writes "-0.0" for a design equal to the one that writes "0.0"."""
    positive, negative = _with_first_coil_angle(0.0), _with_first_coil_angle(-0.0)
    assert positive == negative
    files = {}
    for name, design in (("positive", positive), ("negative", negative)):
        path = tmp_path / f"{name}.embodic.json"
        save_project(path, ProjectFile(design=design, origin=None), saved_utc=STAMP)
        files[name] = path.read_bytes()
    assert files["negative"] == files["positive"]
    assert NEGATIVE_ZERO.search(files["negative"].decode()) is None


@pytest.mark.req("REQ-F-15")
def test_f15_save_load_save_is_byte_identical_with_a_negative_zero_in_the_design(tmp_path: Path) -> None:
    """Catches a second save that differs from the first when the design holds -0.0."""
    first, second = tmp_path / "a.embodic.json", tmp_path / "b.embodic.json"
    save_project(first, ProjectFile(design=_with_first_coil_angle(-0.0), origin=None), saved_utc=STAMP)
    loaded, issues = load_project(first)
    assert loaded is not None, issues
    save_project(second, loaded, saved_utc=STAMP)
    assert first.read_bytes() == second.read_bytes()


@pytest.mark.req("REQ-F-15")
def test_f15_a_file_saved_with_a_negative_zero_is_saved_again_as_the_zero_file(tmp_path: Path) -> None:
    """Catches a file written before the fix ("-0.0" in the angle) that keeps its sign or hash when saved again."""
    zero_file, legacy_file, resaved = (tmp_path / f"{n}.embodic.json" for n in ("zero", "legacy", "resaved"))
    save_project(zero_file, ProjectFile(design=_with_first_coil_angle(0.0), origin=None), saved_utc=STAMP)
    text = zero_file.read_text(encoding="utf-8")
    assert text.count('"first_coil_angle_deg": 0.0') == 1
    legacy_file.write_text(text.replace('"first_coil_angle_deg": 0.0', '"first_coil_angle_deg": -0.0'), encoding="utf-8")
    loaded, issues = load_project(legacy_file)
    assert loaded is not None, issues
    save_project(resaved, loaded, saved_utc=STAMP)
    assert resaved.read_bytes() == zero_file.read_bytes()
