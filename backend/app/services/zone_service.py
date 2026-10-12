from typing import List
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.restaurant import Branch, Zone
from app.schemas.zone import ZoneCreate, ZoneUpdate
from app.services.audit_service import audit


async def list_zones(
    db: AsyncSession,
    branch_id: UUID | None = None,
    include_inactive: bool = False,
) -> List[Zone]:
    query = select(Zone).order_by(Zone.created_at.asc())

    if branch_id:
        query = query.where(Zone.branch_id == branch_id)

    if not include_inactive:
        query = query.where(Zone.is_active.is_(True))

    return (await db.scalars(query)).all()


async def get_zone(
    db: AsyncSession,
    zone_id: UUID,
) -> Zone:
    zone = await db.get(Zone, zone_id)

    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zona no encontrada",
        )

    return zone


async def create_zone(
    db: AsyncSession,
    payload: ZoneCreate,
    request: Request | None = None,
    actor=None,
) -> Zone:
    branch = await db.get(Branch, payload.branch_id)

    if not branch or not branch.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sucursal no encontrada",
        )

    existing_zone = await db.scalar(
        select(Zone).where(
            Zone.branch_id == payload.branch_id,
            Zone.name == payload.name,
        )
    )

    if existing_zone:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una zona con este nombre en la sucursal",
        )

    zone = Zone(
        branch_id=payload.branch_id,
        name=payload.name,
        description=payload.description,
        is_active=True,
    )

    db.add(zone)
    await db.commit()
    await db.refresh(zone)

    await audit(
        db,
        action="zone.created",
        resource="zone",
        resource_id=zone.id,
        user_id=actor.id if actor else None,
        request=request,
        detail={
            "name": zone.name,
            "branch_id": zone.branch_id,
        },
    )

    return zone


async def update_zone(
    db: AsyncSession,
    zone_id: UUID,
    payload: ZoneUpdate,
    request: Request | None = None,
    actor=None,
) -> Zone:
    zone = await get_zone(db, zone_id)

    changes = {}
    data = payload.model_dump(exclude_unset=True)

    if payload.name is not None and payload.name != zone.name:
        existing_zone = await db.scalar(
            select(Zone).where(
                Zone.branch_id == zone.branch_id,
                Zone.name == payload.name,
                Zone.id != zone.id,
            )
        )

        if existing_zone:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una zona con este nombre en la sucursal",
            )

    for field, value in data.items():
        setattr(zone, field, value)
        changes[field] = value

    await db.commit()
    await db.refresh(zone)

    await audit(
        db,
        action="zone.updated",
        resource="zone",
        resource_id=zone.id,
        user_id=actor.id if actor else None,
        request=request,
        detail=changes,
    )

    return zone
