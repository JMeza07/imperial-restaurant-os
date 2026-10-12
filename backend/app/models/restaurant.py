import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.core.enums import TableStatus
from app.db.base import Base


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    legal_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    nit: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    address: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    logo_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    primary_color: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )

    secondary_color: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )

    default_tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.08"),
    )

    default_tip_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.10"),
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="COP",
    )

    timezone: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="America/Bogota",
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


class Branch(Base):
    __tablename__ = "branches"
    __table_args__ = (
        UniqueConstraint(
            "restaurant_id",
            "name",
            name="uq_branches_restaurant_name",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    address: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    latitude: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(9, 6),
        nullable=True,
    )

    longitude: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(9, 6),
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


class Zone(Base):
    __tablename__ = "zones"
    __table_args__ = (
        UniqueConstraint(
            "branch_id",
            "name",
            name="uq_zones_branch_name",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    branch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("branches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        String(500),
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


class Table(Base):
    __tablename__ = "tables"
    __table_args__ = (
        UniqueConstraint(
            "branch_id",
            "number",
            name="uq_tables_branch_number",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    branch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("branches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    zone_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("zones.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    capacity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=4,
    )

    status: Mapped[TableStatus] = mapped_column(
        Enum(TableStatus, name="table_status"),
        nullable=False,
        default=TableStatus.LIBRE,
    )

    qr_code: Mapped[uuid.UUID] = mapped_column(
        unique=True,
        nullable=False,
        default=uuid.uuid4,
        index=True,
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

    @property
    def qr_url(self) -> str:
        return f"{settings.QR_BASE_URL}/{self.qr_code}"
