from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import (
    ModificationAction,
    OrderChannel,
    OrderItemStatus,
    OrderStatus,
    OrderType,
)


class ModificationRequest(BaseModel):
    ingredient_id: UUID
    action: ModificationAction


class OrderItemRequest(BaseModel):
    dish_id: UUID
    quantity: int = Field(gt=0)
    observations: Optional[str] = Field(default=None, max_length=1000)
    modifications: List[ModificationRequest] = []


class CreateOrderRequest(BaseModel):
    codigo_qr: str
    customer_name: Optional[str] = Field(default=None, max_length=255)
    customer_phone: Optional[str] = Field(default=None, max_length=50)
    items: List[OrderItemRequest] = Field(min_length=1)


class ModificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ingredient_id: UUID
    ingredient_name: str
    action: ModificationAction
    extra_cost: Decimal
    created_at: datetime


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dish_id: UUID
    dish_name: Optional[str]
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    status: OrderItemStatus
    observations: Optional[str]

    modifications: List[ModificationRead] = []

    created_at: datetime
    prepared_at: Optional[datetime]
    ready_at: Optional[datetime]
    delivered_at: Optional[datetime]
    cancelled_at: Optional[datetime]

    prepared_by_user_id: Optional[UUID] = None
    preparer_name: Optional[str] = None


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_code: Optional[str]

    branch_id: Optional[UUID]
    table_id: Optional[UUID]
    table_number: Optional[int]

    order_type: OrderType
    status: OrderStatus
    channel: OrderChannel

    customer_name: Optional[str]
    customer_phone: Optional[str]
    customer_address: Optional[str]

    notes: Optional[str]

    items: List[OrderItemRead] = []

    subtotal: Decimal
    tax_amount: Decimal
    tip_amount: Decimal
    delivery_fee: Decimal
    discount_amount: Decimal
    total: Decimal
    total_paid: Decimal
    saldo_pendiente: Decimal

    opened_at: datetime
    closed_at: Optional[datetime]
    paid_at: Optional[datetime]

    created_at: datetime
    updated_at: datetime
