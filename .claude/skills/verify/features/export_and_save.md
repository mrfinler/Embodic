# Export and save

## Sub-features

Export dialog (`dlg-export`, `export-format-*`, `export-folder`, `btn-export-run`, `export-result`, `btn-export-close`),
DRC confirmation (`dlg-export-confirm`, `btn-export-confirm-cancel`, `btn-export-confirm-run`), PDF report, Save
(`act-save`) and Open (`act-open`).

## How to get to it (user POV)

Export tab of the toolstrip, or Ctrl+E for all files. Tick the formats, type a folder, press Export; the dialog lists
the written files. Save and Open sit on the Home tab.

## Driving it with pytest-qt

`_export_svg_and_pdf` in `test_walkthroughs.py`; then parse the SVG with `xml.etree` and check the PDF header. Save
and Open go through Qt's file dialog: arm `QTimer.singleShot(0, lambda: answer_file_dialog(path))` before the click.
Prove the round trip with `design_hash` before the save and after the reopen. Capture row S40 checks the colophon is
the last line of the last PDF page and writes `pdffonts`.

## Gotchas

Export stems come from the design name ("Spiral_12_coils_10_poles_D08"). Type a relative folder in captures so no
absolute path shows in a shot. Keyboard input does not accept the offscreen Qt file dialog; the Windows build uses
the native one.
