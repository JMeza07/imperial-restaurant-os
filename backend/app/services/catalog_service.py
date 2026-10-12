from typing import List
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.catalog import (
    Allergen,
    Category,
    DietTag,
    Dish,
    DishDietTag,
    HealthBenefit,
    Ingredient,
    IngredientAllergen,
    IngredientBenefit,
    IngredientDietTag,
    RecipeIngredient,
)
from app.schemas.catalog import (
    AllergenCreate,
    AllergenUpdate,
    AvailabilityUpdate,
    CategoryCreate,
    CategoryUpdate,
    DietTagCreate,
    DietTagUpdate,
    DishCreate,
    DishUpdate,
    HealthBenefitCreate,
    HealthBenefitUpdate,
    IngredientCreate,
    IngredientUpdate,
    RecipeUpdate,
)
from app.services.audit_service import audit


def ingredient_options():
    return [
        selectinload(Ingredient.benefit_links).selectinload(
            IngredientBenefit.benefit
        ),
        selectinload(Ingredient.allergen_links).selectinload(
            IngredientAllergen.allergen
        ),
        selectinload(Ingredient.diet_tag_links).selectinload(
            IngredientDietTag.diet_tag
        ),
    ]


def dish_options():
    return [
        selectinload(Dish.category),
        selectinload(Dish.diet_tag_links).selectinload(DishDietTag.diet_tag),
        selectinload(Dish.recipe)
        .selectinload(RecipeIngredient.ingredient)
        .selectinload(Ingredient.benefit_links)
        .selectinload(IngredientBenefit.benefit),
        selectinload(Dish.recipe)
        .selectinload(RecipeIngredient.ingredient)
        .selectinload(Ingredient.allergen_links)
        .selectinload(IngredientAllergen.allergen),
        selectinload(Dish.recipe)
        .selectinload(RecipeIngredient.ingredient)
        .selectinload(Ingredient.diet_tag_links)
        .selectinload(IngredientDietTag.diet_tag),
    ]


async def list_categories(
    db: AsyncSession,
    include_inactive: bool = False,
) -> List[Category]:
    query = select(Category).order_by(Category.sort_order.asc())

    if not include_inactive:
        query = query.where(Category.is_active.is_(True))

    return (await db.scalars(query)).all()


async def get_category(db: AsyncSession, category_id: UUID) -> Category:
    category = await db.get(Category, category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada",
        )

    return category


async def create_category(
    db: AsyncSession,
    payload: CategoryCreate,
    request: Request | None = None,
    actor=None,
) -> Category:
    existing = await db.scalar(
        select(Category).where(Category.name == payload.name)
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una categoría con este nombre",
        )

    category = Category(
        name=payload.name,
        description=payload.description,
        sort_order=payload.sort_order,
        is_active=payload.is_active,
    )

    db.add(category)
    await db.commit()
    await db.refresh(category)

    await audit(
        db,
        action="category.created",
        resource="category",
        resource_id=category.id,
        user_id=actor.id if actor else None,
        request=request,
        detail={"name": category.name},
    )

    return category


async def update_category(
    db: AsyncSession,
    category_id: UUID,
    payload: CategoryUpdate,
    request: Request | None = None,
    actor=None,
) -> Category:
    category = await get_category(db, category_id)
    changes = {}
    data = payload.model_dump(exclude_unset=True)

    if payload.name is not None and payload.name != category.name:
        existing = await db.scalar(
            select(Category).where(
                Category.name == payload.name,
                Category.id != category.id,
            )
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una categoría con este nombre",
            )

    for field, value in data.items():
        setattr(category, field, value)
        changes[field] = value

    await db.commit()
    await db.refresh(category)

    await audit(
        db,
        action="category.updated",
        resource="category",
        resource_id=category.id,
        user_id=actor.id if actor else None,
        request=request,
        detail=changes,
    )

    return category


async def list_benefits(
    db: AsyncSession,
    include_inactive: bool = False,
) -> List[HealthBenefit]:
    query = select(HealthBenefit).order_by(HealthBenefit.name.asc())

    if not include_inactive:
        query = query.where(HealthBenefit.is_active.is_(True))

    return (await db.scalars(query)).all()


async def create_benefit(
    db: AsyncSession,
    payload: HealthBenefitCreate,
    request: Request | None = None,
    actor=None,
) -> HealthBenefit:
    existing = await db.scalar(
        select(HealthBenefit).where(HealthBenefit.name == payload.name)
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un beneficio con este nombre",
        )

    benefit = HealthBenefit(
        name=payload.name,
        description=payload.description,
        icon=payload.icon,
        category=payload.category,
        is_active=payload.is_active,
    )

    db.add(benefit)
    await db.commit()
    await db.refresh(benefit)

    await audit(
        db,
        action="health_benefit.created",
        resource="health_benefit",
        resource_id=benefit.id,
        user_id=actor.id if actor else None,
        request=request,
        detail={"name": benefit.name},
    )

    return benefit


async def update_benefit(
    db: AsyncSession,
    benefit_id: UUID,
    payload: HealthBenefitUpdate,
    request: Request | None = None,
    actor=None,
) -> HealthBenefit:
    benefit = await db.get(HealthBenefit, benefit_id)

    if not benefit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Beneficio no encontrado",
        )

    changes = {}
    data = payload.model_dump(exclude_unset=True)

    if payload.name is not None and payload.name != benefit.name:
        existing = await db.scalar(
            select(HealthBenefit).where(
                HealthBenefit.name == payload.name,
                HealthBenefit.id != benefit.id,
            )
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un beneficio con este nombre",
            )

    for field, value in data.items():
        setattr(benefit, field, value)
        changes[field] = value

    await db.commit()
    await db.refresh(benefit)

    await audit(
        db,
        action="health_benefit.updated",
        resource="health_benefit",
        resource_id=benefit.id,
        user_id=actor.id if actor else None,
        request=request,
        detail=changes,
    )

    return benefit


async def list_allergens(
    db: AsyncSession,
    include_inactive: bool = False,
) -> List[Allergen]:
    query = select(Allergen).order_by(Allergen.name.asc())

    if not include_inactive:
        query = query.where(Allergen.is_active.is_(True))

    return (await db.scalars(query)).all()


async def create_allergen(
    db: AsyncSession,
    payload: AllergenCreate,
    request: Request | None = None,
    actor=None,
) -> Allergen:
    existing = await db.scalar(
        select(Allergen).where(Allergen.name == payload.name)
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un alérgeno con este nombre",
        )

    allergen = Allergen(
        name=payload.name,
        description=payload.description,
        severity=payload.severity,
        is_active=payload.is_active,
    )

    db.add(allergen)
    await db.commit()
    await db.refresh(allergen)

    await audit(
        db,
        action="allergen.created",
        resource="allergen",
        resource_id=allergen.id,
        user_id=actor.id if actor else None,
        request=request,
        detail={"name": allergen.name},
    )

    return allergen


async def update_allergen(
    db: AsyncSession,
    allergen_id: UUID,
    payload: AllergenUpdate,
    request: Request | None = None,
    actor=None,
) -> Allergen:
    allergen = await db.get(Allergen, allergen_id)

    if not allergen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alérgeno no encontrado",
        )

    changes = {}
    data = payload.model_dump(exclude_unset=True)

    if payload.name is not None and payload.name != allergen.name:
        existing = await db.scalar(
            select(Allergen).where(
                Allergen.name == payload.name,
                Allergen.id != allergen.id,
            )
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un alérgeno con este nombre",
            )

    for field, value in data.items():
        setattr(allergen, field, value)
        changes[field] = value

    await db.commit()
    await db.refresh(allergen)

    await audit(
        db,
        action="allergen.updated",
        resource="allergen",
        resource_id=allergen.id,
        user_id=actor.id if actor else None,
        request=request,
        detail=changes,
    )

    return allergen


async def list_diet_tags(
    db: AsyncSession,
    include_inactive: bool = False,
) -> List[DietTag]:
    query = select(DietTag).order_by(DietTag.name.asc())

    if not include_inactive:
        query = query.where(DietTag.is_active.is_(True))

    return (await db.scalars(query)).all()


async def create_diet_tag(
    db: AsyncSession,
    payload: DietTagCreate,
    request: Request | None = None,
    actor=None,
) -> DietTag:
    existing = await db.scalar(
        select(DietTag).where(DietTag.name == payload.name)
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una etiqueta dietaria con este nombre",
        )

    tag = DietTag(
        name=payload.name,
        description=payload.description,
        is_active=payload.is_active,
    )

    db.add(tag)
    await db.commit()
    await db.refresh(tag)

    await audit(
        db,
        action="diet_tag.created",
        resource="diet_tag",
        resource_id=tag.id,
        user_id=actor.id if actor else None,
        request=request,
        detail={"name": tag.name},
    )

    return tag


async def update_diet_tag(
    db: AsyncSession,
    diet_tag_id: UUID,
    payload: DietTagUpdate,
    request: Request | None = None,
    actor=None,
) -> DietTag:
    tag = await db.get(DietTag, diet_tag_id)

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Etiqueta dietaria no encontrada",
        )

    changes = {}
    data = payload.model_dump(exclude_unset=True)

    if payload.name is not None and payload.name != tag.name:
        existing = await db.scalar(
            select(DietTag).where(
                DietTag.name == payload.name,
                DietTag.id != tag.id,
            )
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una etiqueta dietaria con este nombre",
            )

    for field, value in data.items():
        setattr(tag, field, value)
        changes[field] = value

    await db.commit()
    await db.refresh(tag)

    await audit(
        db,
        action="diet_tag.updated",
        resource="diet_tag",
        resource_id=tag.id,
        user_id=actor.id if actor else None,
        request=request,
        detail=changes,
    )

    return tag


async def list_ingredients(
    db: AsyncSession,
    available: bool | None = None,
    search: str | None = None,
) -> List[Ingredient]:
    query = select(Ingredient).options(*ingredient_options())

    if available is not None:
        query = query.where(Ingredient.available.is_(available))

    if search:
        query = query.where(Ingredient.name.ilike(f"%{search}%"))

    query = query.order_by(Ingredient.name.asc())

    return (await db.scalars(query)).all()


async def get_ingredient(
    db: AsyncSession,
    ingredient_id: UUID,
) -> Ingredient:
    ingredient = await db.scalar(
        select(Ingredient)
        .options(*ingredient_options())
        .where(Ingredient.id == ingredient_id)
    )

    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingrediente no encontrado",
        )

    return ingredient


async def _validate_and_get_entities_by_ids(
    db: AsyncSession,
    model,
    ids: List[UUID],
    entity_name: str,
):
    unique_ids = list(dict.fromkeys(ids))

    if not unique_ids:
        return []

    rows = await db.scalars(
        select(model).where(model.id.in_(unique_ids))
    )

    rows_list = rows.all()

    if len(rows_list) != len(unique_ids):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Existen {entity_name} inválidos en la solicitud",
        )

    return rows_list


async def create_ingredient(
    db: AsyncSession,
    payload: IngredientCreate,
    request: Request | None = None,
    actor=None,
) -> Ingredient:
    existing = await db.scalar(
        select(Ingredient).where(Ingredient.name == payload.name)
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un ingrediente con este nombre",
        )

    await _validate_and_get_entities_by_ids(
        db=db,
        model=HealthBenefit,
        ids=payload.benefit_ids,
        entity_name="beneficios",
    )

    await _validate_and_get_entities_by_ids(
        db=db,
        model=Allergen,
        ids=payload.allergen_ids,
        entity_name="alérgenos",
    )

    await _validate_and_get_entities_by_ids(
        db=db,
        model=DietTag,
        ids=payload.diet_tag_ids,
        entity_name="etiquetas dietarias",
    )

    data = payload.model_dump(
        exclude={"benefit_ids", "allergen_ids", "diet_tag_ids"}
    )

    ingredient = Ingredient(**data)

    for benefit_id in dict.fromkeys(payload.benefit_ids):
        ingredient.benefit_links.append(
            IngredientBenefit(benefit_id=benefit_id)
        )

    for allergen_id in dict.fromkeys(payload.allergen_ids):
        ingredient.allergen_links.append(
            IngredientAllergen(allergen_id=allergen_id)
        )

    for diet_tag_id in dict.fromkeys(payload.diet_tag_ids):
        ingredient.diet_tag_links.append(
            IngredientDietTag(diet_tag_id=diet_tag_id)
        )

    db.add(ingredient)
    await db.commit()

    ingredient = await get_ingredient(db, ingredient.id)

    await audit(
        db,
        action="ingredient.created",
        resource="ingredient",
        resource_id=ingredient.id,
        user_id=actor.id if actor else None,
        request=request,
        detail={"name": ingredient.name},
    )

    return ingredient


async def update_ingredient(
    db: AsyncSession,
    ingredient_id: UUID,
    payload: IngredientUpdate,
    request: Request | None = None,
    actor=None,
) -> Ingredient:
    ingredient = await get_ingredient(db, ingredient_id)

    changes = {}

    data = payload.model_dump(
        exclude_unset=True,
        exclude={"benefit_ids", "allergen_ids", "diet_tag_ids"},
    )

    if payload.name is not None and payload.name != ingredient.name:
        existing = await db.scalar(
            select(Ingredient).where(
                Ingredient.name == payload.name,
                Ingredient.id != ingredient.id,
            )
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un ingrediente con este nombre",
            )

    for field, value in data.items():
        setattr(ingredient, field, value)
        changes[field] = value

    if payload.benefit_ids is not None:
        await _validate_and_get_entities_by_ids(
            db=db,
            model=HealthBenefit,
            ids=payload.benefit_ids,
            entity_name="beneficios",
        )

        ingredient.benefit_links.clear()

        for benefit_id in dict.fromkeys(payload.benefit_ids):
            ingredient.benefit_links.append(
                IngredientBenefit(benefit_id=benefit_id)
            )

        changes["benefit_ids"] = payload.benefit_ids

    if payload.allergen_ids is not None:
        await _validate_and_get_entities_by_ids(
            db=db,
            model=Allergen,
            ids=payload.allergen_ids,
            entity_name="alérgenos",
        )

        ingredient.allergen_links.clear()

        for allergen_id in dict.fromkeys(payload.allergen_ids):
            ingredient.allergen_links.append(
                IngredientAllergen(allergen_id=allergen_id)
            )

        changes["allergen_ids"] = payload.allergen_ids

    if payload.diet_tag_ids is not None:
        await _validate_and_get_entities_by_ids(
            db=db,
            model=DietTag,
            ids=payload.diet_tag_ids,
            entity_name="etiquetas dietarias",
        )

        ingredient.diet_tag_links.clear()

        for diet_tag_id in dict.fromkeys(payload.diet_tag_ids):
            ingredient.diet_tag_links.append(
                IngredientDietTag(diet_tag_id=diet_tag_id)
            )

        changes["diet_tag_ids"] = payload.diet_tag_ids

    await db.commit()

    ingredient = await get_ingredient(db, ingredient_id)

    await audit(
        db,
        action="ingredient.updated",
        resource="ingredient",
        resource_id=ingredient.id,
        user_id=actor.id if actor else None,
        request=request,
        detail=changes,
    )

    return ingredient


async def set_ingredient_availability(
    db: AsyncSession,
    ingredient_id: UUID,
    payload: AvailabilityUpdate,
    request: Request | None = None,
    actor=None,
) -> Ingredient:
    ingredient = await get_ingredient(db, ingredient_id)

    ingredient.available = payload.available

    await db.commit()

    ingredient = await get_ingredient(db, ingredient_id)

    await audit(
        db,
        action="ingredient.availability_updated",
        resource="ingredient",
        resource_id=ingredient.id,
        user_id=actor.id if actor else None,
        request=request,
        detail={"available": payload.available},
    )

    return ingredient


async def get_public_carta(
    db: AsyncSession,
    category_id: UUID | None = None,
    search: str | None = None,
    diet_tag: str | None = None,
):
    query = (
        select(Dish)
        .join(Category, Dish.category_id == Category.id)
        .options(*dish_options())
        .where(
            Category.is_active.is_(True),
            Dish.available.is_(True),
        )
    )

    if category_id:
        query = query.where(Category.id == category_id)

    if search:
        query = query.where(Dish.name.ilike(f"%{search}%"))

    if diet_tag:
        query = (
            query.join(DishDietTag, Dish.id == DishDietTag.dish_id)
            .join(DietTag, DishDietTag.diet_tag_id == DietTag.id)
            .where(DietTag.name.ilike(f"%{diet_tag}%"))
        )

    query = query.order_by(Category.sort_order.asc(), Dish.name.asc())

    dishes = (await db.scalars(query)).all()

    unique_dishes = {}

    for dish in dishes:
        unique_dishes[str(dish.id)] = dish

    carta = {}

    for dish in unique_dishes.values():
        category = dish.category
        key = str(category.id)

        if key not in carta:
            carta[key] = {
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "dishes": [],
            }

        carta[key]["dishes"].append(dish)

    return list(carta.values())


async def get_public_dish(
    db: AsyncSession,
    dish_id: UUID,
) -> Dish:
    dish = await db.scalar(
        select(Dish)
        .options(*dish_options())
        .where(
            Dish.id == dish_id,
            Dish.available.is_(True),
        )
    )

    if not dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plato no encontrado",
        )

    return dish


async def list_dishes_admin(
    db: AsyncSession,
    category_id: UUID | None = None,
    available: bool | None = None,
    search: str | None = None,
) -> List[Dish]:
    query = select(Dish).options(*dish_options())

    if category_id:
        query = query.where(Dish.category_id == category_id)

    if available is not None:
        query = query.where(Dish.available.is_(available))

    if search:
        query = query.where(Dish.name.ilike(f"%{search}%"))

    query = query.order_by(Dish.name.asc())

    return (await db.scalars(query)).all()


async def get_dish_admin(
    db: AsyncSession,
    dish_id: UUID,
) -> Dish:
    dish = await db.scalar(
        select(Dish)
        .options(*dish_options())
        .where(Dish.id == dish_id)
    )

    if not dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plato no encontrado",
        )

    return dish


async def create_dish(
    db: AsyncSession,
    payload: DishCreate,
    request: Request | None = None,
    actor=None,
) -> Dish:
    category = await db.get(Category, payload.category_id)

    if not category or not category.is_active:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La categoría indicada no es válida",
        )

    existing = await db.scalar(
        select(Dish).where(
            Dish.category_id == payload.category_id,
            Dish.name == payload.name,
        )
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un plato con este nombre en la categoría",
        )

    await _validate_and_get_entities_by_ids(
        db=db,
        model=DietTag,
        ids=payload.diet_tag_ids,
        entity_name="etiquetas dietarias",
    )

    data = payload.model_dump(exclude={"diet_tag_ids"})

    dish = Dish(**data)

    for diet_tag_id in dict.fromkeys(payload.diet_tag_ids):
        dish.diet_tag_links.append(
            DishDietTag(diet_tag_id=diet_tag_id)
        )

    db.add(dish)
    await db.commit()

    dish = await get_dish_admin(db, dish.id)

    await audit(
        db,
        action="dish.created",
        resource="dish",
        resource_id=dish.id,
        user_id=actor.id if actor else None,
        request=request,
        detail={"name": dish.name},
    )

    return dish


async def update_dish(
    db: AsyncSession,
    dish_id: UUID,
    payload: DishUpdate,
    request: Request | None = None,
    actor=None,
) -> Dish:
    dish = await get_dish_admin(db, dish_id)

    changes = {}

    data = payload.model_dump(
        exclude_unset=True,
        exclude={"diet_tag_ids"},
    )

    if payload.category_id is not None:
        category = await db.get(Category, payload.category_id)

        if not category or not category.is_active:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La categoría indicada no es válida",
            )

    if payload.name is not None and payload.name != dish.name:
        category_id = payload.category_id or dish.category_id

        existing = await db.scalar(
            select(Dish).where(
                Dish.category_id == category_id,
                Dish.name == payload.name,
                Dish.id != dish.id,
            )
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un plato con este nombre en la categoría",
            )

    for field, value in data.items():
        setattr(dish, field, value)
        changes[field] = value

    if payload.diet_tag_ids is not None:
        await _validate_and_get_entities_by_ids(
            db=db,
            model=DietTag,
            ids=payload.diet_tag_ids,
            entity_name="etiquetas dietarias",
        )

        dish.diet_tag_links.clear()

        for diet_tag_id in dict.fromkeys(payload.diet_tag_ids):
            dish.diet_tag_links.append(
                DishDietTag(diet_tag_id=diet_tag_id)
            )

        changes["diet_tag_ids"] = payload.diet_tag_ids

    await db.commit()

    dish = await get_dish_admin(db, dish_id)

    await audit(
        db,
        action="dish.updated",
        resource="dish",
        resource_id=dish.id,
        user_id=actor.id if actor else None,
        request=request,
        detail=changes,
    )

    return dish


async def set_dish_availability(
    db: AsyncSession,
    dish_id: UUID,
    payload: AvailabilityUpdate,
    request: Request | None = None,
    actor=None,
) -> Dish:
    dish = await get_dish_admin(db, dish_id)

    dish.available = payload.available

    await db.commit()

    dish = await get_dish_admin(db, dish_id)

    await audit(
        db,
        action="dish.availability_updated",
        resource="dish",
        resource_id=dish.id,
        user_id=actor.id if actor else None,
        request=request,
        detail={"available": payload.available},
    )

    return dish


async def update_dish_recipe(
    db: AsyncSession,
    dish_id: UUID,
    payload: RecipeUpdate,
    request: Request | None = None,
    actor=None,
) -> Dish:
    dish = await get_dish_admin(db, dish_id)

    ingredient_ids = [item.ingredient_id for item in payload.items]
    unique_ingredient_ids = list(dict.fromkeys(ingredient_ids))

    if len(unique_ingredient_ids) != len(ingredient_ids):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La receta contiene ingredientes duplicados",
        )

    await _validate_and_get_entities_by_ids(
        db=db,
        model=Ingredient,
        ids=unique_ingredient_ids,
        entity_name="ingredientes",
    )

    dish.recipe.clear()

    for item in payload.items:
        dish.recipe.append(
            RecipeIngredient(
                dish_id=dish.id,
                ingredient_id=item.ingredient_id,
                quantity=item.quantity,
                unit=item.unit,
                is_removable=item.is_removable,
                is_addable=item.is_addable,
                extra_price=item.extra_price,
                sort_order=item.sort_order,
            )
        )

    await db.commit()

    dish = await get_dish_admin(db, dish_id)

    await audit(
        db,
        action="dish.recipe_updated",
        resource="dish",
        resource_id=dish.id,
        user_id=actor.id if actor else None,
        request=request,
        detail={"ingredients_count": len(payload.items)},
    )

    return dish
