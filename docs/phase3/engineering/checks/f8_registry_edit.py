"""Fix wave F8 (U-E22): apply the EQ-08 and EQ-27 registry texts of fix_wave_f8.md; a second run changes nothing.

    python3 docs/phase3/engineering/checks/f8_registry_edit.py

Each edit replaces one exact text that occurs once, so the rest of the file keeps its bytes. The script then parses the
result and checks the new texts, the unchanged mathematics and that no displayed EQ-08 or EQ-27 text names Xcoil.
"""

import json
import re
from pathlib import Path

REGISTRY = Path(__file__).resolve().parents[4] / "docs" / "phase2" / "engineering" / "equation_registry.json"

EQ08_OLD = "; balance = signed angle sets of B and C equal those of A shifted by 4Q and 8Q units"
EQ08_NEW = (
    "; symmetric 3-phase pattern (a property of the coil pattern only) = signed angle sets of B and C equal those of"
    " A shifted by 4Q and 8Q units"
)

EQ27_FORMULA_OLD = (
    '"formula": "k_u = Ke1 / (sum over series conductors of integral B_z1 r dr over the magnet span); serpentine'
)
EQ27_FORMULA_NEW = (
    '"formula": "k_u = Ke1 / ((1/m) sum over phases of sum over the series conductors c of the phase of integral'
    " B_z1(r, z_c) r dr over the magnet span), Ke1 = (1/m) sum over phases of Ke_1 of the phase; a series conductor"
    " is one radial side of the series path, counted once also where it covers part of the span; serpentine"
)

EQ27_VARIABLES_OLD = """    {
     "symbol": "k_u",
     "unit": "1",
     "meaning": "utilisation factor (numeric)"
    },"""
EQ27_VARIABLES_NEW = (
    """    {
     "symbol": "k_u",
     "unit": "1",
     "meaning": "utilisation factor (numeric)"
    },
    {
     "symbol": "Ke1",
     "unit": "V*s/rad",
     "meaning": "mean over the m phases of the fundamental phase EMF constant (EQ-06 Ke_n, n = 1; EQ-09 Ke_ph)"
    },
    {
     "symbol": "c",
     "unit": "1",
     "meaning": "series conductor: one radial side (PrimitiveRole.SIDE) of the phase's series path; members of a"""
    """ parallel group count once (sides / parallel members)"
    },
    {
     "symbol": "z_c",
     "unit": "mm",
     "meaning": "copper z of conductor c; B_z1 is evaluated at z_c + air gap"
    },"""
)

EQ27_SOURCE_OLD = (
    "k_u is the quantity Xcoil engine.js names 'kw1' (analyze l.983; moved out of the formula, revision 2026-10-17,"
    ' U-E14)"'
)
EQ27_SOURCE_NEW = (
    "k_u is the quantity Xcoil engine.js names 'kw1' (analyze l.983; moved out of the formula, revision 2026-10-17,"
    " U-E14); Xcoil's conductor counts: computeSector l.2478 (coilsPerPhase*4*N), analyzeWave l.2083 (nElements),"
    ' analyze l.1013 (Nt*series layers*poles); rulings per topology: docs/phase3/engineering/fix_wave_f8.md"'
)

EQ27_CHANGES_OLD = '"spiral: k_w from EQ-08, not from kdAnalytic"\n   ],'
EQ27_CHANGES_NEW = (
    '"spiral: k_w from EQ-08, not from kdAnalytic",\n'
    "    \"serpentine: k_u is the three-phase ratio of the formula; analyze l.983 divides phase A's Ke (phases[0]) by"
    " the ideal of phase A's own layers, a per-phase value that depends on which phase is A and is not ported"
    " (fix_wave_f8.md, ruling S); EQT-27-GR compares at 1e-9 with Xcoil kw1 on spiral"
    " (analyzeElements l.1892) and wave (analyzeWave l.2083), and on serpentine with the formula assembled from"
    " Xcoil's Ke1 and analyze's ideal integral (l.977-981) per copper layer\"\n   ],"
)

NOTE_ANCHOR = 'Rulings: docs/phase3/engineering/fix_wave_f2.md"\n ],'
NOTE_NEW = (
    'Rulings: docs/phase3/engineering/fix_wave_f2.md",\n'
    "  \"v1.0 rev. U-E22 (2026-10-18, D-062 b and c, fix wave F8): EQ-08 formula: 'balance =' becomes 'symmetric "
    "3-phase pattern (a property of the coil pattern only) =' (F-UV14-01, D-051 b); the arithmetic is unchanged. "
    "EQ-27: the formula states Ke1 as the three-phase mean, the ideal as the three-phase mean of each phase's "
    "conductor sum at the conductor's z, and what one series conductor is; variables Ke1, c and z_c added; one "
    "change added (serpentine is not Xcoil's phase-A kw1, and what EQT-27-GR compares per topology). The numbers "
    'embodic computes are unchanged. Rulings: docs/phase3/engineering/fix_wave_f8.md"\n ],'
)

EDITS = (
    (EQ08_OLD, EQ08_NEW),
    (EQ27_FORMULA_OLD, EQ27_FORMULA_NEW),
    (EQ27_VARIABLES_OLD, EQ27_VARIABLES_NEW),
    (EQ27_SOURCE_OLD, EQ27_SOURCE_NEW),
    (EQ27_CHANGES_OLD, EQ27_CHANGES_NEW),
    (NOTE_ANCHOR, NOTE_NEW),
)


def apply(text: str) -> str:
    """Return the text with every edit applied; an edit whose new text is present already is skipped."""
    for old, new in EDITS:
        if new in text:
            continue
        assert text.count(old) == 1, f"expected one occurrence of {old[:60]!r}, found {text.count(old)}"
        text = text.replace(old, new)
    return text


def check(text: str, before: dict) -> None:
    """Fail unless the new texts are present and everything else in the registry equals ``before``."""
    reg = json.loads(text)
    eqs = {e["id"]: e for e in reg["equations"]}
    old = {e["id"]: e for e in before["equations"]}
    eq08, eq27 = eqs["EQ-08"], eqs["EQ-27"]
    assert not re.search("balanc", eq08["formula"], re.I), "EQ-08 formula still says balance"
    assert "symmetric 3-phase pattern" in eq08["formula"]
    for e in (eq08, eq27):
        for field in ("name", "formula"):
            assert "xcoil" not in e[field].lower(), f"{e['id']} {field} names Xcoil (D-051 c)"
    assert [v["symbol"] for v in eq27["variables"]] == ["k_u", "Ke1", "c", "z_c", "k_d"]
    for key in (
        "gate_verdict",
        "status",
        "tests",
        "golden_functions",
        "applies_to",
        "reference_case",
        "constants",
        "tolerance",
    ):
        assert eq27[key] == old["EQ-27"][key], f"EQ-27 {key} changed"
        assert eq08.get(key) == old["EQ-08"].get(key), f"EQ-08 {key} changed"
    others = [k for k in eqs if k not in ("EQ-08", "EQ-27")]
    assert all(eqs[k] == old[k] for k in others), "an equation other than EQ-08 and EQ-27 changed"
    assert reg["notes"][-1].startswith("v1.0 rev. U-E22")


def main() -> None:
    """Edit the registry in place when needed, check it and print whether it changed."""
    original = REGISTRY.read_text(encoding="utf-8")
    baseline = json.loads(original)
    edited = apply(original)
    if edited != original:
        REGISTRY.write_text(edited, encoding="utf-8")
    check(edited, baseline)
    print("changed" if edited != original else "unchanged", REGISTRY)


if __name__ == "__main__":
    main()
