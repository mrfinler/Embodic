"""Print one line per packaged example: topology, DRC, Ke_line_peak, P_ic, K_m and the result status counts.

Run from the repository root: ``python -m tests.unit.embodic_io.project.example_summary``.
"""

import dataclasses
from collections import Counter

from embodic.api import compute
from embodic.errors import Severity
from embodic.io.examples import list_examples, load_example
from embodic.io.project import ProjectFile, project_provenance
from embodic.results.traceable import Traceable


def main() -> None:
    """Compute every packaged example and print its summary."""
    for info in list_examples():
        ref, design = load_example(info.example_id)
        outcome = compute(design, project_provenance(ProjectFile(design=design, origin=ref)))
        assert outcome is not None
        severities = Counter(i.severity.value for i in outcome.issues)
        drc = "not run" if outcome.drc is None else " ".join("pass" if r.passed else "FAIL" for r in outcome.drc)
        ke = ic = km = "n/a"
        statuses: Counter[str] = Counter()
        if outcome.analysis is not None:
            ke_line = outcome.analysis.ke_line_peak_v_s_per_rad
            ke = f"{ke_line.value:.6g} V*s/rad ({ke_line.status})"
            p_ic, k_m = outcome.analysis.loss_interconnect_w, outcome.analysis.motor_constant_n_m_per_sqrt_w
            ic = f"{p_ic.value:.6g} W ({p_ic.status})"
            km = f"{k_m.value:.6g} {k_m.unit.display()} ({k_m.status})"
            fields = (getattr(outcome.analysis, f.name) for f in dataclasses.fields(outcome.analysis))
            statuses = Counter(str(v.status) for v in fields if isinstance(v, Traceable))
        print(
            f"{info.example_id}: topology {info.topology}, DRC {drc}, Ke_line_peak {ke}, P_ic {ic}, "
            f"motor_constant {km}, "
            f"ERROR {severities[Severity.ERROR.value]}, WARNING {severities[Severity.WARNING.value]}, "
            f"statuses {dict(sorted(statuses.items()))}"
        )


if __name__ == "__main__":
    main()
