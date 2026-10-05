"""Read the winding oracle cases from docs/phase2/engineering/oracle_cases.json so no expected value is retyped."""

import json
from pathlib import Path
from typing import Any

ORACLE_FILE = Path(__file__).resolve().parents[3] / "docs" / "phase2" / "engineering" / "oracle_cases.json"


def oracle_case(case_id: str) -> dict[str, Any]:
    """Return one case of the oracle file by its ID."""
    cases: list[dict[str, Any]] = json.loads(ORACLE_FILE.read_text(encoding="utf-8"))["cases"]
    return next(c for c in cases if c["case_id"] == case_id)


def cf09_rows() -> list[dict[str, Any]]:
    """CF-09 rows: Q, poles, pattern, balanced_exact, feasible_rule, kd1, belt_edge_coils (EQ-08)."""
    rows: list[dict[str, Any]] = oracle_case("CF-09")["expected"][0]["value"]
    return rows
