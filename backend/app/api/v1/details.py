from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.kitchen import ItemStateUpdateRequest, KitchenItemRead
from app.services import kitchen_service


router = APIRouter()


@router.patch(
    "/detalles/{item_id}/estado",
    response_model=KitchenItemRead,
    summary="Cambiar estado de un plato según rol y regla de negocio",
)
async def change_item_state(
    item_id: UUID,
    payload: ItemStateUpdateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await kitchen_service.change_item_status(
        db=db,
        order_item_id=item_id,
        target_status=payload.status,
        request=request,
        actor_user=current_user,
    )
