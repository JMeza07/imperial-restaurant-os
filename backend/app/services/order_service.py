from datetime import datetime, timezone
from decimal import Decimal
from typing import List
from uuid import UUID, uuid4

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import (
    ModificationAction,
    OrderChannel,
    OrderItemStatus,
    OrderStatus,
    OrderType,
    TableStatus,
)
from app.models.catalog import Dish, RecipeIngredient
from app.models.order import ItemModification, Order, OrderEvent, OrderItem
from app.models.restaurant import Branch, Table
from app.schemas.order import CreateOrderRequest, OrderItemRequest
from app.services.audit_service import audit


def order_options():
    return [
        selectinload(Order.table),
        selectinload(Order.items).selectinload(OrderItem.dish),
        selectinload(Order.items).selectinload(OrderItem.modifications),
        selectinload(Order.items).selectinload(OrderItem.prepared_by),
    ]


def order_item_options():
    return [
        selectinload(OrderItem.dish),
        selectinload(OrderItem.modifications),
        selectinload(OrderItem.prepared_by),
    ]


def calculate_unit_price(
    base_price: Decimal,
    modifications: List[tuple[ModificationAction, Decimal]],
) -> Decimal:
    """
    RN-03:
    El precio unitario de un plato es el precio base más la suma
    de los costos extra de los ingredientes agregados.
    Quitar un ingrediente no reduce el precio.
    """

    extras = Decimal("0")

    for action, cost in modifications:
        if action == ModificationAction.AGREGAR:
            extras += cost

    return base_price + extras


def register_event(
    order: Order,
    action: str,
    db: AsyncSession | None = None,
    order_item: OrderItem | None = None,
    actor_user=None,
    actor_role: str | None = None,
    detail: dict | None = None,
) -> OrderEvent:
    event = OrderEvent(
        order=order,
        order_item_id=order_item.id if order_item and order_item.id else None,
        actor_user_id=actor_user.id if actor_user else None,
        actor_role=actor_role,
        action=action,
        detail=detail,
    )
    if db:
        db.add(event)
    return event


async def _get_table_by_qr(
    db: AsyncSession,
    codigo_qr: str,
) -> Table:
    try:
        qr_uuid = UUID(codigo_qr.strip())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mesa no encontrada",
        )

    table = await db.scalar(
        select(Table).where(Table.qr_code == qr_uuid)
    )

    if not table or not table.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mesa no encontrada",
        )

    branch = await db.get(Branch, table.branch_id)

    if not branch or not branch.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mesa no encontrada",
        )

    if table.status == TableStatus.BLOQUEADA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La mesa está bloqueada y no puede recibir pedidos",
        )

    return table


async def _get_order_by_id(
    db: AsyncSession,
    order_id: UUID,
) -> Order:
    order = await db.scalar(
        select(Order)
        .options(*order_options())
        .where(Order.id == order_id)
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden no encontrada",
        )

    return order


async def _get_order_item_by_id(
    db: AsyncSession,
    order_item_id: UUID,
) -> OrderItem:
    item = await db.scalar(
        select(OrderItem)
        .options(*order_item_options())
        .where(OrderItem.id == order_item_id)
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plato no encontrado",
        )

    return item


async def _build_order_item(
    db: AsyncSession,
    item_request: OrderItemRequest,
) -> OrderItem:
    dish = await db.scalar(
        select(Dish)
        .options(
            selectinload(Dish.recipe)
            .selectinload(RecipeIngredient.ingredient)
        )
        .where(Dish.id == item_request.dish_id)
    )

    if not dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plato no encontrado",
        )

    # RN-04: No se puede pedir un plato no disponible.
    if not dish.available:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No se puede pedir el plato '{dish.name}' porque no está disponible",
        )

    recipe_by_ingredient_id = {
        recipe_item.ingredient_id: recipe_item
        for recipe_item in dish.recipe
    }

    price_modifications: List[tuple[ModificationAction, Decimal]] = []
    modification_rows: List[ItemModification] = []

    for modification in item_request.modifications:
        recipe_item = recipe_by_ingredient_id.get(
            modification.ingredient_id
        )

        if not recipe_item:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El ingrediente indicado no hace parte de la receta del plato",
            )

        ingredient = recipe_item.ingredient

        if modification.action in (ModificationAction.QUITAR, ModificationAction.REMOVE):
            # RN-02: Solo se pueden quitar ingredientes removibles.
            if not recipe_item.is_removable:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"No se puede quitar el ingrediente '{ingredient.name}' porque no es removible",
                )

            extra_cost = Decimal("0")

        else:
            # RN-02: Solo se pueden agregar ingredientes adicionables.
            if not recipe_item.is_addable:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"No se puede agregar el ingrediente '{ingredient.name}' porque no es adicionable",
                )

            # RN-04: No se puede pedir un ingrediente adicional no disponible.
            if not ingredient.available:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"No se puede agregar el ingrediente '{ingredient.name}' porque no está disponible",
                )

            if recipe_item.extra_price is not None:
                extra_cost = recipe_item.extra_price
            else:
                extra_cost = ingredient.price_extra

        price_modifications.append(
            (modification.action, extra_cost)
        )

        modification_rows.append(
            ItemModification(
                ingredient_id=ingredient.id,
                ingredient_name=ingredient.name,
                action=modification.action,
                extra_cost=extra_cost,
            )
        )

    # RN-03: Precio unitario = precio base + extras agregados.
    unit_price = calculate_unit_price(
        dish.price_base,
        price_modifications,
    )

    # Cada plato solicitado llega de forma individual (quantity=1) a cocina,
    # permitiendo que varios cocineros preparen platos iguales en paralelo sin cruzarse.
    qty = max(1, item_request.quantity)
    items_list: List[OrderItem] = []

    for _ in range(qty):
        item_mods = [
            ItemModification(
                ingredient_id=mod_row.ingredient_id,
                ingredient_name=mod_row.ingredient_name,
                action=mod_row.action,
                extra_cost=mod_row.extra_cost,
            )
            for mod_row in modification_rows
        ]

        order_item = OrderItem(
            dish_id=dish.id,
            quantity=1,
            unit_price=unit_price,
            subtotal=unit_price,
            status=OrderItemStatus.RECIBIDO,
            observations=item_request.observations,
        )
        order_item.modifications = item_mods
        items_list.append(order_item)

    return items_list


async def create_or_extend_order(
    db: AsyncSession,
    payload: CreateOrderRequest,
    request: Request | None = None,
    actor_user=None,
) -> Order:
    table = await _get_table_by_qr(db, payload.codigo_qr)

    order = await db.scalar(
        select(Order)
        .options(selectinload(Order.items))
        .where(
            Order.table_id == table.id,
            Order.status == OrderStatus.ABIERTA,
        )
    )

    is_new_order = order is None

    if is_new_order:
        order = Order(
            display_code=uuid4().hex[:8].upper(),
            branch_id=table.branch_id,
            table_id=table.id,
            order_type=OrderType.MESA,
            status=OrderStatus.ABIERTA,
            channel=OrderChannel.QR,
            customer_name=payload.customer_name,
            customer_phone=payload.customer_phone,
            subtotal=Decimal("0"),
            tax_amount=Decimal("0"),
            tip_amount=Decimal("0"),
            delivery_fee=Decimal("0"),
            discount_amount=Decimal("0"),
            total=Decimal("0"),
            total_paid=Decimal("0"),
        )

        db.add(order)
    else:
        # RN-07: No se pueden adicionar platos a una orden CERRADA o PAGADA.
        if order.status != OrderStatus.ABIERTA:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se pueden adicionar platos a una orden cerrada o pagada",
            )
        if payload.customer_name and not order.customer_name:
            order.customer_name = payload.customer_name
        if payload.customer_phone and not order.customer_phone:
            order.customer_phone = payload.customer_phone

    new_items: List[OrderItem] = []

    for item_request in payload.items:
        order_items = await _build_order_item(db, item_request)
        for order_item in order_items:
            order_item.order = order
            db.add(order_item)
            new_items.append(order_item)

    if is_new_order:
        current_items = new_items
    else:
        current_items = list(order.items) + new_items

    order.subtotal = sum(
        (
            item.subtotal
            for item in current_items
            if item.status != OrderItemStatus.CANCELADO
        ),
        Decimal("0"),
    )

    order.total = (
        order.subtotal
        + (order.tax_amount or Decimal("0"))
        + (order.tip_amount or Decimal("0"))
        + (order.delivery_fee or Decimal("0"))
        - (order.discount_amount or Decimal("0"))
    )

    if table.status != TableStatus.OCUPADA:
        table.status = TableStatus.OCUPADA

    await db.flush()

    if is_new_order:
        register_event(
            order=order,
            action="order.created",
            db=db,
            actor_user=actor_user,
            actor_role="CLIENTE",
            detail={
                "table_id": str(table.id),
                "table_number": table.number,
            },
        )

    for item in new_items:
        register_event(
            order=order,
            action="order.item_added",
            db=db,
            order_item=item,
            actor_user=actor_user,
            actor_role="CLIENTE",
            detail={
                "dish_id": str(item.dish_id),
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
                "subtotal": str(item.subtotal),
            },
        )

    await db.commit()

    return await _get_order_by_id(db, order.id)


async def get_order_public(
    db: AsyncSession,
    order_id: UUID,
    codigo_qr: str,
) -> Order:
    order = await _get_order_by_id(db, order_id)

    if order.order_type != OrderType.MESA:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden no encontrada",
        )

    table = await _get_table_by_qr(db, codigo_qr)

    if order.table_id != table.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden no encontrada",
        )

    return order


async def list_orders_admin(
    db: AsyncSession,
    order_status: OrderStatus | None = None,
    table_id: UUID | None = None,
    order_type: OrderType | None = None,
) -> List[Order]:
    query = (
        select(Order)
        .options(*order_options())
        .order_by(Order.created_at.desc())
    )

    if order_status:
        query = query.where(Order.status == order_status)

    if table_id:
        query = query.where(Order.table_id == table_id)

    if order_type:
        query = query.where(Order.order_type == order_type)

    return (await db.scalars(query)).all()


async def get_order_admin(
    db: AsyncSession,
    order_id: UUID,
) -> Order:
    return await _get_order_by_id(db, order_id)


async def cancel_order_item(
    db: AsyncSession,
    order_item_id: UUID,
    request: Request | None = None,
    actor_user=None,
) -> OrderItem:
    item = await db.scalar(
        select(OrderItem)
        .options(selectinload(OrderItem.order))
        .where(OrderItem.id == order_item_id)
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plato no encontrado",
        )

    order = item.order

    if order.status != OrderStatus.ABIERTA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se puede cancelar un plato en una orden que no está abierta",
        )

    # RN-05: Solo RECIBIDO puede pasar a CANCELADO.
    if not item.status.can_transition_to(OrderItemStatus.CANCELADO):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El plato no puede cancelarse en su estado actual",
        )

    item.status = OrderItemStatus.CANCELADO
    item.cancelled_at = datetime.now(timezone.utc)

    order.subtotal = sum(
        (
            order_item.subtotal
            for order_item in order.items
            if order_item.status != OrderItemStatus.CANCELADO
        ),
        Decimal("0"),
    )

    await db.flush()

    register_event(
        order=order,
        action="order.item_cancelled",
        order_item=item,
        actor_user=actor_user,
        actor_role=actor_user.role.value if actor_user else None,
        detail={
            "dish_id": str(item.dish_id),
            "previous_status": item.status.value,
        },
    )

    await db.commit()

    await audit(
        db,
        action="order_item.cancelled",
        resource="order_item",
        resource_id=item.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={
            "order_id": str(order.id),
            "dish_id": str(item.dish_id),
        },
    )

    return await _get_order_item_by_id(db, item.id)
