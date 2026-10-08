"""Interim light.json and dark.json from tokens.json until U-M4r ships the real files (delete when U-M4r merges)."""

import json
import sys
from pathlib import Path

THEMES = Path(__file__).resolve().parents[3] / "resources" / "themes"
DASH = {"solid": "solid", "dashed": "dash", "dotted": "dot"}


def theme_document(tokens: dict, name: str) -> dict:
    """Return one theme in the ThemeTokens shape of interfaces.md section 11."""
    colour = tokens["themes"][name]["color"]
    phases = []
    for phase, style in tokens["phase_style"].items():
        key = f"phase-{phase.lower()}"
        phases.append(
            {
                "phase": phase,
                "colour_hex": colour[key],
                "grey_hex": colour[f"{key}-grey"],
                "hatch_deg": style["hatch_deg"] or 0,
                "dash": DASH[style["line"]],
                "label": style["label"],
            }
        )
    chrome = {k: v for k, v in colour.items() if not k.startswith("phase-")}
    return {"name": name, "colours": chrome, "phases": phases, "focus_ring_px": 2, "control_height_px": 32}


if __name__ == "__main__":
    tokens = json.loads((THEMES / "tokens.json").read_text(encoding="utf-8"))
    for name in ("light", "dark"):
        (THEMES / f"{name}.json").write_text(json.dumps(theme_document(tokens, name), indent=1) + "\n", "utf-8")
    sys.exit(0)
