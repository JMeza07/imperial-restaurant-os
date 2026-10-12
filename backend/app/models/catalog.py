import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import AllergenSeverity, EvidenceLevel
from app.db.base import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    dishes: Mapped[List["Dish"]] = relationship(
        back_populates="category"
    )


class HealthBenefit(Base):
    __tablename__ = "health_benefits"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
    )

    icon: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    category: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Allergen(Base):
    __tablename__ = "allergens"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
    )

    severity: Mapped[AllergenSeverity] = mapped_column(
        Enum(AllergenSeverity, name="allergen_severity"),
        nullable=False,
        default=AllergenSeverity.MEDIUM,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class DietTag(Base):
    __tablename__ = "diet_tags"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
    )

    unit: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="g",
    )

    price_extra: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
    )

    available: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    calories: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    protein: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    carbs: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    fat: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    fiber: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    sodium: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    origin: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    is_organic: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    health_notes: Mapped[Optional[str]] = mapped_column(
        String(2000),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    benefit_links: Mapped[List["IngredientBenefit"]] = relationship(
        back_populates="ingredient",
        cascade="all, delete-orphan",
    )

    allergen_links: Mapped[List["IngredientAllergen"]] = relationship(
        back_populates="ingredient",
        cascade="all, delete-orphan",
    )

    diet_tag_links: Mapped[List["IngredientDietTag"]] = relationship(
        back_populates="ingredient",
        cascade="all, delete-orphan",
    )

    @property
    def benefits(self) -> List["HealthBenefit"]:
        return [link.benefit for link in self.benefit_links if link.benefit]

    @property
    def allergens(self) -> List["Allergen"]:
        return [link.allergen for link in self.allergen_links if link.allergen]

    @property
    def diet_tags(self) -> List["DietTag"]:
        return [link.diet_tag for link in self.diet_tag_links if link.diet_tag]


class IngredientBenefit(Base):
    __tablename__ = "ingredient_benefits"

    ingredient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ingredients.id", ondelete="CASCADE"),
        primary_key=True,
    )

    health_benefit_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("health_benefits.id", ondelete="CASCADE"),
        primary_key=True,
    )

    description: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
    )

    evidence_level: Mapped[EvidenceLevel] = mapped_column(
        Enum(EvidenceLevel, name="evidence_level"),
        nullable=False,
        default=EvidenceLevel.INFO,
    )

    ingredient: Mapped["Ingredient"] = relationship(
        back_populates="benefit_links"
    )

    benefit: Mapped["HealthBenefit"] = relationship()


class IngredientAllergen(Base):
    __tablename__ = "ingredient_allergens"

    ingredient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ingredients.id", ondelete="CASCADE"),
        primary_key=True,
    )

    allergen_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("allergens.id", ondelete="CASCADE"),
        primary_key=True,
    )

    note: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
    )

    ingredient: Mapped["Ingredient"] = relationship(
        back_populates="allergen_links"
    )

    allergen: Mapped["Allergen"] = relationship()


class IngredientDietTag(Base):
    __tablename__ = "ingredient_diet_tags"

    ingredient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ingredients.id", ondelete="CASCADE"),
        primary_key=True,
    )

    diet_tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("diet_tags.id", ondelete="CASCADE"),
        primary_key=True,
    )

    ingredient: Mapped["Ingredient"] = relationship(
        back_populates="diet_tag_links"
    )

    diet_tag: Mapped["DietTag"] = relationship()


class Dish(Base):
    __tablename__ = "dishes"
    __table_args__ = (
        UniqueConstraint(
            "category_id",
            "name",
            name="uq_dishes_category_name",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    short_description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    long_description: Mapped[Optional[str]] = mapped_column(
        String(2000),
        nullable=True,
    )

    price_base: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    cost_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    image_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    preparation_time_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    available: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    calories_estimate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    category: Mapped["Category"] = relationship(
        back_populates="dishes"
    )

    recipe: Mapped[List["RecipeIngredient"]] = relationship(
        back_populates="dish",
        cascade="all, delete-orphan",
        order_by="RecipeIngredient.sort_order",
    )

    diet_tag_links: Mapped[List["DishDietTag"]] = relationship(
        back_populates="dish",
        cascade="all, delete-orphan",
    )

    @property
    def category_name(self) -> Optional[str]:
        return self.category.name if self.category else None

    @property
    def diet_tags(self) -> List["DietTag"]:
        return [link.diet_tag for link in self.diet_tag_links if link.diet_tag]

    @property
    def ingredients(self) -> List["RecipeIngredient"]:
        return self.recipe

    @property
    def allergens(self) -> List["Allergen"]:
        result = {}

        for recipe_item in self.recipe:
            if not recipe_item.ingredient:
                continue

            for allergen in recipe_item.ingredient.allergens:
                result[str(allergen.id)] = allergen

        return list(result.values())

    @property
    def benefits(self) -> List["HealthBenefit"]:
        result = {}

        for recipe_item in self.recipe:
            if not recipe_item.ingredient:
                continue

            for benefit in recipe_item.ingredient.benefits:
                result[str(benefit.id)] = benefit

        return list(result.values())


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    dish_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("dishes.id", ondelete="CASCADE"),
        primary_key=True,
    )

    ingredient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ingredients.id", ondelete="RESTRICT"),
        primary_key=True,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0"),
    )

    unit: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="g",
    )

    is_removable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_addable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    extra_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    dish: Mapped["Dish"] = relationship(
        back_populates="recipe"
    )

    ingredient: Mapped["Ingredient"] = relationship()

    @property
    def ingredient_name(self) -> Optional[str]:
        return self.ingredient.name if self.ingredient else None

    @property
    def effective_extra_price(self) -> Decimal:
        if self.extra_price is not None:
            return self.extra_price

        if self.ingredient:
            return self.ingredient.price_extra

        return Decimal("0")


class DishDietTag(Base):
    __tablename__ = "dish_diet_tags"

    dish_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("dishes.id", ondelete="CASCADE"),
        primary_key=True,
    )

    diet_tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("diet_tags.id", ondelete="CASCADE"),
        primary_key=True,
    )

    dish: Mapped["Dish"] = relationship(
        back_populates="diet_tag_links"
    )

    diet_tag: Mapped["DietTag"] = relationship()
