from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.enums import OrderItemStatus, UserRole
from app.db.session import get_db
from app.models.user import User
from app.schemas.kitchen import KitchenItemRead
from app.schemas.order import OrderRead
from app.services import kitchen_service


router = APIRouter()


@router.get(
    "/cocina/pendientes",
    response_model=List[KitchenItemRead],
    summary="Platos pendientes en cocina",
)
async def kitchen_pending(
    current_user: User = Depends(
        require_roles(UserRole.COCINERO, UserRole.ADMIN)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await kitchen_service.get_kitchen_pending(db)


@router.get(
    "/cocina/ordenes-activas",
    response_model=List[OrderRead],
    summary="Comandas y órdenes activas en cocina para pantalla KDS",
)
async def kitchen_active_orders(
    current_user: User = Depends(
        require_roles(UserRole.COCINERO, UserRole.ADMIN, UserRole.MESERO)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await kitchen_service.get_kitchen_active_orders(db)


@router.patch(
    "/cocina/detalles/{item_id}/en-preparacion",
    response_model=KitchenItemRead,
    summary="Marcar plato en preparación",
)
async def start_preparation(
    item_id: UUID,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.COCINERO, UserRole.ADMIN)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await kitchen_service.change_item_status(
        db=db,
        order_item_id=item_id,
        target_status=OrderItemStatus.EN_PREPARACION,
        request=request,
        actor_user=current_user,
    )


@router.patch(
    "/cocina/detalles/{item_id}/listo",
    response_model=KitchenItemRead,
    summary="Marcar plato listo",
)
async def mark_ready(
    item_id: UUID,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.COCINERO, UserRole.ADMIN)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await kitchen_service.change_item_status(
        db=db,
        order_item_id=item_id,
        target_status=OrderItemStatus.LISTO,
        request=request,
        actor_user=current_user,
    )
