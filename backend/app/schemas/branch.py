from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BranchCreate(BaseModel):
    restaurant_id: UUID
    name: str = Field(min_length=2, max_length=255)
    address: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    latitude: Optional[Decimal] = Field(default=None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(default=None, ge=-180, le=180)


class BranchUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    address: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    latitude: Optional[Decimal] = Field(default=None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(default=None, ge=-180, le=180)
    is_active: Optional[bool] = None


class BranchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    restaurant_id: UUID
    name: str
    address: Optional[str]
    phone: Optional[str]
    latitude: Optional[Decimal]
    longitude: Optional[Decimal]
    is_active: bool
    created_at: datetime
    updated_at: datetime
