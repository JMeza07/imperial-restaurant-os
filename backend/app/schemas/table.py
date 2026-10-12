from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import TableStatus


class TableCreate(BaseModel):
    branch_id: UUID
    zone_id: Optional[UUID] = None
    number: int = Field(gt=0)
    capacity: int = Field(default=4, gt=0)
    status: TableStatus = TableStatus.LIBRE


class TableUpdate(BaseModel):
    zone_id: Optional[UUID] = None
    number: Optional[int] = Field(default=None, gt=0)
    capacity: Optional[int] = Field(default=None, gt=0)
    status: Optional[TableStatus] = None
    is_active: Optional[bool] = None


class TableRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    branch_id: UUID
    zone_id: Optional[UUID]
    number: int
    capacity: int
    status: TableStatus
    qr_code: UUID
    qr_url: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TablePublic(BaseModel):
    id: UUID
    number: int
    capacity: int
    status: TableStatus
    branch_id: UUID
    branch_name: str
    zone_id: Optional[UUID] = None
    zone_name: Optional[str] = None
    open_order: Optional[dict] = None
