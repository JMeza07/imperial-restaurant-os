from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.enums import (
    CommissionEventStatus,
    CommissionPeriodStatus,
    CommissionPayoutStatus,
    CommissionRuleType,
    PaymentMethod,
    UserRole,
)


class CommissionRuleCreate(BaseModel):
    name: str = Field(min_length=3, max_length=255)
    role: UserRole
    rule_type: CommissionRuleType
    value: Decimal = Field(ge=0)
    cap_per_order: Optional[Decimal] = Field(default=None, ge=0)
    cap_per_period: Optional[Decimal] = Field(default=None, ge=0)
    conditions: Dict = {}
    starts_at: Optional[date] = None
    ends_at: Optional[date] = None
    priority: int = 0
    is_active: bool = True

    @model_validator(mode="after")
    def validate_value(self):
        percent_types = {
            CommissionRuleType.PERCENT_NET_SALES,
            CommissionRuleType.PERCENT_ITEM_SALES,
        }

        if self.rule_type in percent_types and self.value > Decimal("100"):
            raise ValueError(
                "El valor de una regla porcentual no puede ser mayor que 100"
            )

        return self


class CommissionRuleUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=3, max_length=255)
    role: Optional[UserRole] = None
    rule_type: Optional[CommissionRuleType] = None
    value: Optional[Decimal] = Field(default=None, ge=0)
    cap_per_order: Optional[Decimal] = Field(default=None, ge=0)
    cap_per_period: Optional[Decimal] = Field(default=None, ge=0)
    conditions: Optional[Dict] = None
    starts_at: Optional[date] = None
    ends_at: Optional[date] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


class CommissionRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    role: str
    rule_type: CommissionRuleType
    value: Decimal
    cap_per_order: Optional[Decimal]
    cap_per_period: Optional[Decimal]
    conditions: Dict
    starts_at: Optional[date]
    ends_at: Optional[date]
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CommissionPeriodCreate(BaseModel):
    branch_id: Optional[UUID] = None
    name: str = Field(min_length=3, max_length=255)
    start_date: date
    end_date: date
    notes: Optional[str] = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date debe ser mayor o igual que start_date")

        return self


class CommissionPeriodRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    branch_id: Optional[UUID]
    branch_name: Optional[str]
    name: str
    start_date: date
    end_date: date
    status: CommissionPeriodStatus
    calculated_at: Optional[datetime]
    approved_at: Optional[datetime]
    paid_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class CommissionEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    period_id: UUID
    rule_id: UUID
    employee_id: UUID
    order_id: Optional[UUID]
    order_item_id: Optional[UUID]

    employee_name: Optional[str]
    rule_name: Optional[str]

    base_amount: Decimal
    amount: Decimal
    status: CommissionEventStatus

    dedup_key: str
    detail: Dict

    created_at: datetime
    updated_at: datetime


class CommissionPayoutRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    period_id: UUID
    employee_id: UUID

    employee_name: Optional[str]

    amount: Decimal
    status: CommissionPayoutStatus

    payment_method: Optional[str]
    reference: Optional[str]
    paid_at: Optional[datetime]

    created_at: datetime
    updated_at: datetime


class AssignWaiterRequest(BaseModel):
    waiter_id: UUID


class PayoutPayRequest(BaseModel):
    payment_method: PaymentMethod
    reference: Optional[str] = Field(default=None, max_length=255)


class SurveyCreateRequest(BaseModel):
    food_score: int = Field(ge=1, le=5)
    service_score: int = Field(ge=1, le=5)
    general_score: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=2000)

    codigo_qr: Optional[str] = None
    telefono: Optional[str] = None


class SurveyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    food_score: int
    service_score: int
    general_score: int
    comment: Optional[str]
    created_at: datetime
