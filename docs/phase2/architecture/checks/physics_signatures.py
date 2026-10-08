# Prepared by: Agent 6 - Software Architecture Specialist - model: claude-opus-5-5
"""Compare interfaces.md section 8 stubs with the merged ``embodic.physics`` (unit U-D4).

Run with the project interpreter, which can import embodic:
    .venv/bin/python docs/phase2/architecture/checks/physics_signatures.py

For every public name of ``embodic.physics`` it compares parameter names, kinds and defaults (functions) or field names
(dataclasses) with the contract stub of the same name. Names listed in PENDING are contract changes a later unit
implements; they must differ today and are reported, not failed. Exit 0 when nothing else differs.
"""

from __future__ import annotations

import dataclasses
import inspect
import re
import sys
import types
from pathlib import Path

INTERFACES = Path(__file__).resolve().parents[1] / "interfaces.md"
PENDING: dict[str, str] = {}  # name -> unit that implements the contract change; emptied by U-D6 after U-M2e-4


def contract_namespace() -> dict[str, object]:
    blocks = re.findall(r"```python\n(.*?)```", INTERFACES.read_text(encoding="utf-8"), re.S)
    module = types.ModuleType("embodic_contract_stub")
    sys.modules[module.__name__] = module
    exec(compile("\n".join(blocks), "interfaces.md", "exec"), module.__dict__)
    return module.__dict__


def shape(obj: object) -> tuple[tuple[str, str, bool], ...]:
    if dataclasses.is_dataclass(obj) and isinstance(obj, type):
        return tuple((f.name, "field", f.default is not dataclasses.MISSING) for f in dataclasses.fields(obj))
    params = inspect.signature(obj).parameters.values()  # type: ignore[arg-type]
    return tuple((p.name, p.kind.name, p.default is not inspect.Parameter.empty) for p in params)


def main() -> int:
    import embodic.physics as physics

    stubs = contract_namespace()
    names = sorted(physics.__all__)
    problems, pending = [], []
    for name in names:
        real = getattr(physics, name)
        stub = stubs.get(name)
        if stub is None:
            problems.append(f"{name}: no stub in interfaces.md")
            continue
        same = shape(real) == shape(stub)
        if name in PENDING:
            (pending if not same else problems).append(
                f"{name}: {'differs as planned' if not same else 'already matches; remove from PENDING'} ({PENDING[name]})"
            )
        elif not same:
            problems.append(f"{name}: code {shape(real)} != contract {shape(stub)}")
    print(f"public physics names compared: {len(names)}")
    for line in pending:
        print(f"PENDING {line}")
    if problems:
        print(f"FAIL: {len(problems)} difference(s)")
        for line in problems:
            print(f"  - {line}")
        return 1
    print("PASS: every other public name of embodic.physics matches its section 8 stub")
    return 0


if __name__ == "__main__":
    sys.exit(main())
