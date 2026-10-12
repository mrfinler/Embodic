Prepared by: Agent 5 (Research & Evidence Specialist), model: claude-opus-5-5. Revised 2026-10-08 (U-S3c) by Agent 5, model: claude-sonnet-5-5. Revised 2026-10-09 (U-S5a) by Agent 5, model: claude-sonnet-5-5. Revised 2026-10-09 (U-S5b: static Inter files) by Agent 5, model: claude-sonnet-5-5. Revised 2026-10-12 (U-S5c: M5 distribution, LGPL route, licence text sources) by Agent 5, model: claude-sonnet-5-5.

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
PyPI JSON API and wheel `.metadata` files, accessed 2026-10-09. Pin = newest final release whose `Requires-Python` admits 3.11.0 (the user's minimum) and that lies inside the version range `pyproject.toml` declares.

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
| [fonttools](https://pypi.org/project/fonttools/4.66.1/) | 4.66.1 | 4.66.1 | MIT | `LICENSE`, `LICENSE.external` | test (pyproject dev, U-M4f font reader oracle) | no | verified (PyPI metadata) |
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

### Pins checked in U-S5a (2026-10-09)

`check_dependency_licences.py --coverage` failed before this unit with `pyproject.toml requirements missing from PACKAGES: ['fonttools']` (`verified`, run on main 3d70170). The script now lists fonttools, and the full run passes. The pins below are the table's pin, the range in `pyproject.toml`, and the copy installed in the project venv (`pip list`, `verified`).

| Package | `pyproject.toml` entry | Table pin | Installed | Result |
|---|---|---|---|---|
| fonttools | `dev`: `fonttools>=4.60,<5` | 4.66.1 | 4.66.1 | New row. PyPI JSON `info.license` is `MIT`; it has no `license_expression` and no licence classifier. The wheel `.metadata` declares `License-File: LICENSE` and `License-File: LICENSE.external`. Row EV-108. |
| pytest-qt | `desktop-dev`: `pytest-qt>=4.5,<5` | 4.5.0 | 4.5.0 | Pin matches the range and the newest release. Licence MIT (PyPI metadata). No change. |
| PySide6-Essentials | `desktop`: `PySide6-Essentials>=6.11,<6.12` | 6.11.2 | 6.11.2 | Pin matches the range and `package_layout.md` §5 (6.11.2). Newest overall is 6.12.0, outside the range. No change. |

fontTools is imported only by tests (`tests/unit/ui/fonts/test_font_files.py`, `tests/unit/embodic_io/exporters/test_pdf_fonts.py`, `tests/unit/embodic_io/exporters/test_svg.py`). A search of `src` for `fontTools` and `fonttools` finds nothing (`verified`, `grep -rn` on main 3d70170). It never reaches a user's machine at run time, so the wheel and the PyInstaller folder carry nothing from it.

## Licence text locations

| Licence | Text URL | Status |
|---|---|---|
| LGPL-3.0-only (Qt, PySide6, shiboken6) | https://www.gnu.org/licenses/lgpl-3.0.txt (refused: the session proxy answered 403 for www.gnu.org on 2026-10-09). Read instead: https://raw.githubusercontent.com/spdx/license-list-data/main/text/LGPL-3.0-only.txt, 42098 bytes, SHA-256 `996af0513df21f7496288951c41428a03c174e9e4a9d63665c57d670f845ccb1` | verified (SPDX copy of the text, read 2026-10-09; section 4 quoted below). Line 73 of that file starts the GPL-3.0 text, so the file holds both |
| GPL-3.0 (LGPL-3.0 adds terms to it, so both texts ship together) | https://www.gnu.org/licenses/gpl-3.0.txt (refused, same 403). Read instead: https://raw.githubusercontent.com/spdx/license-list-data/main/text/GPL-3.0-only.txt, 34674 bytes, SHA-256 `fb981668c18a279e285fc4d83fba1e836cc84dd4daa73c9697d3cfd2d8aca6e0` | verified (SPDX copy, hash only; body not re-read beyond its title) |
| BSD-3-Clause, 0BSD, MIT, Zlib, CC0-1.0 (NumPy) | the 17 `License-File` entries inside the NumPy wheel, top file `numpy-2.4.6.dist-info/licenses/LICENSE.txt` | verified (file names listed from the cp311 win_amd64 wheel) |
| GPL-2.0-or-later with Bootloader Exception (PyInstaller) | `pyinstaller-6.22.3.dist-info/licenses/COPYING.txt` in the wheel | verified (text read from the wheel; excerpt in the snapshot) |
| SIL OFL 1.1 (Inter, JetBrains Mono, bundled) | `resources/fonts/Inter/LICENSE.txt` and `resources/fonts/JetBrainsMono/OFL.txt`, EV-106 and EV-107 in `evidence_register.json` | verified (source read, 2026-10-09; hashes in §Fonts) |
| SIL OFL 1.1 (Noto Sans, Liberation, Cascadia, Manrope; not bundled) | EV-72…EV-74 and EV-76 in `evidence_register.json` | verified (extract, Phase 1) |
| PSF-2.0 (CPython) | https://docs.python.org/3/license.html (not accessed). Read instead: `/usr/lib/python3.11/LICENSE.txt` of the CPython 3.11.15 on this machine, 13936 bytes, SHA-256 `3b2f81fe21d181c499c59a256c8e1968455d6689d269aa85373bfb6af41da3bf` | partly verified (a Linux distribution copy, not the file in the python.org Windows installer; section 2 quoted below) |

## Distribution obligations

### embodic installed with pip into a venv (the Phase 2 default, D-015)

The user's pip downloads NumPy, PySide6-Essentials and shiboken6 from PyPI. embodic's own wheel contains no
third-party code except the two bundled font families under `embodic/_resources/fonts/` (SIL OFL 1.1, see §Fonts; D-039
a). The Qt binaries reach the user from PyPI, not from the embodic project (`inferred`). Obligations for embodic in
this mode:

1. Declare the dependencies and their licences in the README and the About box. PySide6 is used under LGPL-3.0.
2. Do not modify PySide6, shiboken6 or Qt. A modified copy would have to be released under LGPL-3.0 with source.
3. Keep embodic's use dynamic. Python imports the Qt shared libraries at run time, which is the "work that uses the
   library" case on Qt's obligations page (`verified (extract)`, https://www.qt.io/licensing/open-source-lgpl-obligations).

### PyInstaller one-folder build (stretch goal, D-015)

Here embodic distributes the Qt, PySide6, shiboken6, NumPy and CPython binaries itself, so the distributor obligations
fall on embodic. From Qt's obligations page (`verified (extract)`, URL above):

1. Ship a copy of the LGPL-3.0 text and the GPL-3.0 text, and show a prominent notice that the application uses Qt
   under LGPL-3.0. Qt states "providing a copy of the LGPL license text to the user and displaying a prominent notice
   about using the LGPL library". The LGPL-3.0 text says the same in section 4: "a) Give prominent notice with each
   copy of the Combined Work that the Library is used in it and that the Library and its use are covered by this
   License. b) Accompany the Combined Work with a copy of the GNU GPL and this license document. c) For a Combined Work
   that displays copyright notices during execution, include the copyright notice for the Library among these notices,
   as well as a reference directing the user to the copies of the GNU GPL and this license document" (`verified`, SPDX
   copy of the text, hash in §Licence text locations).
2. Deliver the complete corresponding source of the Qt and PySide6 versions shipped, or a written offer for it. Qt
   states the source "should be delivered". The matching sources are the Qt 6.11.2 and PySide6 6.11.2 releases
   (`inferred`; exact source archive URLs not accessed).
3. Let the user replace the Qt libraries and run the result. Qt states the user must be able "to change and re-link
   the library ... including reverse engineering" and "to run the re-linked binary". A one-folder build keeps each
   Qt `.dll` as a separate file, which permits replacement. A one-file build packs them into the executable and makes
   replacement harder (`inferred`). Use one-folder. The LGPL-3.0 text offers two routes in section 4 d). Route 0:
   "Convey the Minimal Corresponding Source under the terms of this License, and the Corresponding Application Code in a
   form suitable for, and under terms that permit, the user to recombine or relink the Application with a modified
   version of the Linked Version to produce a modified Combined Work". Route 1: "Use a suitable shared library
   mechanism for linking with the Library. A suitable mechanism is one that (a) uses at run time a copy of the Library
   already present on the user's computer system, and (b) will operate properly with a modified version of the Library
   that is interface-compatible with the Linked Version" (`verified`, same copy). A one-folder bundle ships its own
   copy of the Library, so whether route 1 (a) is met is `unresolved`. U-S5c: M5 complies with route 0 and does not rely on
   route 1 for the bundle (§M5 distribution). Route 0 needs embodic's own source with the
   bundle, which a Python application can supply (`inferred`; legal review needed).
4. Put no term in the embodic licence or EULA that forbids reverse engineering of the Qt parts (Qt page, "No
   Restrictions on Freedom").
5. Ship NumPy's licence files. The top file `numpy-2.4.6.dist-info/licenses/LICENSE.txt` (45831 bytes, SHA-256
   `a804dff0ead9fadc5293456410bcbfc32bf024be9c4513459663fb7b442d2341`, read from the Cp311 Windows wheel) is
   BSD-3-Clause, "Copyright (c) 2005-2025, NumPy Developers", and says "Redistributions in binary form must reproduce
   the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other
   materials provided with the distribution" (`verified`). It also lists the software that the Windows binary bundles
   as `numpy.libs\libscipy_openblas*.dll`: OpenBLAS (BSD-3-Clause), LAPACK (BSD-3-Clause-Open-MPI) and the GCC runtime
   library (GPL-3.0-or-later WITH GCC-exception-3.1) (`verified`, "Name", "Files" and "License" lines). Ship that whole
   file. The other 16 `License-File` entries of the wheel were listed, not read.
6. Ship the CPython licence text. Section 2 of the PSF License Agreement grants the right to "distribute, and otherwise
   use Python alone or in any derivative version, provided, however, that PSF's License Agreement and PSF's notice of
   copyright ... are retained in Python alone or in any derivative version prepared by Licensee" (`verified` in the
   Linux distribution copy; the python.org Windows file was not read).
7. The PyInstaller bootloader adds no obligation. Its COPYING.txt grants "unlimited permission to link or embed
   compiled bootloader and related files into combinations with other programs, and to distribute those combinations
   without any restriction coming from the use of those files" (`verified`, read from the 6.22.3 wheel).

Defect found (DEF-S3-01). The PySide6-Essentials 6.11.2 and shiboken6 6.11.2 Windows wheels declare only
`LicenseRef-Qt-Commercial.txt` as `License-File`. That file is 470 bytes and is a commercial-licence notice. It does
not contain the LGPL-3.0 text (`verified`, read from the wheel). A PyInstaller build would therefore carry no LGPL text
unless embodic adds it. Reproduce with
`python3 docs/phase2/evidence/tools/check_dependency_licences.py`, then read `notice_files_in_wheel` for
PySide6-Essentials in the snapshot. Fix: the packaging unit (M5) adds `licenses/LGPL-3.0.txt`, `licenses/GPL-3.0.txt`
and the `THIRD_PARTY_LICENSES.md` file of REQ-N-19 to the bundle (U-S5a: the earlier name `THIRD_PARTY_NOTICES` is replaced by the
name `package_layout.md` and REQ-N-19 use). ADR-0008 item 7 (pip-licenses generation) does not catch this,
because pip-licenses reports metadata, not the missing text.

Qt's own third-party components inside the Qt binaries (for example FreeType, HarfBuzz, libpng, PCRE2) have their
own notice terms. Qt lists them at https://doc.qt.io/qt-6/licenses-used-in-qt.html. Status: `not accessed`. The M5
unit must read that page for the modules actually bundled.

### Test and dev tools

pytest, pytest-qt, pytest-cov, pytest-timeout (MIT), hatchling (MIT), fonttools (MIT, EV-108), jsonschema, ezdxf, pypdf, ruff, mypy, pip-licenses (MIT), import-linter (BSD-2-Clause),
pip-audit and pyinstaller-hooks-contrib (Apache-2.0, hooks also GPL-2.0), and hypothesis (MPL-2.0) run only on
developer machines and in CI. embodic does not distribute them, so their licences add no distribution obligation
(`inferred`). import-linter's declared licence is BSD 2-Clause. ADR-0008 records it as "BSD" without the variant.

## Fonts: decision and licence record (D-039)

D-039 a (2026-10-09) decided the question that this section left `unresolved` in Phase 1: "Inter and JetBrains Mono
(SIL OFL 1.1, design_spec.md §4) are bundled under `resources/fonts/` with their licence texts and registered at
startup; no font is fetched at run time; Agent 5 records the licence rows". D-039 b: the PDF report embeds those fonts
"(TrueType, Identity-H, whole file — no subsetting, stdlib only)". Segoe UI and Consolas are system fonts and are never
bundled.

### Bundled files

All files below were hashed with `sha256sum` in the U-S5b worktree (main 9776555) on 2026-10-09. The six hashes equal
the ones in `resources/fonts/FONTS.md`. U-M4e-1 (U-S4e ruling e2) replaced `Inter/InterVariable.ttf` with the two static
Inter files, because Qt ignores the `wght` axis. In U-S5b the release archive `Inter-4.1.zip` was downloaded from
github.com (33707794 bytes, SHA-256 `9883fdd4a49d4fb66bd8177ba6625ef9a64aa45899767dde3d36aa425756b11e`, the value in
`FONTS.md`). `cmp` found `Inter/Inter-Regular.ttf` and `Inter/Inter-SemiBold.ttf` byte-identical to the archive members
`extras/ttf/Inter-Regular.ttf` and `extras/ttf/Inter-SemiBold.ttf`. The archive member `LICENSE.txt` and the file at
https://raw.githubusercontent.com/rsms/inter/v4.1/LICENSE.txt have the same SHA-256 as `Inter/LICENSE.txt`. All of this
is `verified`. The JetBrains Mono files were not downloaded again in U-S5b. Their hashes were measured on disk and equal
`FONTS.md`. Their equality with the upstream files at tag v2.304 was `verified` in U-S5a. The sizes are the byte counts
of the files.

| File | Version | Copyright line (first line of the licence text) | Reserved Font Name | Bytes | SHA-256 | EV |
|---|---|---|---|---|---|---|
| `Inter/Inter-Regular.ttf` | Inter Regular, "Version 4.001;git-9221beed3", release v4.1 | n/a (font) | none | 411640 | `40d692fce188e4471e2b3cba937be967878f631ad3ebbbdcd587687c7ebe0c82` | EV-106 |
| `Inter/Inter-SemiBold.ttf` | Inter SemiBold, "Version 4.001;git-9221beed3", release v4.1 | n/a (font) | none | 419744 | `78a843fade9d4612a5567302fb595b56976eb5fcebf4fea5a5912d638bafcde3` | EV-106 |
| `Inter/LICENSE.txt` | SIL OFL 1.1 | "Copyright (c) 2016 The Inter Project Authors (https://github.com/rsms/inter)" | none | 4380 | `262481e844521b326f5ecd053e59b98c8b2da78c8ee1bdbb6e8174305e54935a` | EV-106 |
| `JetBrainsMono/JetBrainsMono-Regular.ttf` | "Version 2.304", tag v2.304 | n/a (font) | none | 273900 | `a0bf60ef0f83c5ed4d7a75d45838548b1f6873372dfac88f71804491898d138f` | EV-107 |
| `JetBrainsMono/JetBrainsMono-Medium.ttf` | "Version 2.304", tag v2.304 | n/a (font) | none | 273860 | `31c92d01a8a08528b718a43addf0ad3df0af2ca4b7b3290a452f70f358e14d3d` | EV-107 |
| `JetBrainsMono/OFL.txt` | SIL OFL 1.1 | "Copyright 2020 The JetBrains Mono Project Authors (https://github.com/JetBrains/JetBrainsMono)" | none | 4399 | `30f0c136e3c88e422d0791acd97238870f9054a9729bc34cf2ff0d4ed8cac4ad` | EV-107 |

Source URLs (the same as in `FONTS.md`): `https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip` (members
`extras/ttf/Inter-Regular.ttf` and `extras/ttf/Inter-SemiBold.ttf`),
`https://raw.githubusercontent.com/rsms/inter/v4.1/LICENSE.txt`,
`https://raw.githubusercontent.com/JetBrains/JetBrainsMono/v2.304/fonts/ttf/JetBrainsMono-Regular.ttf`,
`https://raw.githubusercontent.com/JetBrains/JetBrainsMono/v2.304/fonts/ttf/JetBrainsMono-Medium.ttf` and
`https://raw.githubusercontent.com/JetBrains/JetBrainsMono/v2.304/OFL.txt`. The "Reserved Font Name" cell is `none`
because no reserved name follows the copyright line in either licence text (see the next heading).

### Candidates from Phase 1

The table of candidates in the earlier version of this section is closed. Inter was not a Phase 1 candidate and is new. U-S5a recorded it as Inter Variable. Since U-M4e-1 the bundled files are the static Regular and SemiBold.

| Font | Phase 1 row | Reserved Font Name | D-039 outcome |
|---|---|---|---|
| Inter v4.1, static Regular and SemiBold | none (added in U-S5a) | none listed | chosen, EV-106 |
| JetBrains Mono v2.304 (Regular, Medium) | EV-75 (read on the `master` branch) | none listed | chosen, EV-107 reads the file shipped |
| Noto Sans | EV-72 | none listed | not chosen, not bundled |
| Liberation Sans, Liberation Mono | EV-73 | Liberation | not chosen, not bundled |
| Cascadia Mono | EV-74 | Cascadia Code | not chosen, not bundled |
| Manrope | EV-76 | none listed | not chosen, not bundled |

### What the two licence texts say

The two files are the same SIL OFL 1.1 text ("SIL OPEN FONT LICENSE Version 1.1 - 26 February 2007"). They differ in the
copyright line, the licence URL (`http://scripts.sil.org/OFL` and `https://scripts.sil.org/OFL`), the heading
"PERMISSION AND CONDITIONS" against "PERMISSION & CONDITIONS", and whitespace (`verified`, `diff` with runs of spaces
collapsed). The
lines that decide the packaging (`verified`, read in both files):

- Definition, in the licence's words: `"Reserved Font Name" refers to any names specified as such after the
  copyright statement(s).` In both files the copyright line is followed directly by "This Font Software is licensed under the SIL Open Font License,
  Version 1.1." and names no reserved font name. Condition 3 ("No Modified Version of the Font Software may use the
  Reserved Font Name(s) unless explicit written permission is granted") therefore has no name to protect (`inferred`
  from the two texts; not legal advice).
- Condition 1: "Neither the Font Software nor any of its individual components, in Original or Modified Versions, may be
  sold by itself."
- Condition 2: "Original or Modified Versions of the Font Software may be bundled, redistributed and/or sold with any
  software, provided that each copy contains the above copyright notice and this license. These can be included either
  as stand-alone text files, human-readable headers or in the appropriate machine-readable metadata fields within text
  or binary files as long as those fields can be easily viewed by the user."
- Condition 5 and the preamble: "The requirement for fonts to remain under this license does not apply to any document
  created using the fonts or their derivatives."

### The PDF report embeds the whole, unmodified file

The Phase 1 note read "A PDF report that embeds a subset of an RFN font is a modified copy". That reading does not apply
to the bundled fonts, for two reasons.

1. Neither font has a Reserved Font Name (above).
2. The writer does not subset. `src/embodic/io/pdf_writer.py` on main 9776555 (`verified` by reading the code; the line numbers below were re-read in U-S5b):
   `bundled_font` (l.143 to 145) reads the file bytes. `parse_truetype` (l.120 to 139) keeps them unchanged as
   `data=data`. `_embed` (l.223 to 246) writes them with `file_id = stream(ttf.data, f" /Length1 {len(ttf.data)}")`
   (l.229), references that stream as `/FontFile2` in the descriptor (l.234), and wraps it in a `Type0` font with
   `/Encoding /Identity-H` over a `CIDFontType2` descendant (l.237 to 245). The `stream` helper in `to_bytes` (l.358 to
   361) compresses with `zlib.compress` and `/FlateDecode`, which loses no byte. The module docstring (l.3 to 4) says the
   same.

The check script `docs/phase2/evidence/tools/check_pdf_font_embedding.py` reproduces this by decoding each `FontFile2`
stream of a report PDF with pypdf and hashing it. The script takes the PDF path as an optional argument. Without one it
runs the real exporter (`write_report_pdf` on the packaged example `spiral_12c10p_d08`) itself. In U-S5b the PDF came
from a separate six-line script that calls `write_report_pdf` on that example, and the checker read it from its path
(`verified`, run 2026-10-09 on main 9776555). A second run without the argument printed the same text.

```
Inter/Inter-Regular.ttf: disk 40d692fce188e4471e2b3cba937be967878f631ad3ebbbdcd587687c7ebe0c82 bytes 411640
  embedded /Inter-Regular: 40d692fce188e4471e2b3cba937be967878f631ad3ebbbdcd587687c7ebe0c82 bytes 411640
  identical to disk: True | FONTS.md hash matches disk: True
Inter/Inter-SemiBold.ttf: disk 78a843fade9d4612a5567302fb595b56976eb5fcebf4fea5a5912d638bafcde3 bytes 419744
  embedded /Inter-SemiBold: 78a843fade9d4612a5567302fb595b56976eb5fcebf4fea5a5912d638bafcde3 bytes 419744
  identical to disk: True | FONTS.md hash matches disk: True
JetBrainsMono/JetBrainsMono-Regular.ttf: disk a0bf60ef0f83c5ed4d7a75d45838548b1f6873372dfac88f71804491898d138f bytes 273900
  embedded /JetBrainsMono-Regular: a0bf60ef0f83c5ed4d7a75d45838548b1f6873372dfac88f71804491898d138f bytes 273900
  identical to disk: True | FONTS.md hash matches disk: True
fonts in the PDF: ['/Inter-Regular', '/Inter-SemiBold', '/JetBrainsMono-Regular']
```

The PDF embeds Inter Regular, Inter SemiBold and JetBrains Mono Regular. `PdfDocument.text` and `PdfDocument.row` draw
bold text in Inter SemiBold (`pdf_writer.py` l.288 and l.311; font constants l.22 to 25), so no stroke trick and no
variable-font instance is involved. JetBrains Mono Medium is used by the UI and is not in the PDF. When the check
meets a changed byte it fails. A one-byte change (byte 1000 flipped) in a copy of `Inter-SemiBold.ttf`, with the checker
pointed at that copy of `resources/fonts`, printed `identical to disk: False | FONTS.md hash matches disk: False` for
that file and exit code 1 (`verified`, run 2026-10-09).

Each embedded copy keeps the font's own `name` table (`verified`, the script prints it). Name ID 0 of both Inter faces reads
"Copyright 2016 The Inter Project Authors". Name ID 13 of both reads "This Font Software is licensed under the SIL Open Font
License, Version 1.1. This license is available with a FAQ at: http://scripts.sil.org/OFL". JetBrains Mono carries
"Copyright 2020 The JetBrains Mono Project Authors (https://github.com/JetBrains/JetBrainsMono)" and the same sentence
with `https://scripts.sil.org/OFL`.

### Open points

1. Does an embedded font inside a PDF count as a copy that "contains the above copyright notice and this license"
   (condition 2)? The name table holds the notice and a licence sentence, but a PDF reader does not show those fields,
   and the condition asks that the fields "can be easily viewed by the user". The preamble sentence on documents
   points the other way. The texts do not decide this (`unresolved`). The conservative step costs little: the About box
   and `THIRD_PARTY_LICENSES.md` carry both full texts. A credit line in the report footer is a design call for Fable
   and Agent 1.
2. The repository has no licence file for embodic itself (the root of main 3d70170 holds `CHANGELOG.md`, `README.md`,
   `pyproject.toml` and the folders; the wheel built from it has no licence member except the fonts). U-S5b listed the root
   of main 9776555 and the wheel built from it again, and found the same (`verified`). REQ-N-19 asks for a recorded licence
   "compatible with the embodic licence". Which licence embodic uses is a decision for the user.

## What the M5 packages must carry

The facts in the "Present today" column come from a wheel built on 2026-10-09 with
`pip wheel --no-build-isolation --no-deps .` from main 9776555 (U-S5b), listed with `unzip -l` (`verified`). The wheel carries all
of `resources/` at `embodic/_resources/` through `[tool.hatch.build.targets.wheel.force-include]`.

### Wheel (pip into a venv, D-015 default)

| File in the wheel | Why | Present today |
|---|---|---|
| `embodic/_resources/fonts/Inter/LICENSE.txt` | OFL condition 2, next to `Inter-Regular.ttf` and `Inter-SemiBold.ttf` | yes, 4380 bytes |
| `embodic/_resources/fonts/JetBrainsMono/OFL.txt` | OFL condition 2, next to both JetBrains Mono files | yes, 4399 bytes |
| `embodic/_resources/fonts/FONTS.md` | source URLs and hashes of the font files | yes, 3812 bytes |
| `THIRD_PARTY_LICENSES.md` (REQ-N-19, `package_layout.md` line 35, U-M5b) | licence, copyright line and pin of NumPy, PySide6-Essentials, shiboken6, Inter and JetBrains Mono, and the notice that Qt is used under LGPL-3.0 | no. The file does not exist and the wheel has no licence member besides the fonts |
| embodic's own licence file | REQ-N-19 | no. Open point 2 above |

NumPy, PySide6-Essentials and shiboken6 are downloaded by pip from PyPI and are not in the wheel. fontTools and every
other dev tool are not needed at run time.

### PyInstaller one-folder build (D-015 stretch goal)

| File in the folder | Why | Present today |
|---|---|---|
| the four font files plus `LICENSE.txt` and `OFL.txt` beside them | OFL condition 2. The spec `datas` entry must take the two text files as well as `*.ttf` | no build exists. The wheel shows the right tree |
| `licenses/LGPL-3.0.txt` and `licenses/GPL-3.0.txt` | LGPL-3.0 section 4 b): "Accompany the Combined Work with a copy of the GNU GPL and this license document". The PySide6-Essentials wheel carries only `LicenseRef-Qt-Commercial.txt` (DEF-S3-01) | no. Text sources: the SPDX copies (hashes in §Licence text locations) or gnu.org (refused by the proxy in this session) |
| `THIRD_PARTY_LICENSES.md` with a prominent notice | LGPL-3.0 section 4 a) and c): notice that the Library is used, its copyright notice among those the app displays, and a reference to the licence copies. The About box shows the same | no |
| the Qt libraries as separate files, and embodic's source (wheel or sdist) with the bundle | LGPL-3.0 section 4 d), route 0 (relink) or route 1 (shared library). Open: whether route 1 (a) is met by a bundled copy | one-folder keeps each Qt library a separate file (`inferred`). No bundle exists |
| a written offer, or the files, for the Qt 6.11.2 and PySide6 6.11.2 source | Qt obligations page (`verified (extract)`, §Distribution obligations item 2) | no |
| `licenses/numpy/LICENSE.txt` (whole file) | BSD-3-Clause binary clause, plus the OpenBLAS, LAPACK and GCC runtime notices for `libscipy_openblas*.dll`. The other 16 `License-File` entries still need a reading | no |
| `licenses/PYTHON-LICENSE.txt` | PSF License Agreement section 2: the agreement and the copyright notice "are retained" | no |
| Qt's third-party component notices for the bundled modules | https://doc.qt.io/qt-6/licenses-used-in-qt.html (`not accessed`: refused by the proxy on 2026-10-09). M5 reads it | no |

Not needed in the folder: fontTools (dev only, never imported by `src`), pytest and the other test or dev tools, and the
PyInstaller bootloader (§Distribution obligations item 7). The folder lists the licences it carries. It does not need to
list the dev tools.

## M5 distribution

This section is the reference for unit U-M5b (`THIRD_PARTY_LICENSES.md`) and U-M5c (the PyInstaller one-folder build). It
quotes the licence clauses that bind a one-folder distribution of embodic when PySide6 is used under LGPL-3.0, says what
embodic does about each clause, lists where every licence text lives, and records the licence decision that stays with the
user. It is not legal advice. Each reading marked `inferred` is Agent 5's reading of the quoted words, and a lawyer should
review the final distribution.

Label meanings follow the standing orders. `verified` means the source was read in this unit, or a command
was run and its output read. Every quote in the next table is checked by a script, so a quote that drifts from its source
fails the check (`python3 docs/phase2/evidence/tools/check_m5_licence_quotes.py`, output in §Run of the check).

### Sources read and hosts refused

The session proxy answered 403 to CONNECT for these hosts on 2026-10-12, so none of their pages was read:
`www.qt.io`, `doc.qt.io`, `code.qt.io`, `download.qt.io`, `wiki.qt.io`, `www.gnu.org`, `docs.python.org`, `www.python.org`,
`opensource.org` and `spdx.org` (`verified`, the proxy status endpoint lists each host as `connect_rejected`). Qt's own
statements therefore come from four places that were reachable.

1. The Qt project's licence texts at the release tag, on the GitHub mirror: `https://raw.githubusercontent.com/qt/qtbase/v6.11.2/LICENSES/`
   (`LGPL-3.0-only.txt`, 7651 bytes; `GPL-3.0-only.txt`, 35147 bytes). The repositories `qt/qtbase`, `qt/qtdeclarative`,
   `qt/qttools`, `qt/qtsvg`, `qt/qtshadertools` and `qt/qtimageformats` each answered 200 for `LICENSES/LGPL-3.0-only.txt`
   at tag `v6.11.2` (`verified`, `curl` status codes). `qt/pyside-setup` answered 404 for every path tried, so PySide6 is not
   mirrored there.
2. The long description of the PySide6-Essentials 6.11.2 metadata (installed copy and the Windows wheel's `.metadata`), which
   carries the section "Licensing".
3. The licence headers of the installed PySide6 files and the commercial notice file in the Windows wheel.
4. The SPDX licence list copies and the Qt attribution files at the tag.

The Qt page that U-S5a cited ("Open Source LGPL obligations", https://www.qt.io/licensing/open-source-lgpl-obligations) was
read in U-S5a through a model-written extract. It was not re-read here. Nothing below depends on it. Where U-S5a quoted it,
this section quotes the licence text instead.

### Quoted requirements

Source ids: `lgpl3-qtbase` is `https://raw.githubusercontent.com/qt/qtbase/v6.11.2/LICENSES/LGPL-3.0-only.txt`. `gpl3-spdx` and the
other `-spdx` ids are the files under `https://raw.githubusercontent.com/spdx/license-list-data/main/text/`. The other ids are
installed files: `pyside-metadata` is `pyside6_essentials-6.11.2.dist-info/METADATA`, `numpy-licence-linux` is
`numpy-2.4.6.dist-info/licenses/LICENSE.txt`, `psf-cpython-linux` is `/usr/lib/python3.11/LICENSE.txt`. An ellipsis (`...`) marks a
cut inside a quote. "Section" is the section of the named licence. Where the LGPL text says "section 6 of the GNU GPL" it means
section 6 of the GPL-3.0 text (Q12 to Q14), not section 6 of the LGPL, which is about revised versions.

| Q | Source id | Section | Quote |
|---|---|---|---|
| Q1 | lgpl3-qtbase | LGPL-3.0 §4, opening | "You may convey a Combined Work under terms of your choice that, taken together, effectively do not restrict modification of the portions of the Library contained in the Combined Work and reverse engineering for debugging such modifications, if you also do each of the following" |
| Q2 | lgpl3-qtbase | LGPL-3.0 §4 a) | "Give prominent notice with each copy of the Combined Work that the Library is used in it and that the Library and its use are covered by this License." |
| Q3 | lgpl3-qtbase | LGPL-3.0 §4 b) | "Accompany the Combined Work with a copy of the GNU GPL and this license document." |
| Q4 | lgpl3-qtbase | LGPL-3.0 §4 c) | "For a Combined Work that displays copyright notices during execution, include the copyright notice for the Library among these notices, as well as a reference directing the user to the copies of the GNU GPL and this license document." |
| Q5 | lgpl3-qtbase | LGPL-3.0 §4 d) 0) | "Convey the Minimal Corresponding Source under the terms of this License, and the Corresponding Application Code in a form suitable for, and under terms that permit, the user to recombine or relink the Application with a modified version of the Linked Version to produce a modified Combined Work, in the manner specified by section 6 of the GNU GPL for conveying Corresponding Source." |
| Q6 | lgpl3-qtbase | LGPL-3.0 §4 d) 1) | "Use a suitable shared library mechanism for linking with the Library. A suitable mechanism is one that (a) uses at run time a copy of the Library already present on the user's computer system, and (b) will operate properly with a modified version of the Library that is interface-compatible with the Linked Version." |
| Q7 | lgpl3-qtbase | LGPL-3.0 §4 e) | "Provide Installation Information, but only if you would otherwise be required to provide such information under section 6 of the GNU GPL, and only to the extent that such information is necessary to install and execute a modified version of the Combined Work produced by recombining or relinking the Application with a modified version of the Linked Version." |
| Q8 | lgpl3-qtbase | LGPL-3.0 §0 | "An "Application" is any work that makes use of an interface provided by the Library, but which is not otherwise based on the Library." |
| Q9 | lgpl3-qtbase | LGPL-3.0 §0 | "A "Combined Work" is a work produced by combining or linking an Application with the Library. The particular version of the Library with which the Combined Work was made is also called the "Linked Version"." |
| Q10 | lgpl3-qtbase | LGPL-3.0 §0 | "The "Minimal Corresponding Source" for a Combined Work means the Corresponding Source for the Combined Work, excluding any source code for portions of the Combined Work that, considered in isolation, are based on the Application, and not on the Linked Version." |
| Q11 | lgpl3-qtbase | LGPL-3.0 §0 | "The "Corresponding Application Code" for a Combined Work means the object code and/or source code for the Application, including any data and utility programs needed for reproducing the Combined Work from the Application, but excluding the System Libraries of the Combined Work." |
| Q12 | gpl3-spdx | GPL-3.0 §6, opening | "You may convey a covered work in object code form under the terms of sections 4 and 5, provided that you also convey the machine-readable Corresponding Source under the terms of this License, in one of these ways:" |
| Q13 | gpl3-spdx | GPL-3.0 §6 d) | "Convey the object code by offering access from a designated place (gratis or for a charge), and offer equivalent access to the Corresponding Source in the same way through the same place at no further charge. ... the Corresponding Source may be on a different server (operated by you or a third party) that supports equivalent copying facilities, provided you maintain clear directions next to the object code saying where to find the Corresponding Source. Regardless of what server hosts the Corresponding Source, you remain obligated to ensure that it is available for as long as needed to satisfy these requirements." |
| Q14 | gpl3-spdx | GPL-3.0 §6 b) | "Convey the object code in, or embodied in, a physical product (including a physical distribution medium), accompanied by a written offer, valid for at least three years and valid for as long as you offer spare parts or customer support for that product model" |
| Q15 | gpl3-spdx | GPL-3.0 §1 | "The "Corresponding Source" for a work in object code form means all the source code needed to generate, install, and (for an executable work) run the object code and to modify the work, including scripts to control those activities. However, it does not include the work's System Libraries, or general-purpose tools or generally available free programs which are used unmodified in performing those activities but which are not part of the work." |
| Q16 | gpl3-spdx | GPL-3.0 §6 | "A "User Product" is either (1) a "consumer product", which means any tangible personal property which is normally used for personal, family, or household purposes, or (2) anything designed or sold for incorporation into a dwelling." |
| Q17 | lgpl3-qtbase | LGPL-3.0, preamble | "This version of the GNU Lesser General Public License incorporates the terms and conditions of version 3 of the GNU General Public License, supplemented by the additional permissions listed below." |
| Q18 | pyside-metadata | PySide6-Essentials 6.11.2, "Licensing" | "PySide6 is available under both Open Source (LGPLv3 or GPLv2 or GPLv3) and commercial license. Using PyPi is the recommended installation source, because the content of the wheels is valid for both cases." |
| Q19 | pyside-qtcore-pyi | `PySide6/QtCore.pyi`, lines 1 and 2 | "Copyright (C) 2022 The Qt Company Ltd. # SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only" |
| Q20 | qt-qglobal-h | Qt 6.11.2 `src/corelib/global/qglobal.h`, lines 1 to 3 | "Copyright (C) 2020 The Qt Company Ltd. // Copyright (C) 2019 Intel Corporation. // SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only" |
| Q21 | qt-commercial-win | `LicenseRef-Qt-Commercial.txt` in the Windows wheel | "Licensees holding valid commercial Qt licenses may use this software in accordance with the the terms contained in a written agreement between you and The Qt Company." |
| Q22 | mit-spdx | MIT, grant | "Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software" |
| Q23 | mit-spdx | MIT, condition | "The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software." |
| Q24 | apache2-spdx | Apache-2.0 §4 a) | "You must give any other recipients of the Work or Derivative Works a copy of this License" |
| Q25 | apache2-spdx | Apache-2.0 §3 | "If You institute patent litigation against any entity (including a cross-claim or counterclaim in a lawsuit) alleging that the Work or a Contribution incorporated within the Work constitutes direct or contributory patent infringement, then any patent licenses granted to You under this License for that Work shall terminate as of the date such litigation is filed." |
| Q26 | gpl3-spdx | GPL-3.0 §5 c) | "You must license the entire work, as a whole, under this License to anyone who comes into possession of a copy." |
| Q27 | gpl3-spdx | GPL-3.0 §10 | "Each time you convey a covered work, the recipient automatically receives a license from the original licensors, to run, modify and propagate that work, subject to this License." |
| Q28 | numpy-licence-linux | NumPy `LICENSE.txt`, BSD-3-Clause | "Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution." |
| Q29 | psf-cpython-linux | PSF License Agreement §2 | "provided, however, that PSF's License Agreement and PSF's notice of copyright, i.e., "Copyright (c) 2001, ... Python Software Foundation; All Rights Reserved" are retained in Python alone or in any derivative version prepared by Licensee." |
| Q30 | ofl-inter | SIL OFL 1.1, condition 2 | "Original or Modified Versions of the Font Software may be bundled, redistributed and/or sold with any software, provided that each copy contains the above copyright notice and this license." |

### What the one-folder build must do about LGPL-3.0

The mapping onto the LGPL terms (`inferred`, from Q8, Q9 and Q10). embodic's Python code is the "Application", because
it uses the interfaces of PySide6 and is not based on it. Qt and PySide6 are the "Library". The PyInstaller folder is the
"Combined Work", and the Qt and PySide6 files in it, version 6.11.2, are the "Linked Version". embodic links nothing
statically. Python imports `PySide6/QtCore.pyd` and its `Qt6Core.dll` at run time, and both are separate files in the Windows
wheel (`verified`, member names in the wheel listing: `PySide6/Qt6Core.dll`, `PySide6/Qt6Gui.dll`, `PySide6/Qt6Widgets.dll`,
`PySide6/Qt6Svg.dll`, `PySide6/QtCore.pyd`, `PySide6/QtGui.pyd`, `PySide6/QtWidgets.pyd`, `PySide6/QtSvg.pyd`). The Qt version in
the project venv is 6.11.2, and `QtCore.qVersion()` printed `6.11.2` next to PySide6 6.11.2 and shiboken6 6.11.2 (`verified`, run 2026-10-12).
embodic's runtime imports are QtCore, QtGui, QtWidgets and QtSvg (`verified`, `grep` of `src`). QtTest appears only in tests.

| Ref | Requirement (quote) | Our action | Label |
|---|---|---|---|
| R1 | Q1: the terms must "effectively do not restrict modification of the portions of the Library contained in the Combined Work and reverse engineering for debugging such modifications" | The embodic licence and any EULA contain no term against modifying or reverse engineering the Qt and PySide6 files. The application does not check the hash or signature of those files at start-up and does not refuse to run when they change. Replacing `Qt6Core.dll` with an interface-compatible build must leave embodic running. | `inferred` for the start-up check, which is not named in the text |
| R2 | Q2: "Give prominent notice with each copy of the Combined Work that the Library is used in it and that the Library and its use are covered by this License." | Put the notice in `THIRD_PARTY_LICENSES.md` at the top of the folder, in the About box, and on the page that offers the download. Proposed wording below. | `verified` for the requirement, `assumption` for the wording |
| R3 | Q3: "Accompany the Combined Work with a copy of the GNU GPL and this license document." | Put `licenses/LGPL-3.0.txt` and `licenses/GPL-3.0.txt` in the folder. Use the two Qt files at tag v6.11.2 (sources below). The PySide6 wheels carry neither text (DEF-S3-01). | `verified` |
| R4 | Q4: a Combined Work "that displays copyright notices during execution" must include the Library's copyright notice "as well as a reference directing the user to the copies of the GNU GPL and this license document" | embodic shows no About box today (`grep -rn About src` prints nothing, `verified`). When U-M5b adds one, it lists "Copyright (C) The Qt Company Ltd. and other contributors" for Qt and PySide6 and names `licenses/LGPL-3.0.txt` and `licenses/GPL-3.0.txt`. The Qt files carry year-specific lines, for example Q19 (2022, PySide6) and Q20 (2020, Qt). The wording of the combined line is a decision for Fable. | `verified` for the requirement and for today's absence of an About box, `assumption` for the wording |
| R5 | Q5 with Q10 and Q15: convey "the Minimal Corresponding Source under the terms of this License", the "Corresponding Source" being "all the source code needed to generate, install, and ... run the object code and to modify the work, including scripts to control those activities" | Offer the source of Qt 6.11.2 and PySide6 6.11.2 as shipped, next to the download (R6). The Qt modules in the Essentials wheel that embodic loads come from the repositories `qt/qtbase` (Core, Gui, Widgets), `qt/qtsvg` (Svg) and the other modules the wheel carries (`qt/qtdeclarative`, `qt/qttools`, `qt/qtshadertools`, `qt/qtimageformats`), at tag `v6.11.2`. The PySide6 source is at https://code.qt.io/cgit/pyside/pyside-setup.git/ (PyPI `Project-URL` "Repository", `verified` in the installed METADATA), tag name `v6.11.2` by analogy with the Qt tags (`inferred`, host refused). | `verified` for the six Qt tags, `inferred` for the module-to-repository mapping and for the PySide6 tag |
| R6 | Q13: "offer equivalent access to the Corresponding Source in the same way through the same place at no further charge", with "clear directions next to the object code saying where to find the Corresponding Source" and a duty "to ensure that it is available for as long as needed" | A download is a case for GPL-3.0 §6 d), not b), because Q14 concerns "a physical product" (`inferred`). Next to the download link and in `THIRD_PARTY_LICENSES.md`, name the source locations of R5. Because the duty to keep the source available outlasts a link on a third-party host, mirror the Qt 6.11.2 and PySide6 6.11.2 source archives with the embodic release (a decision for Fable, `assumption`). | `inferred` |
| R7 | Q5: "the Corresponding Application Code in a form suitable for, and under terms that permit, the user to recombine or relink the Application with a modified version of the Linked Version" | Ship the folder as built. A user who drops a rebuilt `Qt6Core.dll` into `PySide6/` relinks nothing in embodic and gets a modified Combined Work (`inferred`). Also publish embodic's source (the wheel or the source distribution), the `.spec` file and the build script, because Q11 counts "utility programs needed for reproducing the Combined Work" as Application code. | `inferred` |
| R8 | Q6 (route 1): a shared-library mechanism that "uses at run time a copy of the Library already present on the user's computer system" | Do not rely on route 1 for the bundle. Use route 0 (R5 to R7). Route 1 fits the pip install, where Qt comes from PyPI and was not delivered by embodic. See the next subsection. | `inferred` |
| R9 | Q7: Installation Information "only if you would otherwise be required to provide such information under section 6 of the GNU GPL" | GPL-3.0 §6 asks for Installation Information only for a "User Product", defined in Q16 as "tangible personal property" for personal use or dwelling equipment. A downloadable desktop application is not tangible personal property, so embodic provides none beyond R7 (`inferred`; a lawyer should confirm). | `inferred` |
| R10 | Q9 and Q6 (b): the Linked Version stays replaceable | Build with one-folder mode. Do not use `--onefile`, which packs the Qt files into the executable. Do not compress the Qt files with UPX. After the build, run `dir /s /b *.dll` on the output and confirm that `Qt6Core.dll`, `Qt6Gui.dll`, `Qt6Widgets.dll` and `Qt6Svg.dll` are separate files. The venv has no PyInstaller (no `pyinstaller` entry in `site-packages`, `verified` by `ls`), so this unit could not check the real folder layout. | `inferred`, `not tested` on a real build |
| R11 | Q4 and R3 | The About box and `THIRD_PARTY_LICENSES.md` give the PySide6 and Qt versions. The code can read them: `PySide6.__version__` and `QtCore.qVersion()` printed `6.11.2` in the venv. | `verified` |

Proposed notice for R2 (`assumption`, wording for Fable and the lawyer):

> embodic uses Qt 6.11.2 and PySide6 6.11.2 (Qt for Python), which are covered by the GNU Lesser General Public License,
> version 3 (LGPL-3.0-only). The Qt and PySide6 libraries are separate files in the `PySide6` folder of this download. You can
> replace them with a modified, interface-compatible version. The licence texts are `licenses/LGPL-3.0.txt` and
> `licenses/GPL-3.0.txt`. The source code of the Qt and PySide6 versions in this download is available at
> https://github.com/qt/qtbase/tree/v6.11.2 and the other Qt repositories at tag v6.11.2, and at
> https://code.qt.io/cgit/pyside/pyside-setup.git/.

The URL `https://github.com/qt/qtbase/tree/v6.11.2` is the browsing form of the raw URL that answered 200. It was not opened (the
proxy gives `github.com/qt/qtbase` a 403), so M5 should open it from a normal network before it goes into a release.

### Route 4 d) 1 against a bundled Qt copy

U-S5a left this `unresolved`. The words that decide it are in Q6: a suitable mechanism "uses at run time a copy of the Library
already present on the user's computer system". Two readings fit the text.

1. Narrow reading. "Already present" means present before and apart from the Combined Work, such as a system package or a
   pip install by the user. A Qt copy that embodic delivers in its own folder is delivered with the Combined Work, so route 1
   (a) is not met.
2. Broad reading. Any separate library file on the user's disk at run time counts, as opposed to code linked into the
   executable. A bundled `Qt6Core.dll` that the executable loads from the folder meets it.

The licence text does not choose between them, and this unit found no Qt or PySide6 statement on the point that it could
read (the Qt pages were refused). The reading stays `unresolved`. The decision does not depend on it. Route 0 needs no
"already present" copy: it asks for the Minimal Corresponding Source (R5), the Corresponding Application Code in a recombinable form
(R7), and the GPL §6 delivery of source (R6). A one-folder build with separate Qt files can do all three. The rule for
M5 is therefore "comply with route 0 for the bundle, and treat route 1 as met only in the pip install" (`inferred`).

### Text sources for THIRD_PARTY_LICENSES.md

One section per row. "Venv path" starts at the main checkout, `/home/claude/embodic`, and the folder `site-packages` is under the venv's `lib/python3.11`.
The venv is a Linux install, so its wheels differ from the Windows wheels that M5 packages. Where they differ, the row gives both.
The files that Q18 and Q19 read are `.venv/lib/python3.11/site-packages/pyside6_essentials-6.11.2.dist-info/METADATA` and
`.venv/lib/python3.11/site-packages/PySide6/QtCore.pyi`. The NumPy licence directory is
`.venv/lib/python3.11/site-packages/numpy-2.4.6.dist-info/licenses/`.

| Component | Version | Licence (declared) | Text to ship | Where the text is | Label |
|---|---|---|---|---|---|
| embodic | 0.0.1 | open (no licence file) | embodic's own licence file | does not exist. See §The embodic licence | `unresolved` (user decision) |
| numpy | 2.4.6 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | the whole directory `licenses/` of the dist-info (17 files) | venv path `.venv/lib/python3.11/site-packages/numpy-2.4.6.dist-info/licenses/LICENSE.txt` (46794 bytes, Linux wheel) and the 16 other files under `licenses/` there. Windows wheel member `numpy-2.4.6.dist-info/licenses/LICENSE.txt` is 45831 bytes and differs, because the Windows binary bundles OpenBLAS, LAPACK and the GCC runtime where the Linux one also lists libquadmath. Take the file from the wheel that the build uses | `verified` (both files hashed and read) |
| PySide6-Essentials | 6.11.2 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only (metadata); the commercial option is named in Q19 | `licenses/LGPL-3.0.txt`, `licenses/GPL-3.0.txt` (R3) and the notice of R2 | LGPL: `https://raw.githubusercontent.com/qt/qtbase/v6.11.2/LICENSES/LGPL-3.0-only.txt`, SHA-256 `da7eabb7bafdf7d3ae5e9f223aa5bdc1eece45ac569dc21b3b037520b4464768`, 7651 bytes. GPL: `https://raw.githubusercontent.com/qt/qtbase/v6.11.2/LICENSES/GPL-3.0-only.txt`, SHA-256 `8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b165a1dcd80c7c545eb65b903`, 35147 bytes. Neither wheel carries them. The Windows wheel's `pyside6_essentials-6.11.2.dist-info/licenses/LicenseRef-Qt-Commercial.txt` (470 bytes, Q21) is the commercial notice; it is not a licence embodic uses, and the Linux wheel has no such file | `verified` (LGPL read in full; GPL hashed and compared with the SPDX copy, which differs in 5 spans, "(C)" against the copyright sign and four one-letter insertions) |
| shiboken6 | 6.11.2 | same as PySide6-Essentials | no extra file. Its section in `THIRD_PARTY_LICENSES.md` points to the PySide6 texts | the Windows wheel's `shiboken6-6.11.2.dist-info/licenses/LicenseRef-Qt-Commercial.txt` is byte-identical to the PySide6 one (SHA-256 `4f54763ac0fe2abd8f7f8d8fe370a94a08ebf84786aa0b91045bd6628deb08a3` for both) | `verified` |
| Qt (the libraries in the wheel) | 6.11.2 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only OR commercial, per the file header in Q20 | covered by the two rows above | the same two texts | `verified` for the one qtbase header read (Q20); the other modules were not each opened (`inferred`) |
| Qt's built-in third-party code | see the next table | per library | each library's licence file, named in its `qt_attribution.json` | `https://raw.githubusercontent.com/qt/qtbase/v6.11.2/src/3rdparty/<name>/qt_attribution.json` | `verified` for the six read; the full list for the Windows binaries is `unresolved` |
| Microsoft C++ runtime DLLs and `opengl32sw.dll` in the Windows wheel | see the list below | not read | licence terms not read | no text found in the wheel (the wheel has no file named like a licence besides the commercial notice) | `unresolved` |
| Inter (static Regular and SemiBold) | v4.1 | SIL OFL 1.1 | `LICENSE.txt` beside the font | `resources/fonts/Inter/LICENSE.txt` (4380 bytes) | `verified` |
| JetBrains Mono (Regular, Medium) | v2.304 | SIL OFL 1.1 | `OFL.txt` beside the font | `resources/fonts/JetBrainsMono/OFL.txt` (4399 bytes) | `verified` |
| CPython | 3.11.x | PSF-2.0 | the Python `LICENSE.txt` | Linux build: `/usr/lib/python3.11/LICENSE.txt` (13936 bytes, SHA-256 `3b2f81fe21d181c499c59a256c8e1968455d6689d269aa85373bfb6af41da3bf`). Windows build: the python.org installer puts a `LICENSE.txt` in the install folder (`inferred`; not read, python.org refused). Take the file from the Python that runs PyInstaller | `verified` for the Linux copy, `inferred` for the Windows location |
| PyInstaller bootloader | 6.22.3 | GPL-2.0-or-later with bootloader exception | no obligation (§Distribution obligations item 7) | wheel member `pyinstaller-6.22.3.dist-info/licenses/COPYING.txt`, read in U-S5a. It is not in the venv | `verified` in U-S5a, not re-read here |

The Qt attribution files at tag v6.11.2 that this unit fetched and parsed (`verified`, the JSON parsed with Python). The table
lists what each file declares. Whether the PyPI Windows binaries were built with these bundled copies, or with system copies, is
not stated in anything read (`unresolved`), so U-M5b should list a library only after Qt's page
https://doc.qt.io/qt-6/licenses-used-in-qt.html (refused here) or the wheel itself confirms it.

| Library | Version | Licence id declared | Licence file named | Usage line in the file |
|---|---|---|---|---|
| double-conversion | 3.4.0 | BSD-3-Clause | `LICENSE` | "Used in Qt Core." |
| FreeType | 2.14.3 | FTL OR GPL-2.0-only (plus Zlib, MIT and MIT-open-group parts) | `LICENSE.txt` and three others | "Optionally used in Qt GUI and platform plugins." |
| HarfBuzz | 14.3.0 | MIT | `COPYING` | "Optionally used in Qt GUI." |
| libpng | 1.6.58 | Libpng AND libpng-2.0 | `LICENSE` | "Used in the qpng image plugin." |
| PCRE2 | 10.47 | LicenseRef-BSD-3-Clause-with-PCRE2-Binary-Like-Packages-Exception, and BSD-2-Clause for SLJIT | `LICENCE.md`, `LICENSE-SLJIT` | "Used in Qt Core (QRegularExpression)." |
| zlib | 1.3.2 | Zlib | `LICENSE` | "Optionally used in Qt Core and development tools." |

The non-Qt binaries inside the PySide6-Essentials Windows wheel (`verified`, central directory of
`pyside6_essentials-6.11.2-cp310-abi3-win_amd64.whl`, read with HTTP range requests on 2026-10-12): `PySide6/concrt140.dll`,
`msvcp140.dll`, `msvcp140_1.dll`, `msvcp140_2.dll`, `msvcp140_codecvt_ids.dll`, `vcamp140.dll`, `vccorlib140.dll`,
`vcomp140.dll`, `vcruntime140.dll`, `vcruntime140_1.dll`, and `PySide6/opengl32sw.dll` (20639544 bytes). The shiboken6 wheel
holds the same ten runtime DLLs under `shiboken6/`. The ten file names are the Microsoft Visual C++ runtime (`inferred` from the
names). The file name `opengl32sw.dll` suggests a software OpenGL fallback (`inferred`). Their licence terms were not read.
The wheel contains no `.exe`, `.dll` or `.pyd` of a name that matches a licence file, and its only licence member is the
commercial notice (`verified`, the same file listing).

The Linux wheel in the venv keeps its licence files out of the dist-info. `pyside6_essentials-6.11.2.dist-info` holds `INSTALLER`,
`METADATA`, `RECORD`, `WHEEL`, `entry_points.txt` and `top_level.txt`, with no `licenses/` folder (`verified`, `find`). The
Windows wheel's `.metadata` declares `License-File: LicenseRef-Qt-Commercial.txt` and the Linux one does not (`verified`,
both read).

### The embodic licence: what each common choice means for LGPL use

The embodic licence is a decision for the user (D-015: "embodic licence left open"). This unit does not choose it. The
table says what the quoted texts say about each common choice when PySide6 is used under LGPL-3.0 as in §What the one-folder
build must do. All rows are `inferred`.

| Choice | What the licence text says | Effect with the Qt and PySide6 files | Work it adds |
|---|---|---|---|
| MIT | Q22 grants the rights "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies"; Q23 asks that the notice "shall be included in all copies or substantial portions" | Nothing in the MIT text restricts modification of the Qt files or reverse engineering, so Q1 holds. Q5 asks that embodic be conveyed "under terms that permit" recombining, which MIT does. The Qt and PySide6 files stay under LGPL-3.0, with R2 to R7 done. | The MIT notice in `THIRD_PARTY_LICENSES.md`. Nothing else |
| Apache-2.0 | Q24: "You must give any other recipients of the Work or Derivative Works a copy of this License". Q25 ends the patent licence of a recipient who sues over the Work | The text has no clause on modifying the Qt files, so Q1 holds. Q25 applies to patent suits about the embodic Work and does not touch Qt. This unit read no source on the Apache-2.0 and GPL-2.0 pairing, and the Qt option in use is LGPL-3.0, so the pairing is not needed. | `LICENSE` and a `NOTICE` file if one exists, plus R2 to R7 |
| GPL-3.0 | Q17: the LGPL-3.0 "incorporates the terms and conditions of version 3 of the GNU General Public License, supplemented by the additional permissions". Q26: "You must license the entire work, as a whole, under this License". Q27: each recipient "automatically receives a license ... to run, modify and propagate that work" | Q1 allows "terms of your choice", and GPL-3.0 is among them. The metadata also offers GPL-3.0-only as an option for PySide6 (Q18), so the whole bundle can be GPL-3.0 and then R2 to R7 shrink: the GPL gives every recipient the embodic source (Q12, Q15), which also meets Q5. | The GPL text in `licenses/`. The source offer of R5 and R6 for embodic itself |
| Proprietary | There is no text to quote for an unwritten licence. The limits come from Q1 ("effectively do not restrict modification ... and reverse engineering for debugging such modifications") and Q5 ("under terms that permit, the user to recombine or relink") | A proprietary licence can ship the Qt and PySide6 files only if its terms leave the user free to replace them and to reverse engineer them for debugging those modifications, and only if embodic reaches the user in a form that can be recombined (R7). A "no reverse engineering" clause without a carve-out for the Qt files conflicts with Q1. Q21 shows the alternative: a commercial Qt licence from The Qt Company, whose terms are in a written agreement and were not read | The carve-out clause, R2 to R7, and a lawyer's review of the EULA. The commercial Qt licence avoids R2 to R7 and costs money (not researched) |

NumPy (BSD-3-Clause, Q28) and the two fonts (SIL OFL 1.1, Q30) place no condition on the licence of embodic itself in any
row above beyond keeping their notices (`inferred` from the quoted conditions; the OFL sentence on documents is in §What the two
licence texts say). CPython (Q29) asks for its agreement and copyright notice to be "retained" and nothing more about the embodic licence.

Decision for the user, in one line: pick one of MIT, Apache-2.0, GPL-3.0 or a proprietary licence. The first three need no
change to the plan above. A proprietary licence needs the carve-out clause and a lawyer.

### Open points after U-S5c

1. Route 4 d) 1 (a) against a bundled copy stays `unresolved` as a reading. M5 does not rely on it (§Route 4 d) 1).
2. The exact build recipe of the Qt libraries in the PyPI wheels is not stated in anything read. Q15 asks for "scripts to
   control those activities". Pointing to the upstream release source is an `inferred` way to meet it for unmodified
   files. A lawyer should confirm.
3. The full list of third-party code inside the Windows Qt binaries is `unresolved`. Six libraries are read (above).
4. The licence terms of the Microsoft runtime DLLs and `opengl32sw.dll` are not read.
5. No real PyInstaller output exists, so R10 is `not tested`. U-M5c checks the folder with a listing and records it.
6. `docs/phase2/architecture/package_layout.md` §5.1 still says "Route 1 (a) against a bundled Qt copy is `unresolved`" and
   lists no `source/` or `licenses/` row for embodic's source and the spec file. The owner (Agent 3) updates it through Fable.
7. The Qt pages (`qt.io`, `doc.qt.io`) and `gnu.org` stay unread. If the user gets the proxy to allow them, a second reading of
   Qt's own LGPL statement would close the gap left by §Sources read and hosts refused.

### Run of the check

`python3 docs/phase2/evidence/tools/check_m5_licence_quotes.py --wheels` from the worktree on 2026-10-12, with the project
venv, exited 0 (`verified`). Each source below was hashed against the value recorded in the script before any quote was
searched. Without `--wheels` the script skips Q21 and reads no wheel.

```
source lgpl3-qtbase: 7651 bytes, sha256 matches, https://raw.githubusercontent.com/qt/qtbase/v6.11.2/LICENSES/LGPL-3.0-only.txt
source lgpl3-spdx: 42098 bytes, sha256 matches, https://raw.githubusercontent.com/spdx/license-list-data/main/text/LGPL-3.0-only.txt
source gpl3-spdx: 34674 bytes, sha256 matches, https://raw.githubusercontent.com/spdx/license-list-data/main/text/GPL-3.0-only.txt
source mit-spdx: 1078 bytes, sha256 matches, https://raw.githubusercontent.com/spdx/license-list-data/main/text/MIT.txt
source apache2-spdx: 10280 bytes, sha256 matches, https://raw.githubusercontent.com/spdx/license-list-data/main/text/Apache-2.0.txt
source pyside-metadata: 3637 bytes, sha256 matches, /home/claude/embodic/.venv/lib/python3.11/site-packages/pyside6_essentials-6.11.2.dist-info/METADATA
source pyside-qtcore-pyi: 556957 bytes, sha256 matches, /home/claude/embodic/.venv/lib/python3.11/site-packages/PySide6/QtCore.pyi
source numpy-licence-linux: 46794 bytes, sha256 matches, /home/claude/embodic/.venv/lib/python3.11/site-packages/numpy-2.4.6.dist-info/licenses/LICENSE.txt
source psf-cpython-linux: 13936 bytes, sha256 matches, /usr/lib/python3.11/LICENSE.txt
source ofl-inter: 4380 bytes, sha256 matches, /home/claude/wt/U-S5c/resources/fonts/Inter/LICENSE.txt
source qt-qglobal-h: 1917 bytes, sha256 matches, https://raw.githubusercontent.com/qt/qtbase/v6.11.2/src/corelib/global/qglobal.h
source qt-commercial-win: 470 bytes, sha256 matches, pyside6_essentials-6.11.2-cp310-abi3-win_amd64.whl:pyside6_essentials-6.11.2.dist-info/licenses/LicenseRef-Qt-Commercial.txt
source numpy-licence-win: 45831 bytes, sha256 matches, numpy-2.4.6-cp311-cp311-win_amd64.whl:numpy-2.4.6.dist-info/licenses/LICENSE.txt
Q1 to Q30: ok (one line each in the full output)
30 quote rows, 0 failed
  556957 439e2bd3f6f8576f .venv/lib/python3.11/site-packages/PySide6/QtCore.pyi
   46794 4860083caa0de2ac .venv/lib/python3.11/site-packages/numpy-2.4.6.dist-info/licenses/LICENSE.txt
    1018 fbc539f47d0cf83b .venv/lib/python3.11/site-packages/numpy-2.4.6.dist-info/licenses/numpy/_core/include/numpy/libdivide/LICENSE.txt
     690 3f2c1ffa76383a55 .venv/lib/python3.11/site-packages/numpy-2.4.6.dist-info/licenses/numpy/_core/src/common/pythoncapi-compat/COPYING
   20785 e340270d4f643845 .venv/lib/python3.11/site-packages/numpy-2.4.6.dist-info/licenses/numpy/_core/src/highway/LICENSE
    1414 f7b14309e5f54e50 .venv/lib/python3.11/site-packages/numpy-2.4.6.dist-info/licenses/numpy/_core/src/multiarray/dragon4_LICENSE.txt
    1514 211e7d737d6179a0 .venv/lib/python3.11/site-packages/numpy-2.4.6.dist-info/licenses/numpy/_core/src/npysort/x86-simd-sort/LICENSE.md
    1543 c17011467b4fe6e2 .venv/lib/python3.11/site-packages/numpy-2.4.6.dist-info/licenses/numpy/_core/src/umath/svml/LICENSE
    1498 a85ca13fdf90160b .venv/lib/python3.11/site-packages/numpy-2.4.6.dist-info/licenses/numpy/fft/pocketfft/LICENSE.md
    2266 a14cc25e10d40a3a .venv/lib/python3.11/site-packages/numpy-2.4.6.dist-info/licenses/numpy/linalg/lapack_lite/LICENSE.txt
    1593 05f3b88351988ecf .venv/lib/python3.11/site-packages/numpy-2.4.6.dist-info/licenses/numpy/ma/LICENSE
    3511 103166b62b80443a .venv/lib/python3.11/site-packages/numpy-2.4.6.dist-info/licenses/numpy/random/LICENSE.md
    2745 469778be8f33d54e .venv/lib/python3.11/site-packages/numpy-2.4.6.dist-info/licenses/numpy/random/src/distributions/LICENSE.md
    2926 0e111337b25494a7 .venv/lib/python3.11/site-packages/numpy-2.4.6.dist-info/licenses/numpy/random/src/mt19937/LICENSE.md
    1154 e7d4f4fb20358f31 .venv/lib/python3.11/site-packages/numpy-2.4.6.dist-info/licenses/numpy/random/src/pcg64/LICENSE.md
    1509 6f5828a57223d4cc .venv/lib/python3.11/site-packages/numpy-2.4.6.dist-info/licenses/numpy/random/src/philox/LICENSE.md
    1226 9d4098846018319c .venv/lib/python3.11/site-packages/numpy-2.4.6.dist-info/licenses/numpy/random/src/sfc64/LICENSE.md
     332 268b0ca06759d31e .venv/lib/python3.11/site-packages/numpy-2.4.6.dist-info/licenses/numpy/random/src/splitmix64/LICENSE.md
   46794 4860083caa0de2ac .venv/lib/python3.11/site-packages/numpy-2.4.6.dist-info/licenses/LICENSE.txt
    3637 a4e0d97dfc9aeb7f .venv/lib/python3.11/site-packages/pyside6_essentials-6.11.2.dist-info/METADATA
    4380 262481e844521b32 resources/fonts/Inter/LICENSE.txt
    4399 30f0c136e3c88e42 resources/fonts/JetBrainsMono/OFL.txt
6 paths (22 files), 0 missing
```

The listing is the `ls` output that the paths of §Text sources for THIRD_PARTY_LICENSES.md call for. The left column is the
size in bytes and the middle column is the first 16 hex digits of the SHA-256. The NumPy licence directory has 17 files, and
the line for `licenses/LICENSE.txt` appears twice, once inside the directory and once as its own path.

Mutation test (`verified`). A copy of this document had the word "recombine" in Q5 changed to "recompile". The script printed
`Q5: FAIL, fragment not found after offset 0 in lgpl3-qtbase: 'Convey the Minimal Corresponding Source under the terms of
this License, and the Correspon'`, then `30 quote rows, 1 failed`, and exited 1.

Full run of the register script (`verified`). `check_dependency_licences.py --coverage` printed `every pyproject.toml requirement
is listed in PACKAGES` and exited 0 in this worktree. The full run, made in a copy of the evidence folder so that it did not
overwrite the table above, also exited 0 on 2026-10-12. PyPI then showed newer releases than the table of 2026-10-09: NumPy
2.5.4 as newest overall (the pin stays 2.4.6), hypothesis 6.169.0, pypdf 6.20.0 and ruff 0.17.0 as newest overall. The
PySide6-Essentials and shiboken6 pins stay at 6.11.2. The table keeps its 2026-10-09 values. Rerun the script in the main
checkout to refresh it.
