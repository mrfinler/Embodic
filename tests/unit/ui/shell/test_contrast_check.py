"""tools/contrast_check.py: WCAG ratios of every theme pair (AX-01, AX-09, AX-08 contrast part)."""

import dataclasses
import importlib.util
from pathlib import Path

import pytest

from embodic.ui.theme import load_theme

TOOL = Path(__file__).resolve().parents[4] / "tools" / "contrast_check.py"


@pytest.fixture(scope="module")
def contrast_check():
    """Import the tool from its file (tools/ is not a package)."""
    spec = importlib.util.spec_from_file_location("contrast_check", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.req("REQ-N-11", "REQ-N-27")
def test_ax01_ratio_matches_known_wcag_values(contrast_check):
    """Catches a wrong luminance formula: black on white is 21:1 and #767676 on white is 4.54:1 (WebAIM, WCAG)."""
    assert contrast_check.contrast_ratio("#000000", "#ffffff") == pytest.approx(21.0)
    assert contrast_check.contrast_ratio("#767676", "#ffffff") == pytest.approx(4.54, abs=0.005)
    assert contrast_check.contrast_ratio("#ffffff", "#767676") == contrast_check.contrast_ratio("#767676", "#ffffff")


@pytest.mark.req("REQ-N-11", "REQ-L-04", "REQ-N-28", "REQ-F-39", "REQ-N-27")
def test_ax01_ax09_every_pair_of_both_shipped_themes_passes(contrast_check, capsys):
    """Catches a theme file whose text, border, focus ring, phase stroke or icon falls below its WCAG minimum."""
    assert contrast_check.main() == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[-1] == "0 failures"
    assert sum(" icon;" in line for line in lines) == 6


@pytest.mark.req("REQ-N-11", "REQ-N-27")
def test_ax01_a_too_light_hint_text_fails_the_check(contrast_check, monkeypatch, capsys):
    """Catches a check that passes whatever the colours are."""
    light = load_theme("light")
    pale = dataclasses.replace(light, colours={**light.colours, "text-3": "#aaaaaa"})
    monkeypatch.setattr(contrast_check, "load_theme", lambda name: pale if name == "light" else load_theme(name))
    assert contrast_check.main() == 1
    assert "FAIL   light text-3" in capsys.readouterr().out
