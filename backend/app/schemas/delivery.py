from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import DeliveryStatus, OrderItemStatus, OrderStatus
from app.schemas.order import OrderItemRequest


class DeliveryZoneCreate(BaseModel):
    branch_id: Optional[UUID] = None
    name: str = Field(min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    delivery_fee: Decimal = Field(default=Decimal("0"), ge=0)
    max_distance_km: Decimal = Field(default=Decimal("5.00"), ge=0)
    is_active: bool = True


class DeliveryZoneUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    delivery_fee: Optional[Decimal] = Field(default=None, ge=0)
    max_distance_km: Optional[Decimal] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class DeliveryZoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    branch_id: Optional[UUID]
    name: str
    description: Optional[str]
    delivery_fee: Decimal
    max_distance_km: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DeliveryCreateRequest(BaseModel):
    customer_name: str = Field(min_length=3, max_length=255)
    customer_phone: str = Field(min_length=7, max_length=50)
    customer_address: str = Field(min_length=5, max_length=500)
    delivery_zone_id: UUID
    delivery_fee: Optional[Decimal] = Field(default=None, ge=0)
    notes: Optional[str] = Field(default=None, max_length=2000)
    items: List[OrderItemRequest] = Field(min_length=1)


class DeliveryAssignRequest(BaseModel):
    domiciliario_id: UUID


class DeliveryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID

    delivery_zone_id: Optional[UUID]
    zone_name: Optional[str]

    customer_name: str
    customer_phone: str
    customer_address: str

    delivery_fee: Decimal
    status: DeliveryStatus

    assigned_domiciliario_id: Optional[UUID]
    assigned_user_name: Optional[str]

    assigned_at: Optional[datetime]
    enroute_at: Optional[datetime]
    delivered_at: Optional[datetime]
    cancelled_at: Optional[datetime]

    notes: Optional[str]

    created_at: datetime
    updated_at: datetime

    order_status: Optional[OrderStatus]
    order_total: Optional[Decimal]
    order_total_paid: Optional[Decimal]
    order_saldo_pendiente: Optional[Decimal]


class DeliveryTrackingItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dish_name: Optional[str]
    quantity: int
    status: OrderItemStatus


class DeliveryTrackingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_id: UUID
    delivery_status: DeliveryStatus = Field(validation_alias="status")
    order_status: Optional[OrderStatus]

    order_total: Optional[Decimal]
    order_total_paid: Optional[Decimal]
    order_saldo_pendiente: Optional[Decimal]

    items: List[DeliveryTrackingItemRead] = Field(
        validation_alias="tracking_items"
    )
