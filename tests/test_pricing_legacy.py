# tests/test_pricing_legacy.py
import datetime

import pytest

import pricing_legacy
import pricing_refactored


@pytest.fixture(autouse=True)
def reset_global_states():
    """Fixture ล้างค่า Global Mutable State ของทั้งสองโมดูลก่อนและหลังทุก test"""
    pricing_legacy.member_points.clear()
    pricing_legacy.LOG.clear()
    pricing_refactored.member_points.clear()
    pricing_refactored.LOG.clear()
    yield
    pricing_legacy.member_points.clear()
    pricing_legacy.LOG.clear()
    pricing_refactored.member_points.clear()
    pricing_refactored.LOG.clear()


# Parameterize ทั้ง pricing_legacy และ pricing_refactored เพื่อพิสูจน์ว่าพฤติกรรมทั้ง 2 โมดูลเหมือนกัน 100%
@pytest.fixture(params=[pricing_legacy, pricing_refactored], ids=["legacy", "refactored"])
def pricing_module(request):
    return request.param


# ==============================================================================
# Characterization Tests พิสูจน์พฤติกรรมของทั้ง pricing_legacy และ pricing_refactored
# ==============================================================================

def test_calc_normal_single_item(pricing_module):
    """กลุ่มราคาปกติ: สินค้า 1 รายการ จำนวนน้อย (2 ชิ้น ชิ้นละ 100 บ.) ไม่ใช้สิทธิ์ใดๆ -> 200 + 7% VAT = 214.0"""
    result = pricing_module.calc([("Notebook", 2, 100.0)])
    assert result == 214.0


def test_calc_bulk_discount_threshold_50(pricing_module):
    """กลุ่มซื้อจำนวนมาก: 50 ชิ้นพอดี ได้ลด 5% -> (50 * 100 * 0.95) = 4,750 + 7% VAT = 5,082.5"""
    result = pricing_module.calc([("Pen", 50, 100.0)])
    assert result == 5082.5


def test_calc_bulk_discount_threshold_100(pricing_module):
    """กลุ่มซื้อจำนวนมาก: 100 ชิ้นพอดี ได้ลด 10% -> (100 * 100 * 0.90) = 9,000 + 7% VAT = 9,630.0"""
    result = pricing_module.calc([("Pencil", 100, 100.0)])
    assert result == 9630.0


def test_calc_zero_quantity_item(pricing_module):
    """กลุ่มจำนวนเป็นศูนย์: รายการที่มีจำนวน 0 ชิ้นจะถูกข้าม (continue) -> ยอดรวม 0.0"""
    result = pricing_module.calc([("Free Item", 0, 500.0)])
    assert result == 0.0


def test_calc_member_discount_and_points(pricing_module):
    """กลุ่มสมาชิก: สมาชิกลด 5% และสะสมแต้ม 1 แต้มต่อ 100 บาท -> ยอด 1,016.5 และแต้มสะสม = 9"""
    result = pricing_module.calc([("Hard Drive", 1, 1000.0)], member="somchai")
    assert result == 1016.5
    assert pricing_module.member_points["somchai"] == 9


def test_calc_coupon_save50(pricing_module):
    """กลุ่มคูปอง: คูปอง SAVE50 หักลด 50 บาท -> (100 - 50) = 50 + 7% VAT = 53.5"""
    result = pricing_module.calc([("Mouse", 1, 100.0)], coupon="SAVE50")
    assert result == 53.5


def test_calc_coupon_half(pricing_module):
    """กลุ่มคูปอง: คูปอง HALF ลด 50% -> (100 * 0.5) = 50 + 7% VAT = 53.5"""
    result = pricing_module.calc([("Keyboard", 1, 100.0)], coupon="HALF")
    assert result == 53.5


def test_calc_coupon_newyear_in_january(pricing_module):
    """กลุ่มคูปอง: คูปอง NEWYEAR ในเดือนมกราคม ลด 20% -> (100 * 0.8) = 80 + 7% VAT = 85.6"""
    jan_date = datetime.date(2026, 1, 15)
    result = pricing_module.calc([("Flash Drive", 1, 100.0)], coupon="NEWYEAR", today=jan_date)
    assert result == 85.6


def test_calc_coupon_newyear_outside_january(pricing_module):
    """กลุ่มคูปอง: คูปอง NEWYEAR นอกเดือนมกราคม (เช่น ก.พ.) ไม่ได้ส่วนลด -> 100 + 7% VAT = 107.0"""
    feb_date = datetime.date(2026, 2, 20)
    result = pricing_module.calc([("Flash Drive", 1, 100.0)], coupon="NEWYEAR", today=feb_date)
    assert result == 107.0


def test_calc_coupon_newyear_default_today(pricing_module):
    """กลุ่มคูปอง: คูปอง NEWYEAR โดยไม่ระบุ today (ใช้ datetime.date.today())"""
    result = pricing_module.calc([("Flash Drive", 1, 100.0)], coupon="NEWYEAR")
    assert isinstance(result, float)


def test_calc_discount_greater_than_price_capped_at_zero(pricing_module):
    """กลุ่มยอดติดลบ: ส่วนลดคูปองมากกว่าราคาสินค้า (30 - 50 = -20) -> ปัดเป็น 0.0 ไม่ติดลบ"""
    result = pricing_module.calc([("Small Cable", 1, 30.0)], coupon="SAVE50")
    assert result == 0.0


def test_calc_side_effect_logging(pricing_module):
    """กลุ่มค่าที่ฟังก์ชันเก็บไว้: ฟังก์ชันต้องบันทึกประวัติ (member, total) ลงใน LOG เสมอ"""
    res1 = pricing_module.calc([("Item1", 1, 100.0)], member="alice")
    res2 = pricing_module.calc([("Item2", 2, 50.0)])
    assert pricing_module.LOG == [("alice", res1), (None, res2)]
