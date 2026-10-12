import pytest

from app.core.enums import ShiftStatus
from app.services.turnos_service import can_transition_shift


@pytest.mark.parametrize(
    "current,target",
    [
        (ShiftStatus.PROGRAMADO, ShiftStatus.CONFIRMADO),
        (ShiftStatus.PROGRAMADO, ShiftStatus.AUSENTE),
        (ShiftStatus.PROGRAMADO, ShiftStatus.CANCELADO),
        (ShiftStatus.CONFIRMADO, ShiftStatus.EN_TURNO),
        (ShiftStatus.CONFIRMADO, ShiftStatus.AUSENTE),
        (ShiftStatus.CONFIRMADO, ShiftStatus.CANCELADO),
        (ShiftStatus.EN_TURNO, ShiftStatus.EN_DESCANSO),
        (ShiftStatus.EN_TURNO, ShiftStatus.FINALIZADO),
        (ShiftStatus.EN_DESCANSO, ShiftStatus.EN_TURNO),
    ],
)
def test_valid_shift_transitions(current, target):
    assert can_transition_shift(current, target) is True


@pytest.mark.parametrize(
    "current,target",
    [
        (ShiftStatus.PROGRAMADO, ShiftStatus.EN_TURNO),
        (ShiftStatus.PROGRAMADO, ShiftStatus.FINALIZADO),
        (ShiftStatus.CONFIRMADO, ShiftStatus.FINALIZADO),
        (ShiftStatus.EN_TURNO, ShiftStatus.CANCELADO),
        (ShiftStatus.EN_DESCANSO, ShiftStatus.FINALIZADO),
        (ShiftStatus.FINALIZADO, ShiftStatus.EN_TURNO),
        (ShiftStatus.AUSENTE, ShiftStatus.CONFIRMADO),
        (ShiftStatus.CANCELADO, ShiftStatus.PROGRAMADO),
    ],
)
def test_invalid_shift_transitions(current, target):
    assert can_transition_shift(current, target) is False
