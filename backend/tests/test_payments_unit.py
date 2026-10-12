from decimal import Decimal

import pytest

from app.core.enums import OrderItemStatus
from app.services.payment_service import calculate_order_totals, can_close_order


def test_can_close_order_with_delivered_and_cancelled():
    statuses = [
        OrderItemStatus.ENTREGADO,
        OrderItemStatus.CANCELADO,
    ]

    assert can_close_order(statuses) is True


def test_cannot_close_order_with_pending_items():
    statuses = [
        OrderItemStatus.ENTREGADO,
        OrderItemStatus.EN_PREPARACION,
    ]

    assert can_close_order(statuses) is False


def test_cannot_close_empty_order():
    assert can_close_order([]) is False


def test_calculate_totals_with_tax_and_tip_rate():
    totals = calculate_order_totals(
        subtotal=Decimal("100000"),
        tax_rate=Decimal("0.08"),
        tip_rate=Decimal("0.10"),
    )

    assert totals["subtotal"] == Decimal("100000.00")
    assert totals["tax_amount"] == Decimal("8000.00")
    assert totals["tip_amount"] == Decimal("10000.00")
    assert totals["total"] == Decimal("118000.00")


def test_calculate_totals_with_tip_amount():
    totals = calculate_order_totals(
        subtotal=Decimal("50000"),
        tax_rate=Decimal("0.08"),
        tip_amount=Decimal("5000"),
    )

    assert totals["tax_amount"] == Decimal("4000.00")
    assert totals["tip_amount"] == Decimal("5000.00")
    assert totals["total"] == Decimal("59000.00")


def test_calculate_totals_with_delivery_and_discount():
    totals = calculate_order_totals(
        subtotal=Decimal("80000"),
        tax_rate=Decimal("0.08"),
        delivery_fee=Decimal("6000"),
        discount_amount=Decimal("10000"),
    )

    # subtotal 80000
    # tax 6400
    # delivery 6000
    # discount -10000
    assert totals["total"] == Decimal("82400.00")


def test_calculate_totals_rejects_tip_rate_and_tip_amount():
    with pytest.raises(ValueError):
        calculate_order_totals(
            subtotal=Decimal("100000"),
            tax_rate=Decimal("0.08"),
            tip_rate=Decimal("0.10"),
            tip_amount=Decimal("5000"),
        )


def test_calculate_totals_rejects_negative_subtotal():
    with pytest.raises(ValueError):
        calculate_order_totals(
            subtotal=Decimal("-100"),
            tax_rate=Decimal("0.08"),
        )
