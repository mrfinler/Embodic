"""Agent 4's V3-01 re-rulings on main c0f4894 (U-V14) that replace rows of v3_01_rulings_v13.py.

RULINGS has the shape of v3_01_rulings_v13.RULINGS; PINS has the shape of records/V3-01_pins_260191f.json (the SHA-256
of each cited function's source segment, or of the cited record file, on c0f4894). req_audit.py --target main applies
v13 first and these on top.

- REQ-T-11: the reviewer record that the v13 ruling named as missing now exists (LG-04_T-11_reviewer.md).
- REQ-N-07: D-061d supersedes the Windows campaign record of the 0.0.1 wheel; the Linux record is redone on c0f4894.

Each ruling is `verified` by reading the cited test sources on c0f4894.
"""

import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("v3_01_rulings_v13", Path(__file__).with_name("v3_01_rulings_v13.py"))
_v13 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_v13)
Ruling = _v13.Ruling

BASE = "c0f4894"
WORDING = "tests/static/test_lg_wording.py"
EXPORTS = "tests/unit/embodic_io/exporters/test_lg_exports.py"
REVIEWER = "tests/independent/m4/records/LG-04_T-11_reviewer.md"

RULINGS = {
    "REQ-T-11": Ruling(
        "checks",
        "Wording scan: LG-04 finds no balance, torque or efficiency text outside the reviewed allow-list in the string "
        "constants of src, the resources with the equation guide as rendered, and the exports and disclosures of the "
        "five examples; planted controls show a 'Balanced.' catalogue value and a new torque sentence are hits. "
        "Reviewer check: Agent 4's record reads every card, chart, guide line and PDF row that names those words and "
        "finds no claim from geometry or phase angles alone (allow-list a19b5c80).",
        (
            f"{WORDING}::test_lg04_source_strings_make_no_balance_torque_or_efficiency_claim",
            f"{WORDING}::test_lg04_resources_make_no_balance_torque_or_efficiency_claim",
            f"{EXPORTS}::test_lg04_exports_and_disclosure_make_no_balance_torque_or_efficiency_claim",
            f"{WORDING}::test_lg04_a_balanced_claim_in_the_catalogue_is_a_hit",
            f"{WORDING}::test_lg04_a_new_sentence_about_torque_is_a_hit_and_the_result_name_is_not",
            f"record:{REVIEWER}",
        ),
    ),
    "REQ-N-07": Ruling(
        "partial",
        "D-061d: the Windows PK-06 runs of docs/phase3/fable/windows_campaign_w1.md used the 0.0.1 wheel and are "
        "superseded for 0.0.2; the Linux walkthrough is redone on c0f4894 (PK-06_walkthrough_c0f4894.md, 17.4 s to "
        "26.8 s). The acceptance needs a clean Windows machine.",
        missing="The timed PK-06 walkthrough of the 0.0.2 build on the clean Windows laptop, cold and warm cache.",
        kind="person's check",
        owner="the user",
    ),
}

PINS = {
    "REQ-T-11": {
        f"{WORDING}::test_lg04_source_strings_make_no_balance_torque_or_efficiency_claim": (
            "7405cd7e6bf4b59ab125e37dfa513df44c0a189892b91bca7a7444835cef5c5e"
        ),
        f"{WORDING}::test_lg04_resources_make_no_balance_torque_or_efficiency_claim": (
            "943538667c24ae69e7d88ac65c972cee0cc7ad1dfdcfc947fbd9098c2b7ca0fc"
        ),
        f"{EXPORTS}::test_lg04_exports_and_disclosure_make_no_balance_torque_or_efficiency_claim": (
            "4b85903ba8a51298595e1a1b270044cc15e52b7d34e5cc097006f51627665f1d"
        ),
        f"{WORDING}::test_lg04_a_balanced_claim_in_the_catalogue_is_a_hit": (
            "fa1f5e68f411ab91d4e4a1e825fc2969f51c7a0e3672797fe202014434ea20fd"
        ),
        f"{WORDING}::test_lg04_a_new_sentence_about_torque_is_a_hit_and_the_result_name_is_not": (
            "413d119f1ff20ae13d7a992c1c413553c1fe8aca0e4690762fa92d68f1fd9dc3"
        ),
        f"record:{REVIEWER}": "a1c3feec3b8223805dd759373c7bdb70709b3221d28820a8557730c98517e1dd",
    },
}
