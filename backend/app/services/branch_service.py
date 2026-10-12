from typing import List
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.restaurant import Branch, Restaurant
from app.schemas.branch import BranchCreate, BranchUpdate
from app.services.audit_service import audit


async def list_branches(
    db: AsyncSession,
    include_inactive: bool = False,
) -> List[Branch]:
    query = select(Branch).order_by(Branch.created_at.asc())

    if not include_inactive:
        query = query.where(Branch.is_active.is_(True))

    return (await db.scalars(query)).all()


async def get_branch(
    db: AsyncSession,
    branch_id: UUID,
) -> Branch:
    branch = await db.get(Branch, branch_id)

    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sucursal no encontrada",
        )

    return branch


async def create_branch(
    db: AsyncSession,
    payload: BranchCreate,
    request: Request | None = None,
    actor=None,
) -> Branch:
    restaurant = await db.get(Restaurant, payload.restaurant_id)

    if not restaurant or not restaurant.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurante no encontrado",
        )

    existing_branch = await db.scalar(
        select(Branch).where(
            Branch.restaurant_id == payload.restaurant_id,
            Branch.name == payload.name,
        )
    )

    if existing_branch:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una sucursal con este nombre",
        )

    branch = Branch(
        restaurant_id=payload.restaurant_id,
        name=payload.name,
        address=payload.address,
        phone=payload.phone,
        latitude=payload.latitude,
        longitude=payload.longitude,
        is_active=True,
    )

    db.add(branch)
    await db.commit()
    await db.refresh(branch)

    await audit(
        db,
        action="branch.created",
        resource="branch",
        resource_id=branch.id,
        user_id=actor.id if actor else None,
        request=request,
        detail={
            "name": branch.name,
            "restaurant_id": branch.restaurant_id,
        },
    )

    return branch


async def update_branch(
    db: AsyncSession,
    branch_id: UUID,
    payload: BranchUpdate,
    request: Request | None = None,
    actor=None,
) -> Branch:
    branch = await get_branch(db, branch_id)

    changes = {}
    data = payload.model_dump(exclude_unset=True)

    if payload.name is not None and payload.name != branch.name:
        existing_branch = await db.scalar(
            select(Branch).where(
                Branch.restaurant_id == branch.restaurant_id,
                Branch.name == payload.name,
                Branch.id != branch.id,
            )
        )

        if existing_branch:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una sucursal con este nombre",
            )

    for field, value in data.items():
        setattr(branch, field, value)
        changes[field] = value

    await db.commit()
    await db.refresh(branch)

    await audit(
        db,
        action="branch.updated",
        resource="branch",
        resource_id=branch.id,
        user_id=actor.id if actor else None,
        request=request,
        detail=changes,
    )

    return branch
