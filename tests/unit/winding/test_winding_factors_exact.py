"""F02-1 (V3-01 union ruling): k_w1 of every A2-TOP section 2.2 row against Agent 4's exact instrument to 1e-9."""

import importlib.util
import math
from pathlib import Path
from types import ModuleType

import pytest

from embodic.results import Registry, load_registry
from embodic.winding import assign_phases, compute_winding_factors

from .test_winding_factors import A2_TOP_TABLE

pytestmark = [pytest.mark.req("REQ-F-02"), pytest.mark.eq("EQ-08")]

_OWN_WINDING = Path(__file__).resolve().parents[2] / "independent" / "m2" / "own_winding.py"


def _load_own_winding() -> ModuleType:
    """Load the Fraction-exact star of slots without putting tests/independent/m2 on sys.path for other tests."""
    spec = importlib.util.spec_from_file_location("own_winding_f02", _OWN_WINDING)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def registry() -> Registry:
    """Load the packaged equation registry; EQ-08 supplies status, sources and tolerance."""
    return load_registry()


@pytest.mark.parametrize(("q", "poles"), [(row[0], row[1]) for row in A2_TOP_TABLE], ids=lambda v: str(v))
def test_f02_1_kw1_of_every_a2_top_row_matches_the_exact_instrument_to_1e_9(
    q: int, poles: int, registry: Registry
) -> None:
    """Catches a k_d sum or pitch argument off by over 1e-9 on any A2-TOP row, which the 1e-3 table check passes."""
    own_winding = _load_own_winding()
    factors = compute_winding_factors(assign_phases(q, poles), poles, q, (2 * math.pi / q,), (1,), registry)
    assert factors[1].value == pytest.approx(own_winding.winding_factor(q, poles, 1), abs=1e-9)
