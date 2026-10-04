จัดทำโดย: Fable 5.1 — ผู้ประสานงานและผู้ตรวจสอบขั้นสุดท้าย — model: claude-fable-5-1

# embodic — สรุป Phase 1 (สำรวจ วิจัย และจัดทำ draft) — 4 ต.ค. 2026

เอกสารนี้สรุปเป็นภาษาไทยสำหรับผู้ใช้ เอกสารฉบับเต็มทั้งหมดเป็นภาษาอังกฤษอยู่ใน `docs/phase1/` (ดัชนีใน
`00_phase1_summary.md`) Phase 1 ยังไม่มีการเขียนโค้ดของซอฟต์แวร์ใหม่ และยังไม่แก้ไฟล์ต้นฉบับใด ๆ

สถานะที่ใช้ทั้งโครงการ: `verified` = อ่านพบในแหล่งอ้างอิงหรือคำนวณซ้ำได้ (ไม่ได้แปลว่ายืนยันด้วยการทดลอง),
`inferred` = สรุปจากหลักฐานพร้อมเหตุผล, `assumption` = ข้อสมมติในการออกแบบ, `unresolved` = ยังไม่ทราบ/ต้องทดสอบ,
`not tested` = ยังไม่ได้ทดสอบ

## 1. ทีมและกระบวนการ

- โมเดล: agent ทั้ง 6 รันด้วย alias `opus` ซึ่ง probe และทุกไฟล์รายงานตัวเองว่า `claude-opus-5-5` (Opus 5.5) ผู้ประสานงานคือ
  Fable 5.1 — ไม่มีการเปลี่ยนโมเดลโดยไม่แจ้ง มีการติด session limit ของ Opus 1 ครั้ง (รีเซ็ต 18:40) ทำให้รอบแก้ไขสุดท้ายล่าช้า
  ประมาณ 15 นาที
- รูปแบบ: ใช้ subagent (ไม่ใช่ workflow) ตามการประเมินที่แจ้งไว้ ทำงานเป็นรอบ: วิจัย → ออกแบบมอเตอร์ → UX/ซอฟต์แวร์/สถาปัตยกรรม
  ขนานกัน → ปรับให้สอดคล้อง → ตรวจสอบอิสระ (Agent 4) → แก้ defect → ตรวจซ้ำ 2 ครั้ง
- ผลการตรวจสอบอิสระ: พบ defect 22 รายการ (major 2, minor 20) ปิดและตรวจซ้ำครบทั้ง 22 เหลือ minor ใหม่ 1 รายการ (DEF-23
  เรื่องการติดป้ายสถานะของค่าปรับแก้ขอบแม่เหล็ก) ไม่มี blocker — Agent 4 แนะนำให้ส่ง draft ให้ผู้ใช้อนุมัติได้
- Version control: git repository ใน `C:\Users\Sayoomphu\Desktop\embodic` (คอมมิตแยกตามรอบงาน ดู diff/ย้อนกลับได้)

## 2. สิ่งที่พบ

1. **Repository magnetless_motor** (GPL-3.0, commit c6ec327): ไม่มีโค้ด มีแต่ไฟล์ Altium/Inventor/Gerber บอร์ดในนั้นเป็น **wave winding**
   (ตัวนำรัศมี 144 เส้นต่อชั้น, 6 ชั้นแบ่งเป็น 2 กลุ่มหมุนต่างกัน 15°, via 617 ตัว) ไม่ใช่ spiral coil — `verified` จาก Gerber
2. **ภาพ Instagram** ที่ส่งมา: เห็นตำแหน่ง coil 8+8 ซ้อนเหลื่อมกัน แต่ความละเอียดภาพแยกไม่ได้ว่าเป็น spiral coil หรือ wave winding —
   `unresolved` จึงใช้เป็น "แบบอ้างอิงสไตล์" เท่านั้น (ต้องยืนยัน UD-13)
3. **เปเปอร์ 18 ฉบับ (ไม่ซ้ำ)** ถูกบันทึกใน evidence register พร้อมหน้าที่อ้างอิง 79 แถว + ตารางกรณีอ้างอิงที่มีตัวเลขวัดจริง
   (วิทยานิพนธ์ UGent: spiral coil 12/10 วัด Ke = 0.031 V·s/rad; Tokgöz 2020: 12 coil/16 ขั้ว วัด R 1.07 Ω, L 14.8 µH;
   Pan 2026: spiral 8 ชั้น วัด 46.4 mN·m) และสิทธิบัตรของ ECM PCB Stator ถูกสำรวจ — มีข้อถือสิทธิที่ครอบคลุม serpentine/spiral และ
   การต่อชั้นอนุกรมด้วย via นอกพื้นที่ใช้งาน → **ควรให้ทนายความตรวจก่อนปล่อยผลิตภัณฑ์** (เราไม่ใช่นักกฎหมาย)
4. **KiCad 9.x** (จากเอกสารทางการ): plugin แบบ SWIG ถูก deprecate ตั้งแต่ 9.0 (วางแผนถอดใน 11.0); IPC API (`kicad-python`, MIT)
   ใช้ได้เฉพาะเมื่อ PCB editor เปิดอยู่ ต้องเปิดใช้ใน Preferences ▸ Plugins และแต่ละ plugin ได้ venv ของตัวเองบน Python ที่ KiCad
   แพ็กมา — **ยังไม่ได้ทดสอบบนเครื่องคุณเลย** (smoke test T0–T6 รอ Phase 2)
5. **Engine เดิม (Xcoil v3)**: test 131/131 ผ่าน แต่พบ bug 2 จุดที่ยืนยันซ้ำแล้ว: `starOfSlots` ปฏิเสธชุด 12/14 (ที่สมดุล) เพราะ
   floating-point tie และ sector generator ใส่ turn ได้ 0 ในเรขาคณิตที่วิทยานิพนธ์สร้างจริง 3 turn → ส่วนนี้ต้องเขียนใหม่ สมการ
   สนามแม่เหล็ก/EMF/ความต้านทานคำนวณซ้ำได้ตรงกับ closed form

## 3. สิ่งที่เสนอ (ทั้งหมดเป็น `assumption` จนกว่าคุณจะอนุมัติ)

- **Topology**: spiral coil แบบ concentrated **12 coil / 16 ขั้ว** ทุกเฟสอยู่บนทุกชั้น (winding factor 0.866) คงใช้ rotor 16 แม่เหล็ก
  จาก repo ได้; รองรับ 12/10 และ 12/14 เพื่อเทียบกับเปเปอร์; 16 coil ทำ 3 เฟสสมดุลบนชั้นเดียวกันไม่ได้ (16 หาร 3 ไม่ลงตัว) ทำได้
  เฉพาะแบบ "หนึ่งเฟสต่อคู่ชั้น" — ดู `engineering/topology_analysis.md` และภาพแนวคิด `spiral_coil_concept.svg`
  (ภาพแนวคิดแยกจากเรขาคณิตคำนวณจริงชัดเจน)
- **Equation specification** EQ-01…EQ-22 แต่ละสมการมีแหล่งอ้างอิง หน่วย ช่วงที่ใช้ได้ กรณีอ้างอิง tolerance และ "ประตูตรวจ" ว่าจะ
  reuse / reuse with change / cannot verify yet / replace จาก engine เดิม — ค่าคงที่ทองแดงมีแหล่งแล้ว (IACS/NBS Handbook 100)
  ส่วน inductance, IPC-2221 และ torque–speed ยังเป็นค่าประมาณที่ยังไม่ validate
- **ประเภทแอป**: เสนอ **Python desktop (PySide6/Qt) + KiCad 9 IPC plugin แบบไม่มี UI (วางเรขาคณิตลงบอร์ดที่เปิดอยู่) +
  ตัวเขียนไฟล์ `.kicad_pcb` เป็น fallback** ทางเลือกที่สอง: web UI แบบ local (FastAPI + browser) เหตุผล ข้อจำกัด และ licence ของ
  framework อยู่ใน `architecture/app_type_comparison.md`
- **สถาปัตยกรรม**: engine เป็น Python ล้วน (`embodic.geometry / winding / physics / drc / results / io`) ไม่ import UI หรือ KiCad;
  UI/CLI/plugin เป็น adapter บาง ๆ; ทุกผลคำนวณพกค่า หน่วย EQ-ID หลักฐาน รายการข้อสมมติ และสถานะ; requirements 98 ข้อพร้อม
  acceptance criteria; ADR 9 ฉบับ; test plan พร้อม traceability matrix
- **UX/UI**: ระบบสีขาว/เทา/ดำ (tokens ตรวจ contrast แล้ว), mockup 8 หน้า (ขั้นตอน Coil → Phases → Layers → Board → Results →
  Export, หน้าโทรศัพท์, หน้าแบบ greyscale ล้วน และหน้าต่าง KiCad 880×600) เกณฑ์ accessibility UX-AC-01…22 — ดู
  `design/mockups/png/`
- **การทดสอบ**: กลยุทธ์ทดสอบอิสระ IT-01…IT-56, golden regression ต่อ engine เดิมระดับฟังก์ชัน, กรณี oracle จากเปเปอร์, property test
  "DRC ต้องไม่รายงานต่ำกว่าจริง"

## 4. การตัดสินใจที่ Fable ตัดสินแล้ว (ดู `docs/decision_log.md`)

D-006 กฎ DRC ของ embodic เข้มงวด ไม่มี slack 4 µm แบบ Xcoil (ดีไซน์ default ของ Xcoil จะไม่ผ่านกฎนี้) และ D-007 ป้ายสถานะผล
คำนวณแสดง "ความน่าเชื่อถือของวิธีคำนวณ" ส่วนข้อสมมติแสดงแยกเป็นแท็ก "n assumptions" ที่กางดูได้ — ถ้าคุณไม่เห็นด้วย แจ้งได้

## 5. สิ่งที่ต้องการจากคุณก่อนเริ่ม Phase 2 (ฉบับเต็ม 27 ข้อใน `architecture/user_decisions_needed.md`)

ข้อที่ขวาง Phase 2 ถ้ายังไม่ตอบ:

| # | เรื่อง | ตัวเลือก | ที่ทีมแนะนำ |
|---|---|---|---|
| UD-01 | ประเภทแอป | desktop PySide6 / local web UI | desktop PySide6 |
| UD-02 | licence ของ embodic | proprietary / MIT-BSD-Apache / GPL-3 | ตัดสินตอนนี้ (มีผลต่อการลงใน KiCad plugin store) |
| UD-04 | ความลึกของ KiCad plugin | plugin วางโปรเจกต์ที่บันทึกไว้ลงบอร์ด / เปิดหน้าต่าง embodic เต็มจากใน KiCad | แบบแรก + launcher ถ้า T3 ผ่าน |
| UD-05 | สีเฟส | สีเฟส 3 สีแบบจาง (ตรวจตาบอดสีแล้ว) + โหมด greyscale / greyscale ล้วน | สีจาง + มีโหมด greyscale (เทียบ mockup 01 กับ 07) |
| UD-08 | serpentine และ wave generator เดิม | เก็บ / เลื่อน / ตัด | เลื่อนไปก่อน คง interface ไว้ |
| UD-09/10 | rotor: แม่เหล็ก 16 ก้อน 20×6×2 mm? สองด้าน/ด้านเดียว? | — | คง 16 ก้อน, rotor สองด้าน |
| UD-11 | blind/buried via | อนุญาต / through เท่านั้น | through เท่านั้นเป็น default |
| UD-12 | เป้าหมายใช้งาน: แรงดัน ความเร็ว แรงบิด การระบายความร้อน | ใส่ค่า (ช่วงก็ได้) | จำเป็นเพื่อกำหนดจำนวนรอบ/การต่ออนุกรม-ขนาน |
| UD-13 | ภาพ Instagram เป็นเป้าหมายแบบเป๊ะ หรือแค่สไตล์ | — | สไตล์ (เพราะเลือก spiral แล้ว) |
| UD-21 | รัน smoke test T0–T6 บน Windows + KiCad 9 ของคุณ | ต้นของ Phase 2 / ทีหลัง | ต้น Phase 2 (ทีมเตรียมสคริปต์สั้น ๆ ให้) |

ข้ออื่น ๆ ที่ใช้ค่าแนะนำได้ถ้าไม่ตอบ: ไม่ทำ dark mode ก่อน, ความหนาแน่น compact, ตัวสะกดอังกฤษแบบ British, star เป็น default,
ไม่มี 3D ใน Phase 2, FEMM ติดตั้งได้ไหม (ใช้ validate สนามแม่เหล็ก), ขอติดต่อผู้เขียนเปเปอร์ Tokgöz เรื่องจำนวนรอบ, สร้างบอร์ดอ้างอิง
1 แผ่นเพื่อวัดจริงใน Phase 3

## 6. ข้อจำกัดที่ต้องรับทราบ (จากรายงานตรวจสอบอิสระ)

1. topology ของภาพ render ยังตัดสินไม่ได้ → ใช้เป็นสไตล์เท่านั้น
2. ยังไม่มีอะไรทดสอบบน KiCad จริง (รูปแบบไฟล์, Python ที่แพ็กมา, รุ่น kicad-python, ความสามารถ IPC, การติดตั้งออฟไลน์)
3. ไม่มีกรณีวัดจริงของ stator 3 เฟสที่มีมากกว่า 2 ชั้น; กรณี O2 ต้องสมมติ 8 turn/coil (7 เป็นตัวเลือกสำรอง); inductance,
   IPC และ torque–speed เป็นค่าประมาณที่ยังไม่ validate
4. แบบจำลองสนาม 2 มิติประเมิน EMF สูงเกินใกล้ขอบแม่เหล็ก ~5 % (ดีไซน์ default) ใช้ค่าปรับแก้ที่สอบเทียบจาก FEA ในเปเปอร์
   เพียงกรณีเดียว → `assumption`
5. ยังไม่มีสมการใด validate ด้วยการวัด ป้ายสถานะของผลทางฟิสิกส์จะขึ้นได้สูงสุด `inferred`
6. สูตรความยาว coil แบบวงซ้อน (ในวิทยานิพนธ์) ประเมินสูงกว่า spiral จริง 4–23 % → ค่า 0.39 Ω ของวิทยานิพนธ์เป็นค่าจากโมเดล ไม่ใช่
   ค่าวัด
7. Python ช้ากว่า engine JS เดิมประมาณ 45 เท่าใน loop ของ DRC (วัดแล้ว) ต้องใช้ NumPy/การคำนวณบางส่วนซ้ำ เป้า < 1 s ยังเป็น
   `assumption` จนกว่าจะวัดบนเครื่องคุณ
8. mockup เป็นหน้าคงที่: ตรวจ overflow ภาษา contrast และลำดับคีย์บอร์ดอัตโนมัติแล้ว แต่พฤติกรรมจริงต้องรอ implementation
9. ค่าที่ไม่มีแหล่ง: µ_r ของแม่เหล็ก, "ทองแดง PCB = IACS", ค่า h การพาความร้อน, มาตรฐาน IPC-2152 (ต้องซื้อ)
10. ต้องตรวจสิทธิบัตร ECM ก่อนปล่อยผลิตภัณฑ์; licence ของ embodic ยังไม่กำหนด

## 7. ขั้นตอนต่อไป (หลังอนุมัติ)

Phase 2 เริ่มจาก: smoke test KiCad บนเครื่องคุณ (T0–T6), สรุป scope/app type/topology/acceptance criteria, Agent 2+5 ปิด
equation spec, Agent 1 ปิด design spec, Agent 6 ปิด architecture/interfaces/test plan, Agent 3 implement (เริ่มจาก core +
golden harness + spiral generator), Agent 4 เตรียม independent tests; มี decision log และการแบ่งเจ้าของไฟล์ชัดเจน
