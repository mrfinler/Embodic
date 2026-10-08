"""UT-GEO-20: the generator interface (interfaces.md section 6, ADR-0012, REQ-F-19)."""

from typing import ClassVar

import pytest
from tests.unit.generators.default_example import default_design

import embodic.generators
from embodic.drc import run_drc
from embodic.errors import Unbuildable
from embodic.generators import GENERATORS, build_layout, generate_spiral
from embodic.generators.base import Generator
from embodic.geometry.layout import BoardStack
from embodic.io.board_dump import decode_board_dump, dump_layout, encode_board_dump
from embodic.model.design import DesignParameters
from embodic.model.vocabulary import TopologyKind
from embodic.physics import analyse
from embodic.results import Registry, load_registry


class _StubGenerator:
    """A generator from outside the package: it returns a fixed stack and knows nothing else."""

    kind: ClassVar[TopologyKind] = TopologyKind.SPIRAL

    def __init__(self, stack: BoardStack) -> None:
        self.stack = stack
        self.calls = 0

    def generate(self, design: DesignParameters, registry: Registry) -> BoardStack | Unbuildable:
        del design, registry
        self.calls += 1
        return self.stack


@pytest.mark.req("REQ-F-19")
def test_ut_geo_20_a_generator_registered_at_runtime_passes_drc_physics_and_the_board_dump(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UT-GEO-20: a stub registered in GENERATORS at runtime is dispatched to, and every consumer accepts its stack.

    DRC, physics and the board dump give the same results as on the shipped generator's stack. Catches a consumer
    that bypasses build_layout, or that reads anything but the BoardStack contract.
    """
    registry = load_registry()
    design = default_design()
    shipped = generate_spiral(design, registry)
    assert isinstance(shipped, BoardStack)
    stub = _StubGenerator(shipped)
    as_protocol: Generator = stub
    monkeypatch.setattr(embodic.generators, "GENERATORS", {**GENERATORS, as_protocol.kind: as_protocol.generate})

    stack = build_layout(design, registry)
    assert stub.calls == 1 and isinstance(stack, BoardStack) and stack.stack_hash == shipped.stack_hash
    report = run_drc(stack.boards[0], design.drc_rules)
    assert report is not None and report.violation_count == 0
    result, reference = analyse(design, stack, {}, registry), analyse(design, shipped, {}, registry)
    assert result is not None and reference is not None
    assert result.ke_line_peak_v_s_per_rad.value == reference.ke_line_peak_v_s_per_rad.value > 0.0
    dump = dump_layout(stack.boards[0], case_id="ut-geo-20")
    assert decode_board_dump(encode_board_dump(dump)) == dump
