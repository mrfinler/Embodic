"""UT-UNI-03 and UT-RES-04: engineering number formatting, locale independence and unit symbols (REQ-L-07)."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from embodic.results.formatting import format_quantity, format_value
from embodic.results.traceable import traced
from embodic.units import Unit

# Expected digits for the first rows were printed by Node v22.22.2 on 2026-10-04:
# [1.125, 2.675, 0.000123456, 999.5, 999.4999, -1.125, 1.005].map(x => x.toPrecision(3)) -> 1.13 2.67 0.000123 1.00e+3
# 999 -1.13 1.00. JS ties go away from zero on the exact double; Python's ".3g" would print 1.12 for 1.125.
CASES = [
    (1.125, Unit.ONE, "1.13"),
    (2.675, Unit.ONE, "2.67"),
    (0.000123456, Unit.ONE, "0.000123"),
    (999.5, Unit.OHM, "1.00 kΩ"),
    (999.4999, Unit.OHM, "999 Ω"),
    (-1.125, Unit.V, "−1.13 V"),
    (1.005, Unit.ONE, "1.00"),
    (0.5, Unit.OHM, "500 mΩ"),
    (0.0123, Unit.V_S_PER_RAD, "12.3 mV·s/rad"),
    (1.5e-7, Unit.H, "150 nH"),
    (12.5, Unit.A_PER_MM2, "12.5 A/mm²"),
    (1234.5, Unit.MM, "1230 mm"),
    (120.0, Unit.DEGC, "120 °C"),
    (12.0, Unit.COUNT, "12"),
    (0.0, Unit.OHM, "0 Ω"),
    (-0.0, Unit.V, "0 V"),
    (float("nan"), Unit.V, "n/a"),
    (float("inf"), Unit.W, "n/a"),
    (float("-inf"), Unit.W, "n/a"),
]


@pytest.mark.req("REQ-L-07", "REQ-N-21")
@pytest.mark.parametrize(("value", "unit", "expected"), CASES)
def test_formatting_engineering_text(value, unit, expected):
    """Catches half-even rounding, a hyphen minus, a missing SI prefix or space, '-0', and 'nan' leaking to the UI."""
    assert format_quantity(value, unit) == expected


@pytest.mark.req("REQ-L-07")
def test_formatting_format_value_uses_the_traceable_unit(packaged):
    """Catches format_value ignoring the result's unit or the requested significant figures."""
    result = traced("r", 0.04567, Unit.OHM, eq_ids=["EQ-10"], inputs=[], registry=packaged)
    assert format_value(result) == "45.7 mΩ"
    assert format_value(result, significant=2) == "46 mΩ"


PROBE = (
    "import json, locale, sys; locale.setlocale(locale.LC_ALL, ''); "
    "assert locale.localeconv()['decimal_point'] == sys.argv[1], locale.localeconv(); "
    "from embodic.results.formatting import format_quantity; from embodic.units import Unit; "
    "print(json.dumps([format_quantity(v, Unit(u)) for v, u in json.loads(sys.argv[2])]))"
)


@pytest.fixture(scope="module")
def compiled_locales(tmp_path_factory) -> Path:
    """Compile de_DE.UTF-8 and th_TH.UTF-8 into a private folder, so the test does not depend on the host."""
    localedef = shutil.which("localedef")
    if localedef is None or not Path("/usr/share/i18n/locales/de_DE").is_file():
        pytest.skip("localedef or glibc locale sources are not available")
    folder = tmp_path_factory.mktemp("locales")
    for name in ("de_DE", "th_TH"):
        subprocess.run([localedef, "-i", name, "-f", "UTF-8", str(folder / f"{name}.UTF-8")], check=True)
    return folder


@pytest.mark.req("REQ-L-07")
@pytest.mark.parametrize(("locale_name", "decimal_point"), [("de_DE.UTF-8", ","), ("th_TH.UTF-8", ".")])
def test_formatting_identical_under_german_and_thai_locale(compiled_locales, locale_name, decimal_point):
    """UT-UNI-03: catches locale-aware formatting ('n' format, locale.format_string) giving '1,13' under de_DE."""
    values = [(v, u.value) for v, u, _ in CASES if v == v and abs(v) != float("inf")]
    env = {"LOCPATH": str(compiled_locales), "LC_ALL": locale_name, "PATH": ""}
    completed = subprocess.run(
        [sys.executable, "-c", PROBE, decimal_point, json.dumps(values)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == [format_quantity(v, Unit(u)) for v, u in values]
