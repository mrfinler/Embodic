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
# The literal below is U+00A0 (no-break space), not U+0020: it joins a number and its unit so a line never breaks
# there (U-S4e ruling e1). The LG-01 literal check admits it in this module only (D-040c).
UNIT_SPACE = " "  # noqa: RUF001
NOT_A_NUMBER = "n/a"
_PREFIXES = {-12: "p", -9: "n", -6: "µ", -3: "m", 0: "", 3: "k", 6: "M", 9: "G"}
_PREFIX_WORDS = {-12: "pico", -9: "nano", -6: "micro", -3: "milli", 0: "", 3: "kilo", 6: "mega", 9: "giga"}
# What a screen reader says for each unit symbol (DEF-UV4-07); singular, as "502 milliohm".
_UNIT_WORDS = {
    Unit.MM: "millimetre",
    Unit.MM2: "square millimetre",
    Unit.M: "metre",
    Unit.UM: "micrometre",
    Unit.RAD: "radian",
    Unit.T: "tesla",
    Unit.V: "volt",
    Unit.V_S_PER_RAD: "volt-second per radian",
    Unit.N_M_PER_A: "newton-metre per ampere",
    Unit.RPM_PER_V: "rpm per volt",
    Unit.OHM: "ohm",
    Unit.OHM_M: "ohm-metre",
    Unit.H: "henry",
    Unit.H_PER_M: "henry per metre",
    Unit.W: "watt",
    Unit.W_PER_M2_K: "watt per square metre kelvin",
    Unit.A: "ampere",
    Unit.A_PER_MM2: "ampere per square millimetre",
    Unit.K: "kelvin",
    Unit.PER_K: "per kelvin",
    Unit.DEGC: "degree Celsius",
    Unit.G: "gram",
    Unit.G_PER_CM3: "gram per cubic centimetre",
    Unit.N_M: "newton-metre",
    Unit.N_M_PER_SQRT_W: "newton-metre per square root watt",
    Unit.RPM: "rpm",
    Unit.HZ: "hertz",
    Unit.F_PER_M: "farad per metre",
}
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
    number, shift = _number_and_shift(value, unit, significant)
    return _with_unit(number, _PREFIXES[shift] if shift else "", unit.display())


def spoken_quantity(value: float, unit: Unit, *, significant: int = 3) -> str:
    """Return the number of `format_quantity` and its prefix and unit in words, for a screen reader ("502 milliohm").

    A unit without a symbol (a ratio, a count) adds no words; NaN and infinities read ``n/a``.
    """
    if not math.isfinite(value) or (unit is Unit.COUNT and value == int(value)):
        return format_quantity(value, unit, significant=significant)
    number, shift = _number_and_shift(value, unit, significant)
    words = _UNIT_WORDS.get(unit, "")
    return f"{number} {_PREFIX_WORDS[shift]}{words}" if words else number


def _number_and_shift(value: float, unit: Unit, significant: int) -> tuple[str, int]:
    """Return the signed number text and the power of ten its SI prefix stands for (0 for none)."""
    if value == 0:
        return "0", 0
    digits, exponent = _round_significant(abs(value), significant)
    shift = 3 * math.floor(exponent / 3) if unit in _PREFIXED_UNITS else 0
    shift = min(max(shift, min(_PREFIXES)), max(_PREFIXES))
    return _signed(_positional(digits, exponent - shift, significant), value), shift


def format_value(t: Traceable[float], *, significant: int = 3) -> str:
    """Locale-independent, SI prefixes, U+2212 minus, U+00A0 before the unit (REQ-L-07)."""
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
    return f"{number}{UNIT_SPACE}{prefix}{symbol}" if prefix or symbol else number
