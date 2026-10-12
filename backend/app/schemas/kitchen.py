from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.enums import OrderItemStatus, OrderStatus, OrderType
from app.schemas.order import ModificationRead


class ItemStateUpdateRequest(BaseModel):
    status: OrderItemStatus


class KitchenItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID

    order_display_code: Optional[str]
    order_status: Optional[OrderStatus]
    order_type: Optional[OrderType]
    order_table_id: Optional[UUID]
    order_table_number: Optional[int]
    order_notes: Optional[str]

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

    prepared_by_user_id: Optional[UUID]
    preparer_name: Optional[str] = None
    ready_by_user_id: Optional[UUID]
    delivered_by_user_id: Optional[UUID]
    cancelled_by_user_id: Optional[UUID]
