"""REQ-N-09 (V3-01 gap N-09): the Parameters and Returns entries of a physics docstring name a unit.

MT-04 (`test_mt04_physics_docstrings.py`) matches `name:` and the Returns heading only, so `width : float / Trace
width.` and a `float / Resistance.` return pass it. The unit tokens come from `embodic.units.Unit` (canonical code and
display form). A quantity of dimension one has no unit to name; its description says `dimensionless` (D-056f, BIPM SI
Brochure 9th edition 2019, quantities of dimension one).

An entry is numeric when its docstring type holds `float`, `FloatArray` or `NDArray`. One Returns description covers a
tuple type written as a single entry, so such an entry needs one unit token, not one per element.
"""

import re
import textwrap

import pytest
from tests.static.physics_functions import public_physics_functions

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
DIMENSIONLESS = re.compile(r"(?<!\w)dimensionless(?!\w)")
PARAMETER_ENTRY = re.compile(r"^(?P<name>\w+)\s*:\s*(?P<type>.+)$")
RETURN_ENTRY = re.compile(r"^(?:(?P<name>\w+)\s*:\s*)?(?P<type>\S.*)$")
SECTION_RULE = re.compile(r"^-{3,}$")


# A one-letter unit (A, H, K, T, V, W, g, m) is also a word or a symbol (`A value`, `area A`, `m phases`). The physics
# docstrings write one after "in", after a number, inside a bracket or as the divisor of a compound unit (`N*m/A`).
# `Ω` is no word, so it keeps the plain rule.
UNIT_POSITION = r"(?:(?<=\bin )|(?<=\d )|(?<=[\d(\[/*·]))"


def _unit_pattern(token: str) -> str:
    position = UNIT_POSITION if len(token) == 1 and token.isascii() else r"(?<!\w)"
    return rf"{position}{re.escape(token)}(?!\w)"


def _has_unit_token(description: str) -> bool:
    return bool(DIMENSIONLESS.search(description)) or any(re.search(_unit_pattern(t), description) for t in UNIT_TOKENS)


def _numeric_entries_without_unit(doc: str, section: str, entry: re.Pattern[str]) -> list[str]:
    """Return the names of the float or array entries of one docstring section whose description holds no unit token.

    An entry of a Returns section may have no name; it is then listed by its type.
    """
    lines = doc.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == section) + 2
    except StopIteration:
        return []
    entries: list[tuple[str, str, list[str]]] = []
    for i in range(start, len(lines)):
        if i + 1 < len(lines) and SECTION_RULE.match(lines[i + 1].strip()):
            break
        match = entry.match(lines[i])
        if match:
            entries.append((match["name"] or match["type"], match["type"], []))
        elif entries and lines[i].strip():
            entries[-1][2].append(lines[i].strip())
    return [name for name, kind, text in entries if NUMERIC_TYPE.search(kind) and not _has_unit_token(" ".join(text))]


def check_parameter_units(modules) -> list[str]:
    """Return one 'path:line: message' per public physics function or method with a numeric parameter lacking a unit."""
    violations = []
    for function in public_physics_functions(modules):
        unitless = _numeric_entries_without_unit(function.docstring, "Parameters", PARAMETER_ENTRY)
        if unitless:
            violations.append(f"{function.where}: {function.name}() Parameters name no unit for {', '.join(unitless)}")
    return violations


def check_return_units(modules) -> list[str]:
    """Return one 'path:line: message' per public physics function or method with a numeric return lacking a unit."""
    violations = []
    for function in public_physics_functions(modules):
        unitless = _numeric_entries_without_unit(function.docstring, "Returns", RETURN_ENTRY)
        if unitless:
            violations.append(f"{function.where}: {function.name}() Returns names no unit for {', '.join(unitless)}")
    return violations


def trace_function(description: str, returns: str = "float\n    Resistance in ohm.") -> str:
    """Return module source with one physics function whose only parameter is `width : float`.

    `returns` is the body of the Returns section as it reads after the docstring is cleaned, so a test can plant a
    tuple or a named entry.
    """
    return f'''
def trace_resistance(width: float) -> float:
    """Return the trace resistance.

    Parameters
    ----------
    width : float
        {description}

    Returns
    -------
    {textwrap.indent(returns, "    ").lstrip()}
    """
'''


@pytest.mark.req("REQ-N-09")
def test_n09_every_numeric_parameter_of_a_public_physics_function_names_a_unit(src_modules):
    """REQ-N-09 on the real package: catches a physics docstring that documents a float parameter without its unit.

    A parameter of dimension one passes with the word `dimensionless` (D-056f). There is no exception list.
    """
    assert check_parameter_units(src_modules) == []


@pytest.mark.req("REQ-N-09")
def test_n09_every_numeric_return_of_a_public_physics_function_names_a_unit(src_modules):
    """REQ-N-09 on the real package: catches a physics docstring that returns a float or array without its unit.

    A return of dimension one passes with the word `dimensionless` (D-056f). There is no exception list.
    """
    assert check_return_units(src_modules) == []


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
def test_n09_a_dimensionless_parameter_that_says_so_is_not_reported(planted):
    """Catches a checker with no way to document a quantity of dimension one, so MT-04 never goes green (D-056f)."""
    module = planted("embodic.physics.trace", trace_function("Fundamental winding factor, dimensionless."))
    assert check_parameter_units([module]) == []


@pytest.mark.req("REQ-N-09")
@pytest.mark.parametrize(
    "description", ["Winding factor.", "Winding factor, no unit.", "Winding factor, a pure number."]
)
def test_n09_a_dimensionless_parameter_that_does_not_say_so_is_reported(planted, description):
    """Catches a checker that lets the other wordings for dimension one pass: only `dimensionless` is the word."""
    (violation,) = check_parameter_units([planted("embodic.physics.trace", trace_function(description))])
    assert "width" in violation


@pytest.mark.req("REQ-N-09")
def test_n09_the_word_dimensionless_must_stand_alone_to_count(planted):
    """Catches a substring match, which would accept `nondimensionless` or `dimensionlessness` as the word."""
    module = planted("embodic.physics.trace", trace_function("Trace width, nondimensionless."))
    assert len(check_parameter_units([module])) == 1


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


@pytest.mark.req("REQ-N-09")
def test_n09_a_numeric_return_without_a_unit_is_reported(planted):
    """Catches a Returns entry that types a float but names no unit, which MT-04's section match passes."""
    module = planted("embodic.physics.trace", trace_function("Trace width in mm.", "float\n    Resistance."))
    (violation,) = check_return_units([module])
    assert "trace_resistance()" in violation
    assert "float" in violation


@pytest.mark.req("REQ-N-09")
@pytest.mark.parametrize("returns", ["float\n    Resistance in ohm.", "float\n    Efficiency, dimensionless."])
def test_n09_a_numeric_return_with_a_unit_or_the_word_dimensionless_is_not_reported(planted, returns):
    """Catches a checker that reports every numeric return, so MT-04 could never go green again (D-056f)."""
    module = planted("embodic.physics.trace", trace_function("Trace width in mm.", returns))
    assert check_return_units([module]) == []


@pytest.mark.req("REQ-N-09")
@pytest.mark.parametrize("description", ["Efficiency, no unit.", "Efficiency, a pure number.", "Efficiency."])
def test_n09_a_dimensionless_return_that_does_not_say_so_is_reported(planted, description):
    """Catches a checker that lets the other wordings for dimension one pass: only `dimensionless` is the word."""
    module = planted("embodic.physics.trace", trace_function("Trace width in mm.", f"float\n    {description}"))
    assert len(check_return_units([module])) == 1


@pytest.mark.req("REQ-N-09")
def test_n09_an_array_return_without_a_unit_is_reported(planted):
    """Catches a checker that reads only `float` and lets a FloatArray or NDArray return go without a unit."""
    for kind in ("FloatArray", "NDArray[np.float64]", "list[float]"):
        module = planted("embodic.physics.trace", trace_function("Trace width in mm.", f"{kind}\n    One per path."))
        assert len(check_return_units([module])) == 1, kind


@pytest.mark.req("REQ-N-09")
def test_n09_a_named_numeric_return_is_judged_on_its_own_description(planted):
    """Catches a checker that lets one unit in a tuple excuse the entry beside it, which has none."""
    returns = "speed : FloatArray\n    Speed in rpm.\ntorque : FloatArray\n    Torque of each point."
    module = planted("embodic.physics.trace", trace_function("Trace width in mm.", returns))
    (violation,) = check_return_units([module])
    assert "torque" in violation
    assert "speed" not in violation


@pytest.mark.req("REQ-N-09")
def test_n09_a_return_description_that_continues_on_a_second_line_keeps_its_unit(planted):
    """Catches a parser that reads only the first line of a Returns entry and so reports a unit on the next one."""
    returns = "float\n    Resistance of the trace as drawn,\n    in ohm."
    module = planted("embodic.physics.trace", trace_function("Trace width in mm.", returns))
    assert check_return_units([module]) == []


@pytest.mark.req("REQ-N-09")
@pytest.mark.parametrize("kind", ["bool", "str", "tuple[str, ...]", "TraceResult | None"])
def test_n09_a_non_numeric_return_needs_no_unit(planted, kind):
    """Catches a checker that demands a unit of a flag, a text or an object such as `InterconnectResistance`."""
    module = planted("embodic.physics.trace", trace_function("Trace width in mm.", f"{kind}\n    The answer."))
    assert check_return_units([module]) == []


@pytest.mark.req("REQ-N-09")
def test_n09_a_unit_in_the_parameters_does_not_excuse_the_return(planted):
    """Catches a checker that scans the whole docstring, so `width in mm` would stand for the return value."""
    module = planted("embodic.physics.trace", trace_function("Trace width in mm.", "float\n    Resistance."))
    assert len(check_return_units([module])) == 1


@pytest.mark.req("REQ-N-09")
def test_n09_a_numeric_entry_of_the_section_after_returns_is_not_a_return(planted):
    """Catches a parser that runs past the Returns section and reports the float entry of the next one."""
    returns = "float\n    Resistance in ohm.\n\nOther Parameters\n----------------\nscale : float\n    Scale factor."
    module = planted("embodic.physics.trace", trace_function("Trace width in mm.", returns))
    assert check_return_units([module]) == []


@pytest.mark.req("REQ-N-09")
@pytest.mark.parametrize(
    "description",
    [
        "A value of the trace width.",
        "Trace width. A value from the user.",
        "Face area A of the board.",
        "Number of phases m.",
    ],
)
def test_n09_a_one_letter_word_or_symbol_is_not_a_unit(planted, description):
    """Catches `A` read as the ampere in `A value of ...` or `area A`, and `m` as the metre in `phases m`."""
    assert len(check_parameter_units([planted("embodic.physics.trace", trace_function(description))])) == 1
    returns = f"float\n    {description}"
    assert len(check_return_units([planted("embodic.physics.trace", trace_function("Width in mm.", returns))])) == 1


@pytest.mark.req("REQ-N-09")
@pytest.mark.parametrize(
    "description",
    [
        "Current in A.",
        "Phase current in A rms.",
        "Current (A rms).",
        "Current [A].",
        "Limit of 10 A.",
        "Gain in N*m/A.",
        "Resistance, Ω.",
    ],
)
def test_n09_a_one_letter_unit_counts_where_a_unit_is_written(planted, description):
    """Catches a checker that rejects the ways the physics docstrings write an ampere or ohm (MT-04 never green)."""
    assert check_parameter_units([planted("embodic.physics.trace", trace_function(description))]) == []
    returns = f"float\n    {description}"
    assert check_return_units([planted("embodic.physics.trace", trace_function("Width in mm.", returns))]) == []


METHOD_SOURCE = '''
from typing import Protocol


class Trace:
    """A trace."""

    def resistance(self, width: float) -> float:
        """Return the trace resistance.

        Parameters
        ----------
        width : float
            {width}

        Returns
        -------
        float
            {resistance}
        """


class Cancel(Protocol):
    """Cancellation flag."""

    def budget(self, width: float) -> float:
        """Return a budget.

        Parameters
        ----------
        width : float
            Width.

        Returns
        -------
        float
            Budget.
        """
'''


@pytest.mark.req("REQ-N-09")
def test_n09_a_method_with_a_numeric_parameter_and_return_without_units_is_reported_by_its_class_and_name(planted):
    """Catches a unit check that reads module-level functions only: a method is a physics function (U-D26 item 2)."""
    module = planted("embodic.physics.trace", METHOD_SOURCE.format(width="Trace width.", resistance="Resistance."))
    (parameter_violation,) = check_parameter_units([module])
    (return_violation,) = check_return_units([module])
    assert "Trace.resistance()" in parameter_violation
    assert "width" in parameter_violation
    assert "Trace.resistance()" in return_violation


@pytest.mark.req("REQ-N-09")
def test_n09_a_method_with_units_is_not_reported_and_a_protocol_member_is_left_out(planted):
    """Catches a checker that reports every method, or one that reads a Protocol member (its body is `...`)."""
    module = planted(
        "embodic.physics.trace", METHOD_SOURCE.format(width="Trace width in mm.", resistance="Resistance in ohm.")
    )
    assert check_parameter_units([module]) == []
    assert check_return_units([module]) == []
