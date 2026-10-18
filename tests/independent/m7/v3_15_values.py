"""Dump every computed value of the five packaged examples, for the V3-15 value-identity check (U-V13).

    PYTHONPATH=<tree>/src python3 tests/independent/m7/v3_15_values.py OUT.txt

Run it once per source tree (for example a `git archive <commit> src resources` extract) and compare the files with
`diff`. Each line is `example path = repr(value)` for every Traceable of the outcome's AnalysisResult, layers, phases
and torque-speed estimate included, plus the design hash. Chains, flags, labels and badges are left out on purpose:
fix waves F4 to F6 changed those, and the claim under test is that they changed no value. The last lines give the
SHA-256 and the line count per example and name the embodic package that was imported.
"""

import dataclasses
import hashlib
import sys
from pathlib import Path

import embodic
from embodic.api import compute
from embodic.io.examples import load_example
from embodic.io.project import project_from_example
from embodic.results import Traceable

EXAMPLES = ("spiral_12c10p_d08", "spiral_12c14p", "spiral_12c16p_default", "serpentine_16p_example", "wave_16p_example")


def walk(obj: object, path: str):
    """Yield (path, value) for every Traceable under a result dataclass, tuple items numbered."""
    if isinstance(obj, Traceable):
        yield path, obj.value
    elif dataclasses.is_dataclass(obj):
        for field in dataclasses.fields(obj):
            yield from walk(getattr(obj, field.name), f"{path}.{field.name}")
    elif isinstance(obj, tuple):
        for index, item in enumerate(obj):
            yield from walk(item, f"{path}[{index}]")


def example_lines(example_id: str) -> list[str]:
    """Return the value lines of one example."""
    design = project_from_example(load_example(example_id)).design
    outcome = compute(design, {})
    assert outcome is not None and outcome.analysis is not None, example_id
    lines = [f"{example_id} design_hash = {outcome.design_hash}"]
    lines += [f"{example_id} {path} = {value!r}" for path, value in walk(outcome.analysis, "analysis")]
    return lines


def main(argv: list[str]) -> int:
    """Write the dump and print one digest line per example."""
    out: list[str] = []
    summary = []
    for example_id in EXAMPLES:
        lines = example_lines(example_id)
        out += lines
        digest = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()
        summary.append(f"# {example_id}: {len(lines)} lines, sha256 {digest}")
    summary.append(f"# embodic imported from {Path(embodic.__file__).parent}")
    Path(argv[0]).write_text("\n".join(out + summary) + "\n", encoding="utf-8")
    print("\n".join(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
