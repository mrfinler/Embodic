r"""DEF-U-M8n-02 lever (U-M8o): wall time of the worker's scene build, ``ready_state``, per example.

Computes each example once, then times ``ready_state`` on that outcome ``--runs`` times per example, the examples
alternating so that drift favours none, and prints the median and range. Every run checks that the scene has the
same anchors and coil marks as the first, so a faster run cannot be one that built less. With ``--profile N`` one
extra run per example, not timed, prints the N functions with the most own time.

Not a test. From the repository root, with the project's interpreter:

    PYTHONPATH=src python tests/ui/qt_shell/scene_build_time.py [--runs 7] [--profile 15] [example ...]
"""

import argparse
import cProfile
import io
import pstats
import statistics
import time

from embodic.api import compute
from embodic.io.examples import load_example
from embodic.io.project import project_from_example, project_provenance
from embodic.ui.viewmodels.outcome import GeometryScene, ready_state

DEFAULT_EXAMPLES = ("spiral_12c10p_d08", "wave_16p_example")


def _fingerprint(scene: GeometryScene | None) -> tuple[object, ...]:
    assert scene is not None, "every packaged example builds a board"
    return tuple((marks.anchors, marks.coils) for marks in scene.marks)


def main() -> None:
    """Time ``ready_state`` per example and print the summary."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("examples", nargs="*", default=DEFAULT_EXAMPLES)
    parser.add_argument("--runs", type=int, default=7)
    parser.add_argument("--profile", type=int, default=0, help="rows of an untimed cProfile run per example")
    args = parser.parse_args()
    outcomes = {}
    for example_id in args.examples:
        project = project_from_example(load_example(example_id))
        outcome = compute(project.design, project_provenance(project))
        assert outcome is not None
        outcomes[example_id] = outcome
    expected = {example_id: _fingerprint(ready_state(outcome).scene) for example_id, outcome in outcomes.items()}
    times: dict[str, list[float]] = {example_id: [] for example_id in outcomes}
    for _ in range(args.runs):
        for example_id, outcome in outcomes.items():
            started = time.perf_counter()
            ready = ready_state(outcome)
            times[example_id].append((time.perf_counter() - started) * 1000)
            assert _fingerprint(ready.scene) == expected[example_id], f"{example_id}: the scene changed between runs"
    for example_id, runs in times.items():
        coils = sum(len(marks.coils) for marks in ready_state(outcomes[example_id]).scene.marks)
        print(
            f"== {example_id}: ready_state median {statistics.median(runs):.1f} ms, range {min(runs):.1f} to "
            f"{max(runs):.1f} ms over {len(runs)} runs; {coils} coil marks"
        )
    for example_id, outcome in outcomes.items() if args.profile else ():
        profile = cProfile.Profile()
        profile.runcall(ready_state, outcome)
        text = io.StringIO()
        pstats.Stats(profile, stream=text).sort_stats("tottime").print_stats(args.profile)
        print(f"-- {example_id} (profiled, not timed):")
        print("\n".join(line for line in text.getvalue().splitlines()[4:] if line.strip()))


if __name__ == "__main__":
    main()
