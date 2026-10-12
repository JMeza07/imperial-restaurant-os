from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import (
    PurchaseOrderStatus,
    StockMovementDirection,
    StockMovementType,
)


class StockItemUpdate(BaseModel):
    min_quantity: Optional[Decimal] = Field(default=None, ge=0)


class StockItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    branch_id: Optional[UUID]
    branch_name: Optional[str]
    ingredient_id: UUID
    ingredient_name: Optional[str]

    quantity: Decimal
    min_quantity: Decimal
    last_unit_cost: Decimal

    created_at: datetime
    updated_at: datetime


class StockAdjustmentRequest(BaseModel):
    branch_id: Optional[UUID] = None
    ingredient_id: UUID
    direction: StockMovementDirection
    quantity: Decimal = Field(gt=0)
    reason: Optional[str] = Field(default=None, max_length=1000)


class SupplierCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    contact_name: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=255)
    address: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = True


class SupplierUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    contact_name: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=255)
    address: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = None


class SupplierRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    contact_name: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PurchaseItemRequest(BaseModel):
    ingredient_id: UUID
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(ge=0)


class PurchaseOrderCreate(BaseModel):
    branch_id: Optional[UUID] = None
    supplier_id: UUID
    notes: Optional[str] = Field(default=None, max_length=2000)
    items: List[PurchaseItemRequest] = Field(min_length=1)


class PurchaseItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ingredient_id: UUID
    ingredient_name: Optional[str]
    quantity: Decimal
    unit_cost: Decimal
    received_quantity: Decimal
    subtotal: Decimal


class PurchaseOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    branch_id: Optional[UUID]
    supplier_id: UUID
    supplier_name: Optional[str]

    status: PurchaseOrderStatus
    order_date: datetime
    received_at: Optional[datetime]

    total: Decimal
    notes: Optional[str]

    items: List[PurchaseItemRead] = []

    created_at: datetime
    updated_at: datetime


class WasteCreate(BaseModel):
    branch_id: Optional[UUID] = None
    ingredient_id: UUID
    quantity: Decimal = Field(gt=0)
    reason: Optional[str] = Field(default=None, max_length=1000)


class WasteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    branch_id: Optional[UUID]
    ingredient_id: UUID
    ingredient_name: Optional[str]
    quantity: Decimal
    reason: Optional[str]
    created_at: datetime


class StockMovementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    branch_id: Optional[UUID]
    stock_item_id: UUID
    ingredient_id: UUID
    ingredient_name: Optional[str]

    movement_type: StockMovementType
    direction: StockMovementDirection

    quantity: Decimal
    stock_after: Decimal
    unit_cost: Optional[Decimal]

    order_item_id: Optional[UUID]
    purchase_order_id: Optional[UUID]

    note: Optional[str]
    created_at: datetime
