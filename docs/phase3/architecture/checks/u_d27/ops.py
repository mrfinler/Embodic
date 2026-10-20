r"""U-D27: wall and CPU time of the operations of embodic 0.0.4, and who owns that time.

Not a test. Run with the project's interpreter, one process at a time, from any directory:

    PYTHONPATH=<tree>/src QT_QPA_PLATFORM=offscreen python ops.py time <group> [--rounds 5] [--out runs.json]
    PYTHONPATH=<tree>/src QT_QPA_PLATFORM=offscreen python ops.py sample <group> <op> [--seconds 3]
    python ops.py split <raw.txt> [--all]

``time`` sets every operation of the group up, runs each once untimed, then runs ``rounds`` rounds of all of them in
turn, so drift and the other units' load favour none. Each run records wall time and this process's CPU time; each
round records the CPU the rest of the machine used meanwhile (from /proc/stat, in cores). ``sample`` repeats one
operation for ``seconds`` inside ``_measured`` while py-spy records it (``py-spy record --native --idle -f raw``);
``split`` then sums the samples under ``_measured`` by the owner of the leaf frame. Groups: compute, export, project,
hostile, gui, cold.
"""

import argparse
import dataclasses
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile
import time
from collections import Counter
from collections.abc import Callable
from pathlib import Path

TREE = Path(os.environ.get("EMBODIC_TREE", "/home/claude/wt/U-D27"))
EXAMPLES = TREE / "resources" / "examples"
STEMS = {
    "serp": "serpentine_16p_example",
    "d08": "spiral_12c10p_d08",
    "c14": "spiral_12c14p",
    "default": "spiral_12c16p_default",
    "wave": "wave_16p_example",
}
FIXED_UTC = "2026-10-20T00:00:00Z"
Thunk = Callable[[], object]
Timing = tuple[float, float]  # wall s, process CPU s


def _project(key: str):
    from embodic.io.project import load_project

    project, issues = load_project(EXAMPLES / f"{STEMS[key]}.embodic.json")
    assert project is not None and not any(i.severity.name == "ERROR" for i in issues), issues
    return project


def compute_ops() -> dict[str, Thunk]:
    from embodic.api import _geometry, compute_project, outcome_to_json
    from embodic.drc import run_drc
    from embodic.io.project import project_provenance
    from embodic.physics import analyse
    from embodic.results import load_registry

    registry = load_registry()
    ops: dict[str, Thunk] = {}
    for key, stem in STEMS.items():
        project = _project(key)
        design, provenance = project.design, project_provenance(project)
        outcome = compute_project(EXAMPLES / f"{stem}.embodic.json")
        assert outcome.analysis is not None and outcome.drc is not None, outcome.issues
        boards = outcome.boards
        expected = [len(r.violations) for r in outcome.drc]

        def drc(boards=boards, design=design, expected=expected) -> object:
            reports = [run_drc(b, design.drc_rules, use_symmetry=True) for b in boards.boards]
            assert [len(r.violations) for r in reports] == expected
            return reports

        def physics(design=design, boards=boards, provenance=provenance, want=outcome.analysis.to_json()) -> object:
            result = analyse(design, boards, provenance, registry)
            assert result.to_json() == want
            return result

        def generate(design=design, want=boards.stack_hash) -> object:
            built = _geometry(design, registry).built
            assert built.stack_hash == want
            return built

        def results(outcome=outcome) -> object:
            document = outcome_to_json(outcome)
            return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)

        def end_to_end(path=EXAMPLES / f"{stem}.embodic.json", want=outcome.design_hash) -> object:
            done = compute_project(path)
            assert done.design_hash == want and done.analysis is not None
            return done

        ops |= {
            f"generate/{key}": generate,
            f"drc/{key}": drc,
            f"physics/{key}": physics,
            f"results/{key}": results,
            f"compute/{key}": end_to_end,
        }
    return ops


def export_ops() -> dict[str, Thunk]:
    from embodic.api import compute_project
    from embodic.io.dxf_writer import write_dxf
    from embodic.io.exporters import ExportSummary
    from embodic.io.report import write_report_pdf
    from embodic.io.svg_writer import write_svg

    folder = Path(tempfile.mkdtemp(prefix="u_d27_export_"))
    ops: dict[str, Thunk] = {}
    for key, stem in STEMS.items():
        outcome = compute_project(EXAMPLES / f"{stem}.embodic.json")
        writers = {
            "svg": lambda o, p: write_svg(o, p, allow_drc_errors=True),
            "dxf": lambda o, p: write_dxf(o, p, "complete", allow_drc_errors=True),
            "pdf": lambda o, p: write_report_pdf(o, p),
        }
        for kind, writer in writers.items():

            def export(writer=writer, outcome=outcome, path=folder / f"{key}.{kind}") -> object:
                summary = writer(outcome, path)
                assert isinstance(summary, ExportSummary) and path.stat().st_size > 0, summary
                return summary

            ops[f"export_{kind}/{key}"] = export
    return ops


def project_ops() -> dict[str, Thunk]:
    from embodic.io.project import ProjectFile, load_project, save_project

    folder = Path(tempfile.mkdtemp(prefix="u_d27_project_"))
    ops: dict[str, Thunk] = {}
    for key, stem in STEMS.items():
        path = EXAMPLES / f"{stem}.embodic.json"
        project = _project(key)

        def load(path=path) -> object:
            loaded, _ = load_project(path)
            assert isinstance(loaded, ProjectFile)
            return loaded

        def save(project=project, target=folder / f"{key}.embodic.json") -> object:
            return save_project(target, project, saved_utc=FIXED_UTC)

        ops |= {f"load/{key}": load, f"save/{key}": save}
    return ops


def hostile_design(tiniest: bool):
    """The DEF-M6b-01 example of test_serpentine_inputs.py: r_inner 60, span 40, rule-minimum width, 30 turns."""
    base = _project("serp").design
    size = 5e-324 if tiniest else None
    winding = dataclasses.replace(
        base.winding,
        r_inner_mm=60.0,
        r_outer_mm=100.0,
        trace_width_mm=base.drc_rules.min_trace_width_mm,
        clearance_mm=size if tiniest else base.winding.clearance_mm,
        turns=30,
    )
    return dataclasses.replace(
        base,
        winding=winding,
        vias=dataclasses.replace(base.vias, pad_mm=size if tiniest else base.vias.pad_mm),
        connection=dataclasses.replace(
            base.connection, terminal_pad_mm=size if tiniest else base.connection.terminal_pad_mm
        ),
    )


def hostile_ops() -> dict[str, Thunk]:
    from embodic.generators import generate_serpentine
    from embodic.results import load_registry

    registry = load_registry()
    ops: dict[str, Thunk] = {}
    for label, tiniest in (("near_zero", True), ("default_sizes", False)):
        design = hostile_design(tiniest)

        def build(design=design) -> object:
            built = generate_serpentine(design, registry)
            assert hasattr(built, "stack_hash"), built
            return built

        ops[f"serpentine_hostile/{label}"] = build
    return ops


def _pump(ms: int) -> None:
    from PySide6.QtCore import QEventLoop, QTimer

    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def gui_ops() -> dict[str, Thunk]:
    import functools

    from PySide6.QtCore import QSettings, QStandardPaths
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication

    from embodic.api import compute_project
    from embodic.ui.app import QSettingsStore, create_shell, qt_application
    from embodic.ui.theme import load_theme
    from embodic.ui.viewmodels.appearance import PhaseRenderMode
    from embodic.ui.viewmodels.outcome import OutcomeViewModel, geometry_scene
    from embodic.ui.viewmodels.session import DesignSession
    from embodic.ui.views.geometry_view import GeometryView

    hooked: dict[str, list[Timing]] = {}

    def hook(owner: type, name: str, label: str) -> None:
        original = getattr(owner, name)

        @functools.wraps(original)
        def _measured_hook(*args, **kwargs):
            wall, cpu = time.perf_counter(), time.thread_time()
            try:
                return original(*args, **kwargs)
            finally:
                hooked.setdefault(label, []).append((time.perf_counter() - wall, time.thread_time() - cpu))

        setattr(owner, name, _measured_hook)

    hook(DesignSession, "load_example", "open")
    hook(OutcomeViewModel, "on_finished", "result")
    QStandardPaths.setTestModeEnabled(True)
    app = qt_application()
    root = Path(tempfile.mkdtemp(prefix="u_d27_gui_"))
    store = QSettingsStore(QSettings(str(root / "settings.ini"), QSettings.Format.IniFormat))
    from embodic.ui.views.main_window import ShellPaths

    window = create_shell(store, ShellPaths(recovery_dir=root / "recovery"), prefers_dark=lambda: False).window
    window.resize(1280, 800)
    window.show()
    QTest.qWaitForWindowExposed(window)
    _pump(500)

    def open_example(stem: str) -> dict[str, Timing]:
        hooked.clear()
        window.session.load_example(stem)
        started = time.perf_counter()
        while not hooked.get("result") and time.perf_counter() - started < 60:
            _pump(5)
        assert hooked.get("result"), "no result arrived"
        _pump(200)
        return {"open": hooked["open"][0], "result": sum_timings(hooked["result"])}

    tokens = load_theme("dark")
    serp = geometry_scene(compute_project(EXAMPLES / f"{STEMS['serp']}.embodic.json"))
    view = GeometryView()
    view.resize(1280, 800)
    view.show()
    none = frozenset[str]()
    view.show_geometry(serp, tokens, PhaseRenderMode.COLOUR, none)
    QApplication.processEvents()
    view.viewport().grab()
    modes = [PhaseRenderMode.GREYSCALE_HATCH, PhaseRenderMode.COLOUR]
    flips = {"zoom": 0, "pan": 0, "redraw": 0}

    def redraw() -> object:
        flips["redraw"] += 1
        view.show_geometry(serp, tokens, modes[flips["redraw"] % 2], none)
        QApplication.processEvents()
        return view.viewport().grab()

    def zoom() -> object:
        flips["zoom"] += 1
        view.zoom_by(1.25 if flips["zoom"] % 2 else 0.8)
        QApplication.processEvents()
        return None

    def pan() -> object:
        if flips["pan"] == 0:
            view.zoom_by(4)
            QApplication.processEvents()
        flips["pan"] += 1
        bar = view.horizontalScrollBar()
        bar.setValue(bar.value() + (100 if flips["pan"] % 2 else -100))
        QApplication.processEvents()
        return None

    def d08() -> dict[str, Timing]:
        got = open_example(STEMS["d08"])
        return {"gui_open/d08": got["open"], "gui_result/d08": got["result"]}

    def default() -> dict[str, Timing]:
        got = open_example(STEMS["default"])
        return {"gui_open/default": got["open"], "gui_result/default": got["result"]}

    return {"gui_shell/d08": d08, "gui_shell/default": default, "gui_redraw/serp": redraw,
            "gui_zoom/serp": zoom, "gui_pan/serp": pan}  # fmt: skip


def sum_timings(timings: list[Timing]) -> Timing:
    return sum(t[0] for t in timings), sum(t[1] for t in timings)


COLD_CHILD = """
import sys, time
from pathlib import Path
def _measured():
    from embodic.ui import app as shell
    qt = shell.qt_application()
    window = shell.create_shell(shell.QSettingsStore(), shell.ShellPaths(recovery_dir=Path(sys.argv[1]))).window
    window.resize(1280, 800)
    window.show()
    qt.processEvents()
    window.grab()
    assert window.isVisible()
_measured()
print("shown", flush=True)
"""


def cold_ops() -> dict[str, Thunk]:
    import resource

    root = Path(tempfile.mkdtemp(prefix="u_d27_cold_"))
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen", "HOME": str(root), "XDG_CONFIG_HOME": str(root)}
    count = [0]

    def cold() -> dict[str, Timing]:
        count[0] += 1
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        started = time.perf_counter()
        done = subprocess.run([sys.executable, "-c", COLD_CHILD, str(root / f"r{count[0]}")], env=env,
                              capture_output=True, encoding="utf-8", check=False)  # fmt: skip
        wall = time.perf_counter() - started
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        assert done.stdout.strip().endswith("shown"), done.stderr
        cpu = (after.ru_utime - before.ru_utime) + (after.ru_stime - before.ru_stime)
        return {"gui_cold_start": (wall, cpu)}

    return {"gui_cold_start": cold}


GROUPS: dict[str, Callable[[], dict[str, Thunk]]] = {
    "compute": compute_ops,
    "export": export_ops,
    "project": project_ops,
    "hostile": hostile_ops,
    "gui": gui_ops,
    "cold": cold_ops,
}


def _busy_jiffies() -> tuple[int, int]:
    """Busy jiffies of the whole machine and of this process with its children."""
    fields = open("/proc/stat").readline().split()[1:]
    total_busy = sum(map(int, fields)) - int(fields[3]) - int(fields[4])  # all minus idle and iowait
    own = open("/proc/self/stat").read().rsplit(")", 1)[1].split()
    return total_busy, sum(int(v) for v in own[11:15])  # utime stime cutime cstime


def _run(thunk: Thunk, name: str) -> dict[str, Timing]:
    wall, cpu = time.perf_counter(), time.process_time()
    got = thunk()
    timing = (time.perf_counter() - wall, time.process_time() - cpu)
    return got if isinstance(got, dict) else {name: timing}


def time_group(group: str, rounds: int, out: Path | None) -> None:
    ops = GROUPS[group]()
    for name, thunk in ops.items():
        _run(thunk, name)
    samples: dict[str, list[Timing]] = {}
    others: list[float] = []
    loads = [os.getloadavg()[0]]
    hz = os.sysconf("SC_CLK_TCK")
    for _ in range(rounds):
        busy0, own0 = _busy_jiffies()
        started = time.perf_counter()
        for name, thunk in ops.items():
            for key, timing in _run(thunk, name).items():
                samples.setdefault(key, []).append(timing)
        busy1, own1 = _busy_jiffies()
        others.append(((busy1 - busy0) - (own1 - own0)) / hz / (time.perf_counter() - started))
        loads.append(os.getloadavg()[0])
    report = {
        "group": group,
        "rounds": rounds,
        "python": sys.version.split()[0],
        "loadavg_1min": loads,
        "other_processes_cores_per_round": others,
        "samples_wall_cpu_s": samples,
    }
    for name, runs in samples.items():
        walls = [w * 1000 for w, _ in runs]
        cpus = [c * 1000 for _, c in runs]
        print(f"{name:32s} wall median {statistics.median(walls):9.2f} ms  range {min(walls):9.2f} to "
              f"{max(walls):9.2f}  cpu median {statistics.median(cpus):9.2f} ms")  # fmt: skip
    print(f"other processes, cores per round: {[round(v, 2) for v in others]}; loadavg 1 min: {loads}")
    if out:
        out.write_text(json.dumps(report, indent=1))


def _measured(thunk: Thunk, name: str, seconds: float, min_runs: int) -> int:
    count, started = 0, time.perf_counter()
    while count < min_runs or time.perf_counter() - started < seconds:
        _run(thunk, name)
        count += 1
    return count


def sample(group: str, op: str, seconds: float, min_runs: int) -> None:
    ops = GROUPS[group]()
    if min_runs > 1:
        _run(ops[op], op)
    print(f"{op}: {_measured(ops[op], op, seconds, min_runs)} runs", flush=True)


QT_LIBS = re.compile(r"libQt6|PySide6|shiboken|libpyside|libfreetype|libharfbuzz|libfontconfig|libpng|libjpeg|libicu|libglib|libxkb|libdbus|libgthread|libb2|libpcre2|libdouble-conversion|libmd4c|libbrotli")
IO_CALLS = re.compile(r"^(__)?(libc_)?(read|write|pread64|pwrite64|open|open64|openat|openat64|close|stat|stat64|fstat|fstat64|lstat|newfstatat|statx|lseek|lseek64|getdents|getdents64|fsync|fdatasync|rename|unlink|readlink|access|faccessat|mkdir|mkstemp|__GI___libc_(read|write|open64|close)|__GI___(read|write|close|open64|fstatat64))(_nocancel)?$")
WAIT_CALLS = re.compile(r"poll|select|epoll|futex|cond_wait|cond_timedwait|nanosleep|sem_|pthread_mutex_lock|__lll_lock_wait|take_gil|wait4|waitpid|recv")


def _owner(frames: list[str]) -> str:
    """Owner of one stack sample: the leaf frame's library, walking up through allocator and maths helpers.

    py-spy drops the interpreter's own native frames, so a C library that Python code calls (libm through ``math``,
    libz through ``zlib``) sits right under the Python frame; that time is C, while libc's allocator under a Python
    frame is the interpreter's.
    """
    crossed_c_library = False
    for frame in reversed(frames):
        name, _, where = frame.rpartition(" (")
        where = where.rstrip(")")
        if ".so" not in where and where not in ("python3.11", "?"):
            if crossed_c_library:
                return "other_c"
            return "python_ours" if where.startswith("embodic/") else "python_other"
        if where in ("python3.11", "?") or "libpython" in where:
            return "python_other" if where == "?" else "interpreter_c"
        if "numpy" in where:
            return "numpy"
        if QT_LIBS.search(where):
            return "qt"
        if where.startswith("libc.so") or where.startswith("ld-linux") or where.startswith("libpthread"):
            if IO_CALLS.match(name):
                return "io"
            if WAIT_CALLS.search(name):
                return "wait"
            continue  # malloc, memcpy and the like belong to their caller
        if where.startswith(("libm.so", "libgcc", "libstdc++", "libz.so")):
            crossed_c_library = True
            continue  # belongs to its caller: NumPy, Qt, or (under a Python frame) other C
        if "cpython-311" in where or where.startswith("libcrypto") or where.startswith("libexpat"):
            return "other_c"
        return "other_native:" + where
    return "unknown"


def split(raw: Path, keep_all: bool, frame: str = "_measured") -> dict[str, int]:
    owners: Counter[str] = Counter()
    hot: Counter[str] = Counter()
    for line in raw.read_text().splitlines():
        stack, _, n = line.rpartition(" ")
        frames = stack.split(";")
        cut = next((i for i, f in enumerate(frames) if re.match(frame, f)), None)
        if cut is None and not keep_all:
            continue
        frames = frames if cut is None else frames[cut:]
        owners[_owner(frames)] += int(n)
        ours = [f for f in frames if "(embodic/" in f]
        if ours:
            hot[ours[-1].split(" (")[0] + " " + ours[-1].split(" (")[1].split(":")[0]] += int(n)
    total = sum(owners.values())
    print(f"{raw.name}: {total} samples")
    for owner, n in owners.most_common():
        print(f"  {owner:28s} {n:7d} {100 * n / total:5.1f} %")
    print("  innermost embodic frame, top 8:")
    for frame, n in hot.most_common(8):
        print(f"    {100 * n / total:5.1f} %  {frame}")
    return dict(owners)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    t = sub.add_parser("time")
    t.add_argument("group", choices=GROUPS)
    t.add_argument("--rounds", type=int, default=5)
    t.add_argument("--out", type=Path)
    s = sub.add_parser("sample")
    s.add_argument("group", choices=GROUPS)
    s.add_argument("op")
    s.add_argument("--seconds", type=float, default=3.0)
    s.add_argument("--min-runs", type=int, default=3)
    p = sub.add_parser("split")
    p.add_argument("raw", type=Path, nargs="+")
    p.add_argument("--all", action="store_true")
    p.add_argument("--frame", default="_measured", help="regex: keep samples under the first frame it matches")
    args = parser.parse_args()
    if args.mode == "time":
        time_group(args.group, args.rounds, args.out)
    elif args.mode == "sample":
        sample(args.group, args.op, args.seconds, args.min_runs)
    else:
        for raw in args.raw:
            split(raw, args.all, args.frame)


if __name__ == "__main__":
    main()
