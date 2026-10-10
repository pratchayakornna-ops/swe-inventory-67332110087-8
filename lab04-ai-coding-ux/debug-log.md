# Evidence-Based Debugging Log - Lab 04

บันทึกการสืบสวนและแก้ไขข้อผิดพลาด (Root Cause Analysis) ของโมดูล `discount.py` อย่างมีหลักฐานตามกระบวนการ 5 ขั้นตอน:
1. **Reproduce:** รัน test ให้เห็นข้อผิดพลาดจริง
2. **อ่าน Traceback:** ระบุบรรทัดและประเภท Exception
3. **ตั้งสมมติฐาน:** อธิบายสาเหตุเชิงตรรกะเป็นประโยคเต็ม
4. **ยืนยันสมมติฐาน:** พิสูจน์ด้วยหลักฐานเชิงประจักษ์ (Print / REPL / Assertion)
5. **Root cause และการแก้:** ระบุสาเหตุที่แท้จริงและแนวทางแก้ไขโค้ด

---

## สรุปภาพรวมก่อนการแก้ไข
เมื่อสั่งรันคำสั่งทดสอบเบื้องต้น:
```bash
python -m pytest tests/test_discount.py -v
```
**ผลลัพธ์:** พบข้อผิดพลาด 4 ข้อ จากทั้งหมด 6 ข้อ (4 failed, 2 passed)
- ❌ `test_apply_discount_basic` FAILED (AssertionError: 99.9 == 90.0)
- ✅ `test_apply_discount_zero` PASSED (กับดัก: ผ่านเฉพาะตอนลด 0% เพราะลบด้วย 0)
- ❌ `test_bulk_total` FAILED (AssertionError: 299.9 == 270.0)
- ✅ `test_average_price` PASSED
- ❌ `test_average_price_empty` FAILED (ZeroDivisionError: division by zero)
- ❌ `test_cheapest_n` FAILED (AssertionError: [20.0] == [10.0, 20.0])

---

## บันทึกการ Debug รายจุด

### จุดที่ 1: `test_apply_discount_basic`
- **1. Reproduce:**
  - คำสั่ง: `python -m pytest tests/test_discount.py -k test_apply_discount_basic -v`
  - ผลลัพธ์: `AssertionError: assert 99.9 == 90.0` (where `99.9 = apply_discount(100.0, 10)`)
- **2. Traceback:**
  ```text
  tests\test_discount.py:8: in test_apply_discount_basic
      assert apply_discount(100.0, 10) == 90.0
  E   assert 99.9 == 90.0
  ```
- **3. สมมติฐาน:**
  สูตรคำนวณส่วนลดในฟังก์ชัน `apply_discount` เขียนผิดเชิงคณิตศาสตร์ โดยนำ `percent / 100` มาลบออกจาก `price` โดยตรง แทนที่จะนำมูลค่าส่วนลด `(price * percent / 100)` มาหักออก ส่งผลให้การลด 10% ของ 100 บาท กลายเป็น `100.0 - (10 / 100) = 100.0 - 0.1 = 99.9` บาท
- **4. การยืนยัน:**
  ทดสอบรันด้วย Python REPL:
  ```python
  >>> price = 100.0
  >>> percent = 10
  >>> price - percent / 100
  99.9
  >>> price * (1 - percent / 100)
  90.0
  ```
  ผลลัพธ์ยืนยันว่าสูตรเดิมขาดการคูณด้วยตัวแปร `price` ทำให้ผลลัพธ์ห่างจากความจริงมาก
- **5. Root cause และการแก้:**
  - **Root Cause:** สูตรคำนวณขาดตัวแปร `price` ในเทอมการคิดเปอร์เซ็นต์ส่วนลด
  - **การแก้ไข:** ปรับเป็น `return price * (1 - percent / 100)` หรือ `return price - (price * percent / 100)`

---

### จุดที่ 2: `test_bulk_total`
- **1. Reproduce:**
  - คำสั่ง: `python -m pytest tests/test_discount.py -k test_bulk_total -v`
  - ผลลัพธ์: `AssertionError: assert 299.9 == 270.0` (where `299.9 = bulk_total([100.0, 100.0, 100.0], 10)`)
- **2. Traceback:**
  ```text
  tests\test_discount.py:18: in test_bulk_total
      assert bulk_total([100.0, 100.0, 100.0], 10) == 270.0
  E   assert 299.9 == 270.0
  ```
- **3. สมมติฐาน:**
  ลูปบวกผลรวม `total` ใน `bulk_total` รวมค่าได้ 300.0 ถูกต้องแล้ว แต่ฟังก์ชันพังเนื่องจากเป็น **Cascading Failure (Ripple Effect)** จากการเรียกใช้ `apply_discount(total, discount_percent)` ที่มี bug คำนวณส่วนลดผิดพลาดจากจุดที่ 1
- **4. การยืนยัน:**
  ตรวจสอบการรวมยอด `sum([100.0, 100.0, 100.0])` ได้ `300.0` เมื่อส่งเข้า `apply_discount(300.0, 10)` เดิม จะได้ `300.0 - 0.1 = 299.9` แต่เมื่อใช้ฟังก์ชันที่แก้สูตรแล้ว จะได้ `300.0 * 0.9 = 270.0`
- **5. Root cause และการแก้:**
  - **Root Cause:** ความผิดพลาดสืบเนื่องมาจากฟังก์ชันภายใน `apply_discount`
  - **การแก้ไข:** เมื่อแก้ไข `apply_discount` ให้ถูกต้องในจุดที่ 1 ฟังก์ชัน `bulk_total` จะทำงานได้อย่างถูกต้องสมบูรณ์ทันที (อาจปรับโค้ด `bulk_total` ให้กระชับด้วย `total = sum(prices)` แทนลูปสะสม)

---

### จุดที่ 3: `test_average_price_empty`
- **1. Reproduce:**
  - คำสั่ง: `python -m pytest tests/test_discount.py -k test_average_price_empty -v`
  - ผลลัพธ์: `ZeroDivisionError: division by zero`
- **2. Traceback:**
  ```text
  discount.py:18: in average_price
      return sum(prices) / len(prices)
  E   ZeroDivisionError: division by zero
  ```
- **3. สมมติฐาน:**
  ฟังก์ชัน `average_price` ไม่มีการตรวจสอบกรณีขอบเขต (Edge Case: ลิสต์ว่าง `prices = []`) ทำให้เมื่อ `len(prices)` เท่ากับ 0 ตัวหารจึงกลายเป็น 0 ส่งผลให้ระบบ Crash ทันทีด้วย `ZeroDivisionError`
- **4. การยืนยัน:**
  ทดสอบเรียก `average_price([])` พบว่า `len([]) == 0` ทำให้เกิดการหารด้วย 0 ทันที หากเพิ่มเงื่อนไข `if not prices: return 0.0` ฟังก์ชันจะคืนค่า `0.0` ตรงตามที่ Test Case คาดหวัง
- **5. Root cause และการแก้:**
  - **Root Cause:** ขาด Guard Clause ในการตรวจสอบ Input ลิสต์ว่างก่อนดำเนินการหาร
  - **การแก้ไข:** เพิ่มการตรวจสอบเงื่อนไขที่ต้นฟังก์ชัน:
    ```python
    if not prices:
        return 0.0
    return sum(prices) / len(prices)
    ```

---

### จุดที่ 4: `test_cheapest_n`
- **1. Reproduce:**
  - คำสั่ง: `python -m pytest tests/test_discount.py -k test_cheapest_n -v`
  - ผลลัพธ์: `AssertionError: assert [20.0] == [10.0, 20.0]` (ขาดสมาชิกตัวแรก `10.0`)
- **2. Traceback:**
  ```text
  tests\test_discount.py:33: in test_cheapest_n
      assert cheapest_n([50.0, 10.0, 30.0, 20.0], 2) == [10.0, 20.0]
  E   assert [20.0] == [10.0, 20.0]
  E   Full diff:
  E     [
  E   -     10.0,
  E         20.0,
  E     ]
  ```
- **3. สมมติฐาน:**
  ฟังก์ชัน `cheapest_n` มีข้อผิดพลาดในการตัดช่วงลิสต์ (Slice Off-by-one / Wrong Start Index) โดยเขียนว่า `return ordered[1:n]` ซึ่งเริ่มต้นตัดที่ดัชนี 1 ทำให้สินค้าที่ราคาถูกที่สุดจริง ๆ ซึ่งอยู่ที่ดัชนี 0 ถูกตัดทิ้งไป และได้สมาชิกเพียง `n-1` ตัว
- **4. การยืนยัน:**
  สำหรับลิสต์ `[50.0, 10.0, 30.0, 20.0]` เมื่อผ่าน `sorted()` จะได้ `ordered = [10.0, 20.0, 30.0, 50.0]`
  - `ordered[1:2]` จะได้ `[20.0]` (ผิด)
  - `ordered[:2]` หรือ `ordered[0:2]` จะได้ `[10.0, 20.0]` (ถูกต้องครบถ้วน 2 ตัว)
- **5. Root cause และการแก้:**
  - **Root Cause:** กำหนด Index เริ่มต้นของการ Slice เป็น 1 แทนที่จะเป็น 0
  - **การแก้ไข:** แก้ไขเป็น `return ordered[:n]`

---

## 3. สรุปผลการทดสอบหลังการแก้ไขทั้งหมด (Verification)
เมื่อทำการแก้ไขโค้ดตาม Root Cause ครบทั้ง 4 จุด และสั่งรันชุดทดสอบซ้ำ:
```bash
python -m pytest tests/test_discount.py -v
```
**ผลลัพธ์:** ผ่านครบ 100% (6 passed in 0.02s) ✅
```text
tests/test_discount.py::test_apply_discount_basic PASSED                 [ 16%]
tests/test_discount.py::test_apply_discount_zero PASSED                  [ 33%]
tests/test_discount.py::test_bulk_total PASSED                           [ 50%]
tests/test_discount.py::test_average_price PASSED                        [ 66%]
tests/test_discount.py::test_average_price_empty PASSED                  [ 83%]
tests/test_discount.py::test_cheapest_n PASSED                           [100%]
============================== 6 passed in 0.02s ==============================
```
