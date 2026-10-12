from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.restaurant import Restaurant
from app.schemas.restaurant import RestaurantUpdate
from app.services.audit_service import audit


async def get_default_restaurant(db: AsyncSession) -> Restaurant:
    restaurant = await db.scalar(
        select(Restaurant)
        .where(Restaurant.is_active.is_(True))
        .order_by(Restaurant.created_at.asc())
    )

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurante no encontrado",
        )

    return restaurant


async def update_default_restaurant(
    db: AsyncSession,
    payload: RestaurantUpdate,
    request: Request | None = None,
    actor=None,
) -> Restaurant:
    restaurant = await get_default_restaurant(db)

    changes = {}
    data = payload.model_dump(exclude_unset=True)

    for field, value in data.items():
        setattr(restaurant, field, value)
        changes[field] = value

    await db.commit()
    await db.refresh(restaurant)

    await audit(
        db,
        action="restaurant.updated",
        resource="restaurant",
        resource_id=restaurant.id,
        user_id=actor.id if actor else None,
        request=request,
        detail=changes,
    )

    return restaurant
