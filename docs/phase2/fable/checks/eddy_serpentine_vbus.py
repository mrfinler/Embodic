"""DEF-M2e2-02 lever (Fable 5.1, claude-fable-5-1, 2026-10-05).

Splits embodic's serpentine eddy loss by Xcoil object kind and shows that the strand-only sum, rescaled to Xcoil's
copper resistivity constant, equals Xcoil's pEddy (0.1013001640536671 W, `compute()` on the default serpentine,
engine.js l.909-936 integrates 'strand' objects only). Run from the repo root:

    .venv/bin/python docs/phase2/fable/checks/eddy_serpentine_vbus.py
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "golden"))

from embodic.physics.emf import eddy_loss_w, field_table, integrate_path  # noqa: E402
from embodic.physics.field import symmetry_plane_mm  # noqa: E402
from embodic.physics.resistance import copper_resistivity_ohm_m  # noqa: E402
from embodic.results import load_registry  # noqa: E402

XCOIL_P_EDDY_W = 0.1013001640536671  # Xcoil compute(), default serpentine, 1500 rpm, 60 degC
XCOIL_RHO_20 = 1.724e-8  # engine.js l.12
XCOIL_ALPHA = 0.00393


def main() -> int:
    """Print the eddy loss per object kind and the strand-only agreement with Xcoil."""
    spec = importlib.util.spec_from_file_location("tal", ROOT / "tests/golden/m2_physics/test_analyse_layouts.py")
    tal = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(tal)
    registry = load_registry()
    raw = tal._raw("layout-serpentine-default")
    design = tal._design(raw)
    stack = tal._stack(raw)
    board = stack.boards[0]
    kinds = [o["kind"] for layer in raw["layers"] for o in layer["objs"]]
    assert len(kinds) == len(board.paths)
    rotor = design.rotor
    g_plane = symmetry_plane_mm(rotor, stack.stack_thickness_mm)
    harmonics = tuple(design.analysis.harmonics)
    pole_pairs = rotor.poles // 2
    rho = copper_resistivity_ohm_m(
        design.operating.winding_temperature_degc,
        registry.constant("copper_resistivity_20c_ohm_m").value,
        registry.constant("copper_temp_coeff_per_k").value,
    )
    rho_xcoil = XCOIL_RHO_20 * (1.0 + XCOIL_ALPHA * (design.operating.winding_temperature_degc - 20.0))
    omega_e = 2.0 * math.pi * pole_pairs * design.operating.speed_rpm / 60.0
    tables = {z: field_table(rotor, g_plane, z + rotor.air_gap_mm, harmonics) for z in set(board.copper_z_mm.values())}
    thickness = {layer.name: layer.thickness_mm for layer in design.stackup.copper_layers()}
    by_kind: dict[str, float] = {}
    for path, kind in zip(board.paths, kinds, strict=True):
        field = integrate_path(path.primitives, tables[board.copper_z_mm[path.layer]], pole_pairs, 0.5, 1.0)
        by_kind[kind] = by_kind.get(kind, 0.0) + eddy_loss_w(field, harmonics, thickness[path.layer], omega_e, rho)
    strand_only = by_kind["strand"] * rho / rho_xcoil
    print("eddy loss by Xcoil object kind, W:", {k: round(v, 9) for k, v in by_kind.items()})
    print(f"all kinds / Xcoil pEddy = {sum(by_kind.values()) / XCOIL_P_EDDY_W:.6f}")
    print(f"strand only at Xcoil rho / Xcoil pEddy - 1 = {strand_only / XCOIL_P_EDDY_W - 1:.3e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
