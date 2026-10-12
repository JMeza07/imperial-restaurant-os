from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.enums import OrderItemStatus, UserRole
from app.db.session import get_db
from app.models.user import User
from app.schemas.kitchen import KitchenItemRead
from app.services import kitchen_service


router = APIRouter()


@router.get(
    "/mesero/listos",
    response_model=List[KitchenItemRead],
    summary="Platos listos para entregar en mesa",
)
async def waiter_ready_items(
    current_user: User = Depends(
        require_roles(UserRole.MESERO, UserRole.ADMIN)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await kitchen_service.get_waiter_ready_items(db)


@router.patch(
    "/mesero/detalles/{item_id}/entregado",
    response_model=KitchenItemRead,
    summary="Marcar plato entregado en mesa",
)
async def mark_delivered(
    item_id: UUID,
    request: Request,
    current_user: User = Depends(
        require_roles(UserRole.MESERO, UserRole.ADMIN)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await kitchen_service.change_item_status(
        db=db,
        order_item_id=item_id,
        target_status=OrderItemStatus.ENTREGADO,
        request=request,
        actor_user=current_user,
    )
