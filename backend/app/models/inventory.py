import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import PurchaseOrderStatus, StockMovementDirection, StockMovementType
from app.db.base import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    contact_name: Mapped[Optional[str]] = mapped_column(
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

    address: Mapped[Optional[str]] = mapped_column(
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


class StockItem(Base):
    __tablename__ = "stock_items"
    __table_args__ = (
        UniqueConstraint(
            "branch_id",
            "ingredient_id",
            name="uq_stock_items_branch_ingredient",
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

    ingredient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ingredients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        nullable=False,
        default=Decimal("0"),
    )

    min_quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        nullable=False,
        default=Decimal("0"),
    )

    last_unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
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

    ingredient: Mapped["Ingredient"] = relationship()

    movements: Mapped[List["StockMovement"]] = relationship(
        back_populates="stock_item"
    )

    @property
    def ingredient_name(self) -> Optional[str]:
        return self.ingredient.name if self.ingredient else None

    @property
    def branch_name(self) -> Optional[str]:
        return self.branch.name if self.branch else None


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    branch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("branches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    stock_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("stock_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    ingredient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ingredients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    movement_type: Mapped[StockMovementType] = mapped_column(
        String(50),
        nullable=False,
    )

    direction: Mapped[StockMovementDirection] = mapped_column(
        String(10),
        nullable=False,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        nullable=False,
    )

    stock_after: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        nullable=False,
    )

    unit_cost: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    order_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("order_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    note: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    stock_item: Mapped["StockItem"] = relationship(
        back_populates="movements"
    )

    ingredient: Mapped["Ingredient"] = relationship()

    order_item: Mapped[Optional["OrderItem"]] = relationship()

    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship()

    created_by_user: Mapped[Optional["User"]] = relationship()

    @property
    def ingredient_name(self) -> Optional[str]:
        return self.ingredient.name if self.ingredient else None


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    branch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("branches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    supplier_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    status: Mapped[PurchaseOrderStatus] = mapped_column(
        String(50),
        nullable=False,
        default=PurchaseOrderStatus.BORRADOR,
    )

    order_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    received_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
    )

    notes: Mapped[Optional[str]] = mapped_column(
        String(2000),
        nullable=True,
    )

    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
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

    supplier: Mapped["Supplier"] = relationship()

    created_by_user: Mapped[Optional["User"]] = relationship()

    items: Mapped[List["PurchaseItem"]] = relationship(
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )

    @property
    def supplier_name(self) -> Optional[str]:
        return self.supplier.name if self.supplier else None


class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    ingredient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ingredients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        nullable=False,
    )

    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    received_quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        nullable=False,
        default=Decimal("0"),
    )

    purchase_order: Mapped["PurchaseOrder"] = relationship(
        back_populates="items"
    )

    ingredient: Mapped["Ingredient"] = relationship()

    @property
    def ingredient_name(self) -> Optional[str]:
        return self.ingredient.name if self.ingredient else None

    @property
    def subtotal(self) -> Decimal:
        return self.quantity * self.unit_cost


class WasteEvent(Base):
    __tablename__ = "waste_events"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    branch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("branches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    ingredient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ingredients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        nullable=False,
    )

    reason: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
    )

    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    branch: Mapped[Optional["Branch"]] = relationship()

    ingredient: Mapped["Ingredient"] = relationship()

    created_by_user: Mapped[Optional["User"]] = relationship()

    @property
    def ingredient_name(self) -> Optional[str]:
        return self.ingredient.name if self.ingredient else None
