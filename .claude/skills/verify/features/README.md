# embodic feature map

Each file is one user-facing feature: what it is, how a user reaches it, how the levers drive it, and the end state
that proves it works. The levers are `tests/ui/qt_e2e/` (pytest-qt) and `tests/ui/qt_shell/capture_acceptance.py`.

| Feature | File | Checklist rows | Tests |
|---|---|---|---|
| Open a design and edit it | [design_walkthrough.md](design_walkthrough.md) | S01, S11 to S21, S39 | `test_walkthroughs.py`, `test_review_2_fixes.py` |
| Results, DRC and charts | [results_and_checks.md](results_and_checks.md) | S22 to S28, S34, S35, S37 | `test_walkthroughs.py` |
| Export and save | [export_and_save.md](export_and_save.md) | S29 to S31, S40 | `test_walkthroughs.py` |
| Keyboard and target size | [accessibility.md](accessibility.md) | every Focus cell | `test_ax02_keyboard_only.py`, `test_ax04_target_size.py`, `test_ui09_scaling.py` |
| Canvas and shell | [canvas_and_shell.md](canvas_and_shell.md) | S02 to S10, S36, S38, S41 | `tests/ui/qt_shell/` |
