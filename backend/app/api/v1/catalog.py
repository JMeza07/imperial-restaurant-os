from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.enums import UserRole
from app.db.session import get_db
from app.schemas.catalog import (
    AllergenCreate,
    AllergenRead,
    AllergenUpdate,
    AvailabilityUpdate,
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    DietTagCreate,
    DietTagRead,
    DietTagUpdate,
    DishCreate,
    DishPublic,
    DishRead,
    DishUpdate,
    HealthBenefitCreate,
    HealthBenefitRead,
    HealthBenefitUpdate,
    IngredientCreate,
    IngredientRead,
    IngredientUpdate,
    RecipeUpdate,
)
from app.services import catalog_service


router = APIRouter()
admin_router = APIRouter()


@router.get(
    "/carta",
    summary="Carta pública del restaurante",
)
async def get_carta(
    category_id: UUID | None = None,
    search: str | None = None,
    diet_tag: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.get_public_carta(
        db=db,
        category_id=category_id,
        search=search,
        diet_tag=diet_tag,
    )


@router.get(
    "/carta/platos/{dish_id}",
    response_model=DishPublic,
    summary="Detalle público de un plato",
)
async def get_public_dish(
    dish_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.get_public_dish(db, dish_id)


@admin_router.get(
    "/categorias",
    response_model=List[CategoryRead],
    summary="Listar categorías",
)
async def list_categories(
    include_inactive: bool = False,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.list_categories(db, include_inactive)


@admin_router.post(
    "/categorias",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear categoría",
)
async def create_category(
    payload: CategoryCreate,
    request: Request,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.create_category(
        db=db,
        payload=payload,
        request=request,
        actor=current_user,
    )


@admin_router.get(
    "/categorias/{category_id}",
    response_model=CategoryRead,
    summary="Consultar categoría",
)
async def get_category(
    category_id: UUID,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.get_category(db, category_id)


@admin_router.patch(
    "/categorias/{category_id}",
    response_model=CategoryRead,
    summary="Actualizar categoría",
)
async def update_category(
    category_id: UUID,
    payload: CategoryUpdate,
    request: Request,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.update_category(
        db=db,
        category_id=category_id,
        payload=payload,
        request=request,
        actor=current_user,
    )


@admin_router.get(
    "/beneficios",
    response_model=List[HealthBenefitRead],
    summary="Listar beneficios",
)
async def list_benefits(
    include_inactive: bool = False,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.list_benefits(db, include_inactive)


@admin_router.post(
    "/beneficios",
    response_model=HealthBenefitRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear beneficio",
)
async def create_benefit(
    payload: HealthBenefitCreate,
    request: Request,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.create_benefit(
        db=db,
        payload=payload,
        request=request,
        actor=current_user,
    )


@admin_router.patch(
    "/beneficios/{benefit_id}",
    response_model=HealthBenefitRead,
    summary="Actualizar beneficio",
)
async def update_benefit(
    benefit_id: UUID,
    payload: HealthBenefitUpdate,
    request: Request,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.update_benefit(
        db=db,
        benefit_id=benefit_id,
        payload=payload,
        request=request,
        actor=current_user,
    )


@admin_router.get(
    "/alergenos",
    response_model=List[AllergenRead],
    summary="Listar alérgenos",
)
async def list_allergens(
    include_inactive: bool = False,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.list_allergens(db, include_inactive)


@admin_router.post(
    "/alergenos",
    response_model=AllergenRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear alérgeno",
)
async def create_allergen(
    payload: AllergenCreate,
    request: Request,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.create_allergen(
        db=db,
        payload=payload,
        request=request,
        actor=current_user,
    )


@admin_router.patch(
    "/alergenos/{allergen_id}",
    response_model=AllergenRead,
    summary="Actualizar alérgeno",
)
async def update_allergen(
    allergen_id: UUID,
    payload: AllergenUpdate,
    request: Request,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.update_allergen(
        db=db,
        allergen_id=allergen_id,
        payload=payload,
        request=request,
        actor=current_user,
    )


@admin_router.get(
    "/etiquetas-dietarias",
    response_model=List[DietTagRead],
    summary="Listar etiquetas dietarias",
)
async def list_diet_tags(
    include_inactive: bool = False,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.list_diet_tags(db, include_inactive)


@admin_router.post(
    "/etiquetas-dietarias",
    response_model=DietTagRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear etiqueta dietaria",
)
async def create_diet_tag(
    payload: DietTagCreate,
    request: Request,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.create_diet_tag(
        db=db,
        payload=payload,
        request=request,
        actor=current_user,
    )


@admin_router.patch(
    "/etiquetas-dietarias/{diet_tag_id}",
    response_model=DietTagRead,
    summary="Actualizar etiqueta dietaria",
)
async def update_diet_tag(
    diet_tag_id: UUID,
    payload: DietTagUpdate,
    request: Request,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.update_diet_tag(
        db=db,
        diet_tag_id=diet_tag_id,
        payload=payload,
        request=request,
        actor=current_user,
    )


@admin_router.get(
    "/ingredientes",
    response_model=List[IngredientRead],
    summary="Listar ingredientes",
)
async def list_ingredients(
    available: bool | None = None,
    search: str | None = None,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.list_ingredients(
        db=db,
        available=available,
        search=search,
    )


@admin_router.post(
    "/ingredientes",
    response_model=IngredientRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear ingrediente",
)
async def create_ingredient(
    payload: IngredientCreate,
    request: Request,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.create_ingredient(
        db=db,
        payload=payload,
        request=request,
        actor=current_user,
    )


@admin_router.get(
    "/ingredientes/{ingredient_id}",
    response_model=IngredientRead,
    summary="Consultar ingrediente",
)
async def get_ingredient(
    ingredient_id: UUID,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.get_ingredient(db, ingredient_id)


@admin_router.patch(
    "/ingredientes/{ingredient_id}",
    response_model=IngredientRead,
    summary="Actualizar ingrediente",
)
async def update_ingredient(
    ingredient_id: UUID,
    payload: IngredientUpdate,
    request: Request,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.update_ingredient(
        db=db,
        ingredient_id=ingredient_id,
        payload=payload,
        request=request,
        actor=current_user,
    )


@admin_router.patch(
    "/ingredientes/{ingredient_id}/disponibilidad",
    response_model=IngredientRead,
    summary="Cambiar disponibilidad de ingrediente",
)
async def set_ingredient_availability(
    ingredient_id: UUID,
    payload: AvailabilityUpdate,
    request: Request,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.set_ingredient_availability(
        db=db,
        ingredient_id=ingredient_id,
        payload=payload,
        request=request,
        actor=current_user,
    )


@admin_router.get(
    "/platos",
    response_model=List[DishRead],
    summary="Listar platos",
)
async def list_dishes(
    category_id: UUID | None = None,
    available: bool | None = None,
    search: str | None = None,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.list_dishes_admin(
        db=db,
        category_id=category_id,
        available=available,
        search=search,
    )


@admin_router.post(
    "/platos",
    response_model=DishRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear plato",
)
async def create_dish(
    payload: DishCreate,
    request: Request,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.create_dish(
        db=db,
        payload=payload,
        request=request,
        actor=current_user,
    )


@admin_router.get(
    "/platos/{dish_id}",
    response_model=DishRead,
    summary="Consultar plato",
)
async def get_dish(
    dish_id: UUID,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.get_dish_admin(db, dish_id)


@admin_router.patch(
    "/platos/{dish_id}",
    response_model=DishRead,
    summary="Actualizar plato",
)
async def update_dish(
    dish_id: UUID,
    payload: DishUpdate,
    request: Request,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.update_dish(
        db=db,
        dish_id=dish_id,
        payload=payload,
        request=request,
        actor=current_user,
    )


@admin_router.patch(
    "/platos/{dish_id}/disponibilidad",
    response_model=DishRead,
    summary="Cambiar disponibilidad de plato",
)
async def set_dish_availability(
    dish_id: UUID,
    payload: AvailabilityUpdate,
    request: Request,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.set_dish_availability(
        db=db,
        dish_id=dish_id,
        payload=payload,
        request=request,
        actor=current_user,
    )


@admin_router.put(
    "/platos/{dish_id}/receta",
    response_model=DishRead,
    summary="Reemplazar receta del plato",
)
async def update_recipe(
    dish_id: UUID,
    payload: RecipeUpdate,
    request: Request,
    current_user=Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await catalog_service.update_dish_recipe(
        db=db,
        dish_id=dish_id,
        payload=payload,
        request=request,
        actor=current_user,
    )
