"""DEF-UV15-04 follow-up on 0.0.5: every angle input in radians at a finite value whose degrees are infinite.

Run from the repository root with ``PYTHONPATH=src``:

    python tests/independent/m7/v24_angle_file_form.py

The 0.0.2 record (V3-07.md) left the other radian inputs `not tested`. For each packaged example, every draft value
whose pointer ends in ``_rad`` is set to the PR-05 seed 5 value and to -1e308, and the polygon board and bore rotations
are set on the CF-11 draft with a polygon outline. PR-05 says compute never raises and an invalid value returns an
issue. Exit 1 when a case raises or returns ``ok`` without an error issue.
"""

import sys
from pathlib import Path

from embodic.api import compute, compute_project
from embodic.errors import Severity
from embodic.model.draft import DesignDraft, DraftIncomplete, draft_from_design, parse_draft
from embodic.model.provenance import derive_provenance
from embodic.results import load_registry

REPO = Path(__file__).resolve().parents[3]
EXAMPLES = REPO / "resources" / "examples"
VALUES = (3.137566414384587e306, -1e308)
BOARD_POLYGON = {"/outline/board/shape": "polygon", "/outline/board/sides": 12, "/outline/board/across_flats_mm": 93.0,
                 "/outline/board/corner_radius_mm": 0.0}  # fmt: skip


def bore_polygon(values: dict[str, object]) -> dict[str, object]:
    """Return an octagonal bore inside CF-11's round bore (across flats 1.8 x radius)."""
    radius = values["/outline/bore/radius_mm"]
    return {"/outline/bore/shape": "polygon", "/outline/bore/sides": 8,
            "/outline/bore/across_flats_mm": 1.8 * radius, "/outline/bore/corner_radius_mm": 0.0}  # fmt: skip


def cases() -> list[tuple[str, DesignDraft, str]]:
    """Return (example, draft, radian pointer) for each radian input of each example and both polygon rotations."""
    out = []
    for path in sorted(EXAMPLES.glob("*.embodic.json")):
        outcome = compute_project(path)
        assert not isinstance(outcome, tuple), outcome
        draft = draft_from_design(outcome.design)
        name = path.name.removesuffix(".embodic.json")
        out += [(name, draft, p) for p in sorted(draft.values) if p.endswith("_rad")]
        if name == "spiral_12c16p_default":
            for extra, pointer in ((BOARD_POLYGON, "/outline/board/rotation_rad"),
                                   (bore_polygon(draft.values), "/outline/bore/rotation_rad")):  # fmt: skip
                polygon = DesignDraft(topology=draft.topology, values={**draft.values, **extra, pointer: 0.0})
                out.append((f"{name} (polygon)", polygon, pointer))
    return out


def probe(draft: DesignDraft, pointer: str, value: float) -> tuple[bool, str]:
    """Return (PR-05 holds, what compute did) for one radian input set to ``value``."""
    parsed = parse_draft(DesignDraft(topology=draft.topology, values={**draft.values, pointer: value}))
    if isinstance(parsed, DraftIncomplete):
        return bool(parsed.missing or parsed.issues), f"draft incomplete {sorted(i.code for i in parsed.issues)}"
    try:
        outcome = compute(parsed, derive_provenance(parsed, None, ()), registry=load_registry())
    except Exception as exc:  # the property under test: compute must not raise
        return False, f"raised {type(exc).__name__}: {exc}"
    errors = sorted({i.code for i in outcome.issues if i.severity is Severity.ERROR and pointer in i.pointers})
    return (not outcome.ok and bool(errors)), f"ok={outcome.ok} errors on the pointer {errors}"


def main() -> int:
    """Print one line per case and value; exit 1 when PR-05 fails on any."""
    failed = 0
    for name, draft, pointer in cases():
        for value in VALUES:
            holds, said = probe(draft, pointer, value)
            failed += not holds
            print(f"{'pass' if holds else 'FAIL'} {name} {pointer} = {value!r}: {said}", flush=True)
    print(f"{failed} failing")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
