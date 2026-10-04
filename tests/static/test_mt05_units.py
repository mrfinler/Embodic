"""MT-05: dimensional names carry a unit suffix; no bare power-of-ten literals in embodic.physics (ADR-0009)."""

import ast
import math

import pytest

DIMENSIONAL_PACKAGES = (
    "embodic.units",
    "embodic.model",
    "embodic.winding",
    "embodic.geometry",
    "embodic.generators",
    "embodic.drc",
    "embodic.physics",
)
DIMENSIONAL_WORDS = frozenset(
    "width widths radius radii diameter diameters thickness thicknesses length lengths gap gaps clearance clearances "
    "pitch angle angles temperature temperatures voltage voltages resistance resistances inductance inductances "
    "speed speeds frequency frequencies drill height heights depth depths spacing area areas mass torque remanence "
    "sweep".split()
)
UNIT_SUFFIXES = tuple(
    "_" + suffix
    for suffix in (
        "mm mm2 m um rad deg degc a v ohm t w k h hz rpm g n_m oz mil2 s a_per_mm2 v_s_per_rad n_m_per_a rpm_per_v "
        "rad_per_s w_m2k ohm_m per_k".split()
    )
)
NON_DIMENSIONAL_PREFIXES = ("is_", "has_", "allow_", "use_")
NON_DIMENSIONAL_SUFFIXES = ("_count", "_index", "_kind", "_mode", "_style", "_spec", "_specs", "_status", "_unit")


def needs_unit_suffix(name: str) -> bool:
    """Return True when a name says it holds a dimension but has no unit suffix."""
    bare = name.lstrip("_").lower()
    if bare.startswith(NON_DIMENSIONAL_PREFIXES) or bare.endswith(NON_DIMENSIONAL_SUFFIXES + UNIT_SUFFIXES):
        return False
    return any(word in DIMENSIONAL_WORDS for word in bare.split("_"))


def declared_names(tree: ast.Module):
    """Yield (node, name) for every function parameter and every annotated class attribute."""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda):
            for arg in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs):
                yield arg, arg.arg
        elif isinstance(node, ast.ClassDef):
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    yield stmt, stmt.target.id


def is_power_of_ten_literal(node: ast.AST) -> bool:
    """Return True for a numeric literal equal to 10**k with |k| >= 3 (1e-3, 1000, 1e6, ...)."""
    if not isinstance(node, ast.Constant) or isinstance(node.value, bool) or not isinstance(node.value, int | float):
        return False
    if node.value == 0:
        return False
    exponent = math.log10(abs(node.value))
    return abs(exponent - round(exponent)) < 1e-12 and abs(round(exponent)) >= 3


def check_unit_names(modules) -> list[str]:
    """Return one 'path:line: message' per violation of either MT-05 rule."""
    violations = []
    for module in modules:
        if module.in_package(*DIMENSIONAL_PACKAGES):
            violations += [
                f"{module.where(node)}: '{name}' names a dimension; add a unit suffix such as _mm, _rad or _degc"
                for node, name in declared_names(module.tree)
                if needs_unit_suffix(name)
            ]
        if module.in_package("embodic.physics"):
            violations += [
                f"{module.where(node)}: bare power-of-ten literal {node.value!r}; convert with embodic.units (mm_to_m)"
                for node in ast.walk(module.tree)
                if is_power_of_ten_literal(node)
            ]
    return violations


@pytest.mark.req("REQ-N-08")
def test_mt05_real_package_is_clean(src_modules):
    """MT-05 on the real package."""
    assert check_unit_names(src_modules) == []


@pytest.mark.req("REQ-N-08")
def test_mt05_flags_unsuffixed_dimension_and_power_of_ten(planted):
    """Catches a lint that passes everything: 'width' without suffix and a bare 1e-3 in physics are reported."""
    module = planted(
        "embodic.physics.resistance",
        """
from dataclasses import dataclass


@dataclass
class Track:
    width: float
    length_mm: float
    is_width_fixed: bool
    turn_count: int


def resistance_ohm(thickness_mm: float, temperature: float) -> float:
    return thickness_mm * 1e-3 + 0.5
""",
    )
    violations = check_unit_names([module])
    assert any("'width'" in v for v in violations)
    assert any("'temperature'" in v for v in violations)
    assert any("0.001" in v for v in violations)
    assert len(violations) == 3


@pytest.mark.req("REQ-N-08")
def test_mt05_power_of_ten_rule_is_physics_only(planted):
    """Catches the literal rule leaking into packages it does not cover (1e-6 mm is the geometry tolerance)."""
    module = planted("embodic.geometry.primitives", "COINCIDENCE_TOLERANCE_MM = 1e-6\n")
    assert check_unit_names([module]) == []
