import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import asyncio
from decimal import Decimal

from sqlalchemy import select

from app.core.enums import AllergenSeverity
from app.db.session import SessionLocal
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


async def get_or_create_category(session, name, description, sort_order):
    category = await session.scalar(
        select(Category).where(Category.name == name)
    )

    if not category:
        category = Category(
            name=name,
            description=description,
            sort_order=sort_order,
            is_active=True,
        )
        session.add(category)
        await session.flush()

    return category


async def get_or_create_benefit(session, name, description, category):
    benefit = await session.scalar(
        select(HealthBenefit).where(HealthBenefit.name == name)
    )

    if not benefit:
        benefit = HealthBenefit(
            name=name,
            description=description,
            category=category,
            is_active=True,
        )
        session.add(benefit)
        await session.flush()

    return benefit


async def get_or_create_allergen(session, name, description, severity):
    allergen = await session.scalar(
        select(Allergen).where(Allergen.name == name)
    )

    if not allergen:
        allergen = Allergen(
            name=name,
            description=description,
            severity=severity,
            is_active=True,
        )
        session.add(allergen)
        await session.flush()

    return allergen


async def get_or_create_diet_tag(session, name, description):
    tag = await session.scalar(
        select(DietTag).where(DietTag.name == name)
    )

    if not tag:
        tag = DietTag(
            name=name,
            description=description,
            is_active=True,
        )
        session.add(tag)
        await session.flush()

    return tag


from sqlalchemy.orm import selectinload

async def get_or_create_ingredient(
    session,
    name,
    unit,
    price_extra,
    benefits=None,
    allergens=None,
    diet_tags=None,
    calories=None,
    protein=None,
    carbs=None,
    fat=None,
):
    ingredient = await session.scalar(
        select(Ingredient)
        .options(
            selectinload(Ingredient.benefit_links),
            selectinload(Ingredient.allergen_links),
            selectinload(Ingredient.diet_tag_links),
        )
        .where(Ingredient.name == name)
    )

    if not ingredient:
        ingredient = Ingredient(
            name=name,
            unit=unit,
            price_extra=price_extra,
            available=True,
            calories=calories,
            protein=protein,
            carbs=carbs,
            fat=fat,
        )
        session.add(ingredient)
        await session.flush()
        # Re-fetch with selectinload
        ingredient = await session.scalar(
            select(Ingredient)
            .options(
                selectinload(Ingredient.benefit_links),
                selectinload(Ingredient.allergen_links),
                selectinload(Ingredient.diet_tag_links),
            )
            .where(Ingredient.id == ingredient.id)
        )

    if benefits:
        existing_benefit_ids = {
            link.health_benefit_id for link in ingredient.benefit_links
        }

        for benefit in benefits:
            if benefit.id not in existing_benefit_ids:
                ingredient.benefit_links.append(
                    IngredientBenefit(health_benefit_id=benefit.id)
                )

    if allergens:
        existing_allergen_ids = {
            link.allergen_id for link in ingredient.allergen_links
        }

        for allergen in allergens:
            if allergen.id not in existing_allergen_ids:
                ingredient.allergen_links.append(
                    IngredientAllergen(allergen_id=allergen.id)
                )

    if diet_tags:
        existing_tag_ids = {
            link.diet_tag_id for link in ingredient.diet_tag_links
        }

        for tag in diet_tags:
            if tag.id not in existing_tag_ids:
                ingredient.diet_tag_links.append(
                    IngredientDietTag(diet_tag_id=tag.id)
                )

    await session.flush()
    return ingredient


async def seed_catalog() -> None:
    async with SessionLocal() as session:
        entradas = await get_or_create_category(
            session,
            "Entradas",
            "Entradas del Restaurante Imperial",
            1,
        )

        principales = await get_or_create_category(
            session,
            "Platos Principales",
            "Platos principales del Restaurante Imperial",
            2,
        )

        sopas = await get_or_create_category(
            session,
            "Sopas",
            "Sopas del Restaurante Imperial",
            3,
        )

        postres = await get_or_create_category(
            session,
            "Postres",
            "Postres del Restaurante Imperial",
            4,
        )

        bebidas = await get_or_create_category(
            session,
            "Bebidas",
            "Bebidas del Restaurante Imperial",
            5,
        )

        proteina = await get_or_create_benefit(
            session,
            "Alto en proteína",
            "Contribuye a la saciedad y al mantenimiento muscular.",
            "Nutrición",
        )

        fibra = await get_or_create_benefit(
            session,
            "Fuente de fibra",
            "Puede apoyar la digestión.",
            "Nutrición",
        )

        vitamina_a = await get_or_create_benefit(
            session,
            "Contiene vitamina A",
            "La vitamina A contribuye al mantenimiento de la visión.",
            "Nutrición",
        )

        antioxidantes = await get_or_create_benefit(
            session,
            "Fuente de antioxidantes",
            "Los antioxidantes ayudan a proteger las células.",
            "Nutrición",
        )

        soya = await get_or_create_allergen(
            session,
            "Soya",
            "Contiene soya.",
            AllergenSeverity.MEDIUM,
        )

        huevo = await get_or_create_allergen(
            session,
            "Huevo",
            "Contiene huevo.",
            AllergenSeverity.MEDIUM,
        )

        gluten = await get_or_create_allergen(
            session,
            "Gluten",
            "Puede contener gluten.",
            AllergenSeverity.MEDIUM,
        )

        alto_proteina = await get_or_create_diet_tag(
            session,
            "Alto en proteína",
            "Plato con ingredientes ricos en proteína.",
        )

        sin_gluten = await get_or_create_diet_tag(
            session,
            "Sin gluten",
            "Plato sin ingredientes con gluten, según receta.",
        )

        arroz = await get_or_create_ingredient(
            session,
            name="Arroz",
            unit="g",
            price_extra=Decimal("0"),
            benefits=[fibra],
            allergens=[],
            diet_tags=[],
            calories=Decimal("130"),
            protein=Decimal("2.5"),
            carbs=Decimal("28"),
            fat=Decimal("0.3"),
        )

        pollo = await get_or_create_ingredient(
            session,
            name="Pollo",
            unit="g",
            price_extra=Decimal("5000"),
            benefits=[proteina],
            allergens=[],
            diet_tags=[alto_proteina],
            calories=Decimal("165"),
            protein=Decimal("31"),
            carbs=Decimal("0"),
            fat=Decimal("3.6"),
        )

        cebolla = await get_or_create_ingredient(
            session,
            name="Cebolla",
            unit="g",
            price_extra=Decimal("0"),
            benefits=[antioxidantes],
            allergens=[],
            diet_tags=[],
            calories=Decimal("40"),
            protein=Decimal("1.1"),
            carbs=Decimal("9"),
            fat=Decimal("0.1"),
        )

        zanahoria = await get_or_create_ingredient(
            session,
            name="Zanahoria",
            unit="g",
            price_extra=Decimal("0"),
            benefits=[vitamina_a, fibra],
            allergens=[],
            diet_tags=[],
            calories=Decimal("41"),
            protein=Decimal("0.9"),
            carbs=Decimal("10"),
            fat=Decimal("0.2"),
        )

        huevo = await get_or_create_ingredient(
            session,
            name="Huevo",
            unit="unidad",
            price_extra=Decimal("2000"),
            benefits=[proteina],
            allergens=[huevo],
            diet_tags=[],
            calories=Decimal("70"),
            protein=Decimal("6"),
            carbs=Decimal("0.6"),
            fat=Decimal("5"),
        )

        salsa_soya = await get_or_create_ingredient(
            session,
            name="Salsa soya",
            unit="ml",
            price_extra=Decimal("0"),
            benefits=[],
            allergens=[soya, gluten],
            diet_tags=[],
            calories=Decimal("8"),
            protein=Decimal("1.3"),
            carbs=Decimal("0.8"),
            fat=Decimal("0"),
        )

        dish = await session.scalar(
            select(Dish)
            .options(selectinload(Dish.recipe))
            .where(Dish.name == "Arroz Chino Especial")
        )

        if not dish:
            dish = Dish(
                category_id=principales.id,
                name="Arroz Chino Especial",
                short_description="Arroz chino con pollo, huevo y verduras.",
                long_description="Arroz chino especial preparado con pollo, huevo, cebolla, zanahoria y salsa soya.",
                price_base=Decimal("22000"),
                image_url=None,
                preparation_time_minutes=15,
                available=True,
                is_featured=True,
                calories_estimate=Decimal("650"),
            )
            session.add(dish)
            await session.flush()
            dish = await session.scalar(
                select(Dish)
                .options(selectinload(Dish.recipe), selectinload(Dish.diet_tag_links))
                .where(Dish.id == dish.id)
            )

        if not dish.recipe:
            dish.recipe.extend(
                [
                    RecipeIngredient(
                        dish_id=dish.id,
                        ingredient_id=arroz.id,
                        quantity=Decimal("200"),
                        unit="g",
                        is_removable=False,
                        is_addable=False,
                        extra_price=None,
                        sort_order=1,
                    ),
                    RecipeIngredient(
                        dish_id=dish.id,
                        ingredient_id=pollo.id,
                        quantity=Decimal("150"),
                        unit="g",
                        is_removable=False,
                        is_addable=True,
                        extra_price=Decimal("5000"),
                        sort_order=2,
                    ),
                    RecipeIngredient(
                        dish_id=dish.id,
                        ingredient_id=cebolla.id,
                        quantity=Decimal("40"),
                        unit="g",
                        is_removable=True,
                        is_addable=False,
                        extra_price=None,
                        sort_order=3,
                    ),
                    RecipeIngredient(
                        dish_id=dish.id,
                        ingredient_id=zanahoria.id,
                        quantity=Decimal("30"),
                        unit="g",
                        is_removable=True,
                        is_addable=False,
                        extra_price=None,
                        sort_order=4,
                    ),
                    RecipeIngredient(
                        dish_id=dish.id,
                        ingredient_id=huevo.id,
                        quantity=Decimal("1"),
                        unit="unidad",
                        is_removable=False,
                        is_addable=True,
                        extra_price=Decimal("2000"),
                        sort_order=5,
                    ),
                    RecipeIngredient(
                        dish_id=dish.id,
                        ingredient_id=salsa_soya.id,
                        quantity=Decimal("20"),
                        unit="ml",
                        is_removable=True,
                        is_addable=False,
                        extra_price=None,
                        sort_order=6,
                    ),
                ]
            )
            await session.flush()

        dish = await session.scalar(
            select(Dish)
            .options(selectinload(Dish.diet_tag_links))
            .where(Dish.id == dish.id)
        )

        existing_tag_ids = {
            link.diet_tag_id for link in dish.diet_tag_links
        }

        if alto_proteina.id not in existing_tag_ids:
            dish.diet_tag_links.append(
                DishDietTag(diet_tag_id=alto_proteina.id)
            )

        await session.commit()
        print("Seed de catálogo completado.")


if __name__ == "__main__":
    asyncio.run(seed_catalog())
