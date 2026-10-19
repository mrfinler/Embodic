"""REQ-N-02 (D-074): the GUI latency tests run in a fresh pytest process of their own, after the main pytest gate.

A latency test measures the app's GUI thread. After about 4000 other tests in one 2.5 h process the heap and the timers
of the suite made two of them fail on the Windows release run of 0.0.2 (UI-05 103 ms, N02-10 arrival 154 ms); alone, in
a fresh process, they passed five runs of five. The nightly and release profiles therefore leave `latency` out of the
main gate and run it in a gate of its own. The commit profile keeps its expression: it runs no slow test and has no
second process to pay for.
"""

import importlib.util
from pathlib import Path

import pytest
from _pytest.mark.expression import Expression

TOOL = Path(__file__).resolve().parents[3] / "tools" / "ci.py"
spec = importlib.util.spec_from_file_location("ci", TOOL)
assert spec is not None and spec.loader is not None
ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)

LATENCY_GATE = "latency tests (REQ-N-02)"
SPLIT_PROFILES = ["nightly", "release"]


def gates(profile_name: str) -> list:
    """Return the gates of a profile in run order."""
    return ci.gates_for(ci.PROFILES[profile_name])


def names(profile_name: str) -> list[str]:
    """Return the gate names of a profile in run order."""
    return [gate.name for gate in gates(profile_name)]


def gate_named(profile_name: str, name: str):
    """Return the one gate of the profile with this exact name."""
    (gate,) = (gate for gate in gates(profile_name) if gate.name == name)
    return gate


def marker_option_index(gate) -> int:
    """Return the index of the gate's pytest -m option, which follows the `-m pytest` that starts the command."""
    return gate.argv.index("-m", gate.argv.index("pytest"))


def marker_expression(gate) -> str:
    """Return the value of the gate's pytest -m option."""
    return gate.argv[marker_option_index(gate) + 1]


def selects(gate, marks: set[str]) -> bool:
    """Return True when pytest, given the gate's -m expression, would run a test that carries exactly these marks."""
    return Expression.compile(marker_expression(gate)).evaluate(lambda name, **_: name in marks)


def option_values(argv: tuple[str, ...], option: str) -> list[str]:
    """Return the values that follow `option` up to the next option, or the value of `option=value`."""
    for index, arg in enumerate(argv):
        if arg == option:
            end = next((i for i in range(index + 1, len(argv)) if argv[i].startswith("--")), len(argv))
            return list(argv[index + 1 : end])
        if arg.startswith(f"{option}="):
            return [arg.removeprefix(f"{option}=")]
    return []


@pytest.mark.req("REQ-N-02")
@pytest.mark.parametrize("profile_name", SPLIT_PROFILES)
def test_the_latency_gate_runs_once_after_the_main_pytest_gate_and_before_the_trace_matrix(profile_name):
    """Catches a latency gate that runs before the main gate, after the matrix that reads its report, or twice."""
    order = names(profile_name)

    assert order.count(LATENCY_GATE) == 1
    assert order.index("pytest") < order.index(LATENCY_GATE) < next(i for i, n in enumerate(order) if "trace" in n)


@pytest.mark.req("REQ-N-02")
def test_the_commit_profile_has_no_latency_gate_and_keeps_its_marker_expression():
    """Catches the second process leaking into every commit, which runs no slow test (D-074)."""
    assert LATENCY_GATE not in names("commit")
    assert marker_expression(gate_named("commit", "pytest")) == "not slow and not manual"


def split_case(*marks: str, in_main: bool, in_latency: bool):
    """Return the marks of a test and where it must run, as one parameter set named after the marks."""
    return pytest.param(set(marks), in_main, in_latency, id="+".join(marks))


SPLIT_CASES = [
    split_case("req", "slow", "latency", in_main=False, in_latency=True),
    split_case("req", "latency", in_main=False, in_latency=True),
    split_case("req", "slow", in_main=True, in_latency=False),
    split_case("req", in_main=True, in_latency=False),
    split_case("req", "latency", "manual", in_main=False, in_latency=False),
    split_case("req", "manual", in_main=False, in_latency=False),
]


@pytest.mark.req("REQ-N-02")
@pytest.mark.parametrize("profile_name", SPLIT_PROFILES)
@pytest.mark.parametrize(("marks", "in_main", "in_latency"), SPLIT_CASES)
def test_every_test_that_is_not_manual_runs_in_exactly_one_of_the_two_gates(profile_name, marks, in_main, in_latency):
    """Catches a latency test that runs in both processes or in neither, and a manual test that reaches either."""
    main, latency = gate_named(profile_name, "pytest"), gate_named(profile_name, LATENCY_GATE)

    assert (selects(main, marks), selects(latency, marks)) == (in_main, in_latency)


@pytest.mark.req("REQ-N-02")
@pytest.mark.parametrize("profile_name", SPLIT_PROFILES)
def test_the_latency_gate_is_a_second_pytest_process_that_differs_from_the_main_gate_only_in_selection(profile_name):
    """Catches a latency gate that narrows the test paths, which would drop a latency test outside them unseen.

    The main gate deselects `latency`, so a latency test that the second gate does not collect would run nowhere.
    """
    main, latency = gate_named(profile_name, "pytest"), gate_named(profile_name, LATENCY_GATE)

    def shared(gate) -> list[str]:
        """Return the arguments of the gate without its marker expression and its report path."""
        option = marker_option_index(gate)
        return [
            a for i, a in enumerate(gate.argv) if i not in (option, option + 1) and not a.startswith("--req-report=")
        ]

    assert latency.argv[1:3] == ("-m", "pytest") == main.argv[1:3]
    assert shared(latency) == shared(main)
    assert latency.env == main.env
    assert option_values(latency.argv, "--req-report") != option_values(main.argv, "--req-report")
    assert option_values(latency.argv, "--req-report") and option_values(main.argv, "--req-report")


@pytest.mark.req("REQ-N-02", "REQ-T-09")
@pytest.mark.parametrize("profile_name", SPLIT_PROFILES)
def test_the_trace_matrix_gate_reads_the_report_of_every_pytest_gate(profile_name):
    """Catches a matrix that reads the main report only: the latency tests would count as not run."""
    trace = next(gate for gate in gates(profile_name) if gate.name.startswith("trace matrix"))
    written = [
        *option_values(gate_named(profile_name, "pytest").argv, "--req-report"),
        *option_values(gate_named(profile_name, LATENCY_GATE).argv, "--req-report"),
    ]

    assert option_values(trace.argv, "--report") == written


@pytest.mark.req("REQ-T-09")
def test_the_commit_trace_matrix_gate_reads_the_one_report_there_is():
    """Catches a commit profile whose matrix waits for a latency report that no gate writes."""
    trace = next(gate for gate in gates("commit") if gate.name.startswith("trace matrix"))

    assert option_values(trace.argv, "--report") == option_values(gate_named("commit", "pytest").argv, "--req-report")
