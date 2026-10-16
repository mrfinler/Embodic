"""Smoke test for the FEA fallback toolchain (gmsh + GetDP, cross-checked with scikit-fem).

Case: 2-D magnet disk (radius a, B_r along x, recoil mu_r) in an air disk (radius R), A_z = 0 on r = R.
Closed form (derived in docs/phase3/evidence/fea_toolchain.md): the interior field is uniform,
B_x = B_r k / (mu_r + k), k = (1 - q) / (1 + q), q = (a / R)^2.

Run: /home/claude/fea/venv/bin/python -I smoke_pm_cylinder.py [work_dir]
The inputs are copied to work_dir (default /home/claude/fea/smoke/run), so meshes never land next to this file.
"""

import pathlib
import re
import shutil
import subprocess
import sys

import numpy as np
from skfem import Basis, BilinearForm, ElementTriP1, LinearForm, MeshTri, asm, condense, solve
from skfem.helpers import dot, grad

INPUTS = pathlib.Path(__file__).resolve().parent / "pm_cylinder"
CASE = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/home/claude/fea/smoke/run")
A, R, BR, MU_R = 0.01, 0.05, 1.33, 1.05
MU0 = 4e-7 * np.pi
MESH_SIZES = (0.002, 0.001, 0.0005)


def closed_form_bx() -> float:
    q = (A / R) ** 2
    k = (1 - q) / (1 + q)
    return BR * k / (MU_R + k)


def run(cmd: list[str]) -> str:
    out = subprocess.run(cmd, cwd=CASE, capture_output=True, text=True, check=True)
    return out.stdout + out.stderr


def getdp_bx(msh: str) -> tuple[float, str]:
    log = run(["getdp", "pm.pro", "-msh", msh, "-solve", "MagSta_a", "-pos", "Get_B"])
    fields = (CASE / "b_center.txt").read_text().split()
    return float(fields[8]), log


def read_msh22(path: pathlib.Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    text = path.read_text()
    nodes_block = re.search(r"\$Nodes\n(.*?)\$EndNodes", text, re.S).group(1).split("\n")
    n = int(nodes_block[0])
    ids, xy = {}, np.empty((2, n))
    for i, line in enumerate(nodes_block[1 : n + 1]):
        tag, x, y, _ = line.split()
        ids[int(tag)] = i
        xy[:, i] = float(x), float(y)
    elems_block = re.search(r"\$Elements\n(.*?)\$EndElements", text, re.S).group(1).split("\n")
    tris, phys = [], []
    for line in elems_block[1 : int(elems_block[0]) + 1]:
        f = [int(v) for v in line.split()]
        if f[1] == 2:
            ntags = f[2]
            tris.append([ids[t] for t in f[3 + ntags : 6 + ntags]])
            phys.append(f[3])
    return xy, np.array(tris).T, np.array(phys)


def skfem_bx(msh: str) -> float:
    xy, t, phys = read_msh22(CASE / msh)
    mesh = MeshTri(xy, t)
    basis = Basis(mesh, ElementTriP1())
    in_magnet = basis.zero_w() + (phys == 1)[:, None]
    nu = (in_magnet / MU_R + (1 - in_magnet)) / MU0

    @BilinearForm
    def stiffness(u, v, w):
        return w["nu"] * dot(grad(u), grad(v))

    @LinearForm
    def magnet(v, w):
        return w["nu"] * w["m"] * BR * grad(v)[1]

    K = asm(stiffness, basis, nu=nu)
    f = asm(magnet, basis, nu=nu, m=in_magnet)
    outer = np.nonzero(np.isclose(np.hypot(*xy), R, rtol=1e-6))[0]
    az = solve(*condense(K, f, D=outer))
    centre = int(np.argmin(np.hypot(*xy)))
    elems = np.nonzero((t == centre).any(axis=0))[0]
    dadx = basis.interpolate(az).grad[1]
    return float(dadx[elems].mean())


def main() -> None:
    CASE.mkdir(parents=True, exist_ok=True)
    for name in ("pm.geo", "pm.pro"):
        shutil.copy(INPUTS / name, CASE / name)
    ref = closed_form_bx()
    print(f"closed form B_x inside magnet = {ref:.6f} T")
    print("lc_m      nodes  getdp_Bx_T   err_%    skfem_Bx_T  err_%")
    for lc in MESH_SIZES:
        msh = f"pm_lc{lc:g}.msh"
        gmsh_log = run(["gmsh", "-2", "-format", "msh22", "-setnumber", "lc", str(lc), "pm.geo", "-o", msh])
        nodes = re.search(r"(\d+) nodes", gmsh_log).group(1)
        bx_g, getdp_log = getdp_bx(msh)
        bx_s = skfem_bx(msh)
        print(
            f"{lc:<9g} {nodes:>6} {bx_g:11.6f} {100 * (bx_g / ref - 1):7.3f} "
            f"{bx_s:11.6f} {100 * (bx_s / ref - 1):7.3f}"
        )
    print("--- GetDP log, last 6 lines of the finest run ---")
    print("\n".join(getdp_log.strip().splitlines()[-6:]))


if __name__ == "__main__":
    main()
