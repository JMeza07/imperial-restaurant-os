from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.enums import UserRole
from app.db.session import get_db
from app.schemas.zone import ZoneCreate, ZoneRead, ZoneUpdate
from app.services import zone_service


admin_router = APIRouter()


@admin_router.get(
    "/zones",
    response_model=List[ZoneRead],
    summary="Listar zonas",
)
async def list_zones(
    branch_id: UUID | None = None,
    include_inactive: bool = False,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await zone_service.list_zones(
        db=db,
        branch_id=branch_id,
        include_inactive=include_inactive,
    )


@admin_router.post(
    "/zones",
    response_model=ZoneRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear zona",
)
async def create_zone(
    payload: ZoneCreate,
    request: Request,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await zone_service.create_zone(
        db=db,
        payload=payload,
        request=request,
        actor=current_user,
    )


@admin_router.get(
    "/zones/{zone_id}",
    response_model=ZoneRead,
    summary="Consultar zona",
)
async def get_zone(
    zone_id: UUID,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await zone_service.get_zone(db, zone_id)


@admin_router.patch(
    "/zones/{zone_id}",
    response_model=ZoneRead,
    summary="Actualizar zona",
)
async def update_zone(
    zone_id: UUID,
    payload: ZoneUpdate,
    request: Request,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await zone_service.update_zone(
        db=db,
        zone_id=zone_id,
        payload=payload,
        request=request,
        actor=current_user,
    )
