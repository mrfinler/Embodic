"""Item 5 (U-V3): the packaged serpentine and wave examples through embodic.api.compute against Xcoil compute().

Xcoil inputs: the serpentine example is Xcoil's defaults (origin note "Xcoil default serpentine preset"); the wave
example is Xcoil's defaults with topology wave and turns 2 (D-016, DEF-P2-03), which the example's design matches
(16 poles, 22 to 40 mm, 0.4 mm trace, arc ratio 0.85, 1500 rpm, 0.8 A, 60 degC).
"""

from functools import cache
from typing import Any

from cases import run_node

XCOIL_INPUT = {
    "serpentine_16p_example": {},
    "wave_16p_example": {"topology": "wave", "turns": 2},
}


@cache
def xcoil(example_id: str) -> dict[str, Any]:
    """Xcoil compute() for the example's inputs: DRC issue count and analysis scalars."""
    (out,) = run_node({"cases": [{"id": example_id, "params": XCOIL_INPUT[example_id]}]})["cases"]
    return out


@cache
def embodic(example_id: str) -> Any:
    """embodic.api.compute on the packaged example design."""
    from embodic.api import compute
    from embodic.io.examples import load_example

    _, design = load_example(example_id)
    return compute(design, {})


def rows(example_id: str) -> list[tuple[str, float, float]]:
    """(quantity, embodic, Xcoil) for the compared quantities."""
    a, x = embodic(example_id).analysis, xcoil(example_id)["analysis"]
    return [
        ("Ke phase fundamental (Xcoil Ke1)", a.ke_phase_v_s_per_rad.value, x["Ke1"]),
        ("Ke line fundamental (Xcoil keLinePk)", a.ke_line_v_s_per_rad.value, x["keLinePk"]),
        ("Ke line waveform peak (embodic only)", a.ke_line_peak_v_s_per_rad.value, x["keLinePk"]),
        ("R phase operating (Xcoil Rphase)", a.resistance_phase_operating_ohm.value, x["Rphase"]),
        ("P_ic (Xcoil pInterconnect)", a.loss_interconnect_w.value, x["pInterconnect"]),
    ]


def main() -> None:
    """Print the item 5 table."""
    for example_id in XCOIL_INPUT:
        out = embodic(example_id)
        counts = [r.violation_count for r in out.drc]
        print(f"{example_id}: DRC embodic {counts} Xcoil {xcoil(example_id)['drcIssues']}")
        for name, e, x in rows(example_id):
            print(f"  {name}: embodic {e:.7g} Xcoil {x:.7g} rel {e / x - 1:+.3e}")


if __name__ == "__main__":
    main()
