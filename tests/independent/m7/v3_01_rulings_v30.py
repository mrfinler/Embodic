"""Agent 4's V3-01 re-rulings on release 0.0.6 (2bfca49, U-V30), applied on top of v13, v14, v18, v19, v20 and v21.

Two rows, whose earlier `partial` ruling named a Windows record as the one missing piece, and whose Windows record
U-V30 indexes in docs/phase3/verification/manual_records.json:

- REQ-N-04: U-V18 named "PK-04 on Windows ... recorded and indexed". PK-04 on the 0.0.6 wheel passed on the laptop
  (D-098a, docs/phase3/fable/windows_campaign_w2.md).
- REQ-N-07: U-V14 named "the timed PK-06 walkthrough ... on the clean Windows laptop, cold and warm cache". D-053c
  rules the row covered by a Linux cold run and a Windows warm run, with the cold Windows result reported. Runs 11
  and 12 on the 0.0.6 wheel passed (D-100a, docs/phase3/fable/PK-06_windows_0.0.6.md).

REQ-N-05 and REQ-N-06 are not re-ruled: the failed W7 and W8 records make both rows `failed` in the audit, and a ruling
gates only a text-verified row. PINS (records/V3-01_pins_2bfca49_v30.json) holds the 2bfca49 SHA-256 of each test
cite and the SHA-256 of each record file in this checkout, in the form of req_audit.py `cite_hash`, written by
`v30_rerule.py --write`. Every ruling is `verified` by reading the cited tests on 2bfca49 and the cited records, unless
its reason labels a part otherwise. The Windows results are Fable's; I ran nothing on Windows (order 8).
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
Ruling = _v13.Ruling

BASE = "2bfca49"
PIN_FILE = HERE / "records/V3-01_pins_2bfca49_v30.json"

MT06 = "tests/static/test_mt06_numerics.py"
W2 = "docs/phase3/fable/windows_campaign_w2.md"
PK06_LINUX = "tests/independent/m5/records/PK-06_walkthrough_2bfca49.md"
PK06_WINDOWS = "docs/phase3/fable/PK-06_windows_0.0.6.md"

RULINGS = {
    "REQ-N-04": Ruling(
        "checks",
        "(1) Same-platform byte identity: PR-09 computes the same design twice with fresh caches and compares the "
        "sorted results JSON text, on CF-11 and on generated spiral designs. (2) Cross-platform: PK-04 on the laptop "
        "compared the five outcome files of the 0.0.6 wheel with U-V29's Linux reference and all five passed at "
        "rel 1e-9 (D-098a, Fable's record). The comparison tool pk04_compare.py applies the array rule, the exact "
        "design_hash and the left-out layout_hash and stack_hash, and its self-test passes 10 of 10 (rerun by U-V22). "
        "(3) No float sum(): MT-06 walks physics, DRC and geometry and passes, with a planted float sum() and round() "
        "found and the integer counting idiom left alone.",
        (
            "tests/unit/api/test_compute.py::test_pr_09_same_design_gives_byte_identical_json",
            "tests/unit/property/test_pipeline_properties.py::test_pr_09_results_json_is_byte_identical_across_runs",
            f"{MT06}::test_mt06_real_package_is_clean",
            f"{MT06}::test_mt06_flags_float_sum_and_round_but_not_counting",
            f"record:{W2}",
        ),
    ),
    "REQ-N-07": Ruling(
        "checks",
        "D-053c rules the row covered by a passed Linux cold walkthrough and a passed Windows warm walkthrough, with "
        "the cold Windows result reported to the user. Linux: three cold runs of the release wheel, 22.9 s to 50.9 s "
        "to the first computed example, self-test 45 of 45 (U-V29). Windows: runs 11 (`embodic-cli` as INSTALL.md "
        "writes it) and 12 (`python -m embodic.cli`), each in a new folder and venv with the hashed lock file and the "
        "wheel, 22.3 s and 19.3 s to the first computed example against 10 minutes, self-test 45 of 45, warm pip "
        "cache (D-100a, Fable's record). The cold Windows results stay as reported: 4154.5 s on 0.0.1 (network), 471 s "
        "on 0.0.2, none since (D-084e).",
        (f"record:{PK06_LINUX}", f"record:{PK06_WINDOWS}"),
    ),
}

PINS = json.loads(PIN_FILE.read_text(encoding="utf-8")) if PIN_FILE.is_file() else {}
