import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import (
    CommissionEventStatus,
    CommissionPeriodStatus,
    CommissionPayoutStatus,
    CommissionRuleType,
)
from app.db.base import Base


class CommissionRule(Base):
    __tablename__ = "commission_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    rule_type: Mapped[CommissionRuleType] = mapped_column(
        String(50),
        nullable=False,
    )

    value: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    cap_per_order: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    cap_per_period: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    conditions: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    starts_at: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    ends_at: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
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


class CommissionPeriod(Base):
    __tablename__ = "commission_periods"

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

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    status: Mapped[CommissionPeriodStatus] = mapped_column(
        String(50),
        nullable=False,
        default=CommissionPeriodStatus.ABIERTA,
    )

    calculated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    paid_at: Mapped[Optional[datetime]] = mapped_column(
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

    branch: Mapped[Optional["Branch"]] = relationship()

    events: Mapped[List["CommissionEvent"]] = relationship(
        back_populates="period"
    )

    payouts: Mapped[List["CommissionPayout"]] = relationship(
        back_populates="period"
    )

    @property
    def branch_name(self) -> Optional[str]:
        return self.branch.name if self.branch else None


class CommissionEvent(Base):
    __tablename__ = "commission_events"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    period_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("commission_periods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    rule_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("commission_rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    order_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("order_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    base_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
    )

    status: Mapped[CommissionEventStatus] = mapped_column(
        String(50),
        nullable=False,
        default=CommissionEventStatus.CALCULADA,
    )

    dedup_key: Mapped[str] = mapped_column(
        String(500),
        unique=True,
        nullable=False,
    )

    detail: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
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

    period: Mapped["CommissionPeriod"] = relationship(
        back_populates="events"
    )

    rule: Mapped["CommissionRule"] = relationship()

    employee: Mapped["Employee"] = relationship()

    order: Mapped[Optional["Order"]] = relationship()

    order_item: Mapped[Optional["OrderItem"]] = relationship()

    @property
    def employee_name(self) -> Optional[str]:
        return self.employee.full_name if self.employee else None

    @property
    def rule_name(self) -> Optional[str]:
        return self.rule.name if self.rule else None


class CommissionPayout(Base):
    __tablename__ = "commission_payouts"
    __table_args__ = (
        UniqueConstraint(
            "period_id",
            "employee_id",
            name="uq_commission_payouts_period_employee",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    period_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("commission_periods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
    )

    status: Mapped[CommissionPayoutStatus] = mapped_column(
        String(50),
        nullable=False,
        default=CommissionPayoutStatus.PENDIENTE,
    )

    payment_method: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    reference: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
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

    period: Mapped["CommissionPeriod"] = relationship(
        back_populates="payouts"
    )

    employee: Mapped["Employee"] = relationship()

    @property
    def employee_name(self) -> Optional[str]:
        return self.employee.full_name if self.employee else None


class Survey(Base):
    __tablename__ = "surveys"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    food_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    service_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    general_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    comment: Mapped[Optional[str]] = mapped_column(
        String(2000),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    order: Mapped["Order"] = relationship()
