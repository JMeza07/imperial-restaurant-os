import asyncio
import os
import sys
from decimal import Decimal
from uuid import uuid4

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.catalog import (
    Allergen,
    Category,
    Dish,
    HealthBenefit,
    Ingredient,
    IngredientAllergen,
    IngredientBenefit,
    RecipeIngredient,
)
from app.core.enums import AllergenSeverity, EvidenceLevel

async def seed_mobile_demo():
    async with SessionLocal() as db:
        cats = (await db.scalars(select(Category))).all()
        cat_map = {c.name: c for c in cats}
        main_cat = cat_map.get("Platos Principales") or cats[0]

        # 1. Ingredientes adicionales
        nuevos_ingredientes = [
            {"name": "Carne Angus", "calories": Decimal("250"), "protein": Decimal("26"), "carbs": Decimal("0"), "fat": Decimal("15"), "unit": "g", "price_extra": Decimal("6000")},
            {"name": "Queso Cheddar", "calories": Decimal("110"), "protein": Decimal("7"), "carbs": Decimal("1"), "fat": Decimal("9"), "unit": "g", "price_extra": Decimal("3000")},
            {"name": "Pan Brioche", "calories": Decimal("150"), "protein": Decimal("4"), "carbs": Decimal("28"), "fat": Decimal("3"), "unit": "unidad", "price_extra": Decimal("2000")},
            {"name": "Tomate Fresco", "calories": Decimal("18"), "protein": Decimal("0.9"), "carbs": Decimal("3.9"), "fat": Decimal("0.2"), "unit": "g", "price_extra": Decimal("1000")},
            {"name": "Lechuga Romana", "calories": Decimal("15"), "protein": Decimal("1.2"), "carbs": Decimal("2.8"), "fat": Decimal("0.3"), "unit": "g", "price_extra": Decimal("1000")},
            {"name": "Langostinos", "calories": Decimal("99"), "protein": Decimal("24"), "carbs": Decimal("0.2"), "fat": Decimal("0.3"), "unit": "g", "price_extra": Decimal("8000")},
            {"name": "Pescado Blanco", "calories": Decimal("85"), "protein": Decimal("18"), "carbs": Decimal("0"), "fat": Decimal("1.2"), "unit": "g", "price_extra": Decimal("7000")},
            {"name": "Palmitos de Cangrejo", "calories": Decimal("80"), "protein": Decimal("12"), "carbs": Decimal("6"), "fat": Decimal("0.5"), "unit": "g", "price_extra": Decimal("5000")},
            {"name": "Aguacate", "calories": Decimal("160"), "protein": Decimal("2"), "carbs": Decimal("8.5"), "fat": Decimal("14.7"), "unit": "g", "price_extra": Decimal("3500")},
            {"name": "Semillas de Ajonjolí", "calories": Decimal("52"), "protein": Decimal("1.6"), "carbs": Decimal("2.1"), "fat": Decimal("4.5"), "unit": "g", "price_extra": Decimal("1500")},
        ]

        ing_db_map = {}
        for ing_data in nuevos_ingredientes:
            exist = await db.scalar(select(Ingredient).where(Ingredient.name == ing_data["name"]))
            if not exist:
                new_ing = Ingredient(
                    id=uuid4(),
                    name=ing_data["name"],
                    unit=ing_data["unit"],
                    price_extra=ing_data["price_extra"],
                    calories=ing_data["calories"],
                    protein=ing_data["protein"],
                    carbs=ing_data["carbs"],
                    fat=ing_data["fat"],
                    available=True,
                )
                db.add(new_ing)
                ing_db_map[ing_data["name"]] = new_ing
            else:
                ing_db_map[ing_data["name"]] = exist
        
        await db.flush()

        # Ingredientes existentes
        for name in ["Arroz", "Pollo", "Cebolla", "Zanahoria", "Huevo", "Salsa soya"]:
            exist = await db.scalar(select(Ingredient).where(Ingredient.name == name))
            if exist:
                ing_db_map[name] = exist

        # 2. Beneficios
        b_omega = await db.scalar(select(HealthBenefit).where(HealthBenefit.name == "Rico en Omega 3"))
        if not b_omega:
            b_omega = HealthBenefit(
                id=uuid4(),
                name="Rico en Omega 3",
                description="Favorece la salud cardiovascular y disminuye la inflamación celular.",
                category="Salud Cardíaca",
                is_active=True,
            )
            db.add(b_omega)
            await db.flush()

        b_grasa_buena = await db.scalar(select(HealthBenefit).where(HealthBenefit.name == "Grasas Saludables"))
        if not b_grasa_buena:
            b_grasa_buena = HealthBenefit(
                id=uuid4(),
                name="Grasas Saludables",
                description="Contiene ácido oleico monoinsaturado que apoya el colesterol HDL beneficioso.",
                category="Nutrición Celular",
                is_active=True,
            )
            db.add(b_grasa_buena)
            await db.flush()

        # Asociar beneficios a aguacate y langostinos si no existen
        for target_ing, b in [(ing_db_map.get("Aguacate"), b_grasa_buena), (ing_db_map.get("Langostinos"), b_omega)]:
            if target_ing:
                link = await db.scalar(
                    select(IngredientBenefit).where(
                        IngredientBenefit.ingredient_id == target_ing.id,
                        IngredientBenefit.health_benefit_id == b.id,
                    )
                )
                if not link:
                    db.add(IngredientBenefit(ingredient_id=target_ing.id, health_benefit_id=b.id, evidence_level=EvidenceLevel.INFO))

        # 3. Platos demo como en la imagen
        platos_demo = [
            {
                "name": "Hamburguesa Imperial Gourmet",
                "short_description": "Carne Angus seleccionada con queso cheddar fundido, guacamole artesanal y pan brioche horneado al día.",
                "long_description": "Nuestra icónica hamburguesa artesanal inspirada en las mejores técnicas culinarias. Carne 100% Angus molida y madurada, queso cheddar americano fundido al punto exacto, base de lechuga romana crujiente, tomate fresco y copa de guacamole con semillas de ajonjolí tostadas en pan brioche suave.",
                "price_base": Decimal("32000"),
                "preparation_time_minutes": 18,
                "calories_estimate": Decimal("680"),
                "is_featured": True,
                "image_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=800&q=80",
                "recipe": [
                    ("Carne Angus", Decimal("180"), "g", False, True, Decimal("6000")),
                    ("Pan Brioche", Decimal("1"), "unidad", False, False, Decimal("0")),
                    ("Queso Cheddar", Decimal("40"), "g", True, True, Decimal("3000")),
                    ("Aguacate", Decimal("50"), "g", True, True, Decimal("3500")),
                    ("Tomate Fresco", Decimal("30"), "g", True, False, Decimal("0")),
                    ("Lechuga Romana", Decimal("20"), "g", True, False, Decimal("0")),
                    ("Cebolla", Decimal("20"), "g", True, False, Decimal("0")),
                ]
            },
            {
                "name": "Baozi Imperial & Dumplings de Cerdo",
                "short_description": "Panecillo bao al vapor relleno de cerdo glaseado con ajonjolí tostado, acompañado de vegetales crujientes y salteado oriental.",
                "long_description": "Tradición milenaria al vapor. Pan bao tierno y esponjoso con ajonjolí dorado, relleno de cerdo glaseado en salsa imperial de soya y jengibre, acompañado de vegetales crujientes (zanahoria en espiral y cebolla caramelizada) y ensalada fresca oriental.",
                "price_base": Decimal("36000"),
                "preparation_time_minutes": 20,
                "calories_estimate": Decimal("540"),
                "is_featured": True,
                "image_url": "https://images.unsplash.com/photo-1541696432-82c6da8ce7bf?auto=format&fit=crop&w=800&q=80",
                "recipe": [
                    ("Pollo", Decimal("120"), "g", False, True, Decimal("5000")),
                    ("Semillas de Ajonjolí", Decimal("10"), "g", True, True, Decimal("1500")),
                    ("Zanahoria", Decimal("60"), "g", True, True, Decimal("1000")),
                    ("Cebolla", Decimal("40"), "g", True, False, Decimal("0")),
                    ("Salsa soya", Decimal("25"), "ml", True, False, Decimal("0")),
                    ("Huevo", Decimal("1"), "unidad", True, True, Decimal("2000")),
                ]
            },
            {
                "name": "Wok Marino Imperial",
                "short_description": "Langostinos crocantes y frutos del mar sobre cama de arroz parbolizado con vegetales seleccionados.",
                "long_description": "Exquisita combinación de langostinos premium salteados al fuego vivo en wok con cebollino, zanahoria juliana, semillas de ajonjolí y nuestra exclusiva salsa de reducción de soya y sésamo.",
                "price_base": Decimal("42000"),
                "preparation_time_minutes": 22,
                "calories_estimate": Decimal("510"),
                "is_featured": False,
                "image_url": "https://images.unsplash.com/photo-1559847844-5315695dadae?auto=format&fit=crop&w=800&q=80",
                "recipe": [
                    ("Langostinos", Decimal("150"), "g", False, True, Decimal("8000")),
                    ("Arroz", Decimal("120"), "g", False, True, Decimal("2000")),
                    ("Zanahoria", Decimal("30"), "g", True, False, Decimal("0")),
                    ("Cebolla", Decimal("25"), "g", True, False, Decimal("0")),
                    ("Salsa soya", Decimal("20"), "ml", True, False, Decimal("0")),
                ]
            },
            {
                "name": "Ensalada Mediterránea Imperial",
                "short_description": "Mix de vegetales frescos, tomates cherry marinados, aguacate hass y semillas nutritivas.",
                "long_description": "Opción fresca y revitalizante con tomates madurados, lechuga romana crujiente, cubos de aguacate fresco, cebolla morada suave y vinagreta cítrica de la casa.",
                "price_base": Decimal("24000"),
                "preparation_time_minutes": 10,
                "calories_estimate": Decimal("320"),
                "is_featured": False,
                "image_url": "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=800&q=80",
                "recipe": [
                    ("Tomate Fresco", Decimal("80"), "g", True, True, Decimal("1000")),
                    ("Aguacate", Decimal("60"), "g", True, True, Decimal("3500")),
                    ("Lechuga Romana", Decimal("50"), "g", True, False, Decimal("0")),
                    ("Cebolla", Decimal("30"), "g", True, False, Decimal("0")),
                    ("Semillas de Ajonjolí", Decimal("10"), "g", True, True, Decimal("1500")),
                ]
            }
        ]

        for p_info in platos_demo:
            exist_dish = await db.scalar(select(Dish).where(Dish.name == p_info["name"]))
            if not exist_dish:
                new_dish = Dish(
                    id=uuid4(),
                    category_id=main_cat.id,
                    name=p_info["name"],
                    short_description=p_info["short_description"],
                    long_description=p_info["long_description"],
                    price_base=p_info["price_base"],
                    preparation_time_minutes=p_info["preparation_time_minutes"],
                    calories_estimate=p_info["calories_estimate"],
                    is_featured=p_info["is_featured"],
                    available=True,
                    image_url=p_info["image_url"],
                )
                db.add(new_dish)
                await db.flush()

                for ing_name, qty, unit, removable, addable, extra_price in p_info["recipe"]:
                    ing_obj = ing_db_map.get(ing_name)
                    if ing_obj:
                        db.add(
                            RecipeIngredient(
                                dish_id=new_dish.id,
                                ingredient_id=ing_obj.id,
                                quantity=qty,
                                unit=unit,
                                is_removable=removable,
                                is_addable=addable,
                                extra_price=extra_price,
                            )
                        )
                print(f"Plato creado: {new_dish.name}")
            else:
                print(f"Plato ya existía: {exist_dish.name}")

        await db.commit()
        print("Seed móvil completado con éxito.")

if __name__ == "__main__":
    asyncio.run(seed_mobile_demo())
