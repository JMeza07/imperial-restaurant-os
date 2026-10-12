from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.enums import UserRole
from app.db.session import get_db
from app.schemas.branch import BranchCreate, BranchRead, BranchUpdate
from app.services import branch_service


admin_router = APIRouter()


@admin_router.get(
    "/branches",
    response_model=List[BranchRead],
    summary="Listar sucursales",
)
async def list_branches(
    include_inactive: bool = False,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await branch_service.list_branches(db, include_inactive)


@admin_router.post(
    "/branches",
    response_model=BranchRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear sucursal",
)
async def create_branch(
    payload: BranchCreate,
    request: Request,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await branch_service.create_branch(
        db=db,
        payload=payload,
        request=request,
        actor=current_user,
    )


@admin_router.get(
    "/branches/{branch_id}",
    response_model=BranchRead,
    summary="Consultar sucursal",
)
async def get_branch(
    branch_id: UUID,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await branch_service.get_branch(db, branch_id)


@admin_router.patch(
    "/branches/{branch_id}",
    response_model=BranchRead,
    summary="Actualizar sucursal",
)
async def update_branch(
    branch_id: UUID,
    payload: BranchUpdate,
    request: Request,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await branch_service.update_branch(
        db=db,
        branch_id=branch_id,
        payload=payload,
        request=request,
        actor=current_user,
    )
