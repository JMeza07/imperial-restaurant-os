from typing import List
from uuid import UUID, uuid4

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import OrderStatus, TableStatus
from app.models.order import Order
from app.models.restaurant import Branch, Table, Zone
from app.schemas.table import TableCreate, TablePublic, TableRead, TableUpdate
from app.services.audit_service import audit
from app.services.order_service import order_options


def generate_qr_code() -> UUID:
    return uuid4()


async def list_tables(
    db: AsyncSession,
    branch_id: UUID | None = None,
    zone_id: UUID | None = None,
    table_status: TableStatus | None = None,
    include_inactive: bool = False,
) -> List[Table]:
    query = select(Table).order_by(Table.number.asc())

    if branch_id:
        query = query.where(Table.branch_id == branch_id)

    if zone_id:
        query = query.where(Table.zone_id == zone_id)

    if table_status:
        query = query.where(Table.status == table_status)

    if not include_inactive:
        query = query.where(Table.is_active.is_(True))

    return (await db.scalars(query)).all()


async def get_table(
    db: AsyncSession,
    table_id: UUID,
) -> Table:
    table = await db.get(Table, table_id)

    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mesa no encontrada",
        )

    return table


async def create_table(
    db: AsyncSession,
    payload: TableCreate,
    request: Request | None = None,
    actor=None,
) -> Table:
    branch = await db.get(Branch, payload.branch_id)

    if not branch or not branch.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sucursal no encontrada",
        )

    if payload.zone_id:
        zone = await db.get(Zone, payload.zone_id)

        if not zone or not zone.is_active or zone.branch_id != branch.id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La zona indicada no pertenece a la sucursal",
            )

    existing_table = await db.scalar(
        select(Table).where(
            Table.branch_id == branch.id,
            Table.number == payload.number,
        )
    )

    if existing_table:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una mesa con este número en la sucursal",
        )

    table = Table(
        branch_id=branch.id,
        zone_id=payload.zone_id,
        number=payload.number,
        capacity=payload.capacity,
        status=payload.status,
        qr_code=generate_qr_code(),
        is_active=True,
    )

    db.add(table)
    await db.commit()
    await db.refresh(table)

    await audit(
        db,
        action="table.created",
        resource="table",
        resource_id=table.id,
        user_id=actor.id if actor else None,
        request=request,
        detail={
            "number": table.number,
            "branch_id": table.branch_id,
            "qr_code": table.qr_code,
        },
    )

    return table


async def update_table(
    db: AsyncSession,
    table_id: UUID,
    payload: TableUpdate,
    request: Request | None = None,
    actor=None,
) -> Table:
    table = await get_table(db, table_id)

    changes = {}

    if payload.number is not None and payload.number != table.number:
        existing_table = await db.scalar(
            select(Table).where(
                Table.branch_id == table.branch_id,
                Table.number == payload.number,
                Table.id != table.id,
            )
        )

        if existing_table:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una mesa con este número en la sucursal",
            )

        table.number = payload.number
        changes["number"] = payload.number

    if payload.zone_id is not None:
        zone = await db.get(Zone, payload.zone_id)

        if not zone or not zone.is_active or zone.branch_id != table.branch_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La zona indicada no pertenece a la sucursal",
            )

        table.zone_id = payload.zone_id
        changes["zone_id"] = payload.zone_id

    if payload.capacity is not None:
        table.capacity = payload.capacity
        changes["capacity"] = payload.capacity

    if payload.status is not None:
        table.status = payload.status
        changes["status"] = payload.status.value

    if payload.is_active is not None:
        table.is_active = payload.is_active
        changes["is_active"] = payload.is_active

    await db.commit()
    await db.refresh(table)

    await audit(
        db,
        action="table.updated",
        resource="table",
        resource_id=table.id,
        user_id=actor.id if actor else None,
        request=request,
        detail=changes,
    )

    return table


async def regenerate_qr(
    db: AsyncSession,
    table_id: UUID,
    request: Request | None = None,
    actor=None,
) -> Table:
    table = await get_table(db, table_id)

    old_qr = table.qr_code
    table.qr_code = generate_qr_code()

    await db.commit()
    await db.refresh(table)

    await audit(
        db,
        action="table.qr_regenerated",
        resource="table",
        resource_id=table.id,
        user_id=actor.id if actor else None,
        request=request,
        detail={
            "old_qr": old_qr,
            "new_qr": table.qr_code,
        },
    )

    return table


async def get_table_by_qr(
    db: AsyncSession,
    qr_code: str,
) -> TablePublic:
    try:
        qr_uuid = UUID(qr_code.strip())
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

    zone = None

    if table.zone_id:
        zone = await db.get(Zone, table.zone_id)

        if zone and not zone.is_active:
            zone = None

    # Consultar orden activa (no pagada, no encuestada ni cancelada) asociada a la mesa
    open_order_entity = await db.scalar(
        select(Order)
        .options(*order_options())
        .where(
            Order.table_id == table.id,
            Order.status.notin_([OrderStatus.PAGADA, OrderStatus.ENCUESTADA, OrderStatus.CANCELADA]),
        )
        .order_by(Order.created_at.desc())
    )

    open_order_dict = None
    if open_order_entity:
        open_order_dict = {
            "id": str(open_order_entity.id),
            "display_code": open_order_entity.display_code,
            "status": open_order_entity.status.value,
            "customer_name": open_order_entity.customer_name,
            "customer_phone": open_order_entity.customer_phone,
            "total": float(open_order_entity.total if (open_order_entity.total and open_order_entity.total > 0) else open_order_entity.subtotal),
            "subtotal": float(open_order_entity.subtotal),
            "items": [
                {
                    "id": str(it.id),
                    "dish_id": str(it.dish_id),
                    "dish_name": it.dish.name if it.dish else "Plato",
                    "quantity": it.quantity,
                    "unit_price": float(it.unit_price),
                    "subtotal": float(it.subtotal),
                    "status": it.status.value,
                    "observations": it.observations,
                    "modifications": [
                        {
                            "ingredient_id": str(m.ingredient_id) if m.ingredient_id else None,
                            "ingredient_name": m.ingredient_name or "Ingrediente",
                            "action": m.action.value if hasattr(m.action, "value") else str(m.action),
                        }
                        for m in (it.modifications or [])
                    ],
                }
                for it in (open_order_entity.items or [])
            ],
        }

    return TablePublic(
        id=table.id,
        number=table.number,
        capacity=table.capacity,
        status=table.status,
        branch_id=branch.id,
        branch_name=branch.name,
        zone_id=zone.id if zone else None,
        zone_name=zone.name if zone else None,
        open_order=open_order_dict,
    )
