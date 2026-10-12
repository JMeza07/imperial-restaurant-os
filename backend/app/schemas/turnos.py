from datetime import date, datetime, time
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.enums import ShiftEventType, ShiftStatus


class EmployeeCreate(BaseModel):
    user_id: UUID
    branch_id: Optional[UUID] = None
    employee_code: str = Field(min_length=2, max_length=50)
    document_number: Optional[str] = Field(default=None, max_length=50)
    position: Optional[str] = Field(default=None, max_length=255)
    hourly_wage: Optional[Decimal] = Field(default=None, ge=0)
    is_active: bool = True


class EmployeeUpdate(BaseModel):
    branch_id: Optional[UUID] = None
    employee_code: Optional[str] = Field(default=None, min_length=2, max_length=50)
    document_number: Optional[str] = Field(default=None, max_length=50)
    position: Optional[str] = Field(default=None, max_length=255)
    hourly_wage: Optional[Decimal] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class EmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    branch_id: Optional[UUID]
    employee_code: str
    document_number: Optional[str]
    position: Optional[str]
    hourly_wage: Optional[Decimal]
    is_active: bool

    full_name: Optional[str]
    email: Optional[str]

    created_at: datetime
    updated_at: datetime


class ShiftTemplateCreate(BaseModel):
    branch_id: Optional[UUID] = None
    name: str = Field(min_length=2, max_length=255)
    start_time: time
    end_time: time
    weekdays: List[int] = []
    notes: Optional[str] = Field(default=None, max_length=2000)
    is_active: bool = True

    @field_validator("weekdays")
    @classmethod
    def validate_weekdays(cls, value):
        for day in value:
            if day < 0 or day > 6:
                raise ValueError("Los días deben estar entre 0=lunes y 6=domingo")

        return value


class ShiftTemplateUpdate(BaseModel):
    branch_id: Optional[UUID] = None
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    weekdays: Optional[List[int]] = None
    notes: Optional[str] = Field(default=None, max_length=2000)
    is_active: Optional[bool] = None

    @field_validator("weekdays")
    @classmethod
    def validate_weekdays(cls, value):
        if value is None:
            return value

        for day in value:
            if day < 0 or day > 6:
                raise ValueError("Los días deben estar entre 0=lunes y 6=domingo")

        return value


class ShiftTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    branch_id: Optional[UUID]
    name: str
    start_time: time
    end_time: time
    weekdays: List[int]
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ShiftCreate(BaseModel):
    employee_id: UUID
    branch_id: Optional[UUID] = None
    scheduled_start: datetime
    scheduled_end: datetime
    notes: Optional[str] = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_schedule(self):
        if self.scheduled_end <= self.scheduled_start:
            raise ValueError("La hora fin del turno debe ser mayor que la hora inicio")

        return self


class ShiftUpdate(BaseModel):
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    notes: Optional[str] = Field(default=None, max_length=2000)


class ShiftAssignmentUpdate(BaseModel):
    table_ids: List[UUID] = []


class GenerateShiftsRequest(BaseModel):
    template_id: UUID
    employee_id: UUID
    date_from: date
    date_to: date

    @model_validator(mode="after")
    def validate_dates(self):
        if self.date_to < self.date_from:
            raise ValueError("date_to debe ser mayor o igual que date_from")

        return self


class GenerateShiftsResult(BaseModel):
    created: int
    skipped: int


class ShiftBreakRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    started_at: datetime
    ended_at: Optional[datetime]
    notes: Optional[str]


class ClockEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: ShiftEventType
    ip_address: Optional[str]
    device: Optional[str]
    created_at: datetime


class AssignedTableRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    number: int
    zone_id: Optional[UUID]


class ShiftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    branch_id: Optional[UUID]

    employee_name: Optional[str]
    branch_name: Optional[str]

    status: ShiftStatus

    scheduled_start: datetime
    scheduled_end: datetime

    actual_start: Optional[datetime]
    actual_end: Optional[datetime]

    scheduled_minutes: Optional[int]
    worked_minutes: Optional[int]

    notes: Optional[str]

    breaks: List[ShiftBreakRead] = []
    clock_events: List[ClockEventRead] = []
    assigned_tables: List[AssignedTableRead] = []

    created_at: datetime
    updated_at: datetime
