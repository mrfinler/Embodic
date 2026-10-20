Prepared by: Fable (coordinator) - model: claude-opus-5-5

# AX-06 record: Windows Narrator check by the user (REQ-N-16)

- Date: 2026-10-20.
- Machine: the user's laptop (Windows 11 Home), Windows Narrator, the real display.
- Build: the editable install in `%USERPROFILE%\Desktop\embodic\.venv`. The checkout was `5f814d4` before 13:11
  local time and `2fb2ec6` after it. `git diff --stat 5f814d4 2fb2ec6 -- src` is empty, so the source under test is the
  0.0.3 source either way (`verified` by running the diff).
- Example: "Spiral, 12 coils, 10 poles (D08)".

## Steps given to the user

1. `cd $env:USERPROFILE\Desktop\embodic`, then start `.\.venv\Scripts\embodic.exe`.
2. Press Ctrl+Shift+N and choose "Spiral, 12 coils, 10 poles (D08)".
3. Start Narrator with Win+Ctrl+Enter.
4. Press Tab through five inputs. Each one is to announce its label, value and unit.
5. Press F6 to move to the results, then Tab through three result cards. Each one is to announce its value, unit and
   status.

The pass criterion is the REQ-N-16 acceptance text in `docs/phase2/architecture/requirements.md`: "inputs announce
label, value, unit; results announce value, unit, status".

## Result

The user reported the check as passed ("ผ่าน", 2026-10-20). Status: `verified` by the user's run. Fable did not hear the
announcements, and they were not transcribed, so this record holds no announcement text.

The same message reported that the spiral coils of D08 look joined. Unit U-V16 measured the copper layer by layer and
found every gap at the 0.8 mm rule. The look comes from the geometry view, which draws the copper layers on top of each
other with no layer cue (DEF-UV16-02, `tests/independent/m7/records/defects.md`). That finding does not change this
record.
