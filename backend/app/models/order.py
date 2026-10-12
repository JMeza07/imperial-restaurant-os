import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import (
    ModificationAction,
    OrderChannel,
    OrderItemStatus,
    OrderStatus,
    OrderType,
)
from app.db.base import Base


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        Index(
            "uq_orders_open_table",
            "table_id",
            unique=True,
            postgresql_where=text("status = 'ABIERTA'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    display_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )

    branch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("branches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    table_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("tables.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    waiter_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    order_type: Mapped[OrderType] = mapped_column(
        Enum(OrderType, name="order_type"),
        nullable=False,
        default=OrderType.MESA,
    )

    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status"),
        nullable=False,
        default=OrderStatus.ABIERTA,
    )

    channel: Mapped[OrderChannel] = mapped_column(
        Enum(OrderChannel, name="order_channel"),
        nullable=False,
        default=OrderChannel.QR,
    )

    customer_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    customer_phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    customer_address: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    notes: Mapped[Optional[str]] = mapped_column(
        String(2000),
        nullable=True,
    )

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
    )

    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
    )

    tip_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
    )

    delivery_fee: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
    )

    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
    )

    total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
    )

    total_paid: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
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

    items: Mapped[List["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderItem.created_at",
    )

    events: Mapped[List["OrderEvent"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderEvent.created_at",
    )

    table: Mapped[Optional["Table"]] = relationship()
    waiter: Mapped[Optional["User"]] = relationship(foreign_keys=[waiter_id])

    @property
    def table_number(self) -> Optional[int]:
        return self.table.number if self.table else None

    @property
    def saldo_pendiente(self) -> Decimal:
        base = self.total if self.total and self.total > 0 else self.subtotal
        paid = self.total_paid or Decimal("0")

        pending = base - paid

        if pending < 0:
            return Decimal("0")

        return pending


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    dish_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("dishes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    status: Mapped[OrderItemStatus] = mapped_column(
        Enum(OrderItemStatus, name="order_item_status"),
        nullable=False,
        default=OrderItemStatus.RECIBIDO,
    )

    observations: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    prepared_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    ready_at: Mapped[Optional[datetime]] = mapped_column(
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

    prepared_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    ready_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    delivered_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    cancelled_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    order: Mapped["Order"] = relationship(
        back_populates="items"
    )

    dish: Mapped["Dish"] = relationship()

    prepared_by: Mapped[Optional["User"]] = relationship(
        foreign_keys=[prepared_by_user_id]
    )

    modifications: Mapped[List["ItemModification"]] = relationship(
        back_populates="order_item",
        cascade="all, delete-orphan",
        order_by="ItemModification.created_at",
    )

    @property
    def dish_name(self) -> Optional[str]:
        return self.dish.name if self.dish else None

    @property
    def preparer_name(self) -> Optional[str]:
        from sqlalchemy import inspect as sa_inspect
        insp = sa_inspect(self)
        if "prepared_by" in insp.attrs and insp.attrs.prepared_by.loaded_value:
            user = insp.attrs.prepared_by.loaded_value
            return user.full_name or user.email
        return None

    @property
    def order_display_code(self) -> Optional[str]:
        return self.order.display_code if self.order else None

    @property
    def order_status(self):
        return self.order.status if self.order else None

    @property
    def order_type(self):
        return self.order.order_type if self.order else None

    @property
    def order_table_id(self):
        return self.order.table_id if self.order else None

    @property
    def order_table_number(self) -> Optional[int]:
        return self.order.table_number if self.order else None

    @property
    def order_notes(self) -> Optional[str]:
        return self.order.notes if self.order else None


class ItemModification(Base):
    __tablename__ = "item_modifications"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    order_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("order_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    ingredient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ingredients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    ingredient_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    action: Mapped[ModificationAction] = mapped_column(
        Enum(ModificationAction, name="modification_action"),
        nullable=False,
    )

    extra_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    order_item: Mapped["OrderItem"] = relationship(
        back_populates="modifications"
    )

    ingredient: Mapped["Ingredient"] = relationship()


class OrderEvent(Base):
    __tablename__ = "order_events"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    order_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("order_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    actor_role: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    action: Mapped[String] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    detail: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    order: Mapped["Order"] = relationship(
        back_populates="events"
    )
