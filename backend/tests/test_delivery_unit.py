import pytest

from app.core.enums import DeliveryStatus
from app.services.delivery_service import can_transition_delivery


@pytest.mark.parametrize(
    "current,target",
    [
        (DeliveryStatus.PENDIENTE, DeliveryStatus.ASIGNADO),
        (DeliveryStatus.PENDIENTE, DeliveryStatus.CANCELADO),
        (DeliveryStatus.ASIGNADO, DeliveryStatus.EN_CAMINO),
        (DeliveryStatus.ASIGNADO, DeliveryStatus.CANCELADO),
        (DeliveryStatus.EN_CAMINO, DeliveryStatus.ENTREGADO),
    ],
)
def test_valid_delivery_transitions(current, target):
    assert can_transition_delivery(current, target) is True


@pytest.mark.parametrize(
    "current,target",
    [
        (DeliveryStatus.PENDIENTE, DeliveryStatus.EN_CAMINO),
        (DeliveryStatus.PENDIENTE, DeliveryStatus.ENTREGADO),
        (DeliveryStatus.ASIGNADO, DeliveryStatus.ENTREGADO),
        (DeliveryStatus.EN_CAMINO, DeliveryStatus.CANCELADO),
        (DeliveryStatus.ENTREGADO, DeliveryStatus.CANCELADO),
        (DeliveryStatus.CANCELADO, DeliveryStatus.ASIGNADO),
    ],
)
def test_invalid_delivery_transitions(current, target):
    assert can_transition_delivery(current, target) is False
