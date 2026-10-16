"""REQ-N-09 (V3-01 gap N-09): a Parameters entry of a physics docstring names a unit, not only the parameter.

MT-04 (`test_mt04_physics_docstrings.py`) matches `name:` only, so `width : float / Trace width.` passes it.
The unit tokens come from `embodic.units.Unit` (canonical code and display form).
"""

import ast
import re

import pytest

from embodic.units import Unit

# Unit.ONE ("one") and Unit.COUNT ("count") are ordinary English words, so they would turn any sentence into a unit.
UNIT_TOKENS = tuple(
    sorted(
        {token for unit in Unit if unit not in (Unit.ONE, Unit.COUNT) for token in (unit.value, unit.display())},
        key=len,
        reverse=True,
    )
)
NUMERIC_TYPE = re.compile(r"float|FloatArray|NDArray")
ENTRY = re.compile(r"^(?P<name>\w+)\s*:\s*(?P<type>.+)$")
SECTION_RULE = re.compile(r"^-{3,}$")


def _has_unit_token(description: str) -> bool:
    return any(re.search(rf"(?<!\w){re.escape(token)}(?!\w)", description) for token in UNIT_TOKENS)


def numeric_parameters_without_unit(doc: str) -> list[str]:
    """Return the names of float or array Parameters entries whose description holds no unit token."""
    lines = doc.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == "Parameters") + 2
    except StopIteration:
        return []
    entries: list[tuple[str, str, list[str]]] = []
    for i in range(start, len(lines)):
        if i + 1 < len(lines) and SECTION_RULE.match(lines[i + 1].strip()):
            break
        match = ENTRY.match(lines[i])
        if match:
            entries.append((match["name"], match["type"], []))
        elif entries and lines[i].strip():
            entries[-1][2].append(lines[i].strip())
    return [name for name, kind, text in entries if NUMERIC_TYPE.search(kind) and not _has_unit_token(" ".join(text))]


def check_parameter_units(modules) -> list[str]:
    """Return one 'path:line: message' per public embodic.physics function with a numeric parameter lacking a unit."""
    violations = []
    for module in modules:
        if not module.in_package("embodic.physics") or module.name.rsplit(".", 1)[-1].startswith("_"):
            continue
        for node in module.tree.body:
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) or node.name.startswith("_"):
                continue
            unitless = numeric_parameters_without_unit(ast.get_docstring(node) or "")
            if unitless:
                violations.append(
                    f"{module.where(node)}: {node.name}() Parameters name no unit for {', '.join(unitless)}"
                )
    return violations


def trace_function(description: str) -> str:
    """Return module source with one physics function whose only parameter is `width : float`."""
    return f'''
def trace_resistance(width: float) -> float:
    """Return the trace resistance.

    Parameters
    ----------
    width : float
        {description}

    Returns
    -------
    float
        Resistance in ohm. References: EQ-10.
    """
'''


@pytest.mark.req("REQ-N-09")
def test_n09_a_numeric_parameter_without_a_unit_is_reported(planted):
    """Catches a docstring that names a parameter but no unit, which MT-04's `name:` match passes."""
    module = planted("embodic.physics.trace", trace_function("Trace width."))
    (violation,) = check_parameter_units([module])
    assert "trace_resistance()" in violation
    assert "width" in violation


@pytest.mark.req("REQ-N-09")
def test_n09_the_same_parameter_with_a_unit_is_not_reported(planted):
    """Catches a checker that reports every numeric parameter, so MT-04 could never go green again."""
    module = planted("embodic.physics.trace", trace_function("Trace width in mm."))
    assert check_parameter_units([module]) == []


@pytest.mark.req("REQ-N-09")
def test_n09_a_description_that_continues_on_a_second_line_keeps_its_unit(planted):
    """Catches a parser that reads only the first line of an entry and so reports a unit written on the next one."""
    module = planted("embodic.physics.trace", trace_function("Trace width as drawn,\n        in mm."))
    assert check_parameter_units([module]) == []


@pytest.mark.req("REQ-N-09")
@pytest.mark.parametrize("unit", [u for u in Unit if u not in (Unit.ONE, Unit.COUNT)], ids=lambda u: u.name)
def test_n09_every_unit_code_and_display_form_counts_as_a_unit(planted, unit):
    """Catches a token list that omits a Unit, so a parameter documented in that unit would be reported."""
    for token in (unit.value, unit.display()):
        module = planted("embodic.physics.trace", trace_function(f"Quantity in {token}."))
        assert check_parameter_units([module]) == [], token


@pytest.mark.req("REQ-N-09")
def test_n09_a_non_numeric_parameter_needs_no_unit(planted):
    """Catches a checker that demands a unit of an enum or object parameter such as `topology : ConnectionTopology`."""
    source = '''
def phase_voltage(topology: str) -> float:
    """Return the phase voltage.

    Parameters
    ----------
    topology : ConnectionTopology
        Star, delta or open.

    Returns
    -------
    float
        Voltage in V. References: EQ-10.
    """
'''
    assert check_parameter_units([planted("embodic.physics.drive", source)]) == []
