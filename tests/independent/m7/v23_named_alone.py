"""Run each named killer of a product mutant on its own, so a ``-x`` stop does not hide which named tests catch it.

Run from the repository root with the dev venv:

    python tests/independent/m7/v23_named_alone.py V3-03 V3-03-03 [more ids]

Uses the copy, the pytest call and the verdict words of ``product_mutants.py``. For every mutant, each named killer runs
once on the unmutated copy and once on the mutant; the line printed per killer is ``clean passes | mutant <verdict>``
with the first failing line, where ``survived`` means the killer passed on the mutant.
"""

import sys
import tempfile
from pathlib import Path

from product_mutant_tables import CAMPAIGNS
from product_mutants import _copy_checkout, _imports_from, _pytest, judge


def main(campaign: str, ids: list[str]) -> int:
    """Print one line per (mutant, killer) pair; exit 0 when the unmutated copy passes every killer, else 2."""
    mutants = [m for m in CAMPAIGNS[campaign] if m.id in ids]
    clean_ok = True
    with tempfile.TemporaryDirectory(prefix="embodic-alone-") as tmp:
        work = _copy_checkout(Path(tmp))
        print(f"imports {_imports_from(work)}")
        for mutant in mutants:
            target = work / "src" / "embodic" / mutant.file
            source = target.read_text(encoding="utf-8")
            assert source.count(mutant.old) == 1, f"{mutant.id}: anchor not exactly once in {mutant.file}"
            for killer in mutant.killers:
                clean = judge(mutant, *_pytest(work, (killer,)))
                clean_ok &= clean.verdict == "survived"
                target.write_text(source.replace(mutant.old, mutant.new), encoding="utf-8")
                try:
                    hit = judge(mutant, *_pytest(work, (killer,)))
                finally:
                    target.write_text(source, encoding="utf-8")
                first = " / ".join(line[:160] for line in hit.failed[:1] + hit.evidence[:1])
                clean_word = "passes" if clean.verdict == "survived" else f"FAILS ({clean.verdict})"
                print(f"{mutant.id} {killer.split('::')[-1]}: clean {clean_word} | mutant {hit.verdict} {first}")
    return 0 if clean_ok else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2:]))
