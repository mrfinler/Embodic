Prepared by: Agent 5 (Research & Evidence Specialist), model: claude-opus-5-5. Revised 2026-10-08 (U-S3c) by Agent 5, model: claude-sonnet-5-5. Revised 2026-10-09 (U-S5a) by Agent 5, model: claude-sonnet-5-5.

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
   copy of the Library, so whether route 1 (a) is met is `unresolved`. Route 0 needs embodic's own source with the
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

All files below were hashed with `sha256sum` in the U-S5a worktree (main 3d70170) on 2026-10-09. The five hashes equal
the ones in `resources/fonts/FONTS.md`. Each file was also downloaded again from its source URL at the release tag and
hashed. Every pair is identical (`verified`). The sizes are the byte counts of the files.

| File | Version | Copyright line (first line of the licence text) | Reserved Font Name | Bytes | SHA-256 | EV |
|---|---|---|---|---|---|---|
| `Inter/InterVariable.ttf` | Inter Variable, "Version 4.001;git-9221beed3", tag v4.1 | n/a (font) | none | 879708 | `4989b125924991b90d05b2d16e0e388c48f7d5bb8b30539bbf9c755278d0ccaf` | EV-106 |
| `Inter/LICENSE.txt` | SIL OFL 1.1 | "Copyright (c) 2016 The Inter Project Authors (https://github.com/rsms/inter)" | none | 4380 | `262481e844521b326f5ecd053e59b98c8b2da78c8ee1bdbb6e8174305e54935a` | EV-106 |
| `JetBrainsMono/JetBrainsMono-Regular.ttf` | "Version 2.304", tag v2.304 | n/a (font) | none | 273900 | `a0bf60ef0f83c5ed4d7a75d45838548b1f6873372dfac88f71804491898d138f` | EV-107 |
| `JetBrainsMono/JetBrainsMono-Medium.ttf` | "Version 2.304", tag v2.304 | n/a (font) | none | 273860 | `31c92d01a8a08528b718a43addf0ad3df0af2ca4b7b3290a452f70f358e14d3d` | EV-107 |
| `JetBrainsMono/OFL.txt` | SIL OFL 1.1 | "Copyright 2020 The JetBrains Mono Project Authors (https://github.com/JetBrains/JetBrainsMono)" | none | 4399 | `30f0c136e3c88e422d0791acd97238870f9054a9729bc34cf2ff0d4ed8cac4ad` | EV-107 |

Source URLs (the same as in `FONTS.md`): `https://raw.githubusercontent.com/rsms/inter/v4.1/docs/font-files/InterVariable.ttf`,
`https://raw.githubusercontent.com/rsms/inter/v4.1/LICENSE.txt`,
`https://raw.githubusercontent.com/JetBrains/JetBrainsMono/v2.304/fonts/ttf/JetBrainsMono-Regular.ttf`,
`https://raw.githubusercontent.com/JetBrains/JetBrainsMono/v2.304/fonts/ttf/JetBrainsMono-Medium.ttf` and
`https://raw.githubusercontent.com/JetBrains/JetBrainsMono/v2.304/OFL.txt`. The "Reserved Font Name" cell is `none`
because no reserved name follows the copyright line in either licence text (see the next heading).

### Candidates from Phase 1

The table of candidates in the earlier version of this section is closed. Inter was not a Phase 1 candidate and is new.

| Font | Phase 1 row | Reserved Font Name | D-039 outcome |
|---|---|---|---|
| Inter Variable v4.1 | none (added in U-S5a) | none listed | chosen, EV-106 |
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
2. The writer does not subset. `src/embodic/io/pdf_writer.py` on main 3d70170 (`verified` by reading the code):
   `bundled_font` (l.143 to 145) reads the file bytes. `parse_truetype` (l.120 to 139) keeps them unchanged as
   `data=data`. `_embed` (l.223 to 246) writes them with `file_id = stream(ttf.data, f" /Length1 {len(ttf.data)}")`
   (l.229), references that stream as `/FontFile2` in the descriptor (l.234), and wraps it in a `Type0` font with
   `/Encoding /Identity-H` over a `CIDFontType2` descendant (l.237 to 245). The `stream` helper in `to_bytes` (l.358 to
   361) compresses with `zlib.compress` and `/FlateDecode`, which loses no byte. The module docstring (l.3 to 4) says the
   same.

The check script `docs/phase2/evidence/tools/check_pdf_font_embedding.py` reproduces this by running the real exporter
(`write_report_pdf` on the packaged example `spiral_12c10p_d08`), decoding each `FontFile2` stream with pypdf and hashing
it (`verified`, run 2026-10-09):

```
Inter/InterVariable.ttf: disk 4989b125924991b90d05b2d16e0e388c48f7d5bb8b30539bbf9c755278d0ccaf bytes 879708
  embedded /InterVariable: 4989b125924991b90d05b2d16e0e388c48f7d5bb8b30539bbf9c755278d0ccaf bytes 879708
  identical to disk: True | FONTS.md hash matches disk: True
JetBrainsMono/JetBrainsMono-Regular.ttf: disk a0bf60ef0f83c5ed4d7a75d45838548b1f6873372dfac88f71804491898d138f bytes 273900
  embedded /JetBrainsMono-Regular: a0bf60ef0f83c5ed4d7a75d45838548b1f6873372dfac88f71804491898d138f bytes 273900
  identical to disk: True | FONTS.md hash matches disk: True
fonts in the PDF: ['/InterVariable', '/JetBrainsMono-Regular']
```

The PDF embeds the Inter file and JetBrains Mono Regular only. JetBrains Mono Medium is used by the UI and is not in the
PDF. Bold text in the PDF is the regular face drawn with a stroke (`PdfDocument._style`, `2 Tr`), so no instance of the
variable font is made. When the check meets a changed byte it fails: a one-byte change to a copy of `InterVariable.ttf`
printed `identical to disk: False | FONTS.md hash matches disk: False` and exit code 1.

Each embedded copy keeps the font's own `name` table (`verified`, the script prints it). Name ID 0 of Inter reads
"Copyright 2016 The Inter Project Authors". Name ID 13 reads "This Font Software is licensed under the SIL Open Font
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
   `pyproject.toml` and the folders; the wheel built from it has no licence member except the fonts). REQ-N-19 asks for a
   recorded licence "compatible with the embodic licence". Which licence embodic uses is a decision for the user.

## What the M5 packages must carry

The facts in the "Present today" column come from a wheel built on 2026-10-09 with
`pip wheel --no-build-isolation --no-deps .` from main 3d70170, listed with `zipfile` (`verified`). The wheel carries all
of `resources/` at `embodic/_resources/` through `[tool.hatch.build.targets.wheel.force-include]`.

### Wheel (pip into a venv, D-015 default)

| File in the wheel | Why | Present today |
|---|---|---|
| `embodic/_resources/fonts/Inter/LICENSE.txt` | OFL condition 2, next to `InterVariable.ttf` | yes, 4380 bytes |
| `embodic/_resources/fonts/JetBrainsMono/OFL.txt` | OFL condition 2, next to both JetBrains Mono files | yes, 4399 bytes |
| `embodic/_resources/fonts/FONTS.md` | source URLs and hashes of the font files | yes, 2951 bytes |
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
