# pricing_refactored.py
"""โมดูลคำนวณราคาและส่วนลดของระบบ Inventory (ฉบับ Refactored สะอาดและปลอดภัย)

ปรับปรุงโครงสร้างจาก pricing_legacy.py โดย:
1. กำหนด Named Constants แทน Magic Numbers
2. แยกฟังก์ชันย่อยตามหลัก Single Responsibility Principle (SRP)
3. ปรับปรุงชื่อตัวแปรให้อ่านง่าย สื่อความหมายชัดเจน
4. ใช้ 'is not None' และ 'is None' ตามมาตรฐาน PEP 8
5. คงพฤติกรรมเดิมและลำดับการคำนวณ (Calculation Sequence) 100%
"""

from __future__ import annotations

import datetime
from collections.abc import Sequence

# --- ค่าคงที่ทางธุรกิจ (Business Constants) ---
TAX_RATE: float = 0.07
BULK_TIER_2_QTY: int = 100
BULK_TIER_2_DISCOUNT_RATE: float = 0.10  # ลด 10% (คูณ 0.9)
BULK_TIER_1_QTY: int = 50
BULK_TIER_1_DISCOUNT_RATE: float = 0.05  # ลด 5% (คูณ 0.95)

MEMBER_DISCOUNT_RATE: float = 0.05       # สมาชิกลด 5% (คูณ 0.95)
POINTS_EARN_DIVISOR: int = 100           # 1 แต้มต่อทุก 100 บาท

COUPON_SAVE50_AMOUNT: float = 50.0
COUPON_HALF_MULTIPLIER: float = 0.5
COUPON_NEWYEAR_DISCOUNT_RATE: float = 0.20  # มกราคมลด 20% (คูณ 0.8)

# ตัวแปรสถานะส่วนกลาง (คงไว้เพื่อ Backward Compatibility กับระบบเดิม)
member_points: dict[str, int] = {}
LOG: list[tuple[str | None, float]] = []


def _calculate_items_subtotal(items: Sequence[tuple[str, int, float]]) -> float:
    """คำนวณยอดรวมราคาสินค้า พร้อมหักส่วนลดการซื้อจำนวนมาก (Bulk Discount)"""
    total_sub = 0.0
    for _name, quantity, unit_price in items:
        if quantity <= 0:
            continue

        item_total = quantity * unit_price
        if quantity >= BULK_TIER_2_QTY:
            item_total *= (1.0 - BULK_TIER_2_DISCOUNT_RATE)
        elif quantity >= BULK_TIER_1_QTY:
            item_total *= (1.0 - BULK_TIER_1_DISCOUNT_RATE)

        total_sub += item_total
    return total_sub


def _apply_member_benefit(total: float, member: str | None) -> float:
    """คำนวณส่วนลดสมาชิก 5% และสะสมแต้ม 1 แต้มต่อ 100 บาท"""
    if member is None:
        return total

    if member not in member_points:
        member_points[member] = 0

    discounted_total = total * (1.0 - MEMBER_DISCOUNT_RATE)
    earned_points = int(discounted_total / POINTS_EARN_DIVISOR)
    member_points[member] += earned_points

    return discounted_total


def _apply_coupon(total: float, coupon: str | None, today: datetime.date | None) -> float:
    """คำนวณส่วนลดคูปองตามเงื่อนไข (SAVE50, HALF, NEWYEAR)"""
    if coupon is None:
        return total

    discounted_total = total
    if coupon == "SAVE50":
        discounted_total -= COUPON_SAVE50_AMOUNT
    elif coupon == "HALF":
        discounted_total *= COUPON_HALF_MULTIPLIER
    elif coupon == "NEWYEAR":
        current_date = datetime.date.today() if today is None else today
        if current_date.month == 1:
            discounted_total *= (1.0 - COUPON_NEWYEAR_DISCOUNT_RATE)

    return max(0.0, discounted_total)


def calc(
    items: Sequence[tuple[str, int, float]],
    member: str | None = None,
    coupon: str | None = None,
    today: datetime.date | None = None,
) -> float:
    """คำนวณราคาสุทธิของสินค้าพร้อมภาษีและบันทึกประวัติการคำนวณ"""
    # 1. ยอดรวมสินค้าและส่วนลดจำนวนมาก
    total = _calculate_items_subtotal(items)

    # 2. ส่วนลดสมาชิกและสะสมแต้ม
    total = _apply_member_benefit(total, member)

    # 3. ส่วนลดคูปองและตรวจสอบยอดไม่ติดลบ
    total = _apply_coupon(total, coupon, today)

    # 4. คำนวณภาษีมูลค่าเพิ่ม (VAT 7%) และปัดเศษทศนิยม 2 ตำแหน่ง
    total_with_tax = total + (total * TAX_RATE)
    final_price = round(total_with_tax, 2)

    # 5. บันทึก Audit Log
    LOG.append((member, final_price))

    return final_price
