"""Up and Down stepping of a numeric field (docs/phase3/design/fix_wave_f2.md (b)). Qt-free.

Expected texts come from the design document's arithmetic and bound rules, worked by hand.
"""

import pytest

from embodic.model.fields import FIELD_BY_KEY, FIELDS, Sign
from embodic.model.schema import ValueType
from embodic.ui.viewmodels.stepping import StepRule, rule_of, stepped_text

pytestmark = pytest.mark.req("REQ-N-12")

TABLE_WIDGETS = frozenset({"screw-table", "pair-list", "layer-list", "phase-table"})


def numeric_widget_specs():
    """Return one spec per numeric widget id outside the four tables: 57 ids in FIELDS (the design's count)."""
    specs = {}
    for spec in FIELDS:
        numeric = spec.value_type in (ValueType.FLOAT, ValueType.INT)
        if spec.widget_id and spec.widget_id not in TABLE_WIDGETS and numeric:
            specs.setdefault(spec.widget_id, spec)
    return specs


def test_every_numeric_field_row_has_a_step_so_up_and_down_work_in_all_57():
    """Catches a numeric row left without a step: its field would ignore Up and Down (the six rows of (b))."""
    specs = numeric_widget_specs()
    assert len(specs) == 57
    assert {widget_id for widget_id, spec in specs.items() if rule_of(spec) is None} == set()


@pytest.mark.parametrize(
    ("key", "step"),
    [
        ("/winding/coil/first_coil_angle_rad", 1),
        ("/winding/start_angle_rad", 1),
        ("/outline/board/rotation_rad#polygon", 1),
        ("/outline/bore/rotation_rad#polygon", 1),
        ("/winding/layers/pairs/*/rotation_rad", 1),
        ("/outline/screws/*/angle_offset_rad", 1),
        ("/outline/screws/*/hole_diameter_mm", 0.1),
    ],
)
def test_the_six_new_steps_are_in_the_unit_the_form_shows(key, step):
    """Catches an angle step given in radians: the form shows degrees, so 1 means one degree (fix_wave_f2 (b))."""
    assert FIELD_BY_KEY[key].step == step


def test_an_angle_rule_compares_its_limits_in_degrees():
    """Catches radian limits compared with a degree text: +-2 pi rad is +-360 degrees."""
    rule = rule_of(FIELD_BY_KEY["/outline/board/rotation_rad#polygon"])
    assert rule == StepRule(step=1, sign=Sign.ANY, low=-360.0, high=360.0)


R_INNER = rule_of(FIELD_BY_KEY["/winding/coil/r_inner_mm"])  # spiral: positive, no range, step 0.5 mm
COIL_GAP = rule_of(FIELD_BY_KEY["/winding/coil/coil_gap_mm"])  # non-negative, step 0.05 mm
AIR_GAP = rule_of(FIELD_BY_KEY["/rotor/air_gap_mm"])  # positive, 0.05 to 50 mm, step 0.05 mm
DC_LINK = rule_of(FIELD_BY_KEY["/operating/dc_link_v"])  # positive, range from 0 to 2000 V, step 1 V
POLES = rule_of(FIELD_BY_KEY["/rotor/poles"])  # integer, 2 to 200, step 2
ROTATION = rule_of(FIELD_BY_KEY["/outline/board/rotation_rad#polygon"])  # degrees, -360 to 360, step 1


@pytest.mark.parametrize(
    ("rule", "text", "steps", "expected"),
    [
        (R_INNER, "11.47", 1, "11.97"),
        (R_INNER, "11.47", -10, "6.47"),
        (R_INNER, "11.47", 5, "13.97"),
        (R_INNER, " 11.47 ", 1, "11.97"),
        (StepRule(step=0.1), "0.2", 1, "0.3"),
        (StepRule(step=0.1), "0.3", -1, "0.2"),
        (POLES, "10", 1, "12"),
        (POLES, "10", 10, "30"),
        (ROTATION, "0", 1, "1"),
        (ROTATION, "0", -10, "-10"),
    ],
)
def test_a_step_adds_n_steps_to_the_text_and_shows_twelve_significant_digits(rule, text, steps, expected):
    """Catches float noise (0.1 + 0.2 shown as 0.30000000000000004), snapping to a multiple, or a wrong shift factor."""
    assert stepped_text(rule, text, steps) == expected


@pytest.mark.parametrize(
    ("rule", "text", "steps", "expected"),
    [
        (COIL_GAP, "0.02", -1, "0"),
        (COIL_GAP, "0", -1, None),
        (R_INNER, "0.3", -1, None),
        (DC_LINK, "0.5", -1, None),
        (AIR_GAP, "0.07", -1, "0.05"),
        (AIR_GAP, "0.05", -1, None),
        (AIR_GAP, "49.98", 1, "50"),
        (AIR_GAP, "50", 1, None),
        (AIR_GAP, "60", 1, None),
        (AIR_GAP, "60", -1, "50"),
        (AIR_GAP, "60", -10, "50"),
        (COIL_GAP, "-3", 1, "0"),
        (COIL_GAP, "-3", -1, None),
        (ROTATION, "359.5", 1, "360"),
        (ROTATION, "360", 1, None),
        (ROTATION, "-360", -1, None),
        (ROTATION, "-359.5", -10, "-360"),
    ],
)
def test_a_step_stops_at_a_valid_bound_and_never_leaves_the_range(rule, text, steps, expected):
    """Catches a step into an invalid value (a 0 mm positive field), a jump over a bound, or a step away that moves.

    None means the field text stays as it is.
    """
    assert stepped_text(rule, text, steps) == expected


def test_a_number_below_the_range_steps_to_the_first_value_that_is_valid_and_in_range():
    """Rule 1 first: 0.01 mm is below the 0.05 mm range, and one step up gives 0.06 mm, which is valid and in range."""
    assert stepped_text(AIR_GAP, "0.01", 1) == "0.06"


@pytest.mark.parametrize("text", ["", "   ", "-", "1e", "12,5", "abc", "nan", "inf", "-inf"])
def test_text_that_is_no_finite_number_does_not_change(text):
    """Catches a step that turns "abc" into a number, or an empty optional field into 0.5 (spiral turns: Maximum)."""
    assert stepped_text(R_INNER, text, 1) is None
    assert stepped_text(R_INNER, text, -1) is None


def test_a_field_without_limits_steps_without_bounds():
    """Catches an invented bound on a field that has none: the two stack-up inputs have no FieldSpec and no Limits."""
    assert stepped_text(StepRule(step=0.5), "0.2", -1) == "-0.3"


@pytest.mark.parametrize("key", ["/name", "/phases", "/winding/coil/side_style", "/outline/board/shape"])
def test_a_field_that_is_no_number_has_no_rule(key):
    """Catches Up and Down on a name, a segment or a combo box: only FLOAT and INT fields step."""
    assert rule_of(FIELD_BY_KEY[key]) is None
