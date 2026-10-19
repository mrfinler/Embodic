"""Product mutation lever for V3-02 to V3-05: seed one defect at a time into a scratch copy of the checkout.

Run from the repository root with the dev venv:

    python tests/independent/m7/product_mutants.py V3-02 [--only V3-02-03 ...] [--json out.json]

Each mutant names, before it runs, the tests that must kill it and the disagreement their failure must show. The
lever copies the checkout (without .git) to a temporary folder once, checks that the unmutated copy passes every named
test, then applies one mutant at a time to the copy's ``src/embodic`` and runs only that mutant's tests with
``PYTHONPATH`` on the copy. The worktree is never edited.

Verdicts: ``killed`` (a named test fails and its failure text matches the prediction), ``killed-other`` (a named test
fails, the text does not match: read the quoted lines), ``broken`` (collection or import error, so the mutant is not
judged), ``timeout``. When every named test passes, the campaign's pass-criterion suite (``SUITES``) runs on the same
mutant: ``suite-killed`` when it fails there (the named tests missed it), else ``survived``. Exit 1 when a mutant is not
``killed``.
"""

import argparse
import json
import os
import re
import resource
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
MEMORY_CAP_BYTES = 3 * 1024**3
TIMEOUT_S = 900
BROKEN = re.compile(r"\b(ImportError|ModuleNotFoundError|SyntaxError|IndentationError|NameError)\b")


@dataclass(frozen=True)
class Mutant:
    """One seeded defect: a text replacement in one product file and the tests that must catch it."""

    id: str
    defect: str
    file: str  # under src/embodic
    old: str  # must occur exactly once
    new: str
    killers: tuple[str, ...]  # pytest node ids or files, named before the run
    predicts: str  # regex the failure text must match


@dataclass
class Outcome:
    """What one mutant run gave: the verdict, the failing tests and the assertion lines quoted from pytest."""

    id: str
    verdict: str
    seconds: float
    exit_code: int
    failed: list[str]
    evidence: list[str]


def _limit_memory() -> None:
    resource.setrlimit(resource.RLIMIT_AS, (MEMORY_CAP_BYTES, MEMORY_CAP_BYTES))


def _copy_checkout(dst: Path) -> Path:
    ignore = shutil.ignore_patterns(".git", "__pycache__", ".venv", "build", ".pytest_cache", "*.pyc")
    shutil.copytree(REPO, dst / "checkout", ignore=ignore)
    return dst / "checkout"


def _pytest(work: Path, targets: tuple[str, ...]) -> tuple[subprocess.CompletedProcess[str] | None, float]:
    env = {**os.environ, "PYTHONPATH": str(work / "src"), "QT_QPA_PLATFORM": "offscreen"}
    argv = [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", "-x", "--tb=short", *targets]
    start = time.monotonic()
    try:
        done = subprocess.run(
            argv, cwd=work, env=env, capture_output=True, text=True, timeout=TIMEOUT_S, preexec_fn=_limit_memory
        )
    except subprocess.TimeoutExpired:
        return None, time.monotonic() - start
    return done, time.monotonic() - start


def _imports_from(work: Path) -> str:
    env = {**os.environ, "PYTHONPATH": str(work / "src")}
    code = "import embodic; print(embodic.__file__)"
    done = subprocess.run([sys.executable, "-c", code], cwd=work, env=env, capture_output=True, text=True)
    return done.stdout.strip()


def judge(mutant: Mutant, done: subprocess.CompletedProcess[str] | None, seconds: float) -> Outcome:
    """Classify one pytest run of a mutant from its exit code, its FAILED lines and its assertion lines."""
    if done is None:
        return Outcome(mutant.id, "timeout", seconds, -1, [], [])
    out = done.stdout + done.stderr
    failed = [line for line in out.splitlines() if line.startswith(("FAILED", "ERROR"))]
    evidence = [line.strip() for line in out.splitlines() if line.lstrip().startswith("E ")][:12]
    if done.returncode == 0:
        verdict = "survived"
    elif done.returncode != 1 or not failed or any(BROKEN.search(line) for line in evidence):
        verdict = "broken"
    elif re.search(mutant.predicts, "\n".join(evidence + failed)):
        verdict = "killed"
    else:
        verdict = "killed-other"
    return Outcome(mutant.id, verdict, round(seconds, 1), done.returncode, failed[:5], evidence)


def run(mutants: list[Mutant], suite: tuple[str, ...]) -> tuple[list[Outcome], dict[str, object]]:
    """Copy the checkout once, check the clean copy passes the named tests, then run every mutant on it."""
    with tempfile.TemporaryDirectory(prefix="embodic-mut-") as tmp:
        work = _copy_checkout(Path(tmp))
        imported = _imports_from(work)
        if not imported.startswith(str(work / "src")):
            raise SystemExit(f"the copy does not import its own src: {imported}")
        every = tuple(dict.fromkeys(k for m in mutants for k in m.killers))
        base, base_s = _pytest(work, every)
        base_info = {"imports": imported, "killers": list(every), "seconds": round(base_s, 1)}
        if base is None or base.returncode != 0:
            tail = "timeout" if base is None else (base.stdout + base.stderr)[-1500:]
            raise SystemExit(f"unmutated copy fails its named tests, no mutant can be judged:\n{tail}")
        base_info["summary"] = base.stdout.strip().splitlines()[-1]
        outcomes = []
        suite_ok: bool | None = None
        for mutant in mutants:
            target = work / "src" / "embodic" / mutant.file
            source = target.read_text(encoding="utf-8")
            if source.count(mutant.old) != 1:
                raise SystemExit(f"{mutant.id}: original text must occur once in {mutant.file}: {mutant.old!r}")
            target.write_text(source.replace(mutant.old, mutant.new), encoding="utf-8")
            try:
                outcome = judge(mutant, *_pytest(work, mutant.killers))
                if outcome.verdict == "survived":
                    if suite_ok is None:
                        target.write_text(source, encoding="utf-8")
                        clean, clean_s = _pytest(work, suite)
                        suite_ok = clean is not None and clean.returncode == 0
                        base_info["suite"] = {"tests": list(suite), "seconds": round(clean_s, 1), "passed": suite_ok}
                        if clean is not None:
                            base_info["suite"]["summary"] = clean.stdout.strip().splitlines()[-1]
                        target.write_text(source.replace(mutant.old, mutant.new), encoding="utf-8")
                    if suite_ok:
                        wide = judge(mutant, *_pytest(work, suite))
                        wide.verdict = {"survived": "survived", "broken": "broken", "timeout": "timeout"}.get(
                            wide.verdict, "suite-killed"
                        )
                        wide.seconds = round(wide.seconds + outcome.seconds, 1)
                        outcome = wide
                    else:
                        outcome.verdict = "survived-named (suite not clean)"
            finally:
                target.write_text(source, encoding="utf-8")
            outcomes.append(outcome)
            print(f"{outcome.verdict:12} {mutant.id} {mutant.defect} ({outcome.seconds} s)", flush=True)
            for line in outcome.failed[:1] + outcome.evidence[:3]:
                print(f"    {line[:200]}", flush=True)
        return outcomes, base_info


def main(argv: list[str] | None = None) -> int:
    """Run one campaign's mutants and print one verdict line per mutant; --json writes the full record."""
    from product_mutant_tables import CAMPAIGNS, SUITES

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("campaign", choices=sorted(CAMPAIGNS))
    parser.add_argument("--only", nargs="*", default=[])
    parser.add_argument("--json", type=Path)
    args = parser.parse_args(argv)
    mutants = [m for m in CAMPAIGNS[args.campaign] if not args.only or m.id in args.only]
    outcomes, base = run(mutants, SUITES[args.campaign])
    killed = sum(o.verdict == "killed" for o in outcomes)
    print(f"{killed}/{len(outcomes)} mutants killed")
    if args.json:
        doc = {"campaign": args.campaign, "baseline": base, "mutants": [asdict(m) for m in mutants]}
        doc["outcomes"] = [asdict(o) for o in outcomes]
        args.json.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    return 0 if killed == len(outcomes) else 1


if __name__ == "__main__":
    sys.exit(main())
