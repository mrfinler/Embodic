Prepared by: Agent 3 (Senior Software), units U-M4f and U-M4e-1 - model: claude-opus-5-5

# Bundled fonts

The app and the PDF report use these files and nothing else; no font is fetched at run time (D-039 a, b). Both
families are licensed under the SIL Open Font License 1.1; the licence text ships beside the font files.

| File | Family, version (name table ID 5) | Source URL | SHA-256 |
|---|---|---|---|
| `Inter/Inter-Regular.ttf` | Inter Regular (family Inter, weight class 400), "Version 4.001;git-9221beed3" (release v4.1) | https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip, member `extras/ttf/Inter-Regular.ttf` | `40d692fce188e4471e2b3cba937be967878f631ad3ebbbdcd587687c7ebe0c82` |
| `Inter/Inter-SemiBold.ttf` | Inter SemiBold (typographic family Inter, subfamily SemiBold, weight class 600), "Version 4.001;git-9221beed3" (release v4.1) | https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip, member `extras/ttf/Inter-SemiBold.ttf` | `78a843fade9d4612a5567302fb595b56976eb5fcebf4fea5a5912d638bafcde3` |
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
  No hash is published for the single files, so each SHA-256 above is the one computed with `sha256sum` after download
  (`verified` by computing; equality with the files inside the release ZIPs is `not tested`).
- The version strings were read from each file's `name` table with fontTools (`verified`).

- U-M4e-1 (2026-10-09, U-S4e ruling e2) replaced `Inter/InterVariable.ttf` with the two static files above, because Qt
  ignores the `wght` axis and weight 600 rendered at body weight. The release archive `Inter-4.1.zip` (SHA-256
  `9883fdd4a49d4fb66bd8177ba6625ef9a64aa45899767dde3d36aa425756b11e`, 33 707 794 bytes) downloaded from github.com
  this time. Its `InterVariable.ttf` and `LICENSE.txt` have the same SHA-256 as the files U-M4f took from
  raw.githubusercontent.com (`verified` with `sha256sum`), so the licence text above is the release's own.

## Glyph coverage

`tests/unit/ui/fonts/test_font_files.py` checks the glyphs embodic prints (µ, Ω, °, U+2212, ≈, ·, U+00A0, η, δ, Δ)
in every bundled file with fontTools; all files cover all of them (`verified` by running). Number and unit are joined
by U+00A0 (U-S4e ruling e1). JetBrains Mono 2.304 has no U+202F (narrow no-break space), which is why embodic does
not use it.
