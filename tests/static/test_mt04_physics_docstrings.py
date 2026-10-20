"""MT-04: public physics functions document every parameter, the return value and an EQ-ID (REQ-N-09).

A physics function is a public function of a public `embodic.physics` module, at module level or as a method of a
public top-level class that is not a `typing.Protocol` (U-D26 item 2, D-084). `tests/static/physics_functions.py` holds
the walk that this file and `test_n09_parameter_units.py` share.
"""

import re
import textwrap

import pytest
from tests.static.physics_functions import public_physics_functions

EQ_ID = re.compile(r"\bEQ-\d{2}\b")


def check_physics_docstrings(modules) -> list[str]:
    """Return one 'path:line: message' per public embodic.physics function whose docstring misses a part."""
    violations = []
    for function in public_physics_functions(modules):
        doc = function.docstring
        missing = [p for p in function.parameters if not re.search(rf"^\s*{re.escape(p)}\s*:", doc, re.MULTILINE)]
        problems = []
        if not EQ_ID.search(doc):
            problems.append("an EQ-ID (e.g. 'References: EQ-10')")
        if missing:
            problems.append(f"a Parameters entry with unit for {', '.join(missing)}")
        if not re.search(r"^\s*Returns\s*\n\s*-+", doc, re.MULTILINE):
            problems.append("a Returns section with the unit")
        if problems:
            violations.append(f"{function.where}: {function.name}() docstring needs " + "; ".join(problems))
    return violations


def flagged(violations: list[str]) -> list[str]:
    """Return the 'Class.method()' or 'function()' name of each violation, in order."""
    return [match[1] for match in (re.search(r": (\S+\(\)) docstring", v) for v in violations) if match]


FLUX_DOCSTRING = '''"""Return the flux.

        References: EQ-05

        Parameters
        ----------
        {parameters}

        Returns
        -------
        float
            Flux in Wb.
        """'''


def magnet_class(methods: str, header: str = "class Magnet:", imports: str = "") -> str:
    """Return module source holding one class; `methods` is the class body, indented four spaces."""
    return f'{imports}\n\n{header}\n    """A magnet."""\n\n{textwrap.indent(textwrap.dedent(methods), "    ")}'


@pytest.mark.req("REQ-N-09")
def test_mt04_flags_missing_eq_id_and_parameter(planted):
    """Catches a lint that passes everything: an undocumented parameter and a missing EQ-ID are both reported."""
    module = planted(
        "embodic.physics.resistance",
        '''
def phase_resistance(length_mm: float, width_mm: float) -> float:
    """Return the phase resistance.

    Parameters
    ----------
    length_mm : float
        Track length in mm.

    Returns
    -------
    float
        Resistance in ohm.
    """


def _helper(x):
    pass
''',
    )
    (violation,) = check_physics_docstrings([module])
    assert "phase_resistance()" in violation
    assert "EQ-ID" in violation
    assert "width_mm" in violation
    assert "length_mm" not in violation


@pytest.mark.req("REQ-N-09")
def test_mt04_physics_functions_are_documented(src_modules):
    """MT-04 on the real package, methods of public classes included."""
    assert check_physics_docstrings(src_modules) == []


@pytest.mark.req("REQ-N-09")
def test_mt04_reaches_the_methods_the_ruling_names_and_not_the_protocol_member(src_modules):
    """Catches a walk that silently stops at module level, which would let the real-package test above pass empty."""
    names = {function.name for function in public_physics_functions(src_modules)}
    assert {"FieldTable.at", "InterconnectResistance.total_ohm"} <= names
    assert "CancelToken.cancelled" not in names


@pytest.mark.req("REQ-N-09")
def test_mt04_flags_an_undocumented_public_method_and_spares_protocol_and_private_members(planted):
    """Catches a checker that reads module-level functions only: a method is a physics function (U-D26 item 2).

    The same planted module holds a Protocol member, a private method, `__init__` and a private class. None is reported.
    """
    source = '''
from typing import Protocol


class Magnet:
    """A magnet."""

    def __init__(self, width_mm):
        pass

    def flux(self, gap_mm: float) -> float:
        """Return the flux."""

    def _helper(self, x):
        pass


class Cancel(Protocol):
    """Cancellation flag; the function that runs belongs to the implementer."""

    def cancelled(self) -> bool: ...


class _Hidden:
    def flux(self, gap_mm):
        pass
'''
    (violation,) = check_physics_docstrings([planted("embodic.physics.rotor", source)])
    assert flagged([violation]) == ["Magnet.flux()"]
    assert "EQ-ID" in violation
    assert "gap_mm" in violation
    assert "self" not in violation


@pytest.mark.req("REQ-N-09")
def test_mt04_a_fully_documented_method_is_not_reported(planted):
    """Catches a checker that reports every method, or one that wants a Parameters entry for `self`."""
    methods = "def flux(self, gap_mm: float) -> float:\n    " + FLUX_DOCSTRING.format(
        parameters="gap_mm : float\n        Gap in mm."
    )
    assert check_physics_docstrings([planted("embodic.physics.rotor", magnet_class(methods))]) == []


@pytest.mark.req("REQ-N-09")
def test_mt04_a_class_method_needs_no_entry_for_cls_but_a_static_method_needs_its_first_parameter(planted):
    """Catches a checker that drops the first parameter of every method: only `self` and `cls` are exempt."""
    methods = (
        "@classmethod\ndef from_gap(cls, gap_mm: float) -> float:\n    "
        + FLUX_DOCSTRING.format(parameters="gap_mm : float\n        Gap in mm.")
        + "\n\n@staticmethod\ndef area(width_mm: float, depth_mm: float) -> float:\n    "
        + FLUX_DOCSTRING.format(parameters="depth_mm : float\n        Depth in mm.")
    )
    (violation,) = check_physics_docstrings([planted("embodic.physics.rotor", magnet_class(methods))])
    assert flagged([violation]) == ["Magnet.area()"]
    assert "width_mm" in violation
    assert "depth_mm" not in violation


@pytest.mark.req("REQ-N-09")
@pytest.mark.parametrize(
    ("header", "imports"),
    [
        ("class Cancel(Protocol):", "from typing import Protocol"),
        ("class Cancel(typing.Protocol):", "import typing"),
        ("class Cancel(Protocol[T]):", "from typing import Protocol, TypeVar\nT = TypeVar('T')"),
    ],
    ids=["Protocol", "typing.Protocol", "Protocol[T]"],
)
def test_mt04_a_protocol_member_is_out_of_scope_however_the_base_is_spelled(planted, header, imports):
    """Catches a base-name match that sees `Protocol` but not `typing.Protocol` or `Protocol[T]` (U-D26 item 2)."""
    source = magnet_class("def cancelled(self) -> bool: ...", header, imports)
    assert check_physics_docstrings([planted("embodic.physics.rotor", source)]) == []


@pytest.mark.req("REQ-N-09")
def test_mt04_a_class_that_only_inherits_from_a_protocol_implementer_is_in_scope(planted):
    """Catches a Protocol exemption that follows inheritance: only a class that names Protocol itself is exempt."""
    source = magnet_class("def flux(self, gap_mm: float) -> float:\n    pass", "class Flux(Cancel):")
    (violation,) = check_physics_docstrings([planted("embodic.physics.rotor", source)])
    assert flagged([violation]) == ["Flux.flux()"]
