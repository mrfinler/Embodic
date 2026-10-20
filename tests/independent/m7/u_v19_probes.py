"""U-V19: measure the expected values of the missing tests that u_v19_id_map.py specifies, on the 0.0.4 package.

    python3 tests/independent/m7/u_v19_probes.py          # needs embodic importable (src equal to c25d8a9)

Each probe prints what the specified test would read, so that the expected values and tolerances of the map are
numbers this script measured, not numbers copied from the product. Nothing here is a pytest test.
"""

import dataclasses
import json
import math
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from tests.unit.generators.d08_example import d08_design
from tests.unit.generators.default_example import default_design

from embodic.api import compute
from embodic.generators import generate_spiral
from embodic.geometry.layout import BoardStack, ViaRole
from embodic.io.examples import load_example
from embodic.io.project import ProjectFile, load_project, save_project
from embodic.model.fields import FIELDS
from embodic.model.validate import validate_design
from embodic.results import load_registry
from embodic.results.status import Status

REGISTRY = load_registry()


def _with_first_coil_angle(design, angle):
    coil = dataclasses.replace(design.winding.coil, first_coil_angle_rad=angle)
    return dataclasses.replace(design, winding=dataclasses.replace(design.winding, coil=coil))


def _ends(primitive):
    return primitive.start_point(), primitive.end_point()


def probe_ut_geo_24() -> None:
    """UT-GEO-24: 1.0, 1.0 + 2 pi and 1.0 - 2 pi build one board; the file keeps the typed angle in degrees."""
    base = default_design()
    angles = (1.0, 1.0 + 2 * math.pi, 1.0 - 2 * math.pi)
    boards = {}
    for a in angles:
        design = _with_first_coil_angle(base, a)
        issues = validate_design(design)
        stack = generate_spiral(design, REGISTRY)
        assert isinstance(stack, BoardStack), a
        boards[a] = stack.boards[0]
        centres = [v for v in stack.boards[0].vias if v.role is ViaRole.CENTRE]
        axis = min((math.atan2(v.y_mm, v.x_mm) for v in centres), key=lambda t: abs(math.remainder(t - 1.0, math.tau)))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "p.embodic.json"
            save_project(path, ProjectFile(design=design, origin=None))
            stored = json.loads(path.read_text(encoding="utf-8"))["design"]["winding"]["coil"]["first_coil_angle_deg"]
            loaded, _ = load_project(path)
        back = loaded.design.winding.coil.first_coil_angle_rad
        print(
            f"UT-GEO-24 a={a!r}: issues {[i.code for i in issues]}, "
            f"typed kept {design.winding.coil.first_coil_angle_rad == a}, "
            f"coil-0 axis - 1.0 = {math.remainder(axis - 1.0, math.tau):.3e} rad, stored deg {stored!r} "
            f"(math.degrees {math.degrees(a)!r}), loaded - a = {back - a:.3e} rad"
        )
    ref = boards[1.0]
    for a in angles[1:]:
        worst = 0.0
        for p, q in zip(ref.paths, boards[a].paths, strict=True):
            assert p.id == q.id
            for x, y in zip(p.primitives, q.primitives, strict=True):
                for u, w in zip(_ends(x), _ends(y), strict=True):
                    worst = max(worst, math.dist(u, w))
        print(f"UT-GEO-24 a={a!r}: largest primitive end point shift against a=1.0 {worst:.3e} mm")


def probe_ut_geo_25() -> None:
    """UT-GEO-25: the closing is no FIELDS pointer and no key of the saved project file."""
    pointers = [f.pointer for f in FIELDS if "closing" in f.pointer or "turn_limit" in f.pointer]
    print(f"UT-GEO-25: FIELDS pointers naming closing or turn_limit: {pointers}")
    for example, design in (("CF-11 default_design", default_design()), ("D08 d08_design", d08_design())):
        stack = generate_spiral(design, REGISTRY)
        closing = stack.boards[0].detail.turn_limit.closing
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "p.embodic.json"
            save_project(path, ProjectFile(design=design, origin=None))
            text = path.read_text(encoding="utf-8")
        print(
            f"UT-GEO-25 {example}: closing {closing.value}; 'closing' in file {'closing' in text}, "
            f"'turn_limit' in file {'turn_limit' in text}"
        )


def probe_bv_21() -> None:
    """BV-21: 1e30 mm screw pitch radius on the three topologies."""
    _, serpentine = load_example("serpentine_16p_example")
    for example in ("spiral_12c16p_default", "serpentine_16p_example", "wave_16p_example"):
        _, design = load_example(example)
        screws = design.outline.screws or serpentine.outline.screws
        pattern = dataclasses.replace(screws[0], pitch_radius_mm=1e30)
        far = dataclasses.replace(design, outline=dataclasses.replace(design.outline, screws=(pattern, *screws[1:])))
        pointer = "/outline/screws/0/pitch_radius_mm"
        found = [(i.code, i.severity.value, i.category.value) for i in validate_design(far) if pointer in i.pointers]
        outcome = compute(far, {}, registry=REGISTRY)
        internal = [i.code for i in outcome.issues if i.code.startswith("INTERNAL_")] if outcome else None
        print(
            f"BV-21 {example} (screws copied: {not design.outline.screws}): issues at the pointer {found}; "
            f"INTERNAL_ issues of compute {internal}"
        )


def probe_t_05() -> None:
    """REQ-T-05 'every': the verified equations of the packaged registry, with their linked test counts."""
    verified = {k: e.tests for k, e in REGISTRY.equations.items() if e.status is Status.VERIFIED}
    print(f"REQ-T-05: {len(verified)} verified equations: " + ", ".join(f"{k} ({len(t)})" for k, t in verified.items()))


def probe_pr_12() -> None:
    """PR-12: the assumed-inputs tag of a result is readable and changes when an input goes back to its example."""
    ref, design = load_example("spiral_12c16p_default")
    from embodic.model.provenance import derive_provenance

    first = compute(design, derive_provenance(design, (ref, design), ()), registry=REGISTRY)
    tag = [a.item for a in first.analysis.ke_phase_v_s_per_rad.assumed_inputs]
    print(f"PR-12: ke_phase assumed_inputs of the example: {len(tag)} entries, e.g. {tag[:3]}")


if __name__ == "__main__":
    for probe in (probe_ut_geo_24, probe_ut_geo_25, probe_bv_21, probe_t_05, probe_pr_12):
        try:
            probe()
        except Exception as error:  # a probe that cannot run says why and the next one still runs
            print(f"{probe.__name__} failed: {type(error).__name__}: {error}")
    print("done:", re.sub(r"\s+", " ", __doc__.splitlines()[0]))
