จัดทำโดย: Fable (ผู้ประสานงาน) - model: claude-opus-5-5 - 2026-10-22

# สรุป Phase 3 ของ embodic release 0.0.6 (ภาษาไทย)

ฉบับนี้สรุปรายงานภาษาอังกฤษ `docs/phase3/verification/phase3_report.md` ของ Agent 4 (U-V22 และ U-V30) และคำตัดสิน
D-100, D-101 ใน `docs/decision_log.md`

## ผลโดยรวม

- งานตรวจสอบของ Phase 3 ที่ทีมทำได้เสร็จหมดแล้ว เหลือ 2 อย่างที่ต้องทำบนเครื่องของคุณพร้อมกับ UAT ของ Phase 4
  คือ AX-06 (ทดสอบกับ Narrator) และ W6 (ตรวจหน้าจอจริง)
- ไม่มี defect ตัวไหนที่ยังเปิดอยู่หรือย้ายไป Phase 5 ที่ทำให้ค่าที่คำนวณผิด (`verified` โดย Agent 4 อ่านทุกแถว)
- Release gate บน cloud ผ่าน 11 จาก 11

## Requirement ระดับ must (73 แถว)

- `verified` 67 แถว
- `partial` 2 แถว: REQ-N-16 และ REQ-N-24 รอ AX-06
- `failed` 4 แถว ทุกแถวมีชื่อในบันทึกการตัดสินใจ:
  - REQ-N-01: ขั้น physics ใช้เวลา 0.62 ถึง 0.66 วินาที เกินงบ 0.3 วินาที คุณย้ายการแก้ไปที่ Phase 5 แล้ว (D-091a, K-2)
  - REQ-N-02: บน Windows หน้าต่างหน่วงเกิน 100 ms ในบางรอบ (114 ถึง 258 ms) คุณย้ายการแก้ไปที่ Phase 5 แล้ว (D-076d, K-1)
  - REQ-N-05 และ REQ-N-06: Windows บล็อก `embodic-cli.exe` ในบางรอบ (DEF-W-16) test อัตโนมัติในรอบนั้นจึงไม่ผ่าน
    แต่ PK-06 รอบ 11 ใช้ `embodic-cli` ได้ และ `python -m embodic.cli` ใช้ได้ในรอบ 12

## ผลบน laptop ของคุณ (0.0.6)

- PK-04: ผลทั้ง 5 ตัวอย่างตรงกับผลบน Linux ภายใน 1e-9
- PK-05: bundle ผ่าน 6 จาก 6 เป็นครั้งแรกบน Windows
- PK-06: ติดตั้งตาม INSTALL.md ผ่านทั้งสองแบบ ได้ตัวอย่างแรกใน 22.3 วินาที (`embodic-cli`) และ 19.3 วินาที
  (`python -m embodic.cli`) self-test ผ่าน 45 จาก 45 ทั้งสองรอบ
- Commit gate: 5 จาก 6 test ที่ไม่ผ่านเทียบกับ bundle ที่เหลือจาก 0.0.5 ผมแก้ที่ต้นเหตุแล้ว: ตอนนี้ tests/bundle
  ไม่รับ bundle ที่สร้างจาก source อื่น (U-M9f)

## V3 campaigns

- Mutation: จับได้ครบทุกตัว (DRC 14/14, generator 5/5, physics 5/5, exporter 4/4, instrument 33/33) และ Hypothesis
  ไม่พบความผิดพลาด
- FEA 2-D (OR-11, OR-12): อยู่ใน band
- V3-14 บน wheel 0.0.6: ไม่พบคำต้องห้ามสักจุด คือไม่มีคำว่า measured กับค่าที่คำนวณ ไม่มีคำว่า Xcoil ใน UI และไม่มีชื่อบุคคล
  หรือ brand asset หลุดเข้าไป ผมดึงโฟลเดอร์ brand เดิม (`Fantastic Creature\pitchdeck\resources`) จากเครื่องของคุณ
  มาเทียบ hash อีกครั้ง โดยเก็บใน git แค่ค่า hash ไม่ได้เก็บรูป

## รายการ DEF ของ Phase 3 (93 แถว)

- ปิดแล้ว 82 แถว
- ย้ายไป Phase 5: 6 แถว
- ปิดเพราะไม่ใช่ defect ของโปรแกรม: 1 แถว (DEF-W-14)
- รับไว้โดยระบุชื่อ: 2 แถว (DEF-W-16 และ DEF-US18-01)
- เลข DEF-W-10 และ DEF-W-11 ไม่มีบันทึกที่ไหนเลย ทั้งใน repo และบนเครื่องของคุณ จึงเลิกใช้สองเลขนี้ (`unresolved`)
- เปิดค้างอยู่: 0 แถว

## สิ่งที่ยังไม่ได้ทดสอบ (`not tested`)

- FEA แบบ 3-D (OR-11c) และค่า inductance จากการวัดจริง เพราะยังไม่มีบอร์ด
- Python 3.12 และ 3.13 บน Windows
- PK-06 แบบ cache ว่างบน Windows หลัง 0.0.2 เพราะเน็ตช้า
- `python -m embodic.ui.app` ยังไม่เคยเปิดบน Windows
- หน้าจอจริง (W6) และ Narrator (AX-06) ซึ่งจะทำใน UAT

## สิ่งที่ต้องให้คุณตัดสินใจ (ทำระหว่าง UAT ได้)

1. S-1 (DEF-W-16): code signing หรือใช้ `python -m` เป็นวิธีหลักบน Windows
2. DEF-US18-01: ปุ่มลัดบน canvas (L, G, C, M, T, A, B, Shift+C) จะให้สร้าง หรือให้เอาออกจาก keyboard map (ขั้น 3.10)
3. K-1 และ K-2: รับข้อจำกัดเรื่องความเร็วไว้ก่อนจนถึง Phase 5 หรือให้แก้ก่อนรับงาน
4. G-1 และ G-2: repo บน GitHub เป็น private หรือไม่ และจะ push main กับ tag v0.0.4 ถึง v0.0.6
5. AX-06: ทำใน UAT หรือไม่ทำก็ได้ ถ้าไม่ทำ แถวนี้จะเป็น `not tested`
