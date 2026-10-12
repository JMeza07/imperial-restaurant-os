from datetime import datetime, timezone
from decimal import Decimal
from typing import List
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import (
    OrderItemStatus,
    OrderStatus,
    OrderType,
    UserRole,
)
from app.models.order import Order, OrderItem
from app.schemas.kitchen import KitchenItemRead
from app.services.audit_service import audit
from app.services.order_service import register_event


def kitchen_item_options():
    return [
        selectinload(OrderItem.order).selectinload(Order.table),
        selectinload(OrderItem.dish),
        selectinload(OrderItem.modifications),
        selectinload(OrderItem.prepared_by),
    ]


def can_change_item_status(
    order_type: OrderType,
    current_status: OrderItemStatus,
    target_status: OrderItemStatus,
    role: UserRole,
) -> bool:
    """
    Regla de negocio RN-05:
    RECIBIDO -> EN_PREPARACION -> LISTO -> ENTREGADO.
    Solo RECIBIDO puede pasar a CANCELADO.

    Regla de negocio RN-06:
    Solo cocinero cambia a EN_PREPARACION y LISTO.
    Solo mesero marca ENTREGADO en mesa.
    Solo domiciliario marca ENTREGADO en domicilio.
    """

    if not current_status.can_transition_to(target_status):
        return False

    if target_status in (
        OrderItemStatus.EN_PREPARACION,
        OrderItemStatus.LISTO,
    ):
        return role in (
            UserRole.COCINERO,
            UserRole.ADMIN,
        )

    if target_status == OrderItemStatus.ENTREGADO:
        if order_type == OrderType.MESA:
            return role in (
                UserRole.MESERO,
                UserRole.ADMIN,
            )

        if order_type == OrderType.DOMICILIO:
            return role in (
                UserRole.DOMICILIARIO,
                UserRole.ADMIN,
            )

        return False

    if target_status == OrderItemStatus.CANCELADO:
        return role == UserRole.ADMIN

    return False


def _assert_role_for_transition(
    order: Order,
    target_status: OrderItemStatus,
    role: UserRole,
) -> None:
    if target_status in (
        OrderItemStatus.EN_PREPARACION,
        OrderItemStatus.LISTO,
    ):
        if role not in (
            UserRole.COCINERO,
            UserRole.ADMIN,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el cocinero o un administrador puede ejecutar esta acción",
            )

        return

    if target_status == OrderItemStatus.ENTREGADO:
        if order.order_type == OrderType.MESA:
            if role not in (
                UserRole.MESERO,
                UserRole.ADMIN,
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo el mesero o un administrador puede entregar un plato en mesa",
                )

            return

        if order.order_type == OrderType.DOMICILIO:
            if role not in (
                UserRole.DOMICILIARIO,
                UserRole.ADMIN,
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo el domiciliario o un administrador puede entregar un domicilio",
                )

            return

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El tipo de orden no soporta entrega",
        )

    if target_status == OrderItemStatus.CANCELADO:
        if role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo un administrador puede cancelar un plato",
            )

        return

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Estado destino no soportado",
    )


async def _get_order_item(
    db: AsyncSession,
    order_item_id: UUID,
) -> OrderItem:
    item = await db.scalar(
        select(OrderItem)
        .options(*kitchen_item_options())
        .where(OrderItem.id == order_item_id)
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plato no encontrado",
        )

    return item


async def get_kitchen_pending(
    db: AsyncSession,
) -> List[OrderItem]:
    query = (
        select(OrderItem)
        .join(Order, OrderItem.order_id == Order.id)
        .options(*kitchen_item_options())
        .where(
            Order.status == OrderStatus.ABIERTA,
            OrderItem.status.in_(
                [
                    OrderItemStatus.RECIBIDO,
                    OrderItemStatus.EN_PREPARACION,
                ]
            ),
        )
        .order_by(OrderItem.created_at.asc())
    )

    return (await db.scalars(query)).all()


async def get_kitchen_active_orders(
    db: AsyncSession,
) -> List[Order]:
    query = (
        select(Order)
        .options(
            selectinload(Order.table),
            selectinload(Order.items).selectinload(OrderItem.dish),
            selectinload(Order.items).selectinload(OrderItem.modifications),
            selectinload(Order.items).selectinload(OrderItem.prepared_by),
        )
        .where(
            Order.status == OrderStatus.ABIERTA,
            Order.items.any(
                OrderItem.status.in_(
                    [
                        OrderItemStatus.RECIBIDO,
                        OrderItemStatus.EN_PREPARACION,
                        OrderItemStatus.LISTO,
                    ]
                )
            ),
        )
        .order_by(Order.opened_at.asc())
    )

    orders = (await db.scalars(query)).unique().all()
    # Filter items to only show active items (not cancelled and not delivered, or show active sequence)
    for ord in orders:
        ord.items = [
            it
            for it in ord.items
            if it.status in [
                OrderItemStatus.RECIBIDO,
                OrderItemStatus.EN_PREPARACION,
                OrderItemStatus.LISTO,
            ]
        ]
    return [ord for ord in orders if len(ord.items) > 0]


async def get_waiter_ready_items(
    db: AsyncSession,
) -> List[OrderItem]:
    query = (
        select(OrderItem)
        .join(Order, OrderItem.order_id == Order.id)
        .options(*kitchen_item_options())
        .where(
            Order.status == OrderStatus.ABIERTA,
            Order.order_type == OrderType.MESA,
            Order.table_id.is_not(None),
            OrderItem.status == OrderItemStatus.LISTO,
        )
        .order_by(OrderItem.ready_at.asc().nulls_last())
    )

    return (await db.scalars(query)).all()


async def change_item_status(
    db: AsyncSession,
    order_item_id: UUID,
    target_status: OrderItemStatus,
    request: Request | None = None,
    actor_user=None,
) -> OrderItem:
    item = await _get_order_item(db, order_item_id)
    order = item.order

    if order.status != OrderStatus.ABIERTA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se puede cambiar el estado de un plato en una orden que no está abierta",
        )

    # RN-05: Validación de transición de estados.
    if not item.status.can_transition_to(target_status):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No se puede cambiar el plato de {item.status.value} a {target_status.value}",
        )

    # RN-06: Validación de rol por tipo de transición.
    _assert_role_for_transition(order, target_status, actor_user.role)

    # REGLA DE EXCLUSIVIDAD DE PREPARACIÓN:
    # Un plato solo puede ser preparado por el cocinero que lo inició.
    # Dos cocineros no pueden cruzarse en la preparación del mismo plato de la comanda.
    if item.status == OrderItemStatus.EN_PREPARACION:
        if item.prepared_by_user_id and item.prepared_by_user_id != actor_user.id:
            # Solo el mismo cocinero o un ADMIN puede cambiar su estado o marcarlo listo
            if actor_user.role != UserRole.ADMIN:
                preparer_name = item.preparer_name or "otro cocinero"
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Este plato ya está siendo preparado por {preparer_name}. Dos cocineros no pueden preparar el mismo plato.",
                )

    old_status = item.status
    now = datetime.now(timezone.utc)

    if target_status == OrderItemStatus.EN_PREPARACION:
        item.prepared_at = now
        item.prepared_by_user_id = actor_user.id

    elif target_status == OrderItemStatus.LISTO:
        item.ready_at = now
        item.ready_by_user_id = actor_user.id

    elif target_status == OrderItemStatus.ENTREGADO:
        item.delivered_at = now
        item.delivered_by_user_id = actor_user.id

    elif target_status == OrderItemStatus.CANCELADO:
        item.cancelled_at = now
        item.cancelled_by_user_id = actor_user.id

        order.subtotal = sum(
            (
                order_item.subtotal
                for order_item in order.items
                if order_item.status != OrderItemStatus.CANCELADO
            ),
            Decimal("0"),
        )

    item.status = target_status

    await db.flush()

    register_event(
        order=order,
        action="order.item_status_changed",
        order_item=item,
        actor_user=actor_user,
        actor_role=actor_user.role.value if actor_user else None,
        detail={
            "old_status": old_status.value,
            "new_status": target_status.value,
        },
    )

    await db.commit()

    await audit(
        db,
        action="order_item.status_changed",
        resource="order_item",
        resource_id=item.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={
            "order_id": str(order.id),
            "dish_id": str(item.dish_id),
            "old_status": old_status.value,
            "new_status": target_status.value,
        },
    )

    return await _get_order_item(db, item.id)
