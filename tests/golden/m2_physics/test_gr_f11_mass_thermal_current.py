"""F11-1 (REQ-F-11 i): EQ-16 mass, EQ-17 thermal estimate, EQ-19 delta circulating loss and EQ-22 current density.

Every Xcoil number comes from tests/golden/data/mass_thermal, written by tools/golden/dump_xcoil.mjs with
tools/golden/functions/mass_thermal.mjs on the params of the three m1_layout layouts (and one delta case). Mass and
the current density run through analyse() on those layouts mapped into embodic, with Xcoil's densities 8.96 and
1.85 g/cm^3 injected, so a diff means the port differs, not the registry constant (EQ-16 changes copper to 8.89).
The thermal estimate and the delta loss take Xcoil's own inputs into embodic's kernels: the mapped layouts carry no
element list, so their loss total is not Xcoil's (test_analysis_golden.py), and no layout fixture is in delta.

Tolerances (V3-01_gaps_a.md F11-1): the kernel class rel 1e-12 for EQ-22 (registry tolerance exact), the integrated
class rel 1e-9 for mass, the thermal estimate and the circulating loss.
"""

import dataclasses
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from harness.codec import load_area
from harness.compare import INTEGRATED, KERNEL, compare_scalar

from embodic.physics import analyse
from embodic.physics.circuit import T_MM2_TO_V_S_PER_RAD, delta_circulating_loss_w
from embodic.physics.estimates import mass_g
from embodic.physics.thermal import temperature_rise_k
from embodic.results import AnalysisResult, Registry, load_registry
from m2_physics.test_analyse_layouts import _design, _raw, _stack

pytestmark = pytest.mark.req("REQ-F-11")
AREA = load_area("mass_thermal")
LAYOUTS = ("sector-default", "serpentine-default", "wave-turns-2")
XCOIL_DENSITY_G_PER_CM3 = {"copper_density_g_per_cm3": 8.96, "laminate_density_g_per_cm3": 1.85}  # engine.js l.1377
DELTA_CASE = "connection-sector-15c14p-delta"


def _output(case_id: str) -> Mapping[str, Any]:
    output: Mapping[str, Any] = AREA[case_id].calls[0].output
    return output


def _xcoil_density_registry() -> Registry:
    registry = load_registry()
    equations = {
        eq_id: dataclasses.replace(
            entry,
            constants=tuple(
                dataclasses.replace(c, value=XCOIL_DENSITY_G_PER_CM3.get(c.name, c.value)) for c in entry.constants
            ),
        )
        for eq_id, entry in registry.equations.items()
    }
    return dataclasses.replace(registry, equations=equations)


@pytest.fixture(scope="module")
def results() -> Mapping[str, AnalysisResult]:
    """analyse() once per m1_layout layout, after checking it was built from the params of this area's fixtures."""
    registry, out = _xcoil_density_registry(), {}
    for tag in LAYOUTS:
        raw = _raw(f"layout-{tag}")
        assert raw["params"] == _output(f"mass-thermal-{tag}")["params"] == _output(f"connection-{tag}")["params"]
        result = analyse(_design(raw), _stack(raw), {}, registry)
        assert result is not None
        out[tag] = result
    return out


@pytest.mark.eqt("EQT-16-GR")
@pytest.mark.parametrize("tag", LAYOUTS)
def test_copper_mass_of_the_mapped_layout_matches_xcoil_mass_thermal(
    results: Mapping[str, AnalysisResult], tag: str
) -> None:
    """Catches a copper area summed over the wrong objects or widths, or a volume-to-mass unit slip (EQ-16)."""
    xcoil = _output(f"mass-thermal-{tag}")["thermal"]["massCopper"]
    verdict = compare_scalar(xcoil, results[tag].mass_copper_g.value, INTEGRATED)
    assert verdict.ok, f"{tag}: {verdict}"


@pytest.mark.eqt("EQT-16-GR")
@pytest.mark.parametrize("tag", LAYOUTS)
def test_laminate_mass_kernel_matches_xcoil_on_xcoils_board_area(tag: str) -> None:
    """Catches a laminate volume that keeps the copper in, or that counts one board of a stack (EQ-16)."""
    x = _output(f"mass-thermal-{tag}")
    assert not x["customStackup"], "embodic ports the auto stack-up branch of massThermal"
    names = [f"L{k}" for k in range(len(x["layerCopperT"]))]
    mass = mass_g(
        dict(zip(names, x["layerCopperArea"], strict=True)),
        dict(zip(names, x["layerCopperT"], strict=True)),
        x["boardArea"] * x["nBoards"],
        x["boardThickness"],
        XCOIL_DENSITY_G_PER_CM3["copper_density_g_per_cm3"],
        XCOIL_DENSITY_G_PER_CM3["laminate_density_g_per_cm3"],
    )
    for name, golden, actual in (
        ("massCopper", x["thermal"]["massCopper"], mass.copper_g),
        ("massLaminate", x["thermal"]["massLaminate"], mass.laminate_g),
    ):
        verdict = compare_scalar(golden, actual, INTEGRATED)
        assert verdict.ok, f"{tag} {name}: {verdict}"


@pytest.mark.eqt("EQT-16-GR")
@pytest.mark.parametrize("tag", LAYOUTS)
@pytest.mark.xfail(
    strict=True,
    reason="DEF-M7b-01: board_area_mm2 integrates 0.5 mm chords of the outline arcs; Xcoil uses the analytic area "
    "(engine.js l.1144), so the board area is 5.6e-6 to 7.5e-6 relative low and the laminate mass with it",
)
def test_laminate_mass_of_the_mapped_layout_matches_xcoil_mass_thermal(
    results: Mapping[str, AnalysisResult], tag: str
) -> None:
    """Catches a board area or laminate volume that differs from Xcoil's on the same outline (EQ-16)."""
    xcoil = _output(f"mass-thermal-{tag}")["thermal"]["massLaminate"]
    verdict = compare_scalar(xcoil, results[tag].mass_laminate_g.value, INTEGRATED)
    assert verdict.ok, f"{tag}: {verdict}"


@pytest.mark.eqt("EQT-17-GR")
@pytest.mark.parametrize("tag", LAYOUTS)
def test_temperature_rise_kernel_matches_xcoil_mass_thermal(tag: str) -> None:
    """Catches a cooling area of one face instead of two, or a mm^2 to m^2 slip (EQ-17, dT = P / (h 2 A))."""
    x = _output(f"mass-thermal-{tag}")
    actual = temperature_rise_k(x["lossTotal"], x["boardArea"], x["params"]["hConv"])
    verdict = compare_scalar(x["thermal"]["tempRiseEst"], actual, INTEGRATED)
    assert verdict.ok, f"{tag}: {verdict}"


@pytest.mark.eqt("EQT-19-GR")
def test_delta_circulating_loss_kernel_matches_xcoil_apply_connection() -> None:
    """Catches a triplen sum that cancels, a peak taken as rms, or a loop without the link copper (EQ-19).

    15 coils with 14 poles in delta: the third-harmonic EMFs of the phases add around the mesh, so Xcoil's loss is
    not 0 and the comparison is not vacuous. Xcoil refuses 12/14 (SECTOR_UNBALANCED), the pairing the spec named.
    """
    x = _output(DELTA_CASE)
    assert x["connection"] == "delta" and x["pDeltaCirc"] > 0.0
    scale = T_MM2_TO_V_S_PER_RAD * x["omegaM"]
    phase_emf_v = [np.array([complex(re, im) for re, im in phase]) * scale for phase in x["phaseE"]]
    loop_ohm = sum(x["phaseR"]) + sum(x["link"])
    verdict = compare_scalar(x["pDeltaCirc"], delta_circulating_loss_w(phase_emf_v, loop_ohm), INTEGRATED)
    assert verdict.ok, str(verdict)


@pytest.mark.eqt("EQT-22-GR")
@pytest.mark.parametrize("tag", LAYOUTS)
def test_current_density_of_the_mapped_layout_matches_xcoil(results: Mapping[str, AnalysisResult], tag: str) -> None:
    """Catches J computed from the wrong width (strand, bus or widest track) or thickness, or the line current (EQ-22).

    Xcoil: J = I_ph / (a w_min t_min) from analyze, analyzeElements or analyzeWave, times I_ph in applyConnection.
    """
    xcoil = _output(f"connection-{tag}")
    assert xcoil["connection"] == "star"
    verdict = compare_scalar(xcoil["currentDensity"], results[tag].current_density_a_per_mm2.value, KERNEL)
    assert verdict.ok, f"{tag}: {verdict}"


def test_every_fixture_of_the_area_is_compared() -> None:
    """Catches a fixture dumped for this area that no test reads."""
    read = {f"mass-thermal-{t}" for t in LAYOUTS} | {f"connection-{t}" for t in LAYOUTS} | {DELTA_CASE}
    on_disk = {p.stem for p in (Path(__file__).parents[1] / "data" / "mass_thermal").glob("*.json")}
    assert on_disk == read
    assert json.loads((Path(__file__).parents[3] / "tools/golden/cases/mass_thermal.json").read_text())["area"] == (
        "mass_thermal"
    )
