from decimal import Decimal
from uuid import uuid4

from app.core.enums import ModificationAction
from app.services.inventory_service import calculate_required_ingredients


def test_base_recipe_consumption():
    ingredient_id = uuid4()

    recipe = [
        {
            "ingredient_id": ingredient_id,
            "quantity": Decimal("100"),
        }
    ]

    result = calculate_required_ingredients(
        recipe=recipe,
        modifications=[],
        item_quantity=2,
    )

    assert result[ingredient_id] == Decimal("200")


def test_removed_ingredient_reduces_consumption():
    ingredient_id = uuid4()

    recipe = [
        {
            "ingredient_id": ingredient_id,
            "quantity": Decimal("50"),
        }
    ]

    modifications = [
        {
            "ingredient_id": ingredient_id,
            "action": ModificationAction.QUITAR,
        }
    ]

    result = calculate_required_ingredients(
        recipe=recipe,
        modifications=modifications,
        item_quantity=1,
    )

    assert ingredient_id not in result


def test_added_ingredient_increases_consumption():
    ingredient_id = uuid4()

    recipe = [
        {
            "ingredient_id": ingredient_id,
            "quantity": Decimal("150"),
        }
    ]

    modifications = [
        {
            "ingredient_id": ingredient_id,
            "action": ModificationAction.AGREGAR,
        }
    ]

    result = calculate_required_ingredients(
        recipe=recipe,
        modifications=modifications,
        item_quantity=1,
    )

    assert result[ingredient_id] == Decimal("300")


def test_remove_and_add_same_ingredient():
    ingredient_id = uuid4()

    recipe = [
        {
            "ingredient_id": ingredient_id,
            "quantity": Decimal("30"),
        }
    ]

    modifications = [
        {
            "ingredient_id": ingredient_id,
            "action": ModificationAction.QUITAR,
        },
        {
            "ingredient_id": ingredient_id,
            "action": ModificationAction.AGREGAR,
        },
    ]

    result = calculate_required_ingredients(
        recipe=recipe,
        modifications=modifications,
        item_quantity=1,
    )

    assert result[ingredient_id] == Decimal("30")
