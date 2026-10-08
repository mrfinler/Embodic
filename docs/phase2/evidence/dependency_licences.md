Prepared by: Agent 5 (Research & Evidence Specialist), model: claude-opus-5-5. Revised 2026-10-08 (U-S3c) by Agent 5, model: claude-sonnet-5-5.

# Dependency licences (Phase 2)

This register lists every package the Phase 2 stack plans to use, its pin for Python 3.11, its declared licence, and
what embodic must do when it distributes the application. Regenerate the table, and its raw data in
`dependency_licences.snapshot.json`, from the repository root:

```
python3 docs/phase2/evidence/tools/check_dependency_licences.py
```

The script reads the PyPI JSON API and each chosen wheel's PEP 658 `.metadata` file. For packages that embodic ships,
it also lists the licence and notice files inside the Windows CPython 3.11 wheel through HTTP range requests, without
downloading the whole wheel. All rows below are `verified` from PyPI metadata unless marked otherwise. "Verified"
means read in the metadata. It is not a legal opinion. A lawyer should review the final distribution.

## Is anything else needed?

No other runtime package is needed (`inferred`). The core imports the standard library and NumPy only, and the
desktop extra adds PySide6-Essentials, which requires shiboken6 (ADR-0008 §Decision items 1–3). The PDF report uses
the in-house writer, so reportlab is not needed. D-009 removed `kicad-python`, `kiutils` and `sexpdata` with KiCad.
`platformdirs` from ADR-0008 is optional, and the standard library can replace it. The test and dev rows come from
ADR-0008 and are never shipped.

Python itself is shipped inside a PyInstaller one-folder build. Its licence is PSF-2.0, and the bundle must carry the
Python licence text. Status: `not accessed` this session. Source to read is https://docs.python.org/3/license.html.

## Package register

<!-- BEGIN GENERATED: tools/check_dependency_licences.py -->
PyPI JSON API and wheel `.metadata` files, accessed 2026-10-08. Pin = newest final release whose `Requires-Python` admits 3.11.0 (the user's minimum) and that lies inside the version range `pyproject.toml` declares.

| Package | Pin (3.11 floor) | Newest overall | Declared licence (PyPI metadata) | `License-File` entries | Scope | Shipped | Status |
|---|---|---|---|---|---|---|---|
| [numpy](https://pypi.org/project/numpy/2.4.6/) | 2.4.6 | 2.5.3 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | 17 files (snapshot JSON) | runtime (core) | yes | verified (PyPI metadata) |
| [PySide6-Essentials](https://pypi.org/project/PySide6-Essentials/6.11.2/) | 6.11.2 | 6.12.0 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only | `LicenseRef-Qt-Commercial.txt` | runtime (desktop extra) | yes | verified (PyPI metadata) |
| [shiboken6](https://pypi.org/project/shiboken6/6.11.2/) | 6.11.2 | 6.12.0 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only | `LicenseRef-Qt-Commercial.txt` | runtime (required by PySide6-Essentials) | yes | verified (PyPI metadata) |
| [pyinstaller](https://pypi.org/project/pyinstaller/6.22.3/) | 6.22.3 | 6.22.3 | GNU General Public License v2 (GPLv2) | `COPYING.txt` | build (D-015 stretch goal) | bootloader only | verified (PyPI metadata) |
| [pyinstaller-hooks-contrib](https://pypi.org/project/pyinstaller-hooks-contrib/2026.8/) | 2026.8 | 2026.8 | Apache Software License; GNU General Public License v2 (GPLv2) | `LICENSE` | build (required by pyinstaller) | no | verified (PyPI metadata) |
| [pytest](https://pypi.org/project/pytest/9.1.1/) | 9.1.1 | 9.1.1 | MIT | `LICENSE` | test | no | verified (PyPI metadata) |
| [pytest-qt](https://pypi.org/project/pytest-qt/4.5.0/) | 4.5.0 | 4.5.0 | MIT | `LICENSE` | test (desktop) | no | verified (PyPI metadata) |
| [pytest-cov](https://pypi.org/project/pytest-cov/7.1.0/) | 7.1.0 | 7.1.0 | MIT | `AUTHORS.rst`, `LICENSE` | test (ADR-0008) | no | verified (PyPI metadata) |
| [pytest-timeout](https://pypi.org/project/pytest-timeout/2.4.0/) | 2.4.0 | 2.4.0 | MIT | `LICENSE` | test (pyproject dev, hang guard) | no | verified (PyPI metadata) |
| [hypothesis](https://pypi.org/project/hypothesis/6.168.5/) | 6.168.5 | 6.168.5 | MPL-2.0 | `LICENSE.txt` | test (ADR-0008) | no | verified (PyPI metadata) |
| [jsonschema](https://pypi.org/project/jsonschema/4.26.0/) | 4.26.0 | 4.26.0 | MIT | `COPYING` | test (ADR-0008) | no | verified (PyPI metadata) |
| [ezdxf](https://pypi.org/project/ezdxf/1.4.4/) | 1.4.4 | 1.4.4 | MIT License | `LICENSE` | test (ADR-0008, DXF parser) | no | verified (PyPI metadata) |
| [pypdf](https://pypi.org/project/pypdf/6.19.0/) | 6.19.0 | 6.19.0 | BSD-3-Clause | `LICENSE` | test (ADR-0008, PDF parser) | no | verified (PyPI metadata) |
| [ruff](https://pypi.org/project/ruff/0.16.10/) | 0.16.10 | 0.16.10 | MIT | `LICENSE` | dev | no | verified (PyPI metadata) |
| [import-linter](https://pypi.org/project/import-linter/2.15/) | 2.15 | 2.15 | BSD 2-Clause License | `LICENSE` | dev | no | verified (PyPI metadata) |
| [mypy](https://pypi.org/project/mypy/2.4.0/) | 2.4.0 | 2.4.0 | MIT | `LICENSE`, `mypy/typeshed/LICENSE` | dev (ADR-0008) | no | verified (PyPI metadata) |
| [hatchling](https://pypi.org/project/hatchling/1.32.4/) | 1.32.4 | 1.32.4 | MIT | `LICENSE.txt` | build backend (pyproject build-system and dev) | no | verified (PyPI metadata) |
| [pip-licenses](https://pypi.org/project/pip-licenses/5.5.5/) | 5.5.5 | 5.5.5 | MIT | `LICENSE` | dev (ADR-0008 licence gate) | no | verified (PyPI metadata) |
| [pip-audit](https://pypi.org/project/pip-audit/2.10.1/) | 2.10.1 | 2.10.1 | Apache Software License | `LICENSE` | dev (ADR-0008 CVE gate) | no | verified (PyPI metadata) |
<!-- END GENERATED -->

## Installed-package check (U-S3c)

The script reads PyPI. These two rows were also read from the installed copies in the project venv (`verified`):

| Package | Installed file | Licence string | Licence file |
|---|---|---|---|
| pytest-timeout 2.4.0 | `.venv/lib/python3.11/site-packages/pytest_timeout-2.4.0.dist-info/METADATA` | `License: MIT`, classifier `License :: OSI Approved :: MIT License` | `licenses/LICENSE`, 1085 bytes, begins "The MIT License", "Copyright (C) 2012, 2014 Floris Bruynooghe" |
| hatchling 1.32.4 | `.venv/lib/python3.11/site-packages/hatchling-1.32.4.dist-info/METADATA` | `License-Expression: MIT` | `licenses/LICENSE.txt`, 1088 bytes, begins "MIT License", "Copyright (c) 2021-present Ofek Lev" |

Every requirement in `pyproject.toml` (build-system, `dependencies` and every extra) now has a row. The script fails before any network call when one is missing, and `check_dependency_licences.py --coverage` runs only that check. The pin follows the range in `pyproject.toml`, so PySide6-Essentials and shiboken6 stay at 6.11.2 although 6.12.0 exists.

## Licence text locations

| Licence | Text URL | Status |
|---|---|---|
| LGPL-3.0-only (Qt, PySide6, shiboken6) | https://www.gnu.org/licenses/lgpl-3.0.txt | not accessed (WebFetch refused: robots.txt) |
| GPL-3.0 (LGPL-3.0 adds terms to it, so both texts ship together) | https://www.gnu.org/licenses/gpl-3.0.txt | not accessed |
| BSD-3-Clause, 0BSD, MIT, Zlib, CC0-1.0 (NumPy) | the 17 `License-File` entries inside the NumPy wheel, top file `numpy-2.4.6.dist-info/licenses/LICENSE.txt` | verified (file names listed from the cp311 win_amd64 wheel) |
| GPL-2.0-or-later with Bootloader Exception (PyInstaller) | `pyinstaller-6.22.3.dist-info/licenses/COPYING.txt` in the wheel | verified (text read from the wheel; excerpt in the snapshot) |
| SIL OFL 1.1 (fonts) | per font, EV-72…EV-76 in `evidence_register.json` | verified (extract, Phase 1) |
| PSF-2.0 (CPython) | https://docs.python.org/3/license.html | not accessed |

## Distribution obligations

### embodic installed with pip into a venv (the Phase 2 default, D-015)

The user's pip downloads NumPy, PySide6-Essentials and shiboken6 from PyPI. embodic's own wheel or sdist contains no
third-party code. The Qt binaries reach the user from PyPI, not from the embodic project (`inferred`). Obligations for
embodic in this mode:

1. Declare the dependencies and their licences in the README and the About box. PySide6 is used under LGPL-3.0.
2. Do not modify PySide6, shiboken6 or Qt. A modified copy would have to be released under LGPL-3.0 with source.
3. Keep embodic's use dynamic. Python imports the Qt shared libraries at run time, which is the "work that uses the
   library" case on Qt's obligations page (`verified (extract)`, https://www.qt.io/licensing/open-source-lgpl-obligations).

### PyInstaller one-folder build (stretch goal, D-015)

Here embodic distributes the Qt, PySide6, shiboken6, NumPy and CPython binaries itself, so the distributor obligations
fall on embodic. From Qt's obligations page (`verified (extract)`, URL above):

1. Ship a copy of the LGPL-3.0 text and the GPL-3.0 text, and show a prominent notice that the application uses Qt
   under LGPL-3.0. Qt states "providing a copy of the LGPL license text to the user and displaying a prominent notice
   about using the LGPL library".
2. Deliver the complete corresponding source of the Qt and PySide6 versions shipped, or a written offer for it. Qt
   states the source "should be delivered". The matching sources are the Qt 6.11.2 and PySide6 6.11.2 releases
   (`inferred`; exact source archive URLs not accessed).
3. Let the user replace the Qt libraries and run the result. Qt states the user must be able "to change and re-link
   the library ... including reverse engineering" and "to run the re-linked binary". A one-folder build keeps each
   Qt `.dll` as a separate file, which permits replacement. A one-file build packs them into the executable and makes
   replacement harder (`inferred`). Use one-folder.
4. Put no term in the embodic licence or EULA that forbids reverse engineering of the Qt parts (Qt page, "No
   Restrictions on Freedom").
5. Ship NumPy's licence files. The BSD-3-Clause, MIT and Zlib texts require the copyright notice and licence text in
   binary redistributions (`inferred` from the licence names; texts listed in the wheel, not read).
6. Ship the CPython licence text (PSF-2.0, `not accessed`).
7. The PyInstaller bootloader adds no obligation. Its COPYING.txt grants "unlimited permission to link or embed
   compiled bootloader and related files into combinations with other programs, and to distribute those combinations
   without any restriction coming from the use of those files" (`verified`, read from the 6.22.3 wheel).

Defect found (DEF-S3-01). The PySide6-Essentials 6.11.2 and shiboken6 6.11.2 Windows wheels declare only
`LicenseRef-Qt-Commercial.txt` as `License-File`. That file is 470 bytes and is a commercial-licence notice. It does
not contain the LGPL-3.0 text (`verified`, read from the wheel). A PyInstaller build would therefore carry no LGPL text
unless embodic adds it. Reproduce with
`python3 docs/phase2/evidence/tools/check_dependency_licences.py`, then read `notice_files_in_wheel` for
PySide6-Essentials in the snapshot. Fix: the packaging unit (M5) adds `licenses/LGPL-3.0.txt`, `licenses/GPL-3.0.txt`
and a `THIRD_PARTY_NOTICES` file to the bundle. ADR-0008 item 7 (pip-licenses generation) does not catch this,
because pip-licenses reports metadata, not the missing text.

Qt's own third-party components inside the Qt binaries (for example FreeType, HarfBuzz, libpng, PCRE2) have their
own notice terms. Qt lists them at https://doc.qt.io/qt-6/licenses-used-in-qt.html. Status: `not accessed`. The M5
unit must read that page for the modules actually bundled.

### Test and dev tools

pytest, pytest-qt, pytest-cov, pytest-timeout (MIT), hatchling (MIT), jsonschema, ezdxf, pypdf, ruff, mypy, pip-licenses (MIT), import-linter (BSD-2-Clause),
pip-audit and pyinstaller-hooks-contrib (Apache-2.0, hooks also GPL-2.0), and hypothesis (MPL-2.0) run only on
developer machines and in CI. embodic does not distribute them, so their licences add no distribution obligation
(`inferred`). import-linter's declared licence is BSD 2-Clause. ADR-0008 records it as "BSD" without the variant.

## Fonts: which files need the licence text shipped

The design spec (`docs/phase1/design/design_spec_draft.md` lines 186–189) lists font stacks. Segoe UI and Consolas
are system fonts and are never bundled. The candidates for bundling are Noto Sans, Liberation Sans, Liberation Mono,
Cascadia Mono, JetBrains Mono and Manrope. No document fixes which of them Phase 2 bundles (`unresolved`, a decision
for Agent 1 and Agent 3).

The rule for any bundled font file is the same. Each is SIL OFL 1.1 (EV-72…EV-76, `verified (extract)`). The OFL
requires each copy of the font software to carry its copyright notice and the licence. Ship `OFL.txt` with the
copyright line next to each bundled font family, inside the wheel and the PyInstaller folder (`inferred` from the OFL
condition 2 wording as summarised in Phase 1; the OFL text was not re-read this session).

| Font | Copyright line (Phase 1 EV row) | Reserved Font Name | Ship licence text if bundled |
|---|---|---|---|
| Noto Sans | Copyright 2022 The Noto Project Authors (EV-72) | none listed | yes |
| Liberation Sans, Liberation Mono | Google 2010; Red Hat 2012 (EV-73) | Liberation | yes; a subset or modified copy must be renamed |
| Cascadia Mono | Microsoft 2019 (EV-74) | Cascadia Code | yes; a subset or modified copy must be renamed |
| JetBrains Mono | 2020 The JetBrains Mono Project Authors (EV-75) | none listed | yes |
| Manrope | 2018 The Manrope Project Authors (EV-76) | none listed | yes |

A PDF report that embeds a subset of an RFN font is a modified copy under that reading (`inferred`, legal
confirmation not sought). The simplest choice is to embed Noto Sans and JetBrains Mono, which carry no reserved name.
