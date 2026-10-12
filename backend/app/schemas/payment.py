from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.enums import (
    CashSessionStatus,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
)


class CloseOrderRequest(BaseModel):
    codigo_qr: Optional[str] = None
    tax_rate: Optional[Decimal] = Field(default=None, ge=0, le=1)
    tip_rate: Optional[Decimal] = Field(default=None, ge=0, le=1)
    tip_amount: Optional[Decimal] = Field(default=None, ge=0)
    delivery_fee: Optional[Decimal] = Field(default=None, ge=0)
    auto_deliver_pending: Optional[bool] = True

    @model_validator(mode="after")
    def validate_tip(self):
        if self.tip_amount is not None and self.tip_rate is not None:
            raise ValueError(
                "No se puede indicar tip_amount y tip_rate al mismo tiempo"
            )

        return self


class PaymentCreateRequest(BaseModel):
    codigo_qr: Optional[str] = None
    payment_method: PaymentMethod
    amount: Decimal = Field(gt=0)
    reference: Optional[str] = Field(default=None, max_length=255)
    note: Optional[str] = Field(default=None, max_length=1000)


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID

    payment_method: PaymentMethod
    status: PaymentStatus
    amount: Decimal
    reference: Optional[str]
    note: Optional[str]

    cash_session_id: Optional[UUID]
    registered_by_user_id: Optional[UUID]

    created_at: datetime
    approved_at: Optional[datetime]

    order_status: Optional[OrderStatus]
    order_total: Optional[Decimal]
    order_total_paid: Optional[Decimal]
    order_saldo_pendiente: Optional[Decimal]


class CashSessionOpenRequest(BaseModel):
    branch_id: Optional[UUID] = None
    opening_amount: Decimal = Field(default=Decimal("0"), ge=0)
    notes: Optional[str] = Field(default=None, max_length=2000)


class CashSessionCloseRequest(BaseModel):
    closing_amount: Decimal = Field(ge=0)
    notes: Optional[str] = Field(default=None, max_length=2000)


class CashSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    branch_id: Optional[UUID]

    opened_by_user_id: Optional[UUID]
    closed_by_user_id: Optional[UUID]

    status: CashSessionStatus

    opening_amount: Decimal
    closing_amount: Optional[Decimal]
    expected_amount: Optional[Decimal]

    notes: Optional[str]

    opened_at: datetime
    closed_at: Optional[datetime]

    created_at: datetime
    updated_at: datetime
