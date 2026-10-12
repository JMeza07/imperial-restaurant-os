from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.enums import TableStatus, UserRole
from app.db.session import get_db
from app.schemas.table import TableCreate, TablePublic, TableRead, TableUpdate
from app.services import table_service


router = APIRouter()
admin_router = APIRouter()


@router.get(
    "/mesas/qr/{codigo_qr}",
    response_model=TablePublic,
    summary="Validar código QR de mesa",
)
async def validate_qr(
    codigo_qr: str,
    db: AsyncSession = Depends(get_db),
):
    return await table_service.get_table_by_qr(db, codigo_qr)


@admin_router.get(
    "/mesas",
    response_model=List[TableRead],
    summary="Listar mesas",
)
async def list_tables(
    branch_id: UUID | None = None,
    zone_id: UUID | None = None,
    table_status: TableStatus | None = None,
    include_inactive: bool = False,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await table_service.list_tables(
        db=db,
        branch_id=branch_id,
        zone_id=zone_id,
        table_status=table_status,
        include_inactive=include_inactive,
    )


@admin_router.post(
    "/mesas",
    response_model=TableRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear mesa",
)
async def create_table(
    payload: TableCreate,
    request: Request,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await table_service.create_table(
        db=db,
        payload=payload,
        request=request,
        actor=current_user,
    )


@admin_router.get(
    "/mesas/{table_id}",
    response_model=TableRead,
    summary="Consultar mesa",
)
async def get_table(
    table_id: UUID,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await table_service.get_table(db, table_id)


@admin_router.patch(
    "/mesas/{table_id}",
    response_model=TableRead,
    summary="Actualizar mesa",
)
async def update_table(
    table_id: UUID,
    payload: TableUpdate,
    request: Request,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await table_service.update_table(
        db=db,
        table_id=table_id,
        payload=payload,
        request=request,
        actor=current_user,
    )


@admin_router.post(
    "/mesas/{table_id}/regenerate-qr",
    response_model=TableRead,
    summary="Regenerar código QR de la mesa",
)
async def regenerate_qr(
    table_id: UUID,
    request: Request,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await table_service.regenerate_qr(
        db=db,
        table_id=table_id,
        request=request,
        actor=current_user,
    )
