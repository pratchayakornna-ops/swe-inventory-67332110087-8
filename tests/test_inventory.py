# tests/test_inventory.py
import pytest

from inventory import Inventory, InventoryItem

# ==============================================================================
# ขั้นที่ 2: TDD Test Cases สำหรับเมธอด low_stock_items (ครบ 6 กรณีตามกำหนด)
# ==============================================================================

def test_low_stock_items_all_above_threshold():
    """กรณีที่ 1: สินค้าทุกรายการมีจำนวนมากกว่า threshold -> ต้องคืน list ว่าง []"""
    inv = Inventory()
    inv.add_item("Keyboard", 10, 1000.0)
    inv.add_item("Mouse", 15, 500.0)
    assert inv.low_stock_items(5) == []


def test_low_stock_items_exactly_at_threshold():
    """กรณีที่ 2: มีสินค้าที่จำนวนเท่ากับ threshold พอดี -> ต้องถูกนับรวมด้วย (<= threshold)"""
    inv = Inventory()
    inv.add_item("Monitor", 5, 4500.0)
    inv.add_item("Laptop", 12, 25000.0)
    assert inv.low_stock_items(5) == ["Monitor"]


def test_low_stock_items_multiple_sorted_alphabetically():
    """กรณีที่ 3: มีสินค้าเข้าเกณฑ์หลายรายการ -> ผลลัพธ์ต้องเรียงตามชื่อตัวอักษร ไม่ใช่ตามลำดับที่เพิ่ม"""
    inv = Inventory()
    inv.add_item("USB Hub", 2, 350.0)
    inv.add_item("Cable", 3, 120.0)
    inv.add_item("Adapter", 1, 250.0)
    inv.add_item("Desk Mat", 20, 400.0)
    assert inv.low_stock_items(5) == ["Adapter", "Cable", "USB Hub"]


def test_low_stock_items_empty_inventory():
    """กรณีที่ 4: คลังว่างเปล่า -> ต้องคืน list ว่าง [] โดยไม่เกิด error หรือ crash"""
    inv = Inventory()
    assert inv.low_stock_items(10) == []


def test_low_stock_items_threshold_zero():
    """กรณีที่ 5: threshold เป็น 0 -> คืนเฉพาะสินค้าที่มีคงเหลือ 0 ชิ้นพอดี"""
    inv = Inventory()
    inv.add_item("Out of Stock Item", 0, 99.0)
    inv.add_item("In Stock Item", 1, 99.0)
    assert inv.low_stock_items(0) == ["Out of Stock Item"]


def test_low_stock_items_negative_threshold():
    """กรณีที่ 6: threshold ติดลบ -> คืน list ว่าง [] เนื่องจากสินค้าในระบบมีจำนวนไม่ติดลบ"""
    inv = Inventory()
    inv.add_item("Webcam", 0, 890.0)
    inv.add_item("Speaker", 4, 1200.0)
    assert inv.low_stock_items(-1) == []


# ==============================================================================
# ขั้นที่ 4: Unit Test สำหรับเมธอด sell (จับ Test ที่ AI ขาด แล้วเขียนเสริม)
# ==============================================================================

# --- กรณีปกติที่ AI ทั่วไปสร้างให้ (Happy Path) ---
def test_sell_basic_happy_path():
    """กรณีปกติที่ AI ให้มา: ขายสินค้าปกติ จำนวนคงเหลือลดลงถูกต้อง"""
    inv = Inventory()
    inv.add_item("Keyboard", 10, 1000.0)
    remaining = inv.sell("Keyboard", 3)
    assert remaining == 7
    assert inv._items["Keyboard"].quantity == 7


# --- Test Cases เสริม 5 กรณีที่มนุษย์เขียนเพิ่มเพื่อปิด Gap ---
def test_sell_boundary_exact_all_quantity():
    """กลุ่มค่าขอบ: ขายสินค้าเท่ากับจำนวนคงเหลือทั้งหมดพอดี -> ต้องเหลือ 0 ชิ้น ไม่เกิด error"""
    inv = Inventory()
    inv.add_item("Mouse", 5, 450.0)
    remaining = inv.sell("Mouse", 5)
    assert remaining == 0
    assert inv._items["Mouse"].quantity == 0


def test_sell_invalid_zero_quantity_raises_value_error():
    """กลุ่มค่าที่ไม่ควรรับ: ขายจำนวน 0 ชิ้น -> ต้อง raise ValueError("จำนวนที่ขายต้องมากกว่าศูนย์")"""
    inv = Inventory()
    inv.add_item("Mouse", 5, 450.0)
    with pytest.raises(ValueError, match="จำนวนที่ขายต้องมากกว่าศูนย์"):
        inv.sell("Mouse", 0)
    # ตรวจสอบว่าสต็อกไม่เปลี่ยน
    assert inv._items["Mouse"].quantity == 5


def test_sell_invalid_negative_quantity_raises_value_error():
    """กลุ่มค่าที่ไม่ควรรับ: ขายจำนวนติดลบ -> ต้อง raise ValueError("จำนวนที่ขายต้องมากกว่าศูนย์")"""
    inv = Inventory()
    inv.add_item("Mouse", 5, 450.0)
    with pytest.raises(ValueError, match="จำนวนที่ขายต้องมากกว่าศูนย์"):
        inv.sell("Mouse", -3)
    assert inv._items["Mouse"].quantity == 5


def test_sell_exceed_available_quantity_raises_value_error():
    """กลุ่มค่าที่ไม่ควรรับ: ขายเกินจำนวนคงเหลือ -> ต้อง raise ValueError พร้อมบอกข้อความชัดเจน"""
    inv = Inventory()
    inv.add_item("Monitor", 3, 5000.0)
    with pytest.raises(ValueError, match="ไม่เพียงพอสำหรับการขาย 4 ชิ้น"):
        inv.sell("Monitor", 4)
    # สต็อกต้องคงเดิม ไม่ถูกตัด
    assert inv._items["Monitor"].quantity == 3


def test_sell_non_existent_item_raises_key_error():
    """กลุ่มเส้นทาง Error: ขายสินค้าที่ไม่มีอยู่ในคลัง -> ต้อง raise KeyError"""
    inv = Inventory()
    inv.add_item("Existing Item", 10, 100.0)
    with pytest.raises(KeyError, match="ไม่พบสินค้า 'Ghost Item' ในระบบ"):
        inv.sell("Ghost Item", 1)


# ==============================================================================
# Additional Tests for 100% Code Coverage of Inventory & InventoryItem
# ==============================================================================

def test_inventory_item_validations():
    """ทดสอบ Validation ของ InventoryItem ในกรณีชื่อว่างเปล่า, จำนวนติดลบ, และราคา <= 0"""
    with pytest.raises(ValueError, match="ชื่อสินค้าต้องไม่ว่างเปล่า"):
        InventoryItem("", 10, 100.0)
    with pytest.raises(ValueError, match="ชื่อสินค้าต้องไม่ว่างเปล่า"):
        InventoryItem("   ", 10, 100.0)
    with pytest.raises(ValueError, match="จำนวนสินค้าต้องไม่ติดลบ"):
        InventoryItem("Item", -1, 100.0)
    with pytest.raises(ValueError, match="ราคาต้องมากกว่าศูนย์"):
        InventoryItem("Item", 10, 0.0)
    with pytest.raises(ValueError, match="ราคาต้องมากกว่าศูนย์"):
        InventoryItem("Item", 10, -50.0)


def test_inventory_add_item_duplicate_raises_value_error():
    """ทดสอบเพิ่มสินค้าซ้ำชื่อเดิม"""
    inv = Inventory()
    inv.add_item("Item1", 5, 100.0)
    with pytest.raises(ValueError, match="สินค้า 'Item1' มีอยู่ในระบบแล้ว"):
        inv.add_item("Item1", 10, 200.0)


def test_inventory_restock():
    """ทดสอบการเติมสต็อกสินค้า ทั้งกรณีปกติ, จำนวน <= 0, และไม่พบสินค้า"""
    inv = Inventory()
    inv.add_item("Item1", 5, 100.0)
    assert inv.restock("Item1", 10) == 15
    assert inv._items["Item1"].quantity == 15

    with pytest.raises(ValueError, match="จำนวนที่เติมต้องมากกว่าศูนย์"):
        inv.restock("Item1", 0)
    with pytest.raises(ValueError, match="จำนวนที่เติมต้องมากกว่าศูนย์"):
        inv.restock("Item1", -5)
    with pytest.raises(KeyError, match="ไม่พบสินค้า 'NonExistent' ในระบบ"):
        inv.restock("NonExistent", 5)


def test_inventory_get_total_value():
    """ทดสอบการคำนวณมูลค่ารวมของสินค้าในคลัง"""
    inv = Inventory()
    assert inv.get_total_value() == 0.0
    inv.add_item("ItemA", 2, 50.0)    # 100.0
    inv.add_item("ItemB", 5, 200.0)   # 1000.0
    assert inv.get_total_value() == 1100.0
