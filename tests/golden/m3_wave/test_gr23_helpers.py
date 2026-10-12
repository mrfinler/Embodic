"""GR-23: the wave helpers against Xcoil on 200 seeded inputs each, 1e-12 relative (REQ-F-35).

The inputs are written into each fixture by `tools/golden/functions/wave.mjs`, so Python needs no PRNG.
"""

import dataclasses
import math
from collections.abc import Mapping, Sequence
from typing import Any

import pytest
from harness import KERNEL, GoldenCase, compare_prims, compare_scalar, compare_sequence, load_case
from harness.codec import DATA_DIR

from embodic.generators.wave.derive import WaveFrame, WaveParams, derive_wave, max_wave_turns
from embodic.generators.wave.fillet import fillet_path, taper_junctions
from embodic.generators.wave.involute import biarc, invol, involute_point, involute_prims
from embodic.generators.wave.track import wave_track
from embodic.generators.wave.xprim import XArc, XLine, XPrim, to_primitive

from .path_distance import chain_deviation_mm

pytestmark = pytest.mark.req("REQ-F-35")

CURVE_MM = 1e-9  # test_plan.md GR-20/GR-21 allow 1e-6 mm of path distance; observed deviations are below 1e-11 mm


def _calls(case_id: str) -> Sequence[Mapping[str, Any]]:
    case: GoldenCase = load_case(DATA_DIR / "wave" / f"{case_id}.json")
    (call,) = case.calls
    assert len(call.output) >= 100, f"{case_id}: fewer than 100 seeded inputs"
    return call.output


def _prim(record: Mapping[str, Any]) -> XPrim:
    if record["type"] == "line":
        return XLine(x1=record["x1"], y1=record["y1"], x2=record["x2"], y2=record["y2"], w=record["width"],
                     kind=record["kind"])  # fmt: skip
    return XArc(cx=record["cx"], cy=record["cy"], r=record["r"], a1=record["a1"], a2=record["a2"], w=record["width"],
                kind=record["kind"])  # fmt: skip


def _prims(records: Sequence[Mapping[str, Any]]) -> list[XPrim]:
    return [_prim(r) for r in records]


def _check(report: Any, case_id: str, golden: Sequence[Mapping[str, Any]], actual: Sequence[XPrim]) -> None:
    assert len(golden) == len(actual), f"{case_id}: {len(golden)} Xcoil primitives, {len(actual)} here"
    report.check(case_id, compare_prims(golden, [to_primitive(q) for q in actual], KERNEL))


def _check_curve(case_id: str, golden: Sequence[Mapping[str, Any]], actual: Sequence[XPrim]) -> None:
    """Arc splines: same pieces, kinds and widths, and the same curve within 1e-9 mm (see path_distance.py)."""
    assert [(r["type"], r["kind"], r["width"]) for r in golden] == [
        ("line" if isinstance(q, XLine) else "arc", q.kind, q.w) for q in actual
    ]
    deviation = chain_deviation_mm([to_primitive(_prim(r)) for r in golden], [to_primitive(q) for q in actual])
    assert deviation <= CURVE_MM, f"{case_id}: curve deviation {deviation:.3e} mm"


def _params(raw: Mapping[str, Any]) -> WaveParams:
    """Xcoil parameter names to WaveParams; Xcoil's `normalizeParams` keeps these values as given."""
    return WaveParams(
        poles=raw["poles"], phases=raw["phases"], turns=raw["turns"], r_in=raw["rIn"], r_out=raw["rOut"],
        trace_width_mm=raw["traceWidth"], clearance_mm=raw["clearance"], end_width_outer_mm=raw["endWidthOuter"],
        end_width_inner_mm=raw["endWidthInner"], via_pad=raw["viaPad"], via_drill_mm=raw["viaDrill"],
        start_angle_deg=raw["startAngleDeg"], wave_style=raw["waveStyle"], rounded=raw["cornerStyle"] != "sharp",
        fillet_radius_mm=raw["filletRadius"], bus_width_mm=raw["busWidth"],
    )  # fmt: skip


@pytest.mark.eqt("EQT-24-GR")
def test_invol_matches_xcoil(golden_report: Any) -> None:
    """Catches tan(a) + a or a sign slip in the involute function."""
    for i, c in enumerate(_calls("wave-helper-invol")):
        golden_report.check(f"invol/{i}", compare_scalar(c["value"], invol(c["alpha"]), KERNEL))


@pytest.mark.eqt("EQT-24-GR")
def test_involute_point_matches_xcoil(golden_report: Any) -> None:
    """Catches a swapped sine and cosine in the involute point."""
    for i, c in enumerate(_calls("wave-helper-involute-point")):
        golden_report.check(
            f"involute-point/{i}",
            compare_sequence(c["point"], list(involute_point(c["rb"], c["phi0"], c["t"])), KERNEL),
        )


@pytest.mark.eqt("EQT-24-GR")
def test_biarc_matches_xcoil(golden_report: Any) -> None:
    """Catches a wrong joint point or arc direction of the biarc."""
    for i, c in enumerate(_calls("wave-helper-biarc")):
        out = biarc(tuple(c["P0"]), tuple(c["T0"]), tuple(c["P1"]), tuple(c["T1"]), c["w"], c["kind"])
        _check(golden_report, f"biarc/{i}", c["prims"], list(out))


@pytest.mark.eqt("EQT-24-GR")
def test_involute_prims_match_xcoil() -> None:
    """Catches a wrong piece count (the deviation loop) or a spline that leaves the involute."""
    for i, c in enumerate(_calls("wave-helper-involute-prims")):
        out = involute_prims(c["rb"], c["phi0"], c["t1"], c["t2"], c["w"], c["kind"])
        _check_curve(f"involute-prims/{i}", c["prims"], out)


def test_fillet_path_matches_xcoil(golden_report: Any) -> None:
    """Catches a fillet on the wrong side or trimmed by the wrong length, for line-line and line-arc corners."""
    for i, c in enumerate(_calls("wave-helper-fillet-path")):
        _check(golden_report, f"fillet-path/{i}", c["out"], fillet_path(_prims(c["prims"]), c["rho"], None))


def test_taper_junctions_match_xcoil(golden_report: Any) -> None:
    """Catches a taper of the wrong length or on the wrong side of a width step."""
    for i, c in enumerate(_calls("wave-helper-taper-junctions")):
        _check(golden_report, f"taper-junctions/{i}", c["out"], taper_junctions(_prims(c["prims"])))


def _summary(frame: WaveFrame) -> dict[str, Any]:
    def end(e: Any) -> dict[str, float]:
        out = {"rv": e.rv, "spacing": e.spacing_mm, "need": e.need, "wEnd": e.w_end}
        return out | ({} if e.rb is None else {"rb": e.rb})

    out: dict[str, Any] = {"rVo": frame.r_vo, "rVi": frame.r_vi, "outer": end(frame.outer), "inner": end(frame.inner)}
    if frame.r_track_min is not None:
        out["rTrackMin"] = frame.r_track_min
    if frame.style == "overlap":
        top = frame.mq - 1
        out |= {"pitchOut": frame.pitch_out_mm, "pitchIn": frame.pitch_in_mm, "rhoOut0": frame.rho_out(0),
                "rhoIn0": frame.rho_in(0), "rhoOutTop": frame.rho_out(top), "rhoInTop": frame.rho_in(top)}  # fmt: skip
    return out


def _flat(summary: Mapping[str, Any], prefix: str = "") -> dict[str, float]:
    flat: dict[str, float] = {}
    for key, value in summary.items():
        if isinstance(value, Mapping):
            flat |= _flat(value, f"{prefix}{key}.")
        else:
            flat[f"{prefix}{key}"] = value
    return flat


@pytest.mark.eqt("EQT-01-GR", "EQT-24-GR")
def test_derive_wave_matches_xcoil_frame_or_refusal(golden_report: Any) -> None:
    """Catches a changed branch order in the style derivation: same refusal codes, same via rings and spacings."""
    seen: set[str] = set()
    for i, c in enumerate(_calls("wave-helper-derive")):
        params = _params(c["params"])
        frame = derive_wave(params)
        if c["errors"]:
            assert isinstance(frame, tuple), f"derive/{i}: Xcoil refuses, the port builds"
            assert [(r.code, r.field) for r in frame] == [(e["code"], e["field"]) for e in c["errors"]]
            assert max_wave_turns(params) == c["maxTurns"]
            seen.add("refusal")
            continue
        assert not isinstance(frame, tuple), f"derive/{i}: Xcoil builds, the port refuses {frame}"
        golden, actual = _flat(c["frame"]), _flat(_summary(frame))
        assert golden.keys() == actual.keys()
        for key, value in golden.items():
            golden_report.check(f"derive/{i}/{key}", compare_scalar(value, actual[key], KERNEL))
        seen.add(c["params"]["waveStyle"])
    assert seen == {"involute", "jog", "chord", "overlap", "refusal"}


@pytest.mark.eqt("EQT-24-GR")
def test_wave_track_matches_xcoil() -> None:
    """Catches a wrong end-turn, fillet or taper of the canonical track and of the shortened commutation track."""
    for i, c in enumerate(_calls("wave-helper-track")):
        frame = derive_wave(_params(c["params"]))
        assert isinstance(frame, WaveFrame)
        _check_curve(f"track/{i}/t0", c["t0"], wave_track(frame, None))
        if c["shift"] is not None:
            _check_curve(f"track/{i}/shift", c["shift"], wave_track(frame, frame.tau / 2 - frame.d_theta))


@pytest.mark.eqt("EQT-01-GR", "EQT-08-GR")
def test_belts_and_slot_angles_match_xcoil(golden_report: Any) -> None:
    """Catches a belt that maps to the wrong phase or sign, or a slot angle off by half a slot."""
    checked = 0
    for i, c in enumerate(_calls("wave-helper-belts")):
        if c.get("ks") is None:
            continue
        frame = derive_wave(_params(c["params"]))
        assert isinstance(frame, WaveFrame)
        assert [frame.belt_phase(b) for b in c["betas"]] == c["phases"]
        assert [frame.belt_sign(b) for b in c["betas"]] == c["signs"]
        angles = [frame.slot_angle(k) for k in c["ks"]]
        golden_report.check(f"belts/{i}", compare_sequence(c["angles"], angles, KERNEL))
        checked += 1
    assert checked > 100


def test_dataclass_frame_is_immutable() -> None:
    """Catches a frame that a builder could mutate between the track and the via ring construction."""
    frame = derive_wave(_params({
        "poles": 16, "phases": 3, "turns": 2, "rIn": 22, "rOut": 40, "traceWidth": 0.4, "clearance": 0.2,
        "endWidthOuter": 0, "endWidthInner": 0, "viaPad": 0.6, "viaDrill": 0.3, "startAngleDeg": 0,
        "waveStyle": "involute", "cornerStyle": "round", "filletRadius": 0.4, "busWidth": 1.0,
    }))  # fmt: skip
    assert isinstance(frame, WaveFrame)
    with pytest.raises(dataclasses.FrozenInstanceError):
        frame.r_vo = math.nan  # type: ignore[misc]
