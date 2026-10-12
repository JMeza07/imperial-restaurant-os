import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import DeliveryStatus
from app.db.base import Base


class DeliveryZone(Base):
    __tablename__ = "delivery_zones"
    __table_args__ = (
        UniqueConstraint(
            "branch_id",
            "name",
            name="uq_delivery_zones_branch_name",
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

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
    )

    delivery_fee: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
    )

    max_distance_km: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        nullable=False,
        default=Decimal("5.00"),
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
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


class Delivery(Base):
    __tablename__ = "deliveries"

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

    delivery_zone_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("delivery_zones.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    customer_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    customer_phone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    customer_address: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    delivery_fee: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
    )

    status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus, name="delivery_status"),
        nullable=False,
        default=DeliveryStatus.PENDIENTE,
    )

    assigned_domiciliario_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    assigned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    enroute_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
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

    order: Mapped["Order"] = relationship()

    zone: Mapped[Optional["DeliveryZone"]] = relationship()

    assigned_user: Mapped[Optional["User"]] = relationship(
        foreign_keys=[assigned_domiciliario_id]
    )

    @property
    def zone_name(self) -> Optional[str]:
        return self.zone.name if self.zone else None

    @property
    def assigned_user_name(self) -> Optional[str]:
        return self.assigned_user.full_name if self.assigned_user else None

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

    @property
    def tracking_items(self):
        if not self.order:
            return []

        return self.order.items
