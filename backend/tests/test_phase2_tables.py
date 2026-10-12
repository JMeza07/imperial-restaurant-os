from uuid import UUID, uuid4

import pytest

from app.core.enums import TableStatus
from app.schemas.table import TableCreate
from app.services.table_service import generate_qr_code


def test_generate_qr_code_returns_uuid4():
    qr = generate_qr_code()

    assert isinstance(qr, UUID)
    assert qr.version == 4


def test_table_create_requires_positive_number():
    with pytest.raises(ValueError):
        TableCreate(
            branch_id=uuid4(),
            number=0,
            capacity=4,
            status=TableStatus.LIBRE,
        )


def test_table_create_requires_positive_capacity():
    with pytest.raises(ValueError):
        TableCreate(
            branch_id=uuid4(),
            number=1,
            capacity=0,
            status=TableStatus.LIBRE,
        )


def test_table_create_defaults():
    payload = TableCreate(
        branch_id=uuid4(),
        number=5,
    )

    assert payload.capacity == 4
    assert payload.status == TableStatus.LIBRE
    assert payload.zone_id is None
