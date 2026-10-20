r"""U-D27: the Rust port of ``integrate_path`` against the Python kernel of 0.0.4, on the inputs ``analyse`` gives it.

Not a test. Build the library first (see u_d27_rust_study.md), then, one process at a time:

    PYTHONPATH=<tree>/src python emf_bench.py <libu_d27_emf.so> [--rounds 7]

Records every ``integrate_path`` call of ``analyse`` on the five packaged examples, then:

- identity: each call through Python and through Rust (glibc ``cexp`` and Rust ``sin``/``cos``), compared bit for bit;
- kernel time: per round and example, all calls through Python, through the Rust wrapper (``discretise_path`` in
  Python, packing, the Rust loop) and through the Rust loop alone on packed rows, the sides alternating;
- physics time: ``analyse`` with the Python kernel and with the Rust wrapper, alternating, and its JSON compared.
"""

import argparse
import ctypes
import json
import statistics
import sys
import time
from pathlib import Path

import numpy as np

from embodic.api import compute_project
from embodic.geometry.discretise import discretise_path
from embodic.io.project import load_project, project_provenance
from embodic.physics.analyse import analyse
from embodic.physics.emf import _RADIAL_EPS_MM, PathField, integrate_path
from embodic.results import load_registry

TREE = Path(__file__).resolve().parents[5]
STEMS = ("serpentine_16p_example", "spiral_12c10p_d08", "spiral_12c14p", "spiral_12c16p_default", "wave_16p_example")
F64P = ctypes.POINTER(ctypes.c_double)
analyse_module = sys.modules["embodic.physics.analyse"]  # the package re-exports the function under the module's name


def load(lib_path: str) -> ctypes.CDLL:
    lib = ctypes.CDLL(lib_path)
    fn = lib.u_d27_integrate_path
    fn.restype = None
    fn.argtypes = [F64P, ctypes.c_size_t, F64P, F64P, ctypes.c_size_t, ctypes.c_size_t, F64P, ctypes.c_double,
                   ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_int,
                   F64P, F64P, F64P, F64P]  # fmt: skip
    return lib


def pack(prims, max_segment_mm: float) -> np.ndarray:
    segments = discretise_path(prims, max_segment_mm)
    rows = np.array([(g.x1_mm, g.y1_mm, g.x2_mm, g.y2_mm, g.length_mm, g.width_mm) for g in segments], dtype=float)
    return rows.reshape(-1, 6)


def rust_kernel(lib, rows: np.ndarray, table, pole_pairs: int, edge_decay_mm: float, use_cexp: int) -> PathField:
    n_h, n_cols = table.bz_t.shape
    bz_t = np.ascontiguousarray(table.bz_t, dtype=np.float64)
    bt_t = np.ascontiguousarray(table.bt_t, dtype=np.float64)
    harmonics = np.array(table.harmonics, dtype=np.float64)
    lam = np.zeros(n_h, dtype=np.complex128)
    ez, et, edge = np.zeros(n_h), np.zeros(n_h), np.zeros(2)
    ptr = lambda a: a.ctypes.data_as(F64P)  # noqa: E731
    lib.u_d27_integrate_path(ptr(rows), len(rows), ptr(bz_t), ptr(bt_t), n_h, n_cols, ptr(harmonics),
                             float(pole_pairs), table.r_inner_mm, table.r_outer_mm, _RADIAL_EPS_MM, edge_decay_mm,
                             use_cexp, ptr(lam.view(np.float64)), ptr(ez), ptr(et), ptr(edge))  # fmt: skip
    return PathField(flux_linkage_t_mm2=lam, eddy_bz_sum=ez, eddy_bt_sum=et, edge_weight=float(edge[0]),
                     edge_weighted=float(edge[1]))  # fmt: skip


def rust_wrapper(lib, use_cexp: int = 1):
    def integrate(prims, table, pole_pairs, max_segment_mm, edge_decay_mm) -> PathField:
        return rust_kernel(lib, pack(prims, max_segment_mm), table, pole_pairs, edge_decay_mm, use_cexp)

    return integrate


def record(stem: str) -> tuple[list[tuple], tuple]:
    path = TREE / "resources" / "examples" / f"{stem}.embodic.json"
    project, _ = load_project(path)
    outcome = compute_project(path)
    calls: list[tuple] = []

    def recorder(*args):
        calls.append(args)
        return integrate_path(*args)

    analyse_module.integrate_path = recorder
    try:
        analyse(project.design, outcome.boards, project_provenance(project), load_registry())
    finally:
        analyse_module.integrate_path = integrate_path
    assert calls, f"{stem}: analyse made no integrate_path call through the patched name"
    return calls,(project.design, outcome.boards, project_provenance(project), load_registry())


def bits(a) -> np.ndarray:
    return np.atleast_1d(np.asarray(a)).view(np.uint64)


def compare(py: PathField, rs: PathField) -> list[tuple[str, float]]:
    """Fields whose bits differ, with the largest relative difference of each."""
    out = []
    for name in ("flux_linkage_t_mm2", "eddy_bz_sum", "eddy_bt_sum", "edge_weight", "edge_weighted"):
        a, b = getattr(py, name), getattr(rs, name)
        if not np.array_equal(bits(a), bits(b)):
            a, b = np.atleast_1d(a), np.atleast_1d(b)
            scale = np.maximum(np.abs(a), np.finfo(float).tiny)
            out.append((name, float(np.max(np.abs(a - b) / scale))))
    return out


def timed(work) -> float:
    started = time.perf_counter()
    work()
    return time.perf_counter() - started


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("lib")
    parser.add_argument("--rounds", type=int, default=7)
    args = parser.parse_args()
    lib = load(args.lib)
    report: dict[str, object] = {"numpy": np.__version__, "python": sys.version.split()[0], "examples": {}}
    for stem in STEMS:
        calls, physics_args = record(stem)
        packed = [pack(c[0], c[3]) for c in calls]
        segments = sum(len(p) for p in packed)
        diffs = {"cexp": [], "sincos": []}
        for c, rows in zip(calls, packed, strict=True):
            py = integrate_path(*c)
            for label, flag in (("cexp", 1), ("sincos", 0)):
                found = compare(py, rust_kernel(lib, rows, c[1], c[2], c[4], flag))
                if found:
                    diffs[label].append(found)
        python_s, wrapper_s, kernel_s = [], [], []
        wrap = rust_wrapper(lib)
        for _ in range(args.rounds + 1):
            python_s.append(timed(lambda: [integrate_path(*c) for c in calls]))
            wrapper_s.append(timed(lambda: [wrap(*c) for c in calls]))
            kernel_s.append(timed(lambda: [rust_kernel(lib, r, c[1], c[2], c[4], 1) for c, r in zip(calls, packed)]))
        python_s, wrapper_s, kernel_s = python_s[1:], wrapper_s[1:], kernel_s[1:]
        phys_py, phys_rs = [], []
        want = json.dumps(analyse(*physics_args).to_json(), sort_keys=True)
        analyse_module.integrate_path = wrap
        same = json.dumps(analyse(*physics_args).to_json(), sort_keys=True) == want
        analyse_module.integrate_path = integrate_path
        for _ in range(args.rounds):
            phys_py.append(timed(lambda: analyse(*physics_args)))
            analyse_module.integrate_path = wrap
            phys_rs.append(timed(lambda: analyse(*physics_args)))
            analyse_module.integrate_path = integrate_path
        med = statistics.median
        row = {
            "paths": len(calls),
            "segments": segments,
            "calls_with_bit_differences": {k: len(v) for k, v in diffs.items()},
            "largest_relative_difference": {k: max((d for f in v for _, d in f), default=0.0) for k, v in diffs.items()},
            "fields_differing": {k: sorted({n for f in v for n, _ in f}) for k, v in diffs.items()},
            "analysis_json_identical_with_rust": same,
            "python_kernel_s": python_s,
            "rust_wrapper_s": wrapper_s,
            "rust_loop_s": kernel_s,
            "analyse_python_s": phys_py,
            "analyse_rust_s": phys_rs,
            "ratio_kernel": med(python_s) / med(wrapper_s),
            "ratio_loop": med(python_s) / med(kernel_s),
            "ratio_analyse": med(phys_py) / med(phys_rs),
        }
        report["examples"][stem] = row
        print(f"{stem}: {len(calls)} paths, {segments} chords; bit differences cexp {len(diffs['cexp'])}, "
              f"sincos {len(diffs['sincos'])} (max rel {row['largest_relative_difference']['sincos']:.3g}); "
              f"analysis JSON identical {same}")  # fmt: skip
        print(f"  kernel python {med(python_s) * 1e3:.1f} ms [{min(python_s) * 1e3:.1f}-{max(python_s) * 1e3:.1f}], "
              f"rust wrapper {med(wrapper_s) * 1e3:.1f} ms [{min(wrapper_s) * 1e3:.1f}-{max(wrapper_s) * 1e3:.1f}], "
              f"rust loop {med(kernel_s) * 1e3:.2f} ms; x{row['ratio_kernel']:.1f} wrapper, x{row['ratio_loop']:.0f} loop")  # fmt: skip
        print(f"  analyse python {med(phys_py) * 1e3:.0f} ms [{min(phys_py) * 1e3:.0f}-{max(phys_py) * 1e3:.0f}], "
              f"rust {med(phys_rs) * 1e3:.0f} ms [{min(phys_rs) * 1e3:.0f}-{max(phys_rs) * 1e3:.0f}], x{row['ratio_analyse']:.2f}")  # fmt: skip
    out = Path(__file__).with_name("emf_bench.json")
    out.write_text(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
