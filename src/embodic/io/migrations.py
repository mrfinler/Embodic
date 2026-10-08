"""Project file versions and the migrations between them (interfaces.md 9.1, schema version rule of U-D4).

v1 is the first version written, so no migration exists yet. A change that makes a v1 reader read a file differently
adds `migrate_v1_to_v2` to MIGRATIONS and raises PROJECT_SCHEMA_VERSION in the same commit.
"""

from collections.abc import Callable, Mapping
from types import MappingProxyType
from typing import Any

from embodic.errors import IssueCategory, Severity, ValidationIssue, message_for

PROJECT_SCHEMA_VERSION = 1

Document = dict[str, Any]
Migration = Callable[[Document], Document]

MIGRATIONS: Mapping[int, Migration] = MappingProxyType({})  # n -> migrate_v<n>_to_v<n+1>


def _issue(code: str, category: IssueCategory, severity: Severity, value: int, limit: int) -> ValidationIssue:
    return ValidationIssue(
        code=code,
        category=category,
        severity=severity,
        message=message_for(code),
        pointers=("/schema_version",),
        value=value,
        limit=limit,
    )


def migrate(
    document: Document, *, current: int = PROJECT_SCHEMA_VERSION, migrations: Mapping[int, Migration] = MIGRATIONS
) -> tuple[Document | None, tuple[ValidationIssue, ...]]:
    """Run every migration from the document's version to `current`; refuse a newer version (None).

    The caller checked that `schema_version` is an integer of 1 or more.
    """
    version: int = document["schema_version"]
    if version > current:
        refused = _issue("INVALID_SCHEMA_VERSION_NEWER", IssueCategory.INVALID, Severity.ERROR, version, current)
        return None, (refused,)
    if version == current:
        return document, ()
    for step in range(version, current):
        document = {**migrations[step](document), "schema_version": step + 1}
    return document, (_issue("INFO_MIGRATED", IssueCategory.INVALID, Severity.INFO, version, current),)
