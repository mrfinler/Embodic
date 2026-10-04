"""MT-04: public physics functions document every parameter, the return value and an EQ-ID (REQ-N-09)."""

import ast
import re

import pytest

EQ_ID = re.compile(r"\bEQ-\d{2}\b")


def check_physics_docstrings(modules) -> list[str]:
    """Return one 'path:line: message' per public embodic.physics function whose docstring misses a part."""
    violations = []
    for module in modules:
        if not module.in_package("embodic.physics") or module.name.rsplit(".", 1)[-1].startswith("_"):
            continue
        for node in module.tree.body:
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) or node.name.startswith("_"):
                continue
            doc = ast.get_docstring(node) or ""
            params = [a.arg for a in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)]
            missing = [p for p in params if not re.search(rf"^\s*{re.escape(p)}\s*:", doc, re.MULTILINE)]
            problems = []
            if not EQ_ID.search(doc):
                problems.append("an EQ-ID (e.g. 'References: EQ-10')")
            if missing:
                problems.append(f"a Parameters entry with unit for {', '.join(missing)}")
            if not re.search(r"^\s*Returns\s*\n\s*-+", doc, re.MULTILINE):
                problems.append("a Returns section with the unit")
            if problems:
                violations.append(f"{module.where(node)}: {node.name}() docstring needs " + "; ".join(problems))
    return violations


@pytest.mark.req("REQ-N-09")
def test_mt04_physics_functions_are_documented(src_modules):
    """MT-04 on the real package."""
    assert check_physics_docstrings(src_modules) == []


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
