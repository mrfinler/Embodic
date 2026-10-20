"""Agent 4's V3-01 re-rulings for release 0.0.5 (99d355d, U-V20), applied on top of v13, v14, v18 and v19.

`v20_repin.py` hashed every non-gate cite of the merged rulings on 99d355d. 258 cites equal their pins, so their
rulings carry unchanged. Two do not, and this file re-rules their rows:

- REQ-F-03: U-M8y renamed `test_m4_one_phase_per_pair_is_refused_until_phase_5` to carry UT-GEO-19 (D-084a). The
  renamed function's node equals the c25d8a9 node under the new name (`ast.dump`), so U-V13's ruling carries with the
  cite under its new name.
- REQ-N-09: U-M8y extended MT-04 and the N-09 unit checks to the methods of public non-Protocol classes (U-D26 item 2,
  D-084a) through the shared walk `tests/static/physics_functions.py`, and changed the docstring of
  `test_mt04_physics_functions_are_documented`. Re-ruled by reading the 99d355d sources.

PINS (records/V3-01_pins_99d355d_v20.json) holds the 99d355d SHA-256 of each cite below, in the form of req_audit.py
`cite_hash`.
"""

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_v13 = _load("v3_01_rulings_v13")
_v19 = _load("v3_01_rulings_v19")
Ruling = _v13.Ruling

BASE = "99d355d"
PIN_FILE = HERE / "records/V3-01_pins_99d355d_v20.json"
PAIRS = "tests/unit/generators/test_spiral_pairs.py"
OLD_M4 = f"{PAIRS}::test_m4_one_phase_per_pair_is_refused_until_phase_5"
NEW_M4 = f"{PAIRS}::test_ut_geo_19_m4_one_phase_per_pair_is_refused_until_phase_5"
MT04 = "tests/static/test_mt04_physics_docstrings.py"
N09 = "tests/static/test_n09_parameter_units.py"

_f03 = _v19.RULINGS["REQ-F-03"]
assert OLD_M4 in _f03.cites, "the REQ-F-03 ruling no longer cites the M4 refusal test"

RULINGS = {
    "REQ-F-03": Ruling(
        "checks",
        f"{_f03.reason} U-M8y renamed the M4 refusal test to carry UT-GEO-19 (D-084a); on 99d355d its node equals the "
        "c25d8a9 node under the new name (v20_repin.py), so the ruling carries with the new cite.",
        tuple(NEW_M4 if cite == OLD_M4 else cite for cite in _f03.cites),
    ),
    "REQ-N-09": Ruling(
        "checks",
        "Acceptance 'every physics function names units and an EQ-ID', read with D-084a: a physics function is a "
        "public function of a public embodic.physics module, at module level or a method of a public top-level class "
        "that does not name Protocol as a base; dataclasses stay outside (the text names functions). On 99d355d MT-04 "
        "and the N-09 unit checks share one walk (tests/static/physics_functions.py, read): module-level functions, "
        "then the methods of each public non-Protocol class, `self` and `cls` exempt and a static method's first "
        "parameter not. MT-04 on the real package requires an EQ-ID, a Parameters entry per parameter and a Returns "
        "section, and the N-09 tests require a unit token of embodic.units.Unit or `dimensionless` in every numeric "
        "Parameters and Returns entry. Controls: a planted module-level miss and a planted undocumented method are "
        "reported, a fully documented method is not, a Protocol member is out of scope in three spellings of the base, "
        "and a walk that stops at module level fails because FieldTable.at and InterconnectResistance.total_ohm must "
        "be reached (the two methods D-084a names, documented in 0.0.5). The N-09 method controls report a method "
        "without units by class and name and pass one with units.",
        (
            f"{MT04}::test_mt04_physics_functions_are_documented",
            f"{MT04}::test_mt04_flags_missing_eq_id_and_parameter",
            f"{MT04}::test_mt04_reaches_the_methods_the_ruling_names_and_not_the_protocol_member",
            f"{MT04}::test_mt04_flags_an_undocumented_public_method_and_spares_protocol_and_private_members",
            f"{MT04}::test_mt04_a_fully_documented_method_is_not_reported",
            f"{MT04}::test_mt04_a_protocol_member_is_out_of_scope_however_the_base_is_spelled",
            f"{N09}::test_n09_every_numeric_parameter_of_a_public_physics_function_names_a_unit",
            f"{N09}::test_n09_every_numeric_return_of_a_public_physics_function_names_a_unit",
            f"{N09}::test_n09_a_numeric_parameter_without_a_unit_is_reported",
            f"{N09}::test_n09_a_numeric_return_without_a_unit_is_reported",
            f"{N09}::test_n09_a_unit_in_the_parameters_does_not_excuse_the_return",
            f"{N09}::test_n09_a_method_with_a_numeric_parameter_and_return_without_units_is_reported_by_its_class_and_name",
            f"{N09}::test_n09_a_method_with_units_is_not_reported_and_a_protocol_member_is_left_out",
        ),
    ),
}

PINS = json.loads(PIN_FILE.read_text(encoding="utf-8")) if PIN_FILE.is_file() else {}
