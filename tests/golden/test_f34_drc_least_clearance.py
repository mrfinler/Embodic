"""F34-1 (V3-01 union ruling): least DRC clearances of every GR-20 and GR-21 board against an arc-exact sweep.

Xcoil cannot be the reference: it measures arcs by chords, with a sagitta up to 0.001 mm, so GR-20 drops value diffs.
The reference is Agent 4's independent sweep (tests/independent/m1 drc_universe and tests/independent/m3 drc_m3),
which measures arcs exactly over the pairs that rule D-006 and interfaces.md section 7 leave non-exempt. This module
imports it read-only and asks it three questions per board instead of one (see _check_case).
"""

import json
import sys
from collections.abc import Mapping
from functools import cache
from pathlib import Path
from typing import Any

import pytest

_INDEPENDENT = Path(__file__).resolve().parents[1] / "independent"
for _folder in (_INDEPENDENT / "m1", _INDEPENDENT / "m3"):
    if str(_folder) not in sys.path:
        sys.path.insert(0, str(_folder))

from board_dump_reader import parse_board_dump  # noqa: E402
from brute_clearance import DRC_EPSILON_MM, Verdict  # noqa: E402
from drc_m3 import universe  # noqa: E402
from drc_universe import contract_exemptions, sweep  # noqa: E402
from embodic_adapter import uniform_rules  # noqa: E402
from harness import GoldenCase, load_area  # noqa: E402
from m3_serpentine.design_map import design_from_xcoil as serpentine_design  # noqa: E402
from m3_wave.param_map import design_from_xcoil as wave_design  # noqa: E402

from embodic.drc import DrcCheckKind, run_drc  # noqa: E402
from embodic.errors import Unbuildable  # noqa: E402
from embodic.generators import build_layout  # noqa: E402
from embodic.generators.wave import generate_wave  # noqa: E402
from embodic.geometry.layout import BoardStack, Layout  # noqa: E402
from embodic.io.board_dump import dump_layout, encode_board_dump  # noqa: E402
from embodic.results import load_registry  # noqa: E402

VALUE_TOLERANCE_MM = 1e-6
KINDS = (DrcCheckKind.TRACE_TRACE.value, DrcCheckKind.TRACE_VIA.value, DrcCheckKind.VIA_VIA.value)

SERPENTINE = {
    c.case_id: c
    for c in load_area("serpentine").values()
    if c.case_id.startswith("layout-") and "layers" in c.calls[0].output
}
WAVE = {c.case_id: c for c in load_area("wave").values() if c.fn == "waveRawLayout"}


def _raw(case: GoldenCase) -> Mapping[str, Any]:
    (call,) = case.calls
    return call.output


@cache
def _boards(topology: str, case_id: str) -> tuple[Layout, ...]:
    registry = load_registry()
    if topology == "serpentine":
        raw = _raw(SERPENTINE[case_id])
        design = serpentine_design(raw["params"], raw["rMinAll"], raw["rMaxAll"])
        stack = build_layout(design, registry)
    else:
        design = wave_design(_raw(WAVE[case_id])["params"])
        stack = generate_wave(design, registry)
    assert isinstance(stack, BoardStack) and not isinstance(stack, Unbuildable), (case_id, stack)
    return stack.boards


def _violated_kinds(items: list[Any], layers: int, exempt: Any, rule_mm_of: Mapping[str, float]) -> set[str]:
    """Return the kinds with a non-exempt pair closer than ``rule_mm_of[kind] - epsilon``, arc-exact (D-006)."""
    found = sweep(items, range(layers), lambda kind: rule_mm_of.get(kind, 0.0), exempt)
    return {r.kind for r in found if r.verdict is Verdict.VIOLATION and r.kind in KINDS}


def _check_case(topology: str, case_id: str, rule_mm: float) -> None:
    """Bracket the engine's least clearance of each kind between two sweeps, and take the verdict from a third.

    A sweep at rule e - tol + epsilon reports a pair exactly when its clearance is below e - tol, so the least is
    inside [e - tol, e + tol] when the first finds nothing and the second finds a pair. A kind with no pair in the
    engine's reach must have no violating pair at the real rule.
    """
    for number, layout in enumerate(_boards(topology, case_id)):
        report = run_drc(layout, uniform_rules(rule_mm))
        assert report is not None
        engine = {s.kind.value: s.least_clearance_mm for s in report.summaries if s.kind.value in KINDS}
        dump = parse_board_dump(json.loads(encode_board_dump(dump_layout(layout, case_id="f34"))))
        items = universe(dump)
        exempt = contract_exemptions(items, frozenset(layout.circuit.interconnect_path_ids))
        layers = len(dump.layers)
        measured = {kind: value for kind, value in engine.items() if value is not None}
        below = _violated_kinds(
            items, layers, exempt, {k: v - VALUE_TOLERANCE_MM + DRC_EPSILON_MM for k, v in measured.items()}
        )
        above = _violated_kinds(
            items, layers, exempt, {k: v + VALUE_TOLERANCE_MM + DRC_EPSILON_MM for k, v in measured.items()}
        )
        at_rule = _violated_kinds(items, layers, exempt, dict.fromkeys(KINDS, rule_mm))
        for kind in KINDS:
            where = f"{case_id} board {number} {kind}"
            if kind in measured:
                assert kind not in below, f"{where}: a pair is closer than the engine's least {measured[kind]}"
                assert kind in above, f"{where}: no pair is within 1e-6 mm of the engine's least {measured[kind]}"
            violating = any(v.kind.value == kind for v in report.violations)
            assert violating == (kind in at_rule), where


@pytest.mark.req("REQ-F-34")
@pytest.mark.slow
@pytest.mark.parametrize("case_id", sorted(SERPENTINE))
def test_f34_1_serpentine_least_clearances_equal_the_arc_exact_sweep(case_id: str) -> None:
    """Catches a clearance off by up to 0.004 mm that the verdict-only comparison with Xcoil passes."""
    _check_case("serpentine", case_id, _raw(SERPENTINE[case_id])["params"]["clearance"])


@pytest.mark.req("REQ-F-35")
@pytest.mark.slow
@pytest.mark.parametrize("case_id", sorted(WAVE))
def test_f34_1_wave_least_clearances_equal_the_arc_exact_sweep(case_id: str) -> None:
    """Catches any wave DRC error: no golden test of tests/golden/m3_wave runs the DRC."""
    _check_case("wave", case_id, _raw(WAVE[case_id])["params"]["clearance"])
