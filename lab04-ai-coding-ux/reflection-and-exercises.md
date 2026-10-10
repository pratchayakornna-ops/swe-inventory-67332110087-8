# แบบฝึกหัดส่งท้ายและสรุปการสะท้อนคิด (Reflection & Exercises) - Lab 04

เอกสารตอบคำถามแบบฝึกหัดส่งท้าย 4 ข้อ ตามเกณฑ์ใบงาน Lab 4 ฉบับเต็ม (Sub-CLO 3.6 ระดับ Evaluate)

---

### ข้อ 1: วิเคราะห์ Bug ที่รันได้ปกติในกรณีทั่วไป แต่พังเฉพาะใน Edge Case หรือ Concurrency
**คำตอบ:** ยกตัวอย่าง 2 ข้อจาก `inventory_service.py`
1. **Bug ในเมธอด `concurrent_restock` (Race Condition / Lost Update):**
   - **พฤติกรรม:** ในการรันแบบปกติแบบ Single Thread การอ่านค่าแล้วบวกเพิ่มจะให้ผลลัพธ์ที่ถูกต้องเสมอ
   - **กรณีที่พัง:** เกิดขึ้นเมื่อมีหลาย Thread เรียกฟังก์ชันพร้อมกัน โดยบรรทัด `current = self._inv._items[name].quantity` อยู่นอก Lock ทำให้ Thread ที่สองอ่านค่าเก่าก่อนที่ Thread แรกจะเขียนเสร็จ เกิด Lost Update สต็อกหายไป
   - **ทำไม Unit Test ธรรมดาจึงจับไม่เจอ:** เพราะ Unit Test ทั่วไปทำงานแบบ Sequential (ทีละคำสั่งตามลำดับบน Single Thread) ซึ่งไม่มีการแย่งชิงทรัพยากร (No Resource Contention) ทำให้ไม่พบความผิดพลาด
2. **Bug ในเมธอด `average_unit_value` (ZeroDivisionError & Wrong Denominator):**
   - **พฤติกรรม:** หากคลังมีสินค้าหลายรายการ และแต่ละรายการมี 1 ชิ้น โค้ดจะคำนวณเหมือนถูกโดยบังเอิญ
   - **กรณีที่พัง:** พังทันทีใน Edge Case เมื่อคลังว่างเปล่า (`len == 0`) จะเกิด `ZeroDivisionError: division by zero` และหากสินค้าแต่ละตัวมีจำนวนชิ้นไม่เท่ากัน ผลลัพธ์จะผิดเพี้ยนอย่างมาก
   - **ทำไม Unit Test ธรรมดาจึงจับไม่เจอ:** หากชุด Test เตรียมข้อมูลไว้ล่วงหน้า (Mock Data) เพียงกรณีทั่วไปที่มีสินค้าเสมอ จะมองข้ามกรณีเริ่มต้นที่ระบบยังไม่มีข้อมูล (Empty State)

---

### ข้อ 2: ออกแบบ Test Case สำหรับตรวจจับ Race Condition ใน Concurrency
**คำตอบ:** ออกแบบ Test Case ด้วย `pytest` และโมดูล `threading` เพื่อทดสอบเมธอด `concurrent_restock`
```python
import threading
import pytest
from inventory import Inventory
from inventory_service import InventoryService

def test_concurrent_restock_race_condition():
    # จัดเตรียมคลังสินค้าและสินค้าเริ่มต้น 0 ชิ้น
    inv = Inventory()
    inv.add_item("RAM", 0, 1000.0)
    service = InventoryService(inv)
    
    # กำหนดให้ 10 เธรด แต่ละเธรดเติมสต็อกทีละ 1 ชิ้น คนละ 100 ครั้ง (ยอดรวมที่ถูกต้องต้องเป็น 1,000 ชิ้น)
    NUM_THREADS = 10
    ITERATIONS = 100
    
    def worker():
        for _ in range(ITERATIONS):
            service.concurrent_restock("RAM", 1)

    threads = [threading.Thread(target=worker) for _ in range(NUM_THREADS)]
    
    # สั่งเริ่มทำงานพร้อมกัน
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        
    # หากมี Race Condition สต็อกจะหายและได้น้อยกว่า 1,000 แน่นอน
    assert inv._items["RAM"].quantity == NUM_THREADS * ITERATIONS, (
        f"เกิด Lost Update! คาดหวัง {NUM_THREADS * ITERATIONS} ชิ้น แต่ได้ {inv._items['RAM'].quantity} ชิ้น"
    )
```
**คำอธิบายการจำลอง:** เราสร้าง Threads จำนวนมากให้ยิงคำสั่งเติมสต็อกถี่ๆ พร้อมกัน เพื่อเพิ่มโอกาสที่ Context Switching ของ CPU จะสลับการทำงานระหว่างการอ่าน `current` และการเข้าสู่ `with self._lock:` ซึ่งจะทำให้ Assertion ล้มเหลวทันทีหากโค้ดมี Bug

---

### ข้อ 3: ประเมินขีดความสามารถของ AI Reviewer และการแบ่งบทบาทที่ปลอดภัย
**คำตอบ:**
- **สิ่งที่ AI Reviewer ทำได้ดี:** ตรวจสอบ Syntax, รูปแบบ Code Style (PEP 8), การตั้งชื่อตัวแปร, การตรวจจับตัวแปรที่ไม่ได้ใช้งาน (Unused Variables), และการสร้าง Docstring พื้นฐาน
- **สิ่งที่ AI Reviewer พลาด:** ขาดความเข้าใจเชิงลึกใน **Business Rules** (เช่น การตัดสต็อกต้องเป็น All-or-Nothing / Atomic), มองข้าม **Race Condition** หากเห็นว่ามีคำว่า `Lock` อยู่แล้ว, และไม่สามารถระบุข้อผิดพลาดเชิงความหมาย (Semantic Meaning) เช่น การสับสนระหว่างจำนวน SKU กับจำนวนชิ้นรวม
- **แนวทางการแบ่งงานที่ปลอดภัยที่สุด (Human-in-the-loop):**
  - **รอบที่ 1 (AI Linter & Pre-review):** ให้ AI ทำ Automated Review ใน Pull Request สำหรับตรวจ Linting, Type Annotations, และความครบถ้วนของ Docstring
  - **รอบที่ 2 (Human Code Review):** วิศวกรซอฟต์แวร์ตรวจทานในจุดวิกฤต ได้แก่ Concurrency/Thread-safety, Data Integrity/Rollback, Authorization & Security, และ Edge Cases ก่อนกด Approve เสมอ

---

### ข้อ 4: สะท้อนคิด (Reflection 100 - 150 คำ)
**คำตอบ:**
> ในยุคที่ AI สามารถสร้างโค้ดจำนวนหลายร้อยบรรทัดได้ภายในไม่กี่วินาที ทักษะการ "พิมพ์โค้ด" จึงลดความสำคัญลงเมื่อเทียบกับทักษะการ "ตรวจสอบและประเมินโค้ด" จากการทำ Lab 4 แสดงให้เห็นอย่างชัดเจนว่า โค้ดที่ AI สร้างขึ้น เช่น `inventory_service.py` และ `discount.py` มีหน้าตาที่เรียบร้อยและรันผ่านในกรณีทั่วไป แต่กลับแฝงข้อผิดพลาดร้ายแรงอย่าง Race Condition, ขาด Atomicity, และคำนวณส่วนลดผิดพลาด หากวิศวกรซอฟต์แวร์ไม่มีความเข้าใจในหลักการและเชื่อใจผลลัพธ์ของ AI โดยขาดการ Review อย่างละเอียด ระบบที่นำไปใช้งานจริงจะเกิดความเสียหายต่อข้อมูลทางธุรกิจอย่างมหาศาล ดังนั้น วิศวกรซอฟต์แวร์ยุคใหม่จึงต้องทำหน้าที่เป็นผู้กำกับคุณภาพที่สามารถตั้งคำถาม สืบสวนหา Root Cause และตรวจทานงานของ AI ได้อย่างมีหลักฐาน
