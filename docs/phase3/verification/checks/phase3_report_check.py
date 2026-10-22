"""Check the Phase 3 report against the audit, the DEF record and the checkout.

    python3 docs/phase3/verification/checks/phase3_report_check.py [--self-test]

Three checks, each a list of problems:

- Audit: the count tables and every row list of section 1 equal `req_audit.md`.
- DEF list: every DEF ID that the Phase 3 record names has one row in section 4, unless a decision row before D-048
  names it, and then it is in the pre-Phase-3 list. No row names an ID that the record lacks, except an `unresolved`
  row for a gap in the DEF-W numbers. A gap stays a gap when a decision clause that says "retired" names it (D-100d
  retires DEF-W-10 and DEF-W-11): the check reads the record without such clauses. The counts sentence
  equals the State column. The record is the decision log rows D-048 on, `tests/independent/m7/records/defects.md`,
  every Markdown file under docs/phase3 and docs/phase4 except this report, CHANGELOG.md, and the commit messages
  that name a DEF-W ID.
- References and prose: `problems_of` of docs/phase4/verification/checks/plan_refs.py (decision rows, REQ IDs, paths,
  no semicolon, long dash or curly quote outside code spans).

Exit 0 when no problem is found. --self-test plants one fault of each kind in a copy and expects each to be found.
"""

import importlib.util
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
REPORT = ROOT / "docs/phase3/verification/phase3_report.md"
AUDIT = ROOT / "docs/phase3/verification/req_audit.md"
LOG = ROOT / "docs/decision_log.md"
DEF = re.compile(r"DEF-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*-\d{2}")
TAIL = re.compile(r"\s*(?:/|,|and|to)\s*-?(\d{2})\b")
GROUPS = {
    "Must, `verified`": ("must", "verified"),
    "Must, `partial`": ("must", "partial"),
    "Must, `failed`": ("must", "failed"),
    "Should, `partial`": ("should", "partial"),
    "Should, `not tested`": ("should", "not tested"),
    "Could, `partial`": ("could", "partial"),
    "Could, `not tested`": ("could", "not tested"),
}


def def_ids(text: str) -> set[str]:
    """Return every DEF ID in a text, with list tails such as `DEF-U-S7-01/02/03` and `-01, -03` expanded."""
    found = set()
    for line in text.splitlines():
        for m in DEF.finditer(line):
            found.add(m.group(0))
            pos = m.end()
            while t := TAIL.match(line, pos):
                found.add(m.group(0)[:-2] + t.group(1))
                pos = t.end()
    return found


def log_rows() -> dict[int, str]:
    """Return the text of each decision row, keyed by its number."""
    rows: dict[int, str] = {}
    for line in LOG.read_text(encoding="utf-8").splitlines():
        if m := re.match(r"\| D-(\d{3})[a-z]? \|", line):
            rows[int(m.group(1))] = rows.get(int(m.group(1)), "") + line + "\n"
    return rows


def retiring_clauses() -> list[str]:
    """Return the lettered clauses of the decision rows from D-048 on that say an ID is retired."""
    clauses = []
    for n, text in log_rows().items():
        if n >= 48:
            clauses += [c for c in re.split(r"(?=\([a-z]\) )", text) if re.search(r"\bretired\b", c)]
    return clauses


def record_text() -> str:
    """Return the Phase 3 record that the DEF list must cover, without this report."""
    parts = [text for n, text in log_rows().items() if n >= 48]
    parts.append((ROOT / "tests/independent/m7/records/defects.md").read_text(encoding="utf-8"))
    parts.append((ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))
    for base in ("docs/phase3", "docs/phase4"):
        parts += [p.read_text(encoding="utf-8") for p in sorted((ROOT / base).rglob("*.md")) if p != REPORT]
    messages = subprocess.run(
        ["git", "-C", str(ROOT), "log", "--all", "--format=%B", "--grep=DEF-W-"], capture_output=True, text=True
    ).stdout
    parts.append(messages)
    return "\n".join(parts)


def audit_groups() -> dict[tuple[str, str], list[str]]:
    """Return the REQ IDs of req_audit.md by (priority, status), in file order."""
    groups: dict[tuple[str, str], list[str]] = {}
    for line in AUDIT.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 8 and cells[0].startswith("REQ-"):
            groups.setdefault((cells[1], cells[3]), []).append(cells[0])
    return groups


def section(text: str, heading: str) -> str:
    """Return the text from a heading to the next level-2 heading."""
    start = text.index(heading)
    end = text.find("\n## ", start + len(heading))
    return text[start : end if end != -1 else len(text)]


def audit_problems(text: str) -> list[str]:
    """Compare the count tables and the row lists of section 1 with req_audit.md."""
    problems = []
    groups = audit_groups()
    body = section(text, "## 1. The requirement audit")
    counts: Counter[tuple[str, str]] = Counter()
    for (prio, status), ids in groups.items():
        counts[("all", status)] += len(ids)
        if prio == "must":
            counts[("must", status)] += len(ids)
    columns = ("verified", "partial", "failed", "not tested", "withdrawn")
    for scope in ("all", "must"):
        total = sum(v for (s, _), v in counts.items() if s == scope)
        want = f"| {scope} {total} | " + " | ".join(str(counts[(scope, c)]) for c in columns) + " |"
        if want not in body:
            problems.append(f"count row `{want}` is not in section 1")
    flat = re.sub(r"\s+", " ", body)
    for label, key in GROUPS.items():
        m = re.search(re.escape(f"- {label} (") + r"(\d+)\): ([^.]*)\.", flat)
        want_ids = groups.get(key, [])
        if not m:
            problems.append(f"no list `{label}` in section 1")
            continue
        listed = re.findall(r"REQ-[A-Z]-\d\d", m.group(2))
        if int(m.group(1)) != len(want_ids) or listed != want_ids:
            problems.append(f"list `{label}` differs from req_audit.md: {sorted(set(listed) ^ set(want_ids))}")
    withdrawn = len(groups.get(("-", "withdrawn"), []))
    if f"- Withdrawn ({withdrawn}):" not in body:
        problems.append(f"withdrawn count {withdrawn} is not in section 1")
    return problems


def def_rows(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Return section 4 and its table rows as (ID, state)."""
    body = section(text, "## 4. The DEF list")
    rows = re.findall(r"^\| (DEF-[A-Za-z0-9-]+\d{2}) \| [^|]* \| ([^|]*) \|", body, re.M)
    return body, [(ident, state.strip()) for ident, state in rows]


def coverage_problems(body: str, rows: list[tuple[str, str]], record: str) -> list[str]:
    """Check that the table and the pre-Phase-3 list cover the record's DEF IDs, each once."""
    table = [ident for ident, _ in rows]
    problems = [f"{ident} has {n} rows" for ident, n in Counter(table).items() if n > 1]
    early = def_ids("".join(t for n, t in log_rows().items() if n < 48))
    in_record = def_ids(record)
    problems += [f"{i} is in the Phase 3 record but has no row" for i in sorted(in_record - early - set(table))]
    gaps = {ident for ident, state in rows if state == "`unresolved`"}
    problems += [
        f"{i} has a row but the record outside this report never names it"
        for i in sorted(set(table) - in_record - gaps)
    ]
    used = {int(i[-2:]) for i in in_record if i.startswith("DEF-W-")}
    unretired = record
    for clause in retiring_clauses():
        unretired = unretired.replace(clause, "")
    named = def_ids(unretired)
    for ident in sorted(gaps):
        if not ident.startswith("DEF-W-") or ident in named or not 0 < int(ident[-2:]) < max(used):
            problems.append(f"{ident} is `unresolved` but is no gap in the DEF-W numbers of the record")
    problems += [f"{i} has a row but a decision row before D-048 names it" for i in sorted(set(table) & early)]
    start = body.index("These IDs appear in the Phase 3 record but were opened before")
    listed_pre = set(DEF.findall(body[start : body.index("Each is named", start)]))
    if listed_pre != in_record & early:
        problems.append(f"the pre-Phase-3 list differs: {sorted(listed_pre ^ (in_record & early))}")
    return problems


def count_problems(body: str, rows: list[tuple[str, str]]) -> list[str]:
    """Check the counts sentence against the State column, and that every state is one of the known ones."""
    states = Counter(state for _, state in rows)
    known = {"closed", "closed on Linux", "open", "`unresolved`", "moved to Phase 5 by Fable"}
    known |= {"moved to Phase 5 by the user", "closed by Fable as not a product defect", "accepted by name by Fable"}
    problems = [f"unknown state `{s}`" for s in states if s not in known and not s.startswith("closed, ")]
    not_product = states["closed by Fable as not a product defect"]
    closed = sum(v for s, v in states.items() if s.startswith("closed")) - not_product
    fable, user = states["moved to Phase 5 by Fable"], states["moved to Phase 5 by the user"]
    want = (
        f"Counts: {len(rows)} rows. {closed} closed ({states['closed on Linux']} of them on Linux only",
        f"{fable + user} moved to Phase 5 ({fable} by Fable",
        f"and {user} by the user",
        f"{not_product} closed by Fable as not a product defect",
        f"{states['accepted by name by Fable']} accepted by name by Fable",
        f"{states['open']} open",
        f"{states['`unresolved`']} `unresolved`",
    )
    flat = re.sub(r"\s+", " ", body)
    return problems + [f"the counts sentence lacks `{piece}`" for piece in want if piece not in flat]


def ref_problems(text: str) -> list[str]:
    """Return the problems that plan_refs.py finds: references that do not resolve, and banned punctuation."""
    path = ROOT / "docs/phase4/verification/checks/plan_refs.py"
    spec = importlib.util.spec_from_file_location("plan_refs", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.problems_of(text)


def problems_of(text: str, record: str) -> list[str]:
    """Return every problem of the report text."""
    body, rows = def_rows(text)
    elsewhere = [int(n) for n in re.findall(r"Section 4 lists (\d+) rows", text)]
    totals = [f"a 'Section 4 lists' sentence says {n}, the table has {len(rows)}" for n in elsewhere if n != len(rows)]
    return (
        totals
        + audit_problems(text)
        + coverage_problems(body, rows, record)
        + count_problems(body, rows)
        + ref_problems(text)
    )


def self_test(text: str, record: str) -> int:
    """Plant one fault of each kind in a copy of the report and return 1 when a plant is missed."""
    plants = {
        "a must count off by one": (text.replace("| must 73 | 67 |", "| must 73 | 66 |", 1), "count row"),
        "a row missing from a list": (text.replace("REQ-F-01, REQ-F-02,", "REQ-F-02,", 1), "differs from req_audit"),
        "a DEF row removed": (re.sub(r"^\| DEF-W-16 \|.*\n", "", text, count=1, flags=re.M), "DEF-W-16 is in the"),
        "a DEF row the record lacks": (
            text.replace("| DEF-US18-01 |", "| DEF-ZZ-98 | x | open | x |\n| DEF-US18-01 |", 1),
            "DEF-ZZ-98 has a row",
        ),
        "a state count off": (
            text.replace("2 accepted by name by Fable", "3 accepted by name by Fable", 1),
            "lacks `2 accepted by name by Fable`",
        ),
        "an `unresolved` row that is no gap and that no clause retires": (
            re.sub(r"^(\| DEF-W-16 \| [^|]* \| )[^|]*( \|)", r"\1`unresolved`\2", text, count=1, flags=re.M),
            "DEF-W-16 is `unresolved` but is no gap",
        ),
        "a row total off in section 6": (
            text.replace("Section 4 lists 93 rows", "Section 4 lists 95 rows", 1),
            "lists",
        ),
        "a semicolon in prose": (text.replace("This is the English", "This is; the English", 1), "semicolon"),
        "a decision row that does not exist": (text.replace("(D-099b)", "(D-199b)", 1), "D-199b"),
    }
    missed = []
    for name, (planted, expect) in plants.items():
        if planted == text:
            missed.append(f"{name} (the plant did not apply)")
            continue
        if not any(expect in p for p in problems_of(planted, record)):
            missed.append(name)
    clean = problems_of(text, record)
    found = len(plants) - len(missed)
    print(f"self-test: {found} of {len(plants)} plants found; the report itself: {len(clean)} problems")
    for m in missed:
        print(f"  missed: {m}")
    return 1 if missed or clean else 0


def main() -> int:
    """Print the problems of the report, or run the self-test."""
    text = REPORT.read_text(encoding="utf-8")
    record = record_text()
    if "--self-test" in sys.argv:
        return self_test(text, record)
    found = problems_of(text, record)
    for problem in found:
        print(problem)
    print(f"{REPORT.name}: {len(found)} problems")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
