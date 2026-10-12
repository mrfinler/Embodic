"""Self-tests for an installed build (interfaces.md section 14): a fixed catalogue of checks and its runner.

The Tests dialog and `embodic-cli selftest` run it. A result never changes a badge: badges follow the registry and the
build's evidence (D-007), and a self-test only says whether this installation reproduces the build's numbers.
"""

from embodic.selftest.catalogue import SELFTESTS
from embodic.selftest.model import (
    SelfTestCheck,
    SelfTestGroup,
    SelfTestReport,
    SelfTestResult,
    SelfTestValue,
    SelfTestVerdict,
    agrees,
)
from embodic.selftest.runner import run_selftests, selftest_to_json

__all__ = [
    "SELFTESTS",
    "SelfTestCheck",
    "SelfTestGroup",
    "SelfTestReport",
    "SelfTestResult",
    "SelfTestValue",
    "SelfTestVerdict",
    "agrees",
    "run_selftests",
    "selftest_to_json",
]
