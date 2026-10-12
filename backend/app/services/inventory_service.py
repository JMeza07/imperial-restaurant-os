from collections import defaultdict
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.enums import (
    ModificationAction,
    PurchaseOrderStatus,
    StockMovementDirection,
    StockMovementType,
)
from app.models.catalog import Ingredient, RecipeIngredient
from app.models.inventory import (
    PurchaseItem,
    PurchaseOrder,
    StockItem,
    StockMovement,
    Supplier,
    WasteEvent,
)
from app.models.order import OrderItem
from app.models.restaurant import Branch
from app.schemas.inventory import (
    PurchaseOrderCreate,
    StockAdjustmentRequest,
    SupplierCreate,
    SupplierUpdate,
    WasteCreate,
)
from app.services.audit_service import audit


def round_quantity(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def calculate_required_ingredients(
    recipe: List[dict],
    modifications: List[dict],
    item_quantity: int,
) -> Dict[UUID, Decimal]:
    """
    Calcula los ingredientes requeridos por un ítem de pedido.

    - La receta base se multiplica por la cantidad del plato.
    - QUITAR descuenta la cantidad del ingrediente.
    - AGREGAR suma una porción adicional del ingrediente.
    """

    recipe_by_ingredient: Dict[UUID, Decimal] = {}

    for recipe_item in recipe:
        ingredient_id = recipe_item["ingredient_id"]
        quantity = Decimal(str(recipe_item["quantity"]))
        recipe_by_ingredient[ingredient_id] = quantity

    required: Dict[UUID, Decimal] = defaultdict(lambda: Decimal("0"))

    for ingredient_id, quantity in recipe_by_ingredient.items():
        required[ingredient_id] += quantity * item_quantity

    for modification in modifications:
        ingredient_id = modification["ingredient_id"]
        action = modification["action"]

        base_quantity = recipe_by_ingredient.get(ingredient_id)

        if base_quantity is None:
            continue

        if action == ModificationAction.QUITAR:
            required[ingredient_id] -= base_quantity * item_quantity

        elif action == ModificationAction.AGREGAR:
            required[ingredient_id] += base_quantity * item_quantity

    return {
        ingredient_id: quantity
        for ingredient_id, quantity in required.items()
        if quantity > 0
    }


async def _get_default_branch(db: AsyncSession) -> Branch:
    branch = await db.scalar(
        select(Branch)
        .where(Branch.is_active.is_(True))
        .order_by(Branch.created_at.asc())
    )

    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe una sucursal activa",
        )

    return branch


async def _get_or_create_stock_item(
    db: AsyncSession,
    branch_id: UUID,
    ingredient_id: UUID,
) -> StockItem:
    stock_item = await db.scalar(
        select(StockItem)
        .where(
            StockItem.branch_id == branch_id,
            StockItem.ingredient_id == ingredient_id,
        )
        .with_for_update()
    )

    if stock_item:
        return stock_item

    stock_item = StockItem(
        branch_id=branch_id,
        ingredient_id=ingredient_id,
        quantity=Decimal("0"),
        min_quantity=Decimal("0"),
        last_unit_cost=Decimal("0"),
    )

    db.add(stock_item)
    await db.flush()

    return stock_item


async def increase_stock(
    db: AsyncSession,
    *,
    branch_id: UUID,
    ingredient_id: UUID,
    quantity: Decimal,
    movement_type: StockMovementType,
    unit_cost: Optional[Decimal] = None,
    order_item_id: Optional[UUID] = None,
    purchase_order_id: Optional[UUID] = None,
    created_by_user_id: Optional[UUID] = None,
    note: Optional[str] = None,
) -> StockMovement:
    quantity = round_quantity(quantity)

    if quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La cantidad del movimiento debe ser mayor que cero",
        )

    stock_item = await _get_or_create_stock_item(db, branch_id, ingredient_id)

    old_quantity = stock_item.quantity
    new_quantity = old_quantity + quantity

    if unit_cost is not None and unit_cost >= 0:
        if old_quantity <= 0:
            stock_item.last_unit_cost = unit_cost
        else:
            old_cost = stock_item.last_unit_cost or Decimal("0")
            stock_item.last_unit_cost = round(
                (
                    (old_quantity * old_cost) + (quantity * unit_cost)
                )
                / new_quantity,
                2,
            )

    stock_item.quantity = new_quantity

    movement = StockMovement(
        branch_id=branch_id,
        stock_item_id=stock_item.id,
        ingredient_id=ingredient_id,
        movement_type=movement_type,
        direction=StockMovementDirection.IN,
        quantity=quantity,
        stock_after=new_quantity,
        unit_cost=unit_cost,
        order_item_id=order_item_id,
        purchase_order_id=purchase_order_id,
        created_by_user_id=created_by_user_id,
        note=note,
    )

    db.add(movement)
    await db.flush()

    return movement


async def decrease_stock(
    db: AsyncSession,
    *,
    branch_id: UUID,
    ingredient_id: UUID,
    quantity: Decimal,
    movement_type: StockMovementType,
    order_item_id: Optional[UUID] = None,
    purchase_order_id: Optional[UUID] = None,
    created_by_user_id: Optional[UUID] = None,
    note: Optional[str] = None,
) -> StockMovement:
    quantity = round_quantity(quantity)

    if quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La cantidad del movimiento debe ser mayor que cero",
        )

    stock_item = await _get_or_create_stock_item(db, branch_id, ingredient_id)

    if (
        not settings.INVENTORY_ALLOW_NEGATIVE_STOCK
        and stock_item.quantity < quantity
    ):
        ingredient = await db.get(Ingredient, ingredient_id)
        ingredient_name = ingredient.name if ingredient else str(ingredient_id)

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Stock insuficiente para el ingrediente '{ingredient_name}'",
        )

    new_quantity = stock_item.quantity - quantity
    stock_item.quantity = new_quantity

    movement = StockMovement(
        branch_id=branch_id,
        stock_item_id=stock_item.id,
        ingredient_id=ingredient_id,
        movement_type=movement_type,
        direction=StockMovementDirection.OUT,
        quantity=quantity,
        stock_after=new_quantity,
        unit_cost=stock_item.last_unit_cost,
        order_item_id=order_item_id,
        purchase_order_id=purchase_order_id,
        created_by_user_id=created_by_user_id,
        note=note,
    )

    db.add(movement)
    await db.flush()

    return movement


async def consume_order(
    db: AsyncSession,
    order,
    order_items: List[OrderItem],
    created_by_user_id: Optional[UUID] = None,
) -> None:
    active_items = [
        item
        for item in order_items
        if item.status != "CANCELADO"
    ]

    if not active_items:
        return

    branch_id = order.branch_id

    if not branch_id:
        branch = await _get_default_branch(db)
        branch_id = branch.id

    dish_ids = [item.dish_id for item in active_items]

    recipe_rows = await db.scalars(
        select(RecipeIngredient).where(
            RecipeIngredient.dish_id.in_(dish_ids)
        )
    )

    recipes_by_dish = defaultdict(list)

    for recipe_item in recipe_rows.all():
        recipes_by_dish[recipe_item.dish_id].append(
            {
                "ingredient_id": recipe_item.ingredient_id,
                "quantity": recipe_item.quantity,
            }
        )

    for item in active_items:
        recipe = recipes_by_dish.get(item.dish_id, [])

        modifications = [
            {
                "ingredient_id": modification.ingredient_id,
                "action": modification.action,
            }
            for modification in item.modifications
        ]

        required = calculate_required_ingredients(
            recipe=recipe,
            modifications=modifications,
            item_quantity=item.quantity,
        )

        for ingredient_id, quantity in required.items():
            await decrease_stock(
                db=db,
                branch_id=branch_id,
                ingredient_id=ingredient_id,
                quantity=quantity,
                movement_type=StockMovementType.VENTA,
                order_item_id=item.id,
                created_by_user_id=created_by_user_id,
                note=f"Consumo por venta orden {order.display_code}",
            )


async def restock_order_item(
    db: AsyncSession,
    order,
    item: OrderItem,
    created_by_user_id: Optional[UUID] = None,
) -> None:
    if item.status != "CANCELADO":
        return

    branch_id = order.branch_id

    if not branch_id:
        branch = await _get_default_branch(db)
        branch_id = branch.id

    item_with_mods = await db.scalar(
        select(OrderItem)
        .options(selectinload(OrderItem.modifications))
        .where(OrderItem.id == item.id)
    )

    if not item_with_mods:
        return

    recipe_rows = await db.scalars(
        select(RecipeIngredient).where(
            RecipeIngredient.dish_id == item_with_mods.dish_id
        )
    )

    recipe = [
        {
            "ingredient_id": recipe_item.ingredient_id,
            "quantity": recipe_item.quantity,
        }
        for recipe_item in recipe_rows.all()
    ]

    modifications = [
        {
            "ingredient_id": modification.ingredient_id,
            "action": modification.action,
        }
        for modification in item_with_mods.modifications
    ]

    required = calculate_required_ingredients(
        recipe=recipe,
        modifications=modifications,
        item_quantity=item_with_mods.quantity,
    )

    for ingredient_id, quantity in required.items():
        await increase_stock(
            db=db,
            branch_id=branch_id,
            ingredient_id=ingredient_id,
            quantity=quantity,
            movement_type=StockMovementType.DEVOLUCION_VENTA,
            order_item_id=item_with_mods.id,
            created_by_user_id=created_by_user_id,
            note=f"Devolución por cancelación orden {order.display_code}",
        )


async def initialize_stock(
    db: AsyncSession,
    branch_id: Optional[UUID] = None,
    request: Request | None = None,
    actor_user=None,
) -> dict:
    if not branch_id:
        branch = await _get_default_branch(db)
        branch_id = branch.id

    ingredients = await db.scalars(
        select(Ingredient).where(Ingredient.available.is_(True))
    ).all()

    created = 0

    for ingredient in ingredients:
        existing = await db.scalar(
            select(StockItem).where(
                StockItem.branch_id == branch_id,
                StockItem.ingredient_id == ingredient.id,
            )
        )

        if not existing:
            stock_item = StockItem(
                branch_id=branch_id,
                ingredient_id=ingredient.id,
                quantity=Decimal("0"),
                min_quantity=Decimal("0"),
                last_unit_cost=Decimal("0"),
            )

            db.add(stock_item)
            created += 1

    await db.commit()

    await audit(
        db,
        action="inventory.initialized",
        resource="inventory",
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={
            "branch_id": str(branch_id),
            "created_stock_items": created,
        },
    )

    return {
        "created": created,
    }


async def list_stock(
    db: AsyncSession,
    branch_id: Optional[UUID] = None,
    low_stock: bool = False,
    search: Optional[str] = None,
) -> List[StockItem]:
    query = (
        select(StockItem)
        .options(
            selectinload(StockItem.ingredient),
            selectinload(StockItem.branch),
        )
        .order_by(StockItem.updated_at.desc())
    )

    if branch_id:
        query = query.where(StockItem.branch_id == branch_id)

    if low_stock:
        query = query.where(StockItem.quantity <= StockItem.min_quantity)

    if search:
        query = query.join(Ingredient).where(
            Ingredient.name.ilike(f"%{search}%")
        )

    return (await db.scalars(query)).all()


async def update_stock_item(
    db: AsyncSession,
    stock_id: UUID,
    payload,
    request: Request | None = None,
    actor_user=None,
) -> StockItem:
    stock_item = await db.get(StockItem, stock_id)

    if not stock_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de stock no encontrado",
        )

    if payload.min_quantity is not None:
        stock_item.min_quantity = payload.min_quantity

    await db.commit()
    await db.refresh(stock_item)

    await audit(
        db,
        action="inventory.stock_updated",
        resource="stock_item",
        resource_id=stock_item.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={
            "min_quantity": str(stock_item.min_quantity),
        },
    )

    return stock_item


async def adjust_stock(
    db: AsyncSession,
    payload: StockAdjustmentRequest,
    request: Request | None = None,
    actor_user=None,
) -> StockMovement:
    ingredient = await db.get(Ingredient, payload.ingredient_id)

    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingrediente no encontrado",
        )

    branch_id = payload.branch_id

    if not branch_id:
        branch = await _get_default_branch(db)
        branch_id = branch.id

    if payload.direction == StockMovementDirection.IN:
        movement = await increase_stock(
            db=db,
            branch_id=branch_id,
            ingredient_id=payload.ingredient_id,
            quantity=payload.quantity,
            movement_type=StockMovementType.AJUSTE_ENTRADA,
            created_by_user_id=actor_user.id if actor_user else None,
            note=payload.reason,
        )
    else:
        movement = await decrease_stock(
            db=db,
            branch_id=branch_id,
            ingredient_id=payload.ingredient_id,
            quantity=payload.quantity,
            movement_type=StockMovementType.AJUSTE_SALIDA,
            created_by_user_id=actor_user.id if actor_user else None,
            note=payload.reason,
        )

    await db.commit()

    await audit(
        db,
        action="inventory.adjusted",
        resource="stock_movement",
        resource_id=movement.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={
            "ingredient_id": str(payload.ingredient_id),
            "direction": payload.direction.value,
            "quantity": str(payload.quantity),
        },
    )

    return movement


async def list_movements(
    db: AsyncSession,
    branch_id: Optional[UUID] = None,
    ingredient_id: Optional[UUID] = None,
    movement_type: Optional[StockMovementType] = None,
    limit: int = 200,
) -> List[StockMovement]:
    query = (
        select(StockMovement)
        .options(selectinload(StockMovement.ingredient))
        .order_by(StockMovement.created_at.desc())
        .limit(limit)
    )

    if branch_id:
        query = query.where(StockMovement.branch_id == branch_id)

    if ingredient_id:
        query = query.where(StockMovement.ingredient_id == ingredient_id)

    if movement_type:
        query = query.where(StockMovement.movement_type == movement_type)

    return (await db.scalars(query)).all()


async def list_low_stock_alerts(
    db: AsyncSession,
    branch_id: Optional[UUID] = None,
) -> List[StockItem]:
    return await list_stock(db, branch_id=branch_id, low_stock=True)


async def list_suppliers(
    db: AsyncSession,
    include_inactive: bool = False,
) -> List[Supplier]:
    query = select(Supplier).order_by(Supplier.name.asc())

    if not include_inactive:
        query = query.where(Supplier.is_active.is_(True))

    return (await db.scalars(query)).all()


async def create_supplier(
    db: AsyncSession,
    payload: SupplierCreate,
    request: Request | None = None,
    actor_user=None,
) -> Supplier:
    existing = await db.scalar(
        select(Supplier).where(Supplier.name == payload.name)
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un proveedor con este nombre",
        )

    supplier = Supplier(
        name=payload.name,
        contact_name=payload.contact_name,
        phone=payload.phone,
        email=payload.email,
        address=payload.address,
        is_active=payload.is_active,
    )

    db.add(supplier)
    await db.commit()
    await db.refresh(supplier)

    await audit(
        db,
        action="supplier.created",
        resource="supplier",
        resource_id=supplier.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={"name": supplier.name},
    )

    return supplier


async def update_supplier(
    db: AsyncSession,
    supplier_id: UUID,
    payload: SupplierUpdate,
    request: Request | None = None,
    actor_user=None,
) -> Supplier:
    supplier = await db.get(Supplier, supplier_id)

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proveedor no encontrado",
        )

    data = payload.model_dump(exclude_unset=True)

    if payload.name is not None and payload.name != supplier.name:
        existing = await db.scalar(
            select(Supplier).where(
                Supplier.name == payload.name,
                Supplier.id != supplier.id,
            )
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un proveedor con este nombre",
            )

    for field, value in data.items():
        setattr(supplier, field, value)

    await db.commit()
    await db.refresh(supplier)

    await audit(
        db,
        action="supplier.updated",
        resource="supplier",
        resource_id=supplier.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={"name": supplier.name},
    )

    return supplier


async def create_purchase_order(
    db: AsyncSession,
    payload: PurchaseOrderCreate,
    request: Request | None = None,
    actor_user=None,
) -> PurchaseOrder:
    supplier = await db.get(Supplier, payload.supplier_id)

    if not supplier or not supplier.is_active:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El proveedor indicado no es válido",
        )

    branch_id = payload.branch_id

    if not branch_id:
        branch = await _get_default_branch(db)
        branch_id = branch.id

    total = Decimal("0")

    purchase_order = PurchaseOrder(
        branch_id=branch_id,
        supplier_id=supplier.id,
        status=PurchaseOrderStatus.BORRADOR,
        notes=payload.notes,
        created_by_user_id=actor_user.id if actor_user else None,
    )

    for item in payload.items:
        ingredient = await db.get(Ingredient, item.ingredient_id)

        if not ingredient:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Uno de los ingredientes no existe",
            )

        subtotal = item.quantity * item.unit_cost
        total += subtotal

        purchase_order.items.append(
            PurchaseItem(
                ingredient_id=item.ingredient_id,
                quantity=item.quantity,
                unit_cost=item.unit_cost,
                received_quantity=Decimal("0"),
            )
        )

    purchase_order.total = round(total, 2)

    db.add(purchase_order)
    await db.commit()
    await db.refresh(purchase_order)

    await audit(
        db,
        action="purchase_order.created",
        resource="purchase_order",
        resource_id=purchase_order.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={
            "supplier_id": str(supplier.id),
            "total": str(purchase_order.total),
        },
    )

    return purchase_order


async def get_purchase_order(
    db: AsyncSession,
    purchase_id: UUID,
) -> PurchaseOrder:
    purchase_order = await db.scalar(
        select(PurchaseOrder)
        .options(
            selectinload(PurchaseOrder.supplier),
            selectinload(PurchaseOrder.branch),
            selectinload(PurchaseOrder.items).selectinload(
                PurchaseItem.ingredient
            ),
        )
        .where(PurchaseOrder.id == purchase_id)
    )

    if not purchase_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden de compra no encontrada",
        )

    return purchase_order


async def list_purchase_orders(
    db: AsyncSession,
    supplier_id: Optional[UUID] = None,
    purchase_status: Optional[PurchaseOrderStatus] = None,
) -> List[PurchaseOrder]:
    query = (
        select(PurchaseOrder)
        .options(
            selectinload(PurchaseOrder.supplier),
            selectinload(PurchaseOrder.items).selectinload(
                PurchaseItem.ingredient
            ),
        )
        .order_by(PurchaseOrder.created_at.desc())
    )

    if supplier_id:
        query = query.where(PurchaseOrder.supplier_id == supplier_id)

    if purchase_status:
        query = query.where(PurchaseOrder.status == purchase_status)

    return (await db.scalars(query)).all()


async def receive_purchase_order(
    db: AsyncSession,
    purchase_id: UUID,
    request: Request | None = None,
    actor_user=None,
) -> PurchaseOrder:
    purchase_order = await get_purchase_order(db, purchase_id)

    if purchase_order.status != PurchaseOrderStatus.BORRADOR:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Solo se puede recibir una orden de compra en estado BORRADOR",
        )

    branch_id = purchase_order.branch_id

    if not branch_id:
        branch = await _get_default_branch(db)
        branch_id = branch.id

    for item in purchase_order.items:
        await increase_stock(
            db=db,
            branch_id=branch_id,
            ingredient_id=item.ingredient_id,
            quantity=item.quantity,
            movement_type=StockMovementType.COMPRA,
            unit_cost=item.unit_cost,
            purchase_order_id=purchase_order.id,
            created_by_user_id=actor_user.id if actor_user else None,
            note=f"Compra proveedor {purchase_order.supplier.name}",
        )

        item.received_quantity = item.quantity

    purchase_order.status = PurchaseOrderStatus.RECIBIDA
    purchase_order.received_at = datetime.now(timezone.utc)

    await db.commit()

    await audit(
        db,
        action="purchase_order.received",
        resource="purchase_order",
        resource_id=purchase_order.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={
            "supplier_id": str(purchase_order.supplier_id),
            "total": str(purchase_order.total),
        },
    )

    return await get_purchase_order(db, purchase_id)


async def create_waste_event(
    db: AsyncSession,
    payload: WasteCreate,
    request: Request | None = None,
    actor_user=None,
) -> WasteEvent:
    ingredient = await db.get(Ingredient, payload.ingredient_id)

    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingrediente no encontrado",
        )

    branch_id = payload.branch_id

    if not branch_id:
        branch = await _get_default_branch(db)
        branch_id = branch.id

    await decrease_stock(
        db=db,
        branch_id=branch_id,
        ingredient_id=payload.ingredient_id,
        quantity=payload.quantity,
        movement_type=StockMovementType.DESPERDICIO,
        created_by_user_id=actor_user.id if actor_user else None,
        note=payload.reason,
    )

    waste_event = WasteEvent(
        branch_id=branch_id,
        ingredient_id=payload.ingredient_id,
        quantity=payload.quantity,
        reason=payload.reason,
        created_by_user_id=actor_user.id if actor_user else None,
    )

    db.add(waste_event)
    await db.commit()
    await db.refresh(waste_event)

    await audit(
        db,
        action="inventory.waste_registered",
        resource="waste_event",
        resource_id=waste_event.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={
            "ingredient_id": str(payload.ingredient_id),
            "quantity": str(payload.quantity),
        },
    )

    return waste_event
