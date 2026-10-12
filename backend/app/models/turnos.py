import uuid
from datetime import datetime, time
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ShiftEventType, ShiftStatus
from app.db.base import Base


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    branch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("branches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    employee_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    document_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
    )

    position: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    hourly_wage: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship()

    branch: Mapped[Optional["Branch"]] = relationship()

    shifts: Mapped[List["Shift"]] = relationship(
        back_populates="employee"
    )

    @property
    def full_name(self) -> Optional[str]:
        return self.user.full_name if self.user else None

    @property
    def email(self) -> Optional[str]:
        return self.user.email if self.user else None


class ShiftTemplate(Base):
    __tablename__ = "shift_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    branch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("branches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    end_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    weekdays: Mapped[List[int]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    notes: Mapped[Optional[str]] = mapped_column(
        String(2000),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    branch: Mapped[Optional["Branch"]] = relationship()


class Shift(Base):
    __tablename__ = "shifts"
    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "scheduled_start",
            name="uq_shifts_employee_scheduled_start",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    branch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("branches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status: Mapped[ShiftStatus] = mapped_column(
        String(50),
        nullable=False,
        default=ShiftStatus.PROGRAMADO,
    )

    scheduled_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    scheduled_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    actual_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    actual_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    notes: Mapped[Optional[str]] = mapped_column(
        String(2000),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    employee: Mapped["Employee"] = relationship(
        back_populates="shifts"
    )

    branch: Mapped[Optional["Branch"]] = relationship()

    breaks: Mapped[List["ShiftBreak"]] = relationship(
        back_populates="shift",
        cascade="all, delete-orphan",
    )

    clock_events: Mapped[List["ClockEvent"]] = relationship(
        back_populates="shift",
        cascade="all, delete-orphan",
    )

    assignments: Mapped[List["ShiftAssignment"]] = relationship(
        back_populates="shift",
        cascade="all, delete-orphan",
    )

    @property
    def employee_name(self) -> Optional[str]:
        return self.employee.full_name if self.employee else None

    @property
    def branch_name(self) -> Optional[str]:
        return self.branch.name if self.branch else None

    @property
    def scheduled_minutes(self) -> Optional[int]:
        if not self.scheduled_start or not self.scheduled_end:
            return None

        delta = self.scheduled_end - self.scheduled_start
        return int(delta.total_seconds() // 60)

    @property
    def worked_minutes(self) -> Optional[int]:
        if not self.actual_start or not self.actual_end:
            return None

        total_seconds = (self.actual_end - self.actual_start).total_seconds()

        break_seconds = 0

        for break_item in self.breaks:
            if break_item.started_at and break_item.ended_at:
                break_seconds += (
                    break_item.ended_at - break_item.started_at
                ).total_seconds()

        minutes = int((total_seconds - break_seconds) // 60)

        return max(minutes, 0)

    @property
    def active_break(self):
        for break_item in self.breaks:
            if break_item.ended_at is None:
                return break_item

        return None

    @property
    def assigned_tables(self):
        return [assignment.table for assignment in self.assignments if assignment.table]


class ShiftBreak(Base):
    __tablename__ = "shift_breaks"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    shift_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("shifts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    notes: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
    )

    shift: Mapped["Shift"] = relationship(
        back_populates="breaks"
    )


class ClockEvent(Base):
    __tablename__ = "clock_events"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    shift_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("shifts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_type: Mapped[ShiftEventType] = mapped_column(
        String(50),
        nullable=False,
    )

    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
    )

    device: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    shift: Mapped["Shift"] = relationship(
        back_populates="clock_events"
    )

    employee: Mapped["Employee"] = relationship()


class ShiftAssignment(Base):
    __tablename__ = "shift_assignments"

    shift_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("shifts.id", ondelete="CASCADE"),
        primary_key=True,
    )

    table_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tables.id", ondelete="CASCADE"),
        primary_key=True,
    )

    shift: Mapped["Shift"] = relationship(
        back_populates="assignments"
    )

    table: Mapped["Table"] = relationship()
