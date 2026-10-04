"""Location of the shipped resources (icons, themes, examples, evidence registries)."""

from importlib.resources import files
from pathlib import Path


def resource_root() -> Path:
    """Return the folder that holds the shipped resources.

    A wheel carries the repository's ``resources/`` folder as ``embodic/_resources``. An editable install imports
    ``embodic`` from ``src/``, where that folder does not exist, so the source checkout's ``resources/`` is used.

    Returns
    -------
    Path
        An existing directory.

    Raises
    ------
    FileNotFoundError
        When neither location exists, which means the package was installed without its resources.
    """
    package_dir = files("embodic")
    if not isinstance(package_dir, Path):
        raise FileNotFoundError(f"embodic must be installed as files on disk, not inside an archive: {package_dir}")
    for candidate in (package_dir / "_resources", package_dir.parents[1] / "resources"):
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"embodic resources are missing next to {package_dir}")
