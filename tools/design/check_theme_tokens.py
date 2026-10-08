"""Validate ``resources/themes/light.json`` and ``dark.json`` against the ThemeTokens contract.

Usage, from the repository root::

    python tools/design/check_theme_tokens.py

Field names come from the ``ThemeTokens`` and ``PhaseStyle`` dataclasses in interfaces.md section 11, so a contract
change fails this check until the generator follows. Rules: exactly the contract fields; ``name`` equals the file
stem; three phases A, B, C in order; ``hatch_deg`` in {0, 45, 135}; ``dash`` in {solid, dash, dot}; every colour a
``#rrggbb`` hex; ``colours`` holds every ``tokens.json`` colour except the ``phase-*`` ones (20 per theme), with the
same values; the chrome tokens and ``grey_hex`` are white, grey or black only (REQ-L-04) and the three status tokens
(D-038a) are the only chromatic ``colours``; pixel sizes positive integers; and the icon colours of ``tokens.json``
equal ``colours["text-1"]`` and ``colours["text-disabled"]``, the keys the icon loader reads. Exit code 1 when a rule
fails.
"""

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
THEMES = REPO / "resources" / "themes"
INTERFACES = REPO / "docs" / "phase2" / "architecture" / "interfaces.md"
HEX = re.compile(r"#[0-9a-f]{6}")
STATUS_TOKENS = ("status-pass", "status-fail", "status-warn")
PHASE_PREFIX = "phase-"


def contract_fields(text: str, cls: str) -> list[str]:
    """Return the field names of one frozen dataclass in interfaces.md, in declaration order."""
    block = re.search(rf"^class {cls}:\n(.*?)(?=^\S)", text, re.M | re.S)
    if block is None:
        raise SystemExit(f"class {cls} not found in {INTERFACES.relative_to(REPO)}")
    return re.findall(r"^    (\w+): ", block.group(1), re.M)


def is_grey(value: str) -> bool:
    """Return True for a ``#rrggbb`` value with equal channels."""
    return value[1:3] == value[3:5] == value[5:7]


def one_phase_problems(where: str, want: str, p: dict) -> list[str]:
    """Return the PhaseStyle rules one entry breaks; ``want`` is the phase its position requires."""
    problems = []
    if p["phase"] != want:
        problems.append(f"{where}: phase is {p['phase']!r}, expected {want!r} in this position")
    if p["hatch_deg"] not in (0, 45, 135) or isinstance(p["hatch_deg"], bool):
        problems.append(f"{where}: hatch_deg {p['hatch_deg']!r} not in 0, 45, 135")
    if p["dash"] not in ("solid", "dash", "dot"):
        problems.append(f"{where}: dash {p['dash']!r} not in solid, dash, dot")
    if not isinstance(p["label"], str) or not p["label"]:
        problems.append(f"{where}: label must be a non-empty string")
    for key in ("colour_hex", "grey_hex"):
        if not isinstance(p[key], str) or not HEX.fullmatch(p[key]):
            problems.append(f"{where}: {key} {p[key]!r} is not #rrggbb")
    if HEX.fullmatch(str(p["grey_hex"])) and not is_grey(p["grey_hex"]):
        problems.append(f"{where}: grey_hex {p['grey_hex']} is not a grey")
    return problems


def phase_problems(phases: object, fields: list[str]) -> list[str]:
    """Return the PhaseStyle rules the ``phases`` list breaks."""
    if not isinstance(phases, list) or len(phases) != 3:
        return ["phases: expected a list of three entries"]
    problems = []
    for want, p in zip("ABC", phases, strict=True):
        where = f"phases[{want}]"
        if sorted(p) != sorted(fields):
            problems.append(f"{where}: fields {sorted(p)}, contract {sorted(fields)}")
        else:
            problems += one_phase_problems(where, want, p)
    return problems


def colour_problems(colours: object, source: dict) -> list[str]:
    """Return the rules the ``colours`` mapping breaks; ``source`` is ``tokens.json`` > ``themes.<theme>``."""
    if not isinstance(colours, dict) or not colours:
        return ["colours: expected a non-empty mapping"]
    wanted = {k: v for k, v in source["color"].items() if not k.startswith(PHASE_PREFIX)}
    problems = [f"colours lacks {k}" for k in sorted({*wanted, *STATUS_TOKENS} - colours.keys())]
    problems += [
        f"colours has {k}, which is not a tokens.json colour outside the phase-* keys"
        for k in sorted(colours.keys() - wanted.keys())
    ]
    for k, v in colours.items():
        if not isinstance(v, str) or not HEX.fullmatch(v):
            problems.append(f"colours[{k}]: {v!r} is not #rrggbb")
        elif k not in STATUS_TOKENS and not is_grey(v):
            problems.append(f"colours[{k}]: {v} is not white, grey or black (REQ-L-04)")
        elif k in wanted and v != wanted[k]:
            problems.append(f"colours[{k}]: {v} differs from tokens.json {wanted[k]}")
    for key, token in (("normal", "text-1"), ("disabled", "text-disabled")):
        if colours.get(token) != source["icon_color"][key]:
            problems.append(
                f"colours[{token}] {colours.get(token)} differs from icon_color.{key} {source['icon_color'][key]}"
            )
    return problems


def theme_problems(path: Path, theme_fields: list[str], phase_fields: list[str], source: dict) -> list[str]:
    """Return every rule one theme file breaks."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if sorted(data) != sorted(theme_fields):
        return [f"fields {sorted(data)}, contract {sorted(theme_fields)}"]
    problems = []
    if data["name"] != path.stem:
        problems.append(f"name {data['name']!r} differs from the file stem {path.stem!r}")
    problems += colour_problems(data["colours"], source)
    problems += phase_problems(data["phases"], phase_fields)
    for key in ("focus_ring_px", "control_height_px"):
        v = data[key]
        if not isinstance(v, int) or isinstance(v, bool) or v <= 0:
            problems.append(f"{key}: {v!r} is not a positive integer")
    return problems


def main() -> int:
    """Check both theme files; return 1 when a rule fails."""
    text = INTERFACES.read_text(encoding="utf-8")
    theme_fields = contract_fields(text, "ThemeTokens")
    phase_fields = contract_fields(text, "PhaseStyle")
    tokens = json.loads((THEMES / "tokens.json").read_text(encoding="utf-8"))
    failures = 0
    for name in ("light", "dark"):
        path = THEMES / f"{name}.json"
        if not path.is_file():
            print(f"{name}: {path.relative_to(REPO)} missing")
            failures += 1
            continue
        problems = theme_problems(path, theme_fields, phase_fields, tokens["themes"][name])
        for p in problems:
            print(f"{name}: {p}")
        failures += len(problems)
        print(f"{name}: {'ok' if not problems else 'FAIL'}")
    print(f"check_theme_tokens: contract ThemeTokens {theme_fields}, PhaseStyle {phase_fields}; {failures} failures")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
