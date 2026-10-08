Prepared by: Agent 3 (Senior Software), unit U-M4f - model: claude-opus-5-5

# Bundled fonts

The app and the PDF report use these files and nothing else; no font is fetched at run time (D-039 a, b). Both
families are licensed under the SIL Open Font License 1.1; the licence text ships beside the font files.

| File | Family, version (name table ID 5) | Source URL | SHA-256 |
|---|---|---|---|
| `Inter/InterVariable.ttf` | Inter Variable, "Version 4.001;git-9221beed3" (release tag v4.1; axes opsz 14 to 32, wght 100 to 900, default wght 400) | https://raw.githubusercontent.com/rsms/inter/v4.1/docs/font-files/InterVariable.ttf | `4989b125924991b90d05b2d16e0e388c48f7d5bb8b30539bbf9c755278d0ccaf` |
| `Inter/LICENSE.txt` | SIL OFL 1.1, Inter v4.1 | https://raw.githubusercontent.com/rsms/inter/v4.1/LICENSE.txt | `262481e844521b326f5ecd053e59b98c8b2da78c8ee1bdbb6e8174305e54935a` |
| `JetBrainsMono/JetBrainsMono-Regular.ttf` | JetBrains Mono Regular, "Version 2.304" (release tag v2.304) | https://raw.githubusercontent.com/JetBrains/JetBrainsMono/v2.304/fonts/ttf/JetBrainsMono-Regular.ttf | `a0bf60ef0f83c5ed4d7a75d45838548b1f6873372dfac88f71804491898d138f` |
| `JetBrainsMono/JetBrainsMono-Medium.ttf` | JetBrains Mono Medium, "Version 2.304" (release tag v2.304) | https://raw.githubusercontent.com/JetBrains/JetBrainsMono/v2.304/fonts/ttf/JetBrainsMono-Medium.ttf | `31c92d01a8a08528b718a43addf0ad3df0af2ca4b7b3290a452f70f358e14d3d` |
| `JetBrainsMono/OFL.txt` | SIL OFL 1.1, JetBrains Mono v2.304 | https://raw.githubusercontent.com/JetBrains/JetBrainsMono/v2.304/OFL.txt | `30f0c136e3c88e422d0791acd97238870f9054a9729bc34cf2ff0d4ed8cac4ad` |

## Provenance

- Downloaded 2026-10-09 over HTTPS from the official repositories (rsms/inter, JetBrains/JetBrainsMono) at their latest
  release tags, v4.1 and v2.304. The `master` branch of rsms/inter names 4.2 in `version.txt`, but no v4.2 tag exists,
  so v4.1 is the latest release (`verified` by requesting both tags).
- The release archives on github.com could not be used: github.com, api.github.com and codeload.github.com answered
  HTTP 403 from this session's egress proxy. The files come from raw.githubusercontent.com at the release tag instead.
  No hash is published for the single files, so each SHA-256 above is the one measured with `sha256sum` after download
  (`verified` by measuring; equality with the files inside the release ZIPs is `not tested`).
- The version strings were read from each file's `name` table with fontTools (`verified`).

## Glyph coverage

`tests/unit/ui/fonts/test_font_files.py` checks the glyphs embodic prints (µ, Ω, °, U+2212, ≈, ·, U+202F) in both
families with fontTools. Inter covers all of them. JetBrains Mono 2.304 has no U+202F (narrow no-break space) glyph
(`verified` with fontTools); embodic does not print U+202F today, and that test case is a strict expected failure so a
font that adds the glyph turns it into a pass to review.
