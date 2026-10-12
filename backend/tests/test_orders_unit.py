from decimal import Decimal

import pytest

from app.core.enums import ModificationAction, OrderItemStatus
from app.services.order_service import calculate_unit_price


def test_price_without_modifications():
    base_price = Decimal("22000")

    result = calculate_unit_price(base_price, [])

    assert result == Decimal("22000")


def test_price_with_added_ingredient():
    base_price = Decimal("22000")

    modifications = [
        (ModificationAction.AGREGAR, Decimal("5000")),
    ]

    result = calculate_unit_price(base_price, modifications)

    assert result == Decimal("27000")


def test_removed_ingredient_does_not_reduce_price():
    base_price = Decimal("22000")

    modifications = [
        (ModificationAction.QUITAR, Decimal("0")),
    ]

    result = calculate_unit_price(base_price, modifications)

    assert result == Decimal("22000")


def test_price_with_multiple_added_ingredients():
    base_price = Decimal("22000")

    modifications = [
        (ModificationAction.AGREGAR, Decimal("5000")),
        (ModificationAction.AGREGAR, Decimal("2000")),
        (ModificationAction.QUITAR, Decimal("0")),
    ]

    result = calculate_unit_price(base_price, modifications)

    assert result == Decimal("29000")


@pytest.mark.parametrize(
    "origin,destination",
    [
        (OrderItemStatus.RECIBIDO, OrderItemStatus.EN_PREPARACION),
        (OrderItemStatus.EN_PREPARACION, OrderItemStatus.LISTO),
        (OrderItemStatus.LISTO, OrderItemStatus.ENTREGADO),
        (OrderItemStatus.RECIBIDO, OrderItemStatus.CANCELADO),
    ],
)
def test_valid_state_transitions(origin, destination):
    assert origin.can_transition_to(destination) is True


@pytest.mark.parametrize(
    "origin,destination",
    [
        (OrderItemStatus.RECIBIDO, OrderItemStatus.LISTO),
        (OrderItemStatus.RECIBIDO, OrderItemStatus.ENTREGADO),
        (OrderItemStatus.EN_PREPARACION, OrderItemStatus.CANCELADO),
        (OrderItemStatus.LISTO, OrderItemStatus.EN_PREPARACION),
        (OrderItemStatus.ENTREGADO, OrderItemStatus.CANCELADO),
        (OrderItemStatus.CANCELADO, OrderItemStatus.RECIBIDO),
    ],
)
def test_invalid_state_transitions(origin, destination):
    assert origin.can_transition_to(destination) is False
