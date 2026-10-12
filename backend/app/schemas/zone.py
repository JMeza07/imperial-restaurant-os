from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ZoneCreate(BaseModel):
    branch_id: UUID
    name: str = Field(min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=500)


class ZoneUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = None


class ZoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    branch_id: UUID
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
