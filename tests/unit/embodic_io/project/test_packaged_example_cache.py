"""packaged_example reads each example file once per process, and what it returns cannot be changed by a caller."""

import dataclasses
import enum
import pathlib
import types

import pytest

from embodic.io.examples import examples_dir, list_examples, load_example, packaged_example

EXAMPLE_IDS = tuple(info.example_id for info in list_examples())
LOOKUPS = 20
IMMUTABLE_LEAVES = (str, int, float, bool, type(None), enum.Enum, frozenset, types.MappingProxyType)


def _mutable_parts(value: object, path: str) -> list[str]:
    """Return the path of every part of `value` that a caller could change in place."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        if not value.__dataclass_params__.frozen:  # type: ignore[attr-defined]
            return [f"{path}: unfrozen {type(value).__name__}"]
        return [
            p for f in dataclasses.fields(value) for p in _mutable_parts(getattr(value, f.name), f"{path}.{f.name}")
        ]
    if isinstance(value, tuple):
        return [p for i, item in enumerate(value) for p in _mutable_parts(item, f"{path}[{i}]")]
    return [] if isinstance(value, IMMUTABLE_LEAVES) else [f"{path}: {type(value).__name__}"]


@pytest.mark.req("REQ-F-25")
def test_repeated_lookups_of_a_packaged_example_read_its_file_at_most_once(monkeypatch: pytest.MonkeyPatch) -> None:
    """Catches a lookup that reads and parses the example file on every call, as every provenance derivation does."""
    ref, design = load_example("spiral_12c10p_d08")
    reads: list[str] = []
    read_text = pathlib.Path.read_text

    def counting(self: pathlib.Path, *args: object, **kwargs: object) -> str:
        if self.parent == examples_dir():
            reads.append(self.name)
        return read_text(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(pathlib.Path, "read_text", counting)
    assert [packaged_example(ref) for _ in range(LOOKUPS)] == [design] * LOOKUPS
    assert len(reads) <= 1, reads


@pytest.mark.req("REQ-F-25")
def test_a_changed_hash_is_still_not_packaged_after_the_example_was_cached() -> None:
    """Catches a cache that answers by example id alone and returns the design for a reference with another hash."""
    ref, _ = load_example("spiral_12c10p_d08")
    assert packaged_example(ref) is not None
    assert packaged_example(dataclasses.replace(ref, example_sha256="sha256:0")) is None
    assert packaged_example(dataclasses.replace(ref, example_id="no_such_example")) is None


@pytest.mark.req("REQ-F-25")
@pytest.mark.parametrize("example_id", EXAMPLE_IDS)
def test_a_caller_cannot_change_the_shared_design_of_an_example(example_id: str) -> None:
    """Catches a mutable field in the design model, which would let one caller corrupt every later lookup."""
    ref, design = load_example(example_id)
    assert _mutable_parts(design, "design") == []
    with pytest.raises(dataclasses.FrozenInstanceError):
        design.name = "changed by a caller"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        ref.example_sha256 = "sha256:0"  # type: ignore[misc]
    assert load_example(example_id)[1].name != "changed by a caller"
