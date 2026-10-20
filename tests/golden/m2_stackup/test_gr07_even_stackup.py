"""GR-07 (REQ-F-04): the even stack-up helper against Xcoil stackupFor, at function level.

Specification: docs/phase3/architecture/v3_contract_rulings.md section 3 (D-051e). The fixtures come from
`tools/golden/functions/stackup.mjs` and `tools/golden/cases/stackup.json`. Every Xcoil number below is read from them.
"""

import itertools
import math
import os
import shutil
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
from harness import (
    DATA_DIR,
    KERNEL_MM,
    GoldenCase,
    GoldenReport,
    compare_scalar,
    compare_sequence,
    fixture_drift,
    load_area,
)

from embodic.errors import Severity
from embodic.model.stackup import CopperLayer, DielectricLayer, StackLayer, Stackup, generate_even_stackup
from embodic.model.validate import even_stackup_issues

pytestmark = pytest.mark.req("REQ-F-04")

REPO_ROOT = Path(__file__).resolve().parents[3]
DUMPER = REPO_ROOT / "tools" / "golden" / "dump_xcoil.mjs"
CASE_LIST = REPO_ROOT / "tools" / "golden" / "cases" / "stackup.json"
ENGINE = Path(os.environ.get("XCOIL_ENGINE", "/home/claude/serpentine/src/engine.js"))
OZ_TO_MM = 0.0348  # Xcoil engine.js l.14: 1 oz/ft^2 copper is 34.8 um
CASES = load_area("stackup")
AUTO = {i: c for i, c in CASES.items() if "auto" in c.tags and "thin-board" not in c.tags}
CUSTOM = {i: c for i, c in CASES.items() if "custom" in c.tags}
THIN = {i: c for i, c in CASES.items() if "thin-board" in c.tags}


def xcoil_view(output: Mapping[str, Any]) -> dict[str, Any]:
    """Return what GR-07 compares of an Xcoil result: copper z, copper thickness, dielectric thickness, board."""
    return {
        "copper_z": output["z"],
        "copper_t": output["t"],
        "dielectric_t": [e["t"] for e in output["entries"] if e["type"] == "diel"],
        "board": output["boardThickness"],
    }


def embodic_view(stackup: Stackup) -> dict[str, Any]:
    """Return the same four quantities of a Stackup."""
    return {
        "copper_z": list(stackup.copper_z_mm().values()),
        "copper_t": [layer.thickness_mm for layer in stackup.copper_layers()],
        "dielectric_t": [layer.thickness_mm for layer in stackup.layers if isinstance(layer, DielectricLayer)],
        "board": stackup.board_thickness_mm(),
    }


def helper_for(case: GoldenCase) -> Stackup:
    """Call generate_even_stackup with the inputs that the fixture gave to Xcoil's auto mode."""
    inputs = case.calls[0].inputs
    p = inputs["p"]
    assert p["copperOzOuter"] == p["copperOzInner"]  # the helper takes one copper thickness for every layer
    return generate_even_stackup(inputs["nCu"], p["copperOzOuter"] * OZ_TO_MM, p["boardThickness"])


def check_against_xcoil(golden_report: GoldenReport, case: GoldenCase, actual: dict[str, Any], keys: list[str]) -> None:
    """Compare the named quantities within 1e-12 mm absolute (KERNEL_MM)."""
    golden = xcoil_view(case.calls[0].output)
    for key in keys:
        if key == "board":
            comparison = compare_scalar(golden[key], actual[key], KERNEL_MM)
        else:
            comparison = compare_sequence(golden[key], actual[key], KERNEL_MM)
        golden_report.check(f"{case.case_id}:{key}", comparison)


def test_gr_07_fixtures_hold_the_cases_of_the_specification() -> None:
    """Catches an emptied or thinned fixture set, which would let the parametrised tests pass without a case."""
    auto = {(c.calls[0].inputs["nCu"], c.calls[0].inputs["p"]["copperOzOuter"]) for c in AUTO.values()}
    assert auto == {(n, oz) for n in (1, 2, 4, 6, 8) for oz in (1, 2)}
    assert {c.calls[0].inputs["p"]["boardThickness"] for c in AUTO.values()} == {1.6}
    assert len(CUSTOM) == 2
    assert all(c.calls[0].output["custom"] and c.calls[0].output["matches"] for c in CUSTOM.values())
    assert [c.calls[0].inputs["nCu"] for c in THIN.values()] == [8]


@pytest.mark.parametrize("case", AUTO.values(), ids=list(AUTO))
def test_gr_07_auto_mode_helper_equals_xcoil_stackupfor(case: GoldenCase, golden_report: GoldenReport) -> None:
    """Catches a wrong pitch, a dielectric that keeps the copper thickness or a z off by half a copper layer.

    Each copper z, copper thickness, dielectric thickness and the board thickness equal Xcoil's within 1e-12 mm.
    """
    check_against_xcoil(
        golden_report, case, embodic_view(helper_for(case)), ["copper_z", "copper_t", "dielectric_t", "board"]
    )


def stackup_from_entries(entries: list[Mapping[str, Any]]) -> Stackup:
    """Build the Stackup that holds the same entries as a custom Xcoil list."""
    layers: list[StackLayer] = []
    for entry in entries:
        if entry["type"] == "cu":
            layers.append(
                CopperLayer(name=f"L{sum(isinstance(x, CopperLayer) for x in layers) + 1}", thickness_mm=entry["t"])
            )
        else:
            name = f"D{sum(isinstance(x, DielectricLayer) for x in layers) + 1}"
            layers.append(DielectricLayer(name=name, thickness_mm=entry["t"], material=entry["material"]))
    return Stackup(layers=tuple(layers))


@pytest.mark.parametrize("case", CUSTOM.values(), ids=list(CUSTOM))
def test_gr_07_custom_list_gives_the_copper_z_of_xcoil(case: GoldenCase, golden_report: GoldenReport) -> None:
    """Catches a z that is not the exact cumulative sum of the listed layers, for equal and for unequal dielectrics.

    The board thickness is the sum of the listed layers in both tools.
    """
    stackup = stackup_from_entries(case.calls[0].inputs["p"]["stackup"])
    check_against_xcoil(golden_report, case, embodic_view(stackup), ["copper_z", "board"])


@pytest.mark.parametrize("case", THIN.values(), ids=list(THIN))
def test_gr_07_case_3_a_board_thinner_than_its_copper_is_refused(case: GoldenCase) -> None:
    """Pins D-053a (DEF-U-M6h-01, gr07_case3_ruling.md): embodic refuses 8 layers of 2 oz on a 0.4 mm board.

    The Xcoil fixture stays as the record of an unbuildable stack: its entries sum past the board thickness it reports
    and its layer centres are closer than one copper thickness. embodic's values are not compared with it.
    """
    xcoil = xcoil_view(case.calls[0].output)
    inputs = case.calls[0].inputs
    copper_count, board_mm = inputs["nCu"], inputs["p"]["boardThickness"]
    copper_t = inputs["p"]["copperOzOuter"] * OZ_TO_MM
    entry_sum = math.fsum(e["t"] for e in case.calls[0].output["entries"])

    assert (copper_count, board_mm, xcoil["board"]) == (8, 0.4, 0.4)
    assert entry_sum - xcoil["board"] == pytest.approx(8 * 0.0696 - 0.4, abs=KERNEL_MM, rel=0.0)
    pitch = [b - a for a, b in itertools.pairwise(xcoil["copper_z"])]
    assert all(step < copper_t for step in pitch), pitch

    (refusal,) = even_stackup_issues(copper_count, copper_t, board_mm)
    assert (refusal.code, refusal.severity, refusal.value) == (
        "INVALID_STACKUP_COPPER_EXCEEDS_BOARD",
        Severity.ERROR,
        0.4,
    )
    assert refusal.limit == pytest.approx(math.fsum([0.0696] * 8), abs=KERNEL_MM, rel=0.0)

    copper_mm = math.fsum([copper_t] * copper_count)
    assert [i.code for i in even_stackup_issues(copper_count, copper_t, copper_mm)] == [refusal.code]
    assert even_stackup_issues(copper_count, copper_t, copper_mm + 1e-6) == ()
    edge = embodic_view(generate_even_stackup(copper_count, copper_t, copper_mm + 1e-6))
    assert all(t > 0.0 for t in edge["dielectric_t"]), edge["dielectric_t"]
    assert math.fsum(edge["copper_t"] + edge["dielectric_t"]) == pytest.approx(copper_mm + 1e-6, abs=KERNEL_MM, rel=0.0)

    with pytest.raises(ValueError, match="board thickness"):
        generate_even_stackup(copper_count, copper_t, board_mm)


@pytest.mark.skipif(shutil.which("node") is None or not ENGINE.is_file(), reason="needs Node and the Xcoil engine")
def test_gr_07_fixtures_equal_a_fresh_dump(tmp_path: Path) -> None:
    """Catches fixtures that are stale against the case list or the engine, or edited by hand."""
    subprocess.run(["node", str(DUMPER), str(CASE_LIST), "--out", str(tmp_path)], check=True, capture_output=True)
    assert fixture_drift(tmp_path, DATA_DIR / "stackup") == []
