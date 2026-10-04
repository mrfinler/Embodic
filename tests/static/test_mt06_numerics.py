"""MT-06: no built-in sum() over floats and no built-in round() in physics, DRC and geometry (REQ-N-04)."""

import ast

import pytest

COVERED_PACKAGES = ("embodic.physics", "embodic.drc", "embodic.geometry")


def is_counting_sum(call: ast.Call) -> bool:
    """Return True for sum(1 for ...), which adds integers and is exact on every Python version."""
    if len(call.args) != 1 or not isinstance(call.args[0], ast.GeneratorExp | ast.ListComp):
        return False
    element = call.args[0].elt
    return isinstance(element, ast.Constant) and type(element.value) is int


def check_numerics(modules) -> list[str]:
    """Return one 'path:line: message' per banned call."""
    violations = []
    for module in modules:
        if not module.in_package(*COVERED_PACKAGES):
            continue
        for node in ast.walk(module.tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            if node.func.id == "sum" and not is_counting_sum(node):
                violations.append(
                    f"{module.where(node)}: built-in sum() changed its float algorithm in Python 3.12; "
                    "use math.fsum or a NumPy reduction"
                )
            elif node.func.id == "round":
                violations.append(
                    f"{module.where(node)}: built-in round() rounds half to even; "
                    "use embodic.units.round_half_away_from_zero"
                )
    return violations


@pytest.mark.req("REQ-N-04")
def test_mt06_real_package_is_clean(src_modules):
    """MT-06 on the real package."""
    assert check_numerics(src_modules) == []


@pytest.mark.req("REQ-N-04")
def test_mt06_flags_float_sum_and_round_but_not_counting(planted):
    """Catches a lint that passes everything, and one that also bans the exact integer counting idiom."""
    module = planted(
        "embodic.drc.check",
        """
import math


def total_length_mm(lengths_mm):
    hits = sum(1 for x in lengths_mm if x > 0)
    exact = math.fsum(lengths_mm)
    return round(sum(lengths_mm), 6), hits, exact
""",
    )
    violations = check_numerics([module])
    assert len(violations) == 2
    assert any("sum()" in v for v in violations)
    assert any("round()" in v for v in violations)


@pytest.mark.req("REQ-N-04")
def test_mt06_ignores_packages_outside_its_scope(planted):
    """Catches the rule leaking into io or ui, where round() on display values is allowed."""
    module = planted("embodic.io.report", "x = round(sum([0.1, 0.2]), 2)\n")
    assert check_numerics([module]) == []
