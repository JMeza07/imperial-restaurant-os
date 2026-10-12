from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.enums import UserRole
from app.db.session import get_db
from app.schemas.restaurant import RestaurantRead, RestaurantUpdate
from app.services import restaurant_service


router = APIRouter()
admin_router = APIRouter()


@router.get(
    "/restaurant/profile",
    response_model=RestaurantRead,
    summary="Perfil público del restaurante",
)
async def get_restaurant_profile(
    db: AsyncSession = Depends(get_db),
):
    return await restaurant_service.get_default_restaurant(db)


@admin_router.put(
    "/restaurant/profile",
    response_model=RestaurantRead,
    summary="Actualizar perfil del restaurante",
)
async def update_restaurant_profile(
    payload: RestaurantUpdate,
    request: Request,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await restaurant_service.update_default_restaurant(
        db=db,
        payload=payload,
        request=request,
        actor=current_user,
    )
