"""Build the subject: embodic's BoardStack for one Xcoil parameter set, through the public generator dispatch.

Deviation (named in the README): the Xcoil-to-design input map is the golden harness's ``design_from_xcoil``. It
maps inputs only; every expected value comes from Agent 4's own Xcoil dump and mapper. A wrong input map shows as a
disagreement in the comparison, not as a hidden pass.
"""

import sys
from functools import cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from cases import xcoil_dumps  # noqa: E402
from tests.golden.m3_serpentine.design_map import design_from_xcoil as serpentine_design  # noqa: E402
from tests.golden.m3_wave.param_map import design_from_xcoil as wave_design  # noqa: E402

from embodic.generators import build_layout  # noqa: E402
from embodic.results import load_registry  # noqa: E402


def design_for(dump: dict[str, Any]) -> Any:
    """Return the embodic design for one Xcoil dump."""
    p = dump["params"]
    if p.get("topology") == "wave":
        return wave_design(p)
    return serpentine_design(p, dump["rMinAll"], dump["rMaxAll"])


@cache
def registry() -> Any:
    """Return the shipped equation registry."""
    return load_registry()


@cache
def stack_for(case_id: str) -> Any:
    """Return embodic's BoardStack (or Unbuildable) for one case id."""
    return build_layout(design_for(xcoil_dumps()[case_id]), registry())
