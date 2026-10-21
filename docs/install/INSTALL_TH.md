ผู้เขียน: Fable (ผู้ประสานงาน), model id: claude-opus-5-5 — แปลจาก `docs/install/INSTALL.md` (unit U-F1)

# ติดตั้งและใช้งาน embodic (ฉบับภาษาไทย)

คู่มือนี้แปลจาก `docs/install/INSTALL.md` ทีละหัวข้อ คำสั่งทุกบรรทัดคงไว้ตามต้นฉบับภาษาอังกฤษทุกตัวอักษร ถ้าสองฉบับขัดกัน
ให้ถือฉบับภาษาอังกฤษเป็นหลัก ข้อความที่โปรแกรมแสดง ชื่อไฟล์ และศัพท์เทคนิคคงเป็นภาษาอังกฤษตามกติกาของโครงการ

คู่มือนี้ติดตั้ง embodic ลงใน virtual environment เปิดโปรแกรมและโปรแกรม command line รันชุดทดสอบ และสร้าง wheel
แต่ละขั้นมีคำสั่งสำหรับ Linux (bash) และ Windows (PowerShell) ตามด้วยผลลัพธ์ที่ควรเห็น

ป้ายกำกับสองแบบบอกว่าอะไรได้รันจริงใน build นี้:

- คำสั่งของ Linux รันจริงบนเครื่อง container Linux x86-64 ที่ใช้ CPython 3.11.15 เมื่อ 2026-10-12 เว้นแต่ขั้นนั้นจะระบุไว้เป็นอื่น
- คำสั่งของ Windows เขียนจากเอกสารของ Python, venv และ pip **ยังไม่ได้ทดสอบบน Windows** ใน build นี้

การทดสอบ PK-06 (unit U-V5) ทำตามขั้นที่ 1 ถึง 6 ของคู่มือนี้บน Linux เมื่อ 2026-10-13 รันสี่รอบ แต่ละรอบใช้โฟลเดอร์ใหม่
virtual environment ใหม่ และ pip cache ว่าง เครื่องที่ใช้คือ container Linux x86-64 มี 2 CPU, RAM 8 GB, CPython 3.11.15
และไม่มีจอแสดงผล ตั้งแต่ขั้นที่ 1 จนได้ผลคำนวณตัวอย่างแรก (คำสั่ง `compute` ในขั้นที่ 5) ทั้งสี่รอบใช้เวลา 19.2 s,
20.7 s, 26.0 s และ 27.7 s ทุกรอบเสร็จภายใน 10 นาทีที่ REQ-N-07 กำหนด ในทั้งสี่รอบ ขั้นที่ 4 หยุดทำงาน (abort)
หลังประมาณ 0.5 s ด้วยข้อผิดพลาดของ Qt ที่อยู่ในหัวข้อการแก้ปัญหาบน Linux container ไม่มีจอแสดงผล ขั้นเปิดหน้าต่างจึง
เป็น `not tested` และเวลาข้างต้นรวมช่วงที่ abort ไว้แล้ว

เวลาถูกจำกัดด้วยการดาวน์โหลด การติดตั้ง dependencies ในขั้นที่ 3 ใช้ 12.7 s ถึง 20.1 s ของแต่ละรอบ และ pip ดาวน์โหลด
wheel ของ PySide6-Essentials ขนาด 80.1 MB ด้วยความเร็ว 5.0 MB/s ถึง 9.7 MB/s ความต่างระหว่างรอบมาจากความเร็ว
ดาวน์โหลด เพราะไม่มีขั้นอื่นที่ต่างกันเกิน 1.5 s เครื่องที่มี pip cache อยู่แล้ว ดิสก์ที่ช้ากว่า หรือ Python build อื่น
เป็น `not tested` การทดสอบบน Windows เป็น `not tested`

## 1. ตรวจสอบความต้องการของระบบ

embodic ต้องใช้ CPython 3.11, 3.12 หรือ 3.13 บน Windows 10 หรือ 11 (x64) หรือบน Linux (x86-64)

Linux:

```
python3.11 --version
```

Windows (ยังไม่ได้ทดสอบบน Windows ใน build นี้):

```
py -3.11 --version
```

ผลที่ควรเห็น: `Python 3.11.` ตามด้วยเลข patch ถ้าไม่พบคำสั่ง ให้ติดตั้ง CPython จาก distribution ของคุณ (Linux)
หรือจากตัวติดตั้งของ python.org (Windows)

## 2. สร้าง virtual environment

Linux:

```
python3.11 -m venv .venv
. .venv/bin/activate
```

Windows (ยังไม่ได้ทดสอบบน Windows ใน build นี้):

```
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```

ผลที่ควรเห็น: prompt ขึ้นต้นด้วย `(.venv)` คำสั่งทุกขั้นหลังจากนี้รันภายใน environment นี้

## 3. ติดตั้ง dependencies และ wheel

ไฟล์ lock ตรึงเวอร์ชันของ NumPy, PySide6-Essentials และ shiboken6 พร้อมค่า SHA-256 ของทุกไฟล์ ให้ใช้ไฟล์ที่ตรงกับเวอร์ชัน
Python ของคุณ: `py311.txt`, `py312.txt` หรือ `py313.txt` จากนั้นติดตั้ง wheel โดยไม่ติดตั้ง dependencies ซ้ำ เพราะ
`--require-hashes` ต้องการ hash ของทุก requirement แต่ wheel ในเครื่องไม่มี hash

Linux:

```
python -m pip install --require-hashes -r requirements/py311.txt
python -m pip install --no-deps embodic-0.0.6-py3-none-any.whl
```

Windows (ยังไม่ได้ทดสอบบน Windows ใน build นี้):

```
python -m pip install --require-hashes -r requirements\py311.txt
python -m pip install --no-deps embodic-0.0.6-py3-none-any.whl
```

หลังคำสั่งติดตั้ง pip อาจพิมพ์ประกาศให้อัปเกรด pip ซึ่งไม่มีผลต่อการติดตั้ง ในการทดสอบ PK-06 ข้อความคือ
`[notice] A new release of pip is available: 24.0 -> 26.2.1`

ตรวจสอบสิ่งที่ติดตั้ง:

```
python -m pip list
```

ผลที่ควรเห็น: รายการมี `embodic 0.0.6`, `numpy 2.4.6`, `PySide6_Essentials 6.11.2` และ `shiboken6 6.11.2`
นอกเหนือจาก `pip` (และ `setuptools` บน Python 3.11) การทดสอบ PK-02 (`tests/packaging/test_pk02_clean_install.py`)
ตรวจรายการนี้แบบตรงทุกตัวบน Linux

## 4. เปิดโปรแกรม

```
embodic
```

ผลที่ควรเห็น: หน้าต่าง embodic เปิดขึ้น การทดสอบ PF-03 เปิดหน้าต่างบน offscreen platform ของ Qt บน Linux
ส่วนการเปิดบน desktop session ของ Linux และบน Windows ยังไม่ได้ทำใน build นี้

## 5. ใช้โปรแกรม command line

ไฟล์ตัวอย่างมาพร้อมกับ package แสดงตำแหน่งโฟลเดอร์ได้ด้วย:

```
python -c "from embodic.paths import resource_root; print(resource_root() / 'examples')"
```

ผลที่ควรเห็น: path ที่ลงท้ายด้วย `embodic/_resources/examples` เมื่อติดตั้งจาก wheel หรือ `resources/examples`
เมื่อใช้ checkout สำหรับพัฒนา ในคำสั่งด้านล่าง ให้แทน `<examples>` ด้วย path นั้น บน Windows ให้เขียน path ด้วย `\`

คำนวณตัวอย่างค่าเริ่มต้นและเขียนผลทั้งหมดเป็น JSON:

```
embodic-cli compute <examples>/spiral_12c16p_default.embodic.json --json outcome.json --timings
```

ผลที่ควรเห็น (ค่าเวลาจะต่างไปตามเครื่อง):

```
Design: Spiral, 12 coils, 16 poles
Design hash: sha256:ac4fab5db06f9e8f733dc495080deeddfe0bcf58faa31ebb7ec841c1b27d9c09
Topology: spiral, boards: 1
Design rule check: passed
Timings (s): validate 0.001, geometry 0.020, drc 0.306, physics 0.702
```

ผลแต่ละค่าใน `outcome.json` มี `status`, `eq_ids` และค่า input ที่เป็นสมมติฐานกำกับไว้

ตรวจแบบตามกฎของ design โดยไม่สร้าง geometry:

```
embodic-cli validate <examples>/spiral_12c16p_default.embodic.json
```

ผลที่ควรเห็น: `Valid: Spiral, 12 coils, 16 poles`

ส่งออกแบบ (drawing):

```
embodic-cli export <examples>/spiral_12c16p_default.embodic.json --format svg -o board.svg
```

ผลที่ควรเห็น: `Wrote board.svg` ตัวเลือก `--format` รับ `dxf`, `dxf-outline`, `dxf-screws`, `pdf`, `readme` และ
`bundle` ได้ด้วย

## 6. ตรวจสอบการติดตั้ง

wheel มี self-test 45 รายการ ซึ่งตรวจว่าการติดตั้งนี้ให้ตัวเลขตรงกับ build ของมัน ให้รันจาก virtual environment
ของขั้นที่ 2 คำสั่งเหมือนกันบน Windows (ยังไม่ได้ทดสอบบน Windows ใน build นี้)

```
embodic-cli selftest
```

ผลที่ควรเห็น: หนึ่งบรรทัดต่อหนึ่งรายการ แสดงคำผลตรวจ (`passed` หรือ `failed`) รหัสรายการ และเวลาที่ใช้ ถ้ารายการใด
ไม่ผ่านจะแสดงข้อความของรายการนั้นด้วย บรรทัดสุดท้ายเป็นสรุป สองบรรทัดสุดท้ายของการรันที่ผ่านบน Linux คือ (เวลาจะต่าง
ไปตามเครื่อง):

```
passed   ST-EXP-BUNDLE                         3.99 s
45 tests: 45 passed, 0 failed
```

exit code เป็น 0 เมื่อทุกรายการผ่าน และเป็น 1 เมื่อมีรายการไม่ผ่าน การทดสอบ PK-06 รันคำสั่งนี้สี่ครั้งบน Linux ที่ไม่มี
จอแสดงผล ทุกครั้งผ่าน ออกด้วย 0 และใช้เวลา 8.6 s ถึง 8.9 s ไม่มีการรันที่ไม่ผ่านให้ตรวจ ค่า exit code 1 จึงมาจาก
interface contract (`docs/phase2/architecture/interfaces.md` section 12) รายการที่ไม่ผ่านชี้ว่าการติดตั้งมีข้อบกพร่อง
เช่น NumPy เสีย หรือไฟล์ resource เสียหาย

โปรแกรมรันชุดตรวจเดียวกันได้ในหน้าต่าง Tests: เปิดแท็บ View หากลุ่ม Help แล้วคลิก **Self-tests** คลิก **Run** เพื่อเริ่ม
**Stop** หรือ Esc ยกเลิกการรัน หลังรันผ่าน บรรทัดสรุปคือ `45 tests: 45 passed, 0 failed` build นี้ไม่ได้เปิดหน้าต่างนี้บน
desktop session คำอธิบายนี้จึงมาจาก source และ `docs/phase2/design/screens.md` section 13

ผลของ self-test ไม่เปลี่ยน badge ของผลคำนวณใด ๆ badge ขึ้นกับ registry และหลักฐานการทดสอบของ build ดังนั้นการผ่าน
หรือไม่ผ่านตรงนี้ไม่ทำให้ badge ใดเปลี่ยน (`docs/phase2/architecture/interfaces.md` section 14)

## 7. รันชุดทดสอบ

การติดตั้งสำหรับพัฒนาใช้ไฟล์ lock แบบ `-dev` ซึ่งเพิ่มเครื่องมือทดสอบและเครื่องมือ build และติดตั้ง embodic แบบ editable
จาก checkout ของ repository การติดตั้งแบบ editable ต้องใช้ network เพราะ pip จะ build ใน environment แยก และดาวน์โหลด
hatchling กับ `editables` มาใช้ที่นั่น ตัวเลือก `--no-build-isolation` จะล้มเหลว เพราะ editable build ของ hatchling
ต้อง import `editables` ซึ่งไฟล์ lock ไม่ได้ตรึงไว้

Linux (คำสั่งติดตั้งสองบรรทัดรันใน environment ใหม่ ส่วน gate รันใน environment เดิมของโครงการ):

```
python -m pip install --require-hashes -r requirements/py311-dev.txt
python -m pip install --no-deps -e .
python tools/ci.py --profile commit
```

Windows (ยังไม่ได้ทดสอบบน Windows ใน build นี้):

```
python -m pip install --require-hashes -r requirements\py311-dev.txt
python -m pip install --no-deps -e .
python tools\ci.py --profile commit
```

ผลที่ควรเห็น: gate พิมพ์หนึ่งบรรทัดต่อหนึ่ง gate และจบด้วย `6 of 6 gates passed` บนเครื่อง 2 CPU commit gate
ใช้เวลาหลายสิบนาที

## 8. สร้าง wheel และบันทึกหลักฐานการทดสอบ

```
python tools/ci.py --profile release
```

ผลที่ควรเห็น: สรุปผลแสดง gate ทั้งหก ตามด้วย `passed-test evidence (TR-05)`, `wheel build` และ `evidence in the
wheel (PK-10)` และจบด้วย `9 of 9 gates passed` wheel อยู่ที่ `build/dist/` และไฟล์
`resources/evidence/passed_tests.v1.json` แสดงรายการ registry tests ที่ผ่าน ถ้า gate ใดล้มเหลว การรันจะหยุดก่อนขั้น
evidence และจะไม่มีไฟล์ evidence เหลืออยู่

## 9. สร้างโฟลเดอร์สำหรับ Windows

`tools/build_bundle.py` สร้าง bundle แบบ one-folder ของ PyInstaller 6.22.3 จาก `packaging/pyinstaller/embodic.spec`
สคริปต์ติดตั้ง PyInstaller ใน venv ชั่วคราวของตัวเองชื่อ `.venv-bundle` และไม่แตะ venv ของขั้นที่ 2 การรันครั้งแรกจะ
ดาวน์โหลด package ตามไฟล์ lock, PyInstaller และ hatchling จึงต้องใช้ network ให้รันจาก source checkout ด้วย Python
เวอร์ชันที่ต้องการให้ bundle ใช้ไฟล์ lock ของเวอร์ชันนั้น

Linux:

```
python3.11 tools/build_bundle.py
```

Windows (ยังไม่ได้ทดสอบบน Windows ใน build นี้):

```
py -3.11 tools\build_bundle.py
```

โฟลเดอร์ผลลัพธ์คือ `build/bundle/embodic` ภายในมีโปรแกรม desktop `embodic` และ command line `embodic-cli`
(`embodic.exe` และ `embodic-cli.exe` บน Windows), `_internal/` ซึ่งมี Python, Qt และ resources ของ embodic,
`THIRD_PARTY_LICENSES.md`, `licenses/` (ข้อความ LGPL-3.0, GPL-3.0, NumPy และ Python) และ `source/` ซึ่งเก็บ source
distribution ของ embodic การ build ใช้โหมด one-folder และไม่ใช้ UPX เพื่อให้ไลบรารี Qt แต่ละตัวเป็นไฟล์แยกที่ผู้ใช้
เปลี่ยนแทนได้ (LGPL-3.0) โฟลเดอร์นี้ยังไม่มีหนังสือเสนอให้ source ของ Qt และ PySide6 (written offer), ประกาศ third-party
ของ Qt และไฟล์สัญญาอนุญาตของ embodic เอง สคริปต์แสดงแต่ละรายการเป็น `absent`

ผลที่ควรเห็น: สคริปต์จบด้วยรายการตรวจสัญญาอนุญาต ไลบรารี Qt สี่ตัว และขนาดโฟลเดอร์ แล้วออกด้วย exit code 0
บน Linux บรรทัดของ Qt คือ:

```
Qt libraries as separate files (dependency_licences.md R10):
  Qt6Core     _internal/PySide6/Qt/lib/libQt6Core.so.6 7524648 bytes
  Qt6Gui      _internal/PySide6/Qt/lib/libQt6Gui.so.6 11412488 bytes
  Qt6Widgets  _internal/PySide6/Qt/lib/libQt6Widgets.so.6 8155496 bytes
  Qt6Svg      _internal/PySide6/Qt/lib/libQt6Svg.so.6 691176 bytes
```

โฟลเดอร์บน Linux มี 444 ไฟล์ ขนาดประมาณ 232 MB และไม่มีไฟล์ `.py` PyInstaller เตือนว่าหา `libxcb-cursor.so.0`
ไม่พบ เพราะเครื่องที่ build ไม่มีไลบรารีนี้ platform plugin `xcb` ในโฟลเดอร์จึงต้องการไลบรารีนี้บนเครื่องของผู้ใช้
ส่วน offscreen platform ทำงานได้โดยไม่ต้องมี

ตรวจโฟลเดอร์ด้วย smoke test จาก venv ของขั้นที่ 7:

```
python -m pytest tests/bundle
```

ผลที่ควรเห็น: `6 passed` การทดสอบจะรัน `embodic-cli compute` และ `export --format svg` แบบ frozen กับตัวอย่าง
ค่าเริ่มต้นและเทียบผลกับ source, เปิดโปรแกรม frozen ด้วย `--smoke` บน offscreen platform ของ Qt, รัน
`embodic-cli selftest` แบบ frozen และตรวจไลบรารี Qt ถ้าไม่มีโฟลเดอร์ การทดสอบทั้งหกจะถูกข้าม (skipped)

สิ่งที่รันจริง: การ build, smoke test และ `build/bundle/embodic/embodic-cli selftest` ซึ่งจบด้วย
`45 tests: 45 passed, 0 failed` บน container Linux ที่ระบุไว้ต้นคู่มือ โฟลเดอร์บน Linux เป็นเพียง smoke test ของ spec
เท่านั้น โฟลเดอร์ของ Windows ซึ่งการทดสอบ bundle PK-05 ต้องใช้ **ยังไม่ได้ทดสอบ**

## การแก้ปัญหาบน Linux

- `ERROR: Hashes are required in --require-hashes mode`: คำสั่งพยายามติดตั้งไฟล์ที่ไฟล์ lock ไม่ได้ตรึงไว้ ให้ติดตั้ง
  wheel ในคำสั่งแยกพร้อม `--no-deps` ตามขั้นที่ 3
- โปรแกรม abort พร้อมข้อความ `qt.qpa.plugin: From 6.5.0, xcb-cursor0 or libxcb-cursor0 is needed to load the Qt xcb platform
  plugin.` ตามด้วย `Could not load the Qt platform plugin "xcb"`: ระบบขาดไลบรารีที่ Qt ระบุ บน Ubuntu 24.04 package
  ชื่อ `libxcb-cursor0` อยู่ใน component universe (`apt-cache policy libxcb-cursor0` บน container ที่ใช้ build แสดง candidate
  0.1.4-1build1) ให้ติดตั้งด้วย package manager ของคุณ หลังติดตั้งแล้วหน้าต่างจะเปิดบน desktop session ได้หรือไม่ ยังไม่ได้
  ทดสอบ Debian และ distribution อื่นยังไม่ได้ทดสอบ ถ้า Qt ระบุไลบรารีอื่น ให้ติดตั้ง package ของ distribution สำหรับ EGL,
  OpenGL, xkbcommon และ fontconfig (ชื่อ package ต่างกันไปตาม distribution; ยังไม่ได้ทดสอบใน build นี้)
- ไม่มีจอแสดงผล: ตั้ง `QT_QPA_PLATFORM=offscreen` ก่อนเปิด `embodic` แล้ว Qt จะใช้ offscreen platform และไม่แสดงหน้าต่าง
  คำสั่ง `QT_QPA_PLATFORM=offscreen embodic --smoke` เปิดหน้าต่าง โหลดตัวอย่าง D08 คำนวณ แล้วออกด้วย code 0 ในการทดสอบ
  PK-06 ทั้งสี่รอบใช้เวลา 2.5 s ถึง 3.0 s
- `embodic-cli: command not found`: virtual environment ยังไม่ active ให้รัน `. .venv/bin/activate`

## การแก้ปัญหาบน Windows

ข้อเหล่านี้เขียนจากเอกสารของ Python และ PowerShell **ยังไม่ได้ทดสอบบน Windows** ใน build นี้ ยกเว้นข้อแรก

- `Activate.ps1 cannot be loaded because running scripts is disabled`: อนุญาต script ในเครื่องเฉพาะหน้าต่าง PowerShell นี้
  ด้วย `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` แล้ว activate อีกครั้ง ค่านี้หมดไปเมื่อปิดหน้าต่าง
  และไม่เปลี่ยน policy ของบัญชีผู้ใช้ ได้รันจริงเมื่อ 2026-10-18 บน Windows 11 Home กับ PowerShell 5.1 ที่ policy เป็น
  `Restricted`: activate ไม่ได้ก่อนรันคำสั่งนี้ และ activate ได้หลังรัน ส่วน policy ระดับ `CurrentUser` ยังเป็น `Undefined`
  (D-051g, DEF-W-04)
- ไม่พบ `py`: ตัวติดตั้งของ python.org เป็นผู้เพิ่ม launcher `py` ให้รันตัวติดตั้งอีกครั้งแล้วเลือกตัวเลือกนั้น
- path ที่มีช่องว่าง: ใส่ path ในเครื่องหมายคำพูดคู่ เช่น `embodic-cli compute "$env:USERPROFILE\My designs\a.embodic.json"`
