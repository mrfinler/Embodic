"""Item 7: DEF-M2e3-01 with Xcoil's own phase members (def_m2e3_01.py) instead of `_series_circuit`.

Sector: with coil objects as the only members, embodic's phase R is +5.8e-5 from Xcoil phaseRtrace (the +3.3 % to
+4.2 % gap of `_series_circuit` was its ring and leg paths). Wave: the -6.0 % gap stays with Xcoil's members, and it is
62 via barrels: Xcoil adds rVia per element into Rtrace (engine.js l.2034 `R += e.R + rVia`, l.2062 `Rtrace: R`).
Own rVia from engine.js constants: rho h / A, A = pi (2 r t - t^2) with drill 0.3 mm and plating t 0.025 mm (l.15,
l.92-94), h = |z_1 - z_0| = 1.5304 mm (l.2209), rho = the golden's `rho`.
Defects caught: a mapping, path-resistance or temperature change that moves either gap.
"""

import json
import math

import def_m2e3_01
import pytest

pytestmark = pytest.mark.req("REQ-F-11")


@pytest.fixture(scope="module")
def measured():
    """Run analyse() on both GR-19 cases with Xcoil's members and with the harness circuit."""
    return def_m2e3_01.measure()


def test_sector_phase_resistance_matches_xcoil_once_rings_and_legs_leave_the_members(measured) -> None:
    """Coil-only members: within 1e-4 of phaseRtrace on every phase."""
    rows = measured["layout-sector-default"]
    assert rows["xcoil_members"] == pytest.approx(rows["xcoil_rtrace"], rel=1e-4)


def test_wave_gap_is_the_via_barrels_xcoil_counts_inside_rtrace(measured) -> None:
    """Xcoil Rtrace minus embodic's equals 62 x own rVia within 0.2 % of the via sum."""
    raw = def_m2e3_01.ROOT / "tests/golden/data/m1_layout/layout-wave-turns-2.json"
    layout = json.loads(raw.read_text())["calls"][0]["output"]
    golden = def_m2e3_01.ROOT / "tests/golden/data/physics/analysis-wave-turns-2.json"
    rho = json.loads(golden.read_text())["calls"][0]["output"]["rho"]
    r, t = layout["params"]["viaDrill"] / 2, 0.025
    h = abs(layout["layers"][1]["z"] - layout["layers"][0]["z"])
    r_via = rho * (h * 1e-3) / (math.pi * (2 * r * t - t * t) * 1e-6)
    tracks = [
        sum(1 for L in layout["layers"] for o in L["objs"] if o["kind"] == "track" and o["phase"] == k)
        for k in range(3)
    ]
    rows = measured["layout-wave-turns-2"]
    for k in range(3):
        gap = rows["xcoil_rtrace"][k] - rows["xcoil_members"][k]
        assert gap == pytest.approx(tracks[k] * r_via, rel=2e-3), (k, tracks[k], gap)
