"""The `design` keyword of the board dump (interfaces.md 9.2, U-M2f): params and params_sha256."""

import hashlib
from pathlib import Path

import pytest

from embodic.generators import build_layout
from embodic.geometry.layout import BoardStack
from embodic.io.board_dump import dump_layout, read_board_dump, write_board_dump
from embodic.io.canonical import dumps_canonical
from embodic.io.examples import load_example
from embodic.results import load_registry


@pytest.mark.req("REQ-F-15")
def test_board_dump_carries_the_design_and_a_hash_a_second_reader_can_check(tmp_path: Path) -> None:
    """Catches params that are not the design, or a params_sha256 a reader cannot recompute from params."""
    _, design = load_example("spiral_12c16p_default")
    stack = build_layout(design, load_registry())
    assert isinstance(stack, BoardStack)
    layout = stack.boards[0]
    assert dump_layout(layout, case_id="cf11")["params"] is None
    path = tmp_path / "cf11.board.json"
    write_board_dump(layout, path, case_id="cf11", design=design)
    dump = read_board_dump(path)
    params = dump["params"]
    assert isinstance(params, dict) and params["rotor"]["poles"] == 16  # type: ignore[index]
    assert dump["params_sha256"] == "sha256:" + hashlib.sha256(dumps_canonical(params)).hexdigest()
