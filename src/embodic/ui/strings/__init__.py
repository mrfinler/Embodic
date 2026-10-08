"""The English string catalogue of the desktop app: every area's table merged, a duplicate key is a build error."""

from collections.abc import Mapping

from embodic.ui.strings import shell


def merge(*tables: Mapping[str, str]) -> dict[str, str]:
    """Return the union of the tables; raise ValueError when two tables define one key."""
    merged: dict[str, str] = {}
    for table in tables:
        duplicates = sorted(merged.keys() & table.keys())
        if duplicates:
            raise ValueError(f"string keys defined twice: {duplicates}")
        merged.update(table)
    return merged


STRINGS: Mapping[str, str] = merge(shell.STRINGS)


def text(key: str, **fields: object) -> str:
    """Return the catalogue text of a key with its ``{field}`` placeholders filled; KeyError for an unknown key."""
    template = STRINGS[key]
    return template.format(**fields) if fields else template
