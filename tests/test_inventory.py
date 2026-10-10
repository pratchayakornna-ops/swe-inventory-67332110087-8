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
    # threshold = 5 (ไม่มีสินค้าใดมีสต็อก <= 5)
    assert inv.low_stock_items(5) == []


def test_low_stock_items_exactly_at_threshold():
    """กรณีที่ 2: มีสินค้าที่จำนวนเท่ากับ threshold พอดี -> ต้องถูกนับรวมด้วย (<= threshold)"""
    inv = Inventory()
    inv.add_item("Monitor", 5, 4500.0)
    inv.add_item("Laptop", 12, 25000.0)
    # threshold = 5 (Monitor มี 5 ชิ้น ต้องติดมาด้วย)
    assert inv.low_stock_items(5) == ["Monitor"]


def test_low_stock_items_multiple_sorted_alphabetically():
    """กรณีที่ 3: มีสินค้าเข้าเกณฑ์หลายรายการ -> ผลลัพธ์ต้องเรียงตามชื่อตัวอักษร ไม่ใช่ตามลำดับที่เพิ่ม"""
    inv = Inventory()
    # เพิ่มสินค้าโดยจงใจไม่เรียงลำดับตัวอักษร: USB Hub (U), Cable (C), Adapter (A)
    inv.add_item("USB Hub", 2, 350.0)
    inv.add_item("Cable", 3, 120.0)
    inv.add_item("Adapter", 1, 250.0)
    inv.add_item("Desk Mat", 20, 400.0)  # ตัวนี้ไม่เข้าเกณฑ์

    # รายการที่เข้าเกณฑ์ (<= 5) คือ Adapter, Cable, USB Hub
    # ต้องเรียงตามตัวอักษร: ["Adapter", "Cable", "USB Hub"]
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
    # threshold ติดลบ (-1) ไม่มีสินค้าใดมีสต็อก <= -1
    assert inv.low_stock_items(-1) == []
