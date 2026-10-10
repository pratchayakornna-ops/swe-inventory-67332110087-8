# Prompt Engineering vs. Context Engineering - Lab 04

การทดลองเปรียบเทียบการสั่งงาน AI Coding Assistant ระหว่าง **Prompt สั้น ๆ ที่ไร้บริบท** กับ **Prompt ที่มีการออกแบบ Context อย่างครบถ้วน** ในโจทย์การเพิ่มฟังก์ชัน `sell_many()` ให้กับระบบ Inventory

---

## 1. การทดลองรอบที่ 1: Prompt สั้น ๆ ที่ขาด Context (Naïve Prompting)

### Prompt ที่ใช้สั่ง AI:
```text
เขียนฟังก์ชัน sell_many เพื่อขายสินค้าหลายรายการพร้อมกันในคลาส Inventory ด้วยภาษา Python
```

### ผลลัพธ์โค้ดที่ AI สร้างขึ้นในรอบที่ 1:
```python
def sell_many(self, orders):
    results = {}
    for item_name, qty in orders.items():
        if item_name in self.items:
            self.items[item_name] -= qty
            results[item_name] = self.items[item_name]
        else:
            print(f"Item {item_name} not found")
    return results
```

### ข้อบกพร่องที่พบจากรอบที่ 1:
1. **Interface ไม่เข้ากับโค้ดเดิม (Incompatible Interface):** AI คาดเดาว่าคลังสินค้าเก็บข้อมูลใน `self.items` ที่เป็นตัวเลขธรรมดา ทั้งที่โครงสร้างจริงของระบบคือ `self._items` เก็บอ็อบเจกต์ `InventoryItem` ทำให้เกิด `AttributeError` ทันทีเมื่อรันจริง
2. **ไม่เป็น Atomic (ขาด Transaction Rollback):** ลูปหักสินค้าทีละตัวทันที หากรายการแรกตัดสต็อกผ่าน แต่รายการที่สองสินค้าไม่พอหรือไม่มีสินค้า รายการแรกจะถูกตัดไปแล้วโดยไม่คืนสต็อก ทำให้สต็อกหายและเกิดสถานะข้อมูลค้างครึ่งทาง (Inconsistent State)
3. **การจัดการข้อผิดพลาดแย่มาก (Poor Error Handling):** ใช้ `print()` แทนการ raise Exception ทำให้ caller ไม่รู้ว่าคำสั่งล้มเหลว
4. **ไม่ตรวจสอบสต็อกติดลบ:** ไม่มีการเช็กว่า `qty` มากกว่าคงเหลือหรือไม่ ทำให้ยอดสต็อกติดลบได้

---

## 2. การทดลองรอบที่ 2: Prompt ที่มี Context ครบถ้วน (Context Engineering)

### Prompt ที่ใช้สั่ง AI:
```text
ปรับปรุงเมธอดของคลาส Inventory ด้านล่างให้รองรับการขายสินค้าหลายรายการพร้อมกัน (sell_many)

[แนบโค้ด inventory.py ฉบับถูกต้องทั้งไฟล์เป็น Context]:
--------------------------------------------------------------------------------
class InventoryItem:
    def __init__(self, name: str, quantity: int, price: float):
        if not name or not name.strip():
            raise ValueError("ชื่อสินค้าต้องไม่ว่างเปล่า")
        if quantity < 0:
            raise ValueError("จำนวนสินค้าต้องไม่ติดลบ")
        if price <= 0:
            raise ValueError("ราคาต้องมากกว่าศูนย์")
        self.name = name.strip()
        self.quantity = quantity
        self.price = price

class Inventory:
    def __init__(self):
        self._items: dict[str, InventoryItem] = {}

    def add_item(self, name: str, quantity: int, price: float) -> InventoryItem:
        if name in self._items:
            raise ValueError(f"สินค้า '{name}' มีอยู่ในระบบแล้ว")
        item = InventoryItem(name, quantity, price)
        self._items[name] = item
        return item

    def restock(self, name: str, amount: int) -> int:
        if name not in self._items:
            raise KeyError(f"ไม่พบสินค้า '{name}' ในระบบ")
        if amount <= 0:
            raise ValueError("จำนวนที่เติมต้องมากกว่าศูนย์")
        self._items[name].quantity += amount
        return self._items[name].quantity

    def sell(self, name: str, amount: int) -> int:
        if name not in self._items:
            raise KeyError(f"ไม่พบสินค้า '{name}' ในระบบ")
        if amount <= 0:
            raise ValueError("จำนวนที่ขายต้องมากกว่าศูนย์")
        if self._items[name].quantity < amount:
            raise ValueError(
                f"สินค้า '{name}' คงเหลือ {self._items[name].quantity} ชิ้น "
                f"ไม่เพียงพอสำหรับการขาย {amount} ชิ้น"
            )
        self._items[name].quantity -= amount
        return self._items[name].quantity

    def get_total_value(self) -> float:
        return sum(item.quantity * item.price for item in self._items.values())
--------------------------------------------------------------------------------

ข้อกำหนด (Requirements & Constraints):
1. เมธอดมี signature: def sell_many(self, orders: dict[str, int]) -> dict[str, int]: คืนผลลัพธ์เป็น {ชื่อสินค้า: จำนวนคงเหลือล่าสุด}
2. คุณสมบัติ Atomicity: ทุกรายการต้องสำเร็จพร้อมกันทั้งหมด หรือหากมีรายการใดล้มเหลว (เช่น ไม่พบสินค้า หรือ สต็อกไม่พอ) ต้องยกเลิกทั้งหมด ห้ามตัดสต็อกสินค้าใดๆ เลย (Full Rollback / All-or-Nothing)
3. ชนิด Exception ต้องตรงตามเดิม:
   - raise KeyError(f"ไม่พบสินค้า '{name}' ในระบบ") หากไม่พบสินค้า
   - raise ValueError("จำนวนที่ขายต้องมากกว่าศูนย์") หากจำนวน <= 0
   - raise ValueError(...) หากสต็อกไม่เพียงพอ
4. ห้ามใช้ external library ภายนอก ใช้เฉพาะ pure Python เท่านั้น

เกณฑ์การทดสอบที่โค้ดต้องผ่าน (Acceptance Test Context):
- กรณีขายสำเร็จหลายรายการพร้อมกัน: สต็อกสินค้าทุกชิ้นถูกตัดอย่างถูกต้อง และคืนค่าคงเหลือถูกต้อง
- กรณีสินค้าชิ้นที่ 2 ในคำสั่งซื้อมีสต็อกไม่พอ: ต้อง raise ValueError และสต็อกของสินค้าชิ้นที่ 1 ต้องคงเดิม ไม่ถูกตัดออก
```

### ผลลัพธ์โค้ดที่ AI สร้างขึ้นในรอบที่ 2:
```python
    def sell_many(self, orders: dict[str, int]) -> dict[str, int]:
        """ขายหลายรายการพร้อมกันแบบ Atomic คืน {ชื่อสินค้า: จำนวนคงเหลือ}"""
        # ขั้นที่ 1: ตรวจสอบความถูกต้องและสต็อกของทุกรายการก่อนล่วงหน้า (Pre-validation phase)
        for name, amount in orders.items():
            if name not in self._items:
                raise KeyError(f"ไม่พบสินค้า '{name}' ในระบบ")
            if amount <= 0:
                raise ValueError("จำนวนที่ขายต้องมากกว่าศูนย์")
            if self._items[name].quantity < amount:
                raise ValueError(
                    f"สินค้า '{name}' คงเหลือ {self._items[name].quantity} ชิ้น "
                    f"ไม่เพียงพอสำหรับการขาย {amount} ชิ้น"
                )

        # ขั้นที่ 2: ดำเนินการตัดสต็อกเมื่อมั่นใจว่าทุกรายการผ่านเงื่อนไข 100% (Commit phase)
        result = {}
        for name, amount in orders.items():
            self._items[name].quantity -= amount
            result[name] = self._items[name].quantity

        return result
```

---

## 3. ตารางสรุปเปรียบเทียบผลลัพธ์ระหว่าง 2 รอบ

| มิติการประเมิน | รอบที่ 1: Prompt สั้นไร้บริบท | รอบที่ 2: Prompt แนบ Context ครบถ้วน |
| :--- | :--- | :--- |
| **ความเข้ากันได้ของโค้ด (Compatibility)** | ล้มเหลว (`self.items` ผิดโครงสร้าง ไม่ตรงกับ `self._items` และ `InventoryItem`) | สมบูรณ์แบบ (อ้างอิง `self._items[name].quantity` ตามโครงสร้างเดิมของโปรเจกต์) |
| **คุณสมบัติ Atomicity** | ไม่มี (หักสต็อกไปเรื่อย ๆ หากเจอ error กลางทาง ข้อมูลจะเสียหายทันที) | มีความสมบูรณ์ (แบ่งเป็น Validation Phase และ Commit Phase รับประกัน All-or-Nothing) |
| **ความสอดคล้องของ Exception** | ไม่ตรง (ใช้ `print()` แทนการ raise exception) | ตรงตามมาตรฐานเดิม 100% (raise `KeyError`, `ValueError` พร้อมข้อความเดียวกัน) |
| **ความพร้อมใช้งานและการทดสอบ** | รันไม่ผ่าน ต้องเขียนใหม่ทั้งหมด | ผ่าน Unit Test ทันทีโดยไม่ต้องแก้โค้ดซ้ำ |

---

## 4. บทวิเคราะห์และข้อสรุป: อะไรทำให้ผลลัพธ์แตกต่างกัน?

1. **Prompt คือ "เจตนา" (Intent) แต่ Context คือ "กรอบความจริง" (Ground Truth):**
   - ในรอบที่ 1 เราบอกแค่ Intent ว่าต้องการ "ขายหลายรายการ" ทำให้ LLM ต้องใช้การเดา (Hallucinate / Assume) โครงสร้างข้อมูลและเงื่อนไขทางธุรกิจขึ้นมาเอง ซึ่งโมเดลภาษาจะเลือกแนวทางที่สั้นที่สุดโดยไม่คำนึงถึง Edge Case
   - ในรอบที่ 2 เมื่อเราทำ **Context Engineering** โดยส่งมอบทั้ง **Source Code เดิม**, **ข้อจำกัดทางสถาปัตยกรรม (Atomicity)**, และ **Acceptance Test Cases** ตัวโมเดลภาษาไม่ต้องเดาโครงสร้าง แต่จะทำหน้าที่เป็น Optimization Engine ที่สังเคราะห์โค้ดให้อยู่ในกรอบข้อกำหนดอย่างแม่นยำ

2. **การป้องกันข้อผิดพลาดเชิงระบบด้วย Context:**
   - เรื่องสำคัญอย่าง Transaction Rollback และ Race Condition เป็นสิ่งที่ AI แทบจะไม่เขียนให้หากไม่ได้ระบุเป็น Context อย่างชัดเจน การออกแบบ Context ที่ครอบคลุมจึงเป็นกุญแจสำคัญที่สุดของ Software Engineering ในยุค AI เพื่อลดต้นทุนและเวลาในการ Debug ในภายหลัง
