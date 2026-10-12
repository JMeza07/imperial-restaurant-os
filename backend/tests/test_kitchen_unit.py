import pytest

from app.core.enums import OrderItemStatus, OrderType, UserRole
from app.services.kitchen_service import can_change_item_status


@pytest.mark.parametrize(
    "order_type,current_status,target_status,role",
    [
        (
            OrderType.MESA,
            OrderItemStatus.RECIBIDO,
            OrderItemStatus.EN_PREPARACION,
            UserRole.COCINERO,
        ),
        (
            OrderType.MESA,
            OrderItemStatus.EN_PREPARACION,
            OrderItemStatus.LISTO,
            UserRole.COCINERO,
        ),
        (
            OrderType.MESA,
            OrderItemStatus.LISTO,
            OrderItemStatus.ENTREGADO,
            UserRole.MESERO,
        ),
        (
            OrderType.MESA,
            OrderItemStatus.RECIBIDO,
            OrderItemStatus.CANCELADO,
            UserRole.ADMIN,
        ),
        (
            OrderType.DOMICILIO,
            OrderItemStatus.LISTO,
            OrderItemStatus.ENTREGADO,
            UserRole.DOMICILIARIO,
        ),
        (
            OrderType.MESA,
            OrderItemStatus.EN_PREPARACION,
            OrderItemStatus.LISTO,
            UserRole.ADMIN,
        ),
        (
            OrderType.MESA,
            OrderItemStatus.LISTO,
            OrderItemStatus.ENTREGADO,
            UserRole.ADMIN,
        ),
    ],
)
def test_can_change_item_status_valid(
    order_type,
    current_status,
    target_status,
    role,
):
    assert can_change_item_status(
        order_type,
        current_status,
        target_status,
        role,
    ) is True


@pytest.mark.parametrize(
    "order_type,current_status,target_status,role",
    [
        (
            OrderType.MESA,
            OrderItemStatus.RECIBIDO,
            OrderItemStatus.LISTO,
            UserRole.COCINERO,
        ),
        (
            OrderType.MESA,
            OrderItemStatus.RECIBIDO,
            OrderItemStatus.ENTREGADO,
            UserRole.COCINERO,
        ),
        (
            OrderType.MESA,
            OrderItemStatus.LISTO,
            OrderItemStatus.ENTREGADO,
            UserRole.COCINERO,
        ),
        (
            OrderType.MESA,
            OrderItemStatus.LISTO,
            OrderItemStatus.ENTREGADO,
            UserRole.DOMICILIARIO,
        ),
        (
            OrderType.DOMICILIO,
            OrderItemStatus.LISTO,
            OrderItemStatus.ENTREGADO,
            UserRole.MESERO,
        ),
        (
            OrderType.MESA,
            OrderItemStatus.EN_PREPARACION,
            OrderItemStatus.CANCELADO,
            UserRole.ADMIN,
        ),
        (
            OrderType.MESA,
            OrderItemStatus.ENTREGADO,
            OrderItemStatus.CANCELADO,
            UserRole.ADMIN,
        ),
        (
            OrderType.MESA,
            OrderItemStatus.RECIBIDO,
            OrderItemStatus.CANCELADO,
            UserRole.COCINERO,
        ),
        (
            OrderType.MESA,
            OrderItemStatus.RECIBIDO,
            OrderItemStatus.EN_PREPARACION,
            UserRole.MESERO,
        ),
    ],
)
def test_can_change_item_status_invalid(
    order_type,
    current_status,
    target_status,
    role,
):
    assert can_change_item_status(
        order_type,
        current_status,
        target_status,
        role,
    ) is False
