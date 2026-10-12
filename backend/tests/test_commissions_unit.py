from decimal import Decimal

from app.core.enums import CommissionRuleType
from app.services.commissions_service import calculate_commission_amount


def test_percent_net_sales():
    result = calculate_commission_amount(
        rule_type=CommissionRuleType.PERCENT_NET_SALES,
        value=Decimal("3"),
        base_amount=Decimal("100000"),
    )

    assert result == Decimal("3000.00")


def test_fixed_per_order():
    result = calculate_commission_amount(
        rule_type=CommissionRuleType.FIXED_PER_ORDER,
        value=Decimal("1500"),
    )

    assert result == Decimal("1500.00")


def test_fixed_per_item_multiplies_quantity():
    result = calculate_commission_amount(
        rule_type=CommissionRuleType.FIXED_PER_ITEM,
        value=Decimal("500"),
        quantity=3,
    )

    assert result == Decimal("1500.00")


def test_percent_item_sales():
    result = calculate_commission_amount(
        rule_type=CommissionRuleType.PERCENT_ITEM_SALES,
        value=Decimal("10"),
        base_amount=Decimal("22000"),
    )

    assert result == Decimal("2200.00")
