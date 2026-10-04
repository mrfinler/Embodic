# Changelog

All notable changes to embodic are listed here. Versions follow semantic versioning; dates are ISO 8601.

## 0.0.1 - 2026-10-04

### Added

- Installable package `embodic` (Python 3.11 or newer) with the `desktop`, `dev` and `desktop-dev` extras.
- `embodic.units`: unit vocabulary with display forms, conversions (degrees, metres, rpm, copper oz, mil²) and
  `round_half_away_from_zero`.
- `embodic.errors`: severities, issue categories, `ValidationIssue`, `Suggestion`, `Unbuildable` and the English
  message catalogue.
- `embodic.paths.resource_root()` for wheel and editable installs.
- Gates: import contracts C1 to C4, mypy strict, ruff, static lints MT-04 to MT-07, LG-01 and LG-08, the
  requirements-to-tests matrix (`tools/trace_matrix.py`) and one entry point for every profile (`tools/ci.py`).
- GitHub Actions workflow running `tools/ci.py` on Ubuntu and Windows with Python 3.11 and 3.12.
