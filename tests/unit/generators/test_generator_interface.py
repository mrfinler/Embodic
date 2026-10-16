"""UT-GEO-20: the generator interface (interfaces.md section 6, ADR-0012, REQ-F-19)."""

import dataclasses
import datetime
import types
from pathlib import Path
from typing import ClassVar

import pytest
from tests.unit.generators.default_example import default_design

import embodic.generators
import embodic.io.exporters
from embodic.api import compute
from embodic.drc import run_drc
from embodic.errors import Unbuildable
from embodic.generators import GENERATORS, build_layout, generate_spiral
from embodic.generators.base import Generator
from embodic.geometry.layout import BoardStack
from embodic.io.board_dump import decode_board_dump, dump_layout, encode_board_dump
from embodic.io.dxf_writer import write_dxf
from embodic.io.exporters import ExportKind, ExportSummary
from embodic.io.project import ProjectFile, save_project
from embodic.io.readme_writer import write_readme
from embodic.io.report import write_report_pdf
from embodic.io.svg_writer import write_svg
from embodic.model.design import DesignParameters
from embodic.model.outline import ScrewFit, ScrewPattern
from embodic.model.provenance import derive_provenance
from embodic.model.vocabulary import TopologyKind
from embodic.model.winding_specs import SpiralWindingSpec
from embodic.outcome import ComputeOutcome
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


EXPORT_UTC = "2026-10-17T12:00:00Z"


class _ExportClock(datetime.datetime):
    """The export clock frozen at EXPORT_UTC, so two exports of one outcome are byte for byte comparable."""

    @classmethod
    def now(cls, tz: datetime.tzinfo | None = None) -> "_ExportClock":
        return cls(2026, 10, 17, 12, 0, 0, tzinfo=tz)


def _with_screws(pitch_radius_mm: float) -> DesignParameters:
    """CF-11 with six 3.4 mm holes on the coil axes; 15.9 mm is DRC-clean (test_spiral_screws.py closed form)."""
    design = default_design()
    assert isinstance(design.winding, SpiralWindingSpec)
    pattern = ScrewPattern(
        size="M3", fit=ScrewFit.NORMAL, count=6, pitch_radius_mm=pitch_radius_mm, hole_diameter_mm=3.4,
        angle_offset_rad=design.winding.coil.first_coil_angle_rad,
    )  # fmt: skip
    return dataclasses.replace(design, outline=dataclasses.replace(design.outline, screws=(pattern,)))


def _export_every_file(outcome: ComputeOutcome, folder: Path) -> dict[str, tuple[ExportKind | None, bytes]]:
    """Write the D-009 set with the product's writers; return each file's kind (None for the project) and bytes."""
    folder.mkdir()
    written = (
        write_svg(outcome, folder / "motor.svg"),
        write_dxf(outcome, folder / "motor.dxf", "complete"),
        write_dxf(outcome, folder / "motor_outline.dxf", "outline"),
        write_dxf(outcome, folder / "motor_screws.dxf", "screws"),
        write_report_pdf(outcome, folder / "motor_report.pdf"),
    )
    summaries = [s for s in written if isinstance(s, ExportSummary)]
    assert len(summaries) == len(written), written
    summaries.append(write_readme(outcome, summaries, folder / "README.txt"))
    project = folder / "motor.embodic.json"
    assert (
        save_project(project, ProjectFile(design=outcome.design, origin=None), saved_utc=EXPORT_UTC)
        == outcome.design_hash
    )
    files: dict[str, tuple[ExportKind | None, bytes]] = {s.path.name: (s.kind, s.path.read_bytes()) for s in summaries}
    files[project.name] = (None, project.read_bytes())
    return files


def _stub_outcome(design: DesignParameters, stack: BoardStack) -> ComputeOutcome:
    """Compute ``design`` with a stub returning ``stack`` registered in GENERATORS, as UT-GEO-20 registers it."""
    stub = _StubGenerator(stack)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(embodic.generators, "GENERATORS", {**GENERATORS, stub.kind: stub.generate})
        outcome = compute(design, derive_provenance(design, None, ()), registry=load_registry())
    assert stub.calls == 1 and outcome is not None and outcome.boards is not None
    return outcome


@pytest.mark.req("REQ-F-19")
def test_f19_1_every_exporter_writes_the_stub_generators_stack_as_it_writes_the_shipped_one(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """F19-1: SVG, the three DXF parts, the PDF report, the README and the project file of a stub-built outcome.

    Each writer returns its summary, and each file equals the same export of the shipped generator's outcome byte for
    byte under one export clock. A stub stack with the holes moved gives different drawings, so the files come from
    the stack the registered generator returned. Catches an exporter that reads a generator module, rebuilds the board
    from the design, or refuses a stack built outside the package.
    """
    registry = load_registry()
    design = _with_screws(15.9)
    shipped = compute(design, derive_provenance(design, None, ()), registry=registry)
    assert shipped is not None and shipped.boards is not None and shipped.drc is not None
    assert all(report.passed for report in shipped.drc)
    stack = generate_spiral(design, registry)
    moved = generate_spiral(_with_screws(15.5), registry)
    assert isinstance(stack, BoardStack) and isinstance(moved, BoardStack)
    from_stub, from_moved = _stub_outcome(design, stack), _stub_outcome(design, moved)

    clock = types.SimpleNamespace(datetime=_ExportClock, UTC=datetime.UTC)
    monkeypatch.setattr(embodic.io.exporters, "datetime", clock)
    reference = _export_every_file(shipped, tmp_path / "shipped")
    stub_files = _export_every_file(from_stub, tmp_path / "stub")
    moved_files = _export_every_file(from_moved, tmp_path / "moved")

    assert [kind for kind, _ in reference.values()] == [
        ExportKind.SVG, ExportKind.DXF_COMPLETE, ExportKind.DXF_OUTLINE, ExportKind.DXF_SCREWS,
        ExportKind.PDF_REPORT, ExportKind.README, None,
    ]  # fmt: skip
    assert EXPORT_UTC.encode() in reference["motor.svg"][1]
    assert stub_files == reference
    drawings = ("motor.svg", "motor.dxf", "motor_screws.dxf")
    assert [name for name in drawings if moved_files[name] == reference[name]] == []
