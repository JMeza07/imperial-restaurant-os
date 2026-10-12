from decimal import Decimal
from uuid import uuid4

import pytest

from app.models.catalog import Ingredient, RecipeIngredient
from app.schemas.catalog import DishCreate, IngredientCreate


def test_recipe_extra_price_uses_override():
    ingredient = Ingredient(
        name="Pollo",
        unit="g",
        price_extra=Decimal("3000"),
    )

    recipe_item = RecipeIngredient(
        dish_id=uuid4(),
        ingredient_id=uuid4(),
        quantity=Decimal("100"),
        unit="g",
        is_removable=False,
        is_addable=True,
        extra_price=Decimal("5000"),
    )

    recipe_item.ingredient = ingredient

    assert recipe_item.effective_extra_price == Decimal("5000")


def test_recipe_extra_price_uses_ingredient_default():
    ingredient = Ingredient(
        name="Pollo",
        unit="g",
        price_extra=Decimal("3000"),
    )

    recipe_item = RecipeIngredient(
        dish_id=uuid4(),
        ingredient_id=uuid4(),
        quantity=Decimal("100"),
        unit="g",
        is_removable=False,
        is_addable=True,
        extra_price=None,
    )

    recipe_item.ingredient = ingredient

    assert recipe_item.effective_extra_price == Decimal("3000")


def test_ingredient_create_rejects_negative_price_extra():
    with pytest.raises(ValueError):
        IngredientCreate(
            name="Pollo",
            unit="g",
            price_extra=Decimal("-100"),
        )


def test_dish_create_requires_positive_price():
    with pytest.raises(ValueError):
        DishCreate(
            category_id=uuid4(),
            name="Arroz Chino",
            price_base=Decimal("0"),
        )
