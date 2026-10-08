# Prepared by: Agent 1 (UX/UI Expert Designer) - model: claude-opus-5-5
"""Check the screens.md section 4 promise that a deleted spiral layer pair returns on a later copper-count change.

    .venv/bin/python docs/phase2/design/checks/pair_delete_probe.py   # exit 1 while the promise fails

It derives 3 pairs from 6 copper layers, deletes the middle pair as a list delete does (later items move down one
position), changes the stack-up to 8 copper layers and derives again. Expected: 4 pairs with distinct indices 0 to 3
joining L1-L2, L3-L4, L5-L6 and L7-L8.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(REPO / "src"), str(REPO)]

from tests.unit.model.test_layer_pairs import GROUPS, PAIRS, _blank_spiral, _with_copper  # noqa: E402

from embodic.model.draft import DesignDraft, derive_layer_pairs  # noqa: E402

LEAVES = ("index", "layer_in", "layer_out", "rotation_rad", "phases")


def _pairs(draft: DesignDraft) -> list[tuple[object, object, object]]:
    count = len([p for p in draft.values if p.startswith(PAIRS) and p.endswith("/index")])
    return [tuple(draft.values[f"{PAIRS}/{k}/{leaf}"] for leaf in LEAVES[:3]) for k in range(count)]


def main() -> int:
    """Print the derived pairs and return 1 when they differ from the expected four."""
    six = _blank_spiral(6)
    values = {p: v for p, v in six.values.items() if not p.startswith(PAIRS) and p != GROUPS}
    for position, kept in enumerate((0, 2)):
        values |= {f"{PAIRS}/{position}/{leaf}": six.values[f"{PAIRS}/{kept}/{leaf}"] for leaf in LEAVES}
    values[GROUPS] = [[0], [2]]
    eight = derive_layer_pairs(_with_copper(DesignDraft(topology=six.topology, values=values), 8))
    got = _pairs(eight)
    want = [(0, "L1", "L2"), (1, "L3", "L4"), (2, "L5", "L6"), (3, "L7", "L8")]
    print(f"pairs after delete and 6 -> 8 copper layers: {got}")
    print("as screens.md section 4 says" if got == want else f"differs from screens.md section 4, expected {want}")
    return 0 if got == want else 1


if __name__ == "__main__":
    sys.exit(main())
