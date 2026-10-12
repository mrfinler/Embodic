# Lock files

Each file pins every package of one install to one version, with the SHA-256 of every wheel and sdist of that version
(REQ-N-06, `docs/phase2/architecture/package_layout.md` section 5.2). One file is valid on Windows and on Linux.

| File | Contents | Use it for |
|---|---|---|
| `py311.txt`, `py312.txt`, `py313.txt` | NumPy, PySide6-Essentials and shiboken6 (extra `desktop`) | running embodic |
| `py311-dev.txt`, `py312-dev.txt`, `py313-dev.txt` | the above plus the test and build tools (extra `desktop-dev`) | developing and testing embodic |

## Install from a lock file

`--require-hashes` needs a hash for every requirement, and a local wheel has none, so the install takes two commands.
Replace `py311` with the file of your Python version.

```
python -m pip install --require-hashes -r requirements/py311.txt
python -m pip install --no-deps build/dist/embodic-0.0.1-py3-none-any.whl
```

For a development checkout:

```
python -m pip install --require-hashes -r requirements/py311-dev.txt
python -m pip install --no-deps -e .
```

## Regenerate the lock files

uv writes the files. It is a build tool only, it is not in `pyproject.toml`, and installing embodic never needs it. The
header of each file names the uv version that wrote it. Run from the repository root:

```
uvv=$(uv --version | cut -d' ' -f2)
for v in 3.11 3.12 3.13; do
  for extra in desktop desktop-dev; do
    out=requirements/py${v/./}${extra#desktop}.txt
    cmd="uv pip compile pyproject.toml --extra $extra --universal --python-version $v --generate-hashes -o $out"
    $cmd -q --custom-compile-command "$cmd  # uv $uvv"
  done
done
```
