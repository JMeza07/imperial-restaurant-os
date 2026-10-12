from datetime import datetime, timezone
from decimal import Decimal
from typing import List
from uuid import UUID, uuid4

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import (
    DeliveryStatus,
    OrderChannel,
    OrderItemStatus,
    OrderStatus,
    OrderType,
    UserRole,
)
from app.models.delivery import Delivery, DeliveryZone
from app.models.order import Order, OrderItem
from app.models.restaurant import Branch
from app.models.user import User
from app.schemas.delivery import (
    DeliveryAssignRequest,
    DeliveryCreateRequest,
    DeliveryZoneCreate,
    DeliveryZoneUpdate,
)
from app.services.audit_service import audit
from app.services.order_service import _build_order_item, register_event


def can_transition_delivery(
    current_status: DeliveryStatus,
    target_status: DeliveryStatus,
) -> bool:
    """
    Máquina de estados del domicilio:

    PENDIENTE -> ASIGNADO
    PENDIENTE -> CANCELADO
    ASIGNADO -> EN_CAMINO
    ASIGNADO -> CANCELADO
    EN_CAMINO -> ENTREGADO
    """

    if current_status == DeliveryStatus.PENDIENTE:
        return target_status in (
            DeliveryStatus.ASIGNADO,
            DeliveryStatus.CANCELADO,
        )

    if current_status == DeliveryStatus.ASIGNADO:
        return target_status in (
            DeliveryStatus.EN_CAMINO,
            DeliveryStatus.CANCELADO,
        )

    if current_status == DeliveryStatus.EN_CAMINO:
        return target_status == DeliveryStatus.ENTREGADO

    return False


def delivery_options():
    return [
        selectinload(Delivery.order).selectinload(Order.items).selectinload(
            OrderItem.dish
        ),
        selectinload(Delivery.zone),
        selectinload(Delivery.assigned_user),
    ]


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


async def _get_delivery_by_id(
    db: AsyncSession,
    delivery_id: UUID,
) -> Delivery:
    delivery = await db.scalar(
        select(Delivery)
        .options(*delivery_options())
        .where(Delivery.id == delivery_id)
    )

    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domicilio no encontrado",
        )

    return delivery


async def list_delivery_zones(
    db: AsyncSession,
    include_inactive: bool = False,
) -> List[DeliveryZone]:
    query = select(DeliveryZone).order_by(DeliveryZone.name.asc())

    if not include_inactive:
        query = query.where(DeliveryZone.is_active.is_(True))

    return (await db.scalars(query)).all()


async def create_delivery_zone(
    db: AsyncSession,
    payload: DeliveryZoneCreate,
    request: Request | None = None,
    actor_user=None,
) -> DeliveryZone:
    branch_id = payload.branch_id

    if not branch_id:
        branch = await _get_default_branch(db)
        branch_id = branch.id

    existing_zone = await db.scalar(
        select(DeliveryZone).where(
            DeliveryZone.branch_id == branch_id,
            DeliveryZone.name == payload.name,
        )
    )

    if existing_zone:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una zona de domicilio con este nombre",
        )

    zone = DeliveryZone(
        branch_id=branch_id,
        name=payload.name,
        description=payload.description,
        delivery_fee=payload.delivery_fee,
        max_distance_km=payload.max_distance_km,
        is_active=payload.is_active,
    )

    db.add(zone)
    await db.commit()
    await db.refresh(zone)

    await audit(
        db,
        action="delivery_zone.created",
        resource="delivery_zone",
        resource_id=zone.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={
            "name": zone.name,
            "delivery_fee": str(zone.delivery_fee),
        },
    )

    return zone


async def update_delivery_zone(
    db: AsyncSession,
    zone_id: UUID,
    payload: DeliveryZoneUpdate,
    request: Request | None = None,
    actor_user=None,
) -> DeliveryZone:
    zone = await db.get(DeliveryZone, zone_id)

    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zona de domicilio no encontrada",
        )

    changes = {}
    data = payload.model_dump(exclude_unset=True)

    if payload.name is not None and payload.name != zone.name:
        existing_zone = await db.scalar(
            select(DeliveryZone).where(
                DeliveryZone.branch_id == zone.branch_id,
                DeliveryZone.name == payload.name,
                DeliveryZone.id != zone.id,
            )
        )

        if existing_zone:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una zona de domicilio con este nombre",
            )

    for field, value in data.items():
        setattr(zone, field, value)
        changes[field] = value

    await db.commit()
    await db.refresh(zone)

    await audit(
        db,
        action="delivery_zone.updated",
        resource="delivery_zone",
        resource_id=zone.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail=changes,
    )

    return zone


async def create_delivery_order(
    db: AsyncSession,
    payload: DeliveryCreateRequest,
    request: Request | None = None,
    actor_user=None,
) -> Delivery:
    zone = await db.get(DeliveryZone, payload.delivery_zone_id)

    if not zone or not zone.is_active:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La zona de domicilio indicada no es válida",
        )

    branch = await db.get(Branch, zone.branch_id)

    if not branch or not branch.is_active:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La sucursal de la zona de domicilio no está activa",
        )

    delivery_fee = (
        payload.delivery_fee
        if payload.delivery_fee is not None
        else zone.delivery_fee
    )

    channel = OrderChannel.WEB if actor_user is None else OrderChannel.STAFF

    order = Order(
        display_code=uuid4().hex[:8].upper(),
        branch_id=branch.id,
        table_id=None,
        order_type=OrderType.DOMICILIO,
        status=OrderStatus.ABIERTA,
        channel=channel,
        customer_name=payload.customer_name,
        customer_phone=payload.customer_phone,
        customer_address=payload.customer_address,
        notes=payload.notes,
        delivery_fee=delivery_fee,
        subtotal=Decimal("0"),
        tax_amount=Decimal("0"),
        tip_amount=Decimal("0"),
        discount_amount=Decimal("0"),
        total=Decimal("0"),
        total_paid=Decimal("0"),
    )

    for item_request in payload.items:
        order_item = await _build_order_item(db, item_request)
        order.items.append(order_item)

    order.subtotal = sum(
        (item.subtotal for item in order.items),
        Decimal("0"),
    )

    delivery = Delivery(
        order=order,
        delivery_zone_id=zone.id,
        customer_name=payload.customer_name,
        customer_phone=payload.customer_phone,
        customer_address=payload.customer_address,
        delivery_fee=delivery_fee,
        status=DeliveryStatus.PENDIENTE,
        notes=payload.notes,
    )

    db.add(order)
    db.add(delivery)

    await db.flush()

    register_event(
        order=order,
        action="delivery.created",
        actor_user=actor_user,
        actor_role=actor_user.role.value if actor_user else "CLIENTE",
        detail={
            "delivery_id": str(delivery.id),
            "zone": zone.name,
            "delivery_fee": str(delivery_fee),
        },
    )

    await db.commit()

    await audit(
        db,
        action="delivery.created",
        resource="delivery",
        resource_id=delivery.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={
            "order_id": str(order.id),
            "customer_name": delivery.customer_name,
            "zone": zone.name,
        },
    )

    return await _get_delivery_by_id(db, delivery.id)


async def list_deliveries_admin(
    db: AsyncSession,
    delivery_status: DeliveryStatus | None = None,
    order_status: OrderStatus | None = None,
) -> List[Delivery]:
    query = (
        select(Delivery)
        .join(Order, Delivery.order_id == Order.id)
        .options(*delivery_options())
        .order_by(Delivery.created_at.desc())
    )

    if delivery_status:
        query = query.where(Delivery.status == delivery_status)

    if order_status:
        query = query.where(Order.status == order_status)

    return (await db.scalars(query)).all()


async def get_delivery_admin(
    db: AsyncSession,
    delivery_id: UUID,
) -> Delivery:
    return await _get_delivery_by_id(db, delivery_id)


async def get_public_delivery_tracking(
    db: AsyncSession,
    order_id: UUID,
    telefono: str,
) -> Delivery:
    delivery = await db.scalar(
        select(Delivery)
        .options(*delivery_options())
        .where(Delivery.order_id == order_id)
    )

    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domicilio no encontrado",
        )

    normalized_phone = telefono.replace(" ", "").strip()
    stored_phone = delivery.customer_phone.replace(" ", "").strip()

    # RN-13: acceso mínimo y controlado para seguimiento.
    if normalized_phone != stored_phone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domicilio no encontrado",
        )

    return delivery


async def assign_delivery(
    db: AsyncSession,
    delivery_id: UUID,
    payload: DeliveryAssignRequest,
    request: Request | None = None,
    actor_user=None,
) -> Delivery:
    delivery = await _get_delivery_by_id(db, delivery_id)

    if delivery.status not in (
        DeliveryStatus.PENDIENTE,
        DeliveryStatus.ASIGNADO,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se puede asignar un domiciliario en el estado actual",
        )

    domiciliario = await db.get(User, payload.domiciliario_id)

    if (
        not domiciliario
        or not domiciliario.is_active
        or domiciliario.role != UserRole.DOMICILIARIO
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El usuario indicado no es un domiciliario activo",
        )

    now = datetime.now(timezone.utc)

    delivery.assigned_domiciliario_id = domiciliario.id
    delivery.status = DeliveryStatus.ASIGNADO
    delivery.assigned_at = now

    await db.flush()

    register_event(
        order=delivery.order,
        action="delivery.assigned",
        actor_user=actor_user,
        actor_role=actor_user.role.value if actor_user else None,
        detail={
            "delivery_id": str(delivery.id),
            "domiciliario_id": str(domiciliario.id),
        },
    )

    await db.commit()

    await audit(
        db,
        action="delivery.assigned",
        resource="delivery",
        resource_id=delivery.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={
            "order_id": str(delivery.order_id),
            "domiciliario_id": str(domiciliario.id),
        },
    )

    return await _get_delivery_by_id(db, delivery.id)


def _validate_assigned_or_admin(
    delivery: Delivery,
    actor_user: User,
) -> None:
    if actor_user.role == UserRole.ADMIN:
        return

    if delivery.assigned_domiciliario_id != actor_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el domiciliario asignado o un administrador puede ejecutar esta acción",
        )


def _validate_items_ready_for_dispatch(order: Order) -> None:
    active_items = [
        item
        for item in order.items
        if item.status != OrderItemStatus.CANCELADO
    ]

    if not active_items:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El domicilio no tiene platos activos para despachar",
        )

    pending_items = [
        item
        for item in active_items
        if item.status
        not in (
            OrderItemStatus.LISTO,
            OrderItemStatus.ENTREGADO,
        )
    ]

    if pending_items:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se puede despachar el domicilio porque hay platos pendientes en cocina",
        )


async def mark_delivery_en_camino(
    db: AsyncSession,
    delivery_id: UUID,
    request: Request | None = None,
    actor_user=None,
) -> Delivery:
    delivery = await _get_delivery_by_id(db, delivery_id)

    if not can_transition_delivery(
        delivery.status,
        DeliveryStatus.EN_CAMINO,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se puede marcar EN_CAMINO en el estado actual",
        )

    _validate_assigned_or_admin(delivery, actor_user)
    _validate_items_ready_for_dispatch(delivery.order)

    now = datetime.now(timezone.utc)

    delivery.status = DeliveryStatus.EN_CAMINO
    delivery.enroute_at = now

    await db.flush()

    register_event(
        order=delivery.order,
        action="delivery.en_camino",
        actor_user=actor_user,
        actor_role=actor_user.role.value if actor_user else None,
        detail={
            "delivery_id": str(delivery.id),
        },
    )

    await db.commit()

    await audit(
        db,
        action="delivery.en_camino",
        resource="delivery",
        resource_id=delivery.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={
            "order_id": str(delivery.order_id),
        },
    )

    return await _get_delivery_by_id(db, delivery.id)


async def mark_delivery_entregado(
    db: AsyncSession,
    delivery_id: UUID,
    request: Request | None = None,
    actor_user=None,
) -> Delivery:
    delivery = await _get_delivery_by_id(db, delivery_id)

    if not can_transition_delivery(
        delivery.status,
        DeliveryStatus.ENTREGADO,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se puede marcar ENTREGADO en el estado actual",
        )

    _validate_assigned_or_admin(delivery, actor_user)
    _validate_items_ready_for_dispatch(delivery.order)

    now = datetime.now(timezone.utc)

    for item in delivery.order.items:
        if item.status == OrderItemStatus.CANCELADO:
            continue

        if item.status == OrderItemStatus.LISTO:
            item.status = OrderItemStatus.ENTREGADO
            item.delivered_at = now
            item.delivered_by_user_id = actor_user.id

            register_event(
                order=delivery.order,
                action="order.item_status_changed",
                order_item=item,
                actor_user=actor_user,
                actor_role=actor_user.role.value if actor_user else None,
                detail={
                    "old_status": OrderItemStatus.LISTO.value,
                    "new_status": OrderItemStatus.ENTREGADO.value,
                    "reason": "delivery_entregado",
                },
            )

        elif item.status != OrderItemStatus.ENTREGADO:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se puede entregar el domicilio porque hay platos pendientes",
            )

    delivery.status = DeliveryStatus.ENTREGADO
    delivery.delivered_at = now

    await db.flush()

    register_event(
        order=delivery.order,
        action="delivery.entregado",
        actor_user=actor_user,
        actor_role=actor_user.role.value if actor_user else None,
        detail={
            "delivery_id": str(delivery.id),
        },
    )

    await db.commit()

    await audit(
        db,
        action="delivery.entregado",
        resource="delivery",
        resource_id=delivery.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={
            "order_id": str(delivery.order_id),
        },
    )

    return await _get_delivery_by_id(db, delivery.id)


async def cancel_delivery(
    db: AsyncSession,
    delivery_id: UUID,
    request: Request | None = None,
    actor_user=None,
) -> Delivery:
    delivery = await _get_delivery_by_id(db, delivery_id)

    if not can_transition_delivery(
        delivery.status,
        DeliveryStatus.CANCELADO,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se puede cancelar el domicilio en el estado actual",
        )

    now = datetime.now(timezone.utc)

    delivery.status = DeliveryStatus.CANCELADO
    delivery.cancelled_at = now

    await db.flush()

    register_event(
        order=delivery.order,
        action="delivery.cancelled",
        actor_user=actor_user,
        actor_role=actor_user.role.value if actor_user else None,
        detail={
            "delivery_id": str(delivery.id),
        },
    )

    await db.commit()

    await audit(
        db,
        action="delivery.cancelled",
        resource="delivery",
        resource_id=delivery.id,
        user_id=actor_user.id if actor_user else None,
        request=request,
        detail={
            "order_id": str(delivery.order_id),
        },
    )

    return await _get_delivery_by_id(db, delivery.id)
