import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import CashSessionStatus, PaymentMethod, PaymentStatus
from app.db.base import Base


class CashSession(Base):
    __tablename__ = "cash_sessions"
    __table_args__ = (
        Index(
            "uq_cash_sessions_open_branch",
            "branch_id",
            unique=True,
            postgresql_where=text("status = 'ABIERTA'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    branch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("branches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    opened_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    closed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    status: Mapped[CashSessionStatus] = mapped_column(
        Enum(CashSessionStatus, name="cash_session_status"),
        nullable=False,
        default=CashSessionStatus.ABIERTA,
    )

    opening_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
    )

    closing_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    expected_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    notes: Mapped[Optional[str]] = mapped_column(
        String(2000),
        nullable=True,
    )

    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    closed_at: Mapped[Optional[datetime]] = mapped_column(
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

    payments: Mapped[List["Payment"]] = relationship(
        back_populates="cash_session"
    )


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, name="payment_method"),
        nullable=False,
    )

    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"),
        nullable=False,
        default=PaymentStatus.APROBADO,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    reference: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    note: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
    )

    cash_session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("cash_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    registered_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    order: Mapped["Order"] = relationship()

    cash_session: Mapped[Optional["CashSession"]] = relationship(
        back_populates="payments"
    )

    @property
    def order_status(self):
        return self.order.status if self.order else None

    @property
    def order_total(self) -> Optional[Decimal]:
        return self.order.total if self.order else None

    @property
    def order_total_paid(self) -> Optional[Decimal]:
        return self.order.total_paid if self.order else None

    @property
    def order_saldo_pendiente(self) -> Optional[Decimal]:
        return self.order.saldo_pendiente if self.order else None
