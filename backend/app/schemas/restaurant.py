from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RestaurantUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    legal_name: Optional[str] = Field(default=None, max_length=255)
    nit: Optional[str] = Field(default=None, max_length=50)
    address: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    email: Optional[EmailStr] = None
    logo_url: Optional[str] = Field(default=None, max_length=500)
    primary_color: Optional[str] = Field(default=None, max_length=20)
    secondary_color: Optional[str] = Field(default=None, max_length=20)
    default_tax_rate: Optional[Decimal] = Field(default=None, ge=0, le=1)
    default_tip_rate: Optional[Decimal] = Field(default=None, ge=0, le=1)
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    timezone: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = None


class RestaurantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    legal_name: Optional[str]
    nit: Optional[str]
    address: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    logo_url: Optional[str]
    primary_color: Optional[str]
    secondary_color: Optional[str]
    default_tax_rate: Decimal
    default_tip_rate: Decimal
    currency: str
    timezone: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
