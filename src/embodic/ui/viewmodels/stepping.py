"""Up and Down stepping of a numeric field: the number a step gives, and when it gives none (fix_wave_f2.md (b)).

Qt-free. Numbers are in the unit the form shows, so an angle is in degrees and its limits are too.
"""

import math
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from embodic.model.fields import FieldSpec, Sign
from embodic.model.schema import ValueType
from embodic.units import Unit, rad_to_deg

SHIFT_STEPS = 10  # Shift+Up and Shift+Down move ten steps (design_spec.md section 10)


@dataclass(frozen=True, slots=True, kw_only=True)
class StepRule:
    """How Up and Down move one field. `sign` is validity; `low` and `high` are the supported range, ends included."""

    step: float
    sign: Sign = Sign.ANY
    low: float | None = None
    high: float | None = None

    def allows(self, number: float) -> bool:
        """Return True when ``number`` is valid and in range."""
        if self.sign is Sign.POSITIVE and number <= 0:
            return False
        if self.sign is Sign.NON_NEGATIVE and number < 0:
            return False
        return (self.low is None or number >= self.low) and (self.high is None or number <= self.high)

    def valid_bounds(self) -> list[float]:
        """Return the numbers that end the range and are themselves allowed, lowest first."""
        ends = {bound for bound in (self.low, self.high) if bound is not None}
        if self.sign is Sign.NON_NEGATIVE:
            ends.add(0.0)
        return sorted(bound for bound in ends if self.allows(bound))


def rule_of(spec: FieldSpec) -> StepRule | None:
    """Return the rule of a numeric field, or None for a field that does not step (text, choices, no step)."""
    if spec.value_type not in (ValueType.FLOAT, ValueType.INT) or spec.step is None:
        return None
    limits = spec.limits

    def shown(bound: float | None) -> float | None:
        return rad_to_deg(bound) if bound is not None and spec.unit is Unit.RAD else bound

    return StepRule(step=spec.step, sign=limits.sign, low=shown(limits.low), high=shown(limits.high))


def stepped_text(rule: StepRule, text: str, steps: int) -> str | None:
    """Return the field text after ``steps`` steps (negative goes down), or None when the field stays as it is.

    The result is the number in the field plus ``steps`` times the step, to 12 significant digits, with no snapping.
    A step never leaves the valid range: it stops at a bound it would cross, and does not move away from the range.
    """
    try:
        current = float(text.strip())
    except ValueError:
        return None
    if not math.isfinite(current):
        return None
    moved = _move(rule, current, current + steps * rule.step)
    return None if moved is None else f"{moved or 0.0:.12g}"  # `or 0.0` turns -0 into 0


def _move(rule: StepRule, current: float, target: float) -> float | None:
    if rule.allows(target):
        return target
    bounds = rule.valid_bounds()
    if target > current:
        reachable = [b for b in bounds if b > current and (b < target or not rule.allows(current))]
        return min(reachable, default=None)
    reachable = [b for b in bounds if b < current and (b > target or not rule.allows(current))]
    return max(reachable, default=None)


# The two stack-up generator inputs have no FieldSpec, so their steps live here (fix_wave_f2.md (b), an assumption:
# no source in the repository gives a step). Neither has limits.
STACKUP_INPUT_RULES: Mapping[str, StepRule] = MappingProxyType(
    {"param-copper-weight": StepRule(step=0.5), "param-board-thickness": StepRule(step=0.1)}
)
