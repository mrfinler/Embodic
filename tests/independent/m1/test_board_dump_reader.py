"""Self-tests of the independent board-dump reader (REQ-F-40, IT-21 input)."""

import copy
import json
import math
from pathlib import Path
from typing import Any

import pytest
from board_dump_reader import DumpError, parse_board_dump, path_adjacent, read_board_dump
from continuity import first_gap
from records import Arc, Line

pytestmark = pytest.mark.req("REQ-F-40")

HERE = Path(__file__).resolve().parent
MINIMAL = HERE / "data" / "minimal_board_dump.json"


def minimal() -> dict[str, Any]:
    """Return a fresh copy of the hand-written dump."""
    return json.loads(MINIMAL.read_text(encoding="utf-8"))


def problems_of(doc: dict[str, Any]) -> list[str]:
    """Return the reader's problem list for a document that must be rejected."""
    with pytest.raises(DumpError) as caught:
        parse_board_dump(doc)
    return caught.value.problems


def test_minimal_dump_parses_into_own_records() -> None:
    """The hand-written dump yields Line, Arc, Line; the arc starts at a1 = pi/2, so its sweep is a2 - a1, not a2."""
    dump = read_board_dump(MINIMAL)
    assert [type(p.prim) for p in dump.primitives] == [Line, Arc, Line]
    assert dump.primitives[1].prim == Arc(0.0, 0.0, 10.0, math.pi / 2, math.pi / 2, 0.2)
    assert [p.id for p in dump.paths[0]] == [0, 1, 2]
    assert dump.vias[0].pad == 0.6
    assert dump.raw["params"]["current_limit_a"] == math.inf


def test_minimal_dump_path_is_continuous_and_adjacency_is_consecutive_only() -> None:
    """Reader output feeds continuity; the only exempt trace pairs are seq neighbours, never (0, 2)."""
    dump = read_board_dump(MINIMAL)
    assert first_gap([p.prim for p in dump.paths[0]]) is None
    assert path_adjacent(dump) == {frozenset((0, 1)), frozenset((1, 2))}


def test_paths_follow_seq_not_file_order() -> None:
    """Catch a reader that orders a path by file position: shuffled records still give seq order."""
    doc = minimal()
    doc["primitives"].reverse()
    assert [p.id for p in parse_board_dump(doc).paths[0]] == [0, 1, 2]


def test_missing_required_fields_are_all_named() -> None:
    """Seeded defects: a missing top key stops parsing; missing record keys are each reported."""
    doc = minimal()
    del doc["circuits"]
    assert problems_of(doc) == ["dump: missing circuits"]
    doc = minimal()
    del doc["primitives"][1]["a2"]
    del doc["vias"][0]["pad"]
    found = problems_of(doc)
    assert "primitives[1] (arc): missing a2" in found
    assert "vias[0]: missing pad" in found


def test_wrong_format_or_units_are_rejected() -> None:
    """A dump in degrees or of another version must not be read as v1 mm/rad."""
    doc = minimal()
    doc["units"]["angle"] = "deg"
    doc["format_version"] = 2
    found = problems_of(doc)
    assert any(p.startswith("format must be") for p in found)
    assert any(p.startswith("units must be") for p in found)


def test_stated_end_point_must_match_geometry() -> None:
    """Seeded defect: the arc's stated end is 1e-6 mm off its geometry (a writer that rounds end points)."""
    doc = minimal()
    doc["primitives"][1]["end"] = [-10.0, 1e-6]
    found = problems_of(doc)
    assert len(found) == 1 and found[0].startswith("primitive 1: stated end")


def test_every_primitive_belongs_to_exactly_one_object() -> None:
    """Seeded defects: a primitive listed by two objects, and one whose object field disagrees with its lister."""
    doc = minimal()
    extra = copy.deepcopy(doc["objects"][0])
    extra.update(id=1, primitive_ids=[2])
    doc["objects"].append(extra)
    assert "primitive 2: listed by 2 objects [0, 1], expected exactly one" in problems_of(doc)
    doc = minimal()
    doc["primitives"][0]["object"] = 7
    assert "primitive 0: object field 7 but listed by object 0" in problems_of(doc)


def test_duplicate_ids_and_unknown_layer_are_rejected() -> None:
    """Ids must be stable and unique within one dump; a primitive's layer must exist."""
    doc = minimal()
    doc["primitives"][2]["id"] = 1
    doc["primitives"][0]["layer"] = 3
    found = problems_of(doc)
    assert "primitives: id 1 appears 2 times" in found
    assert "primitive 0: layer 3 is not in layers[]" in found


def test_non_finite_geometry_is_rejected() -> None:
    """An encoded infinity is legal JSON but not a legal coordinate."""
    doc = minimal()
    doc["primitives"][0]["x2"] = {"$f": "inf"}
    assert "primitive 0: geometry and width must be finite numbers" in problems_of(doc)


def test_golden_layout_fixtures_map_and_parse() -> None:
    """Part 2: every GR-19 layout, mapped by U-M1b's mapper and written by embodic, parses with no contract problem.

    Catches a writer that drops a field, rounds an end point, or lists a primitive under two objects. The objects are
    the ones the mapper gets, each ``ic`` chain on its own; continuity per object is checked in ``test_gr19_drc.py``.
    """
    from gr19 import boards, split_interconnect_chains

    found = boards()
    assert len(found) == 3
    for board in found:
        raw_objects = [obj for layer in split_interconnect_chains(board.raw)["layers"] for obj in layer["objs"]]
        assert len(board.dump.paths) == len(raw_objects)
        assert [len(board.dump.paths[k]) for k in sorted(board.dump.paths)] == [len(o["prims"]) for o in raw_objects]
        assert len(path_adjacent(board.dump)) == sum(len(o["prims"]) - 1 for o in raw_objects)
        assert len(board.dump.vias) == len(board.raw["vias"])
