from datetime import date

import pytest

from app.services.reports_service import get_date_range


def test_default_date_range_uses_last_30_days():
    start_dt, end_dt, date_from, date_to = get_date_range()

    assert date_to >= date_from
    assert start_dt <= end_dt


def test_explicit_date_range():
    start_dt, end_dt, date_from, date_to = get_date_range(
        date_from=date(2026, 10, 1),
        date_to=date(2026, 10, 31),
    )

    assert date_from == date(2026, 10, 1)
    assert date_to == date(2026, 10, 31)
    assert start_dt < end_dt


def test_invalid_date_range():
    with pytest.raises(Exception):
        get_date_range(
            date_from=date(2026, 10, 31),
            date_to=date(2026, 10, 1),
        )
