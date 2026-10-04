"""Engineering number formatting for results: locale-independent, SI prefixes, U+2212 minus (REQ-L-07).

Rounding follows JavaScript `Number.prototype.toPrecision`: the exact decimal value of the double, ties away from zero,
so a result prints the digits Xcoil would print. Python's `format(x, ".3g")` rounds ties to even and differs on
values such as 1.125.
"""

from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

from embodic.units import Unit

if TYPE_CHECKING:
    from embodic.results.traceable import Traceable

MINUS = "−"
NOT_A_NUMBER = "n/a"
_PREFIXES = {-12: "p", -9: "n", -6: "µ", -3: "m", 0: "", 3: "k", 6: "M", 9: "G"}
_PREFIXED_UNITS = frozenset(
    {Unit.V, Unit.W, Unit.A, Unit.OHM, Unit.H, Unit.T, Unit.HZ, Unit.N_M, Unit.V_S_PER_RAD, Unit.N_M_PER_A, Unit.G}
)


def format_quantity(value: float, unit: Unit, *, significant: int = 3) -> str:
    """Return ``value`` with `significant` figures, an SI prefix where the unit takes one, and the unit symbol.

    Counts print as integers. Zero prints as ``0`` and never with a sign. NaN and infinities print as ``n/a``
    without a unit, because no unit applies to a missing number.
    """
    if not math.isfinite(value):
        return NOT_A_NUMBER
    if unit is Unit.COUNT and value == int(value):
        return _signed(f"{abs(int(value))}", value)
    symbol = unit.display()
    if value == 0:
        return _with_unit("0", "", symbol)
    digits, exponent = _round_significant(abs(value), significant)
    shift = 3 * math.floor(exponent / 3) if unit in _PREFIXED_UNITS else 0
    shift = min(max(shift, min(_PREFIXES)), max(_PREFIXES))
    text = _positional(digits, exponent - shift, significant)
    return _with_unit(_signed(text, value), _PREFIXES[shift] if shift else "", symbol)


def format_value(t: Traceable[float], *, significant: int = 3) -> str:
    """Locale-independent, SI prefixes, U+2212 minus, space before the unit (REQ-L-07)."""
    return format_quantity(t.value, t.unit, significant=significant)


def _round_significant(magnitude: float, significant: int) -> tuple[Decimal, int]:
    """Return the significant digits as an integer-valued Decimal and the decimal exponent of the leading digit."""
    exact = Decimal(magnitude)
    exponent = exact.adjusted()
    digits = exact.scaleb(significant - 1 - exponent).quantize(Decimal(1), rounding=ROUND_HALF_UP)
    if digits.adjusted() >= significant:
        exponent += 1
        digits = exact.scaleb(significant - 1 - exponent).quantize(Decimal(1), rounding=ROUND_HALF_UP)
    return digits, exponent


def _positional(digits: Decimal, exponent: int, significant: int) -> str:
    """Write the digits so that the leading one sits at 10**exponent, keeping trailing zeros as significant."""
    decimals = max(significant - 1 - exponent, 0)
    return f"{digits.scaleb(exponent - significant + 1):.{decimals}f}"


def _signed(text: str, value: float) -> str:
    return f"{MINUS}{text}" if value < 0 else text


def _with_unit(number: str, prefix: str, symbol: str) -> str:
    return f"{number} {prefix}{symbol}" if prefix or symbol else number
