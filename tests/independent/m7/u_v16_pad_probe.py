"""U-V16: is the rule 5 miss reachable from a design input? D08 with only ``vias.pad_mm`` changed.

usage: PYTHONPATH=src python tests/independent/m7/u_v16_pad_probe.py [PAD_MM ...]   (default 0.6 0.7 0.8 1.0)

Each value is written into a copy of the packaged D08 project file and computed through ``compute_project``. The own
side is ``u_v16_copper.check_example`` (DXF export, own reader, no section 7 rule), which also names the rule by
which the product exempts each own close pair.
"""

import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from u_v16_copper import EXAMPLES, check_example  # noqa: E402


def main(argv: list[str]) -> int:
    """Print one line per pad diameter."""
    values = [float(v) for v in argv] or [0.6, 0.7, 0.8, 1.0]
    source = json.loads((EXAMPLES / "spiral_12c10p_d08.embodic.json").read_text(encoding="utf-8"))
    for pad in values:
        doc = json.loads(json.dumps(source))
        doc["design"]["vias"]["pad_mm"] = pad
        doc.pop("design_hash", None)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "spiral_12c10p_d08.embodic.json"
            path.write_text(json.dumps(doc), encoding="utf-8")
            r = check_example(path, None)
        outcome = r["_outcome"]
        leg_widths = sorted(
            {q.width_mm for p in outcome.boards.boards[0].paths for q in p.primitives if q.role.value == "leg"}
        )
        by_rule = Counter(str(v["product_exempts_by_rule"]) for v in r["violations"])
        least = min(
            (v["clearance_mm"][0] for v in r["violations"] if v["product_exempts_by_rule"] == "5"), default=None
        )
        print(json.dumps({
            "pad_mm": pad, "leg_widths_mm": leg_widths, "product_drc": r["premises"]["product_drc"],
            "own_close_pairs_by_product_rule": dict(by_rule), "least_rule5_clearance_mm": least,
            "agreement": r["agreement_with_product_violations"]["equal"],
        }))  # fmt: skip
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
