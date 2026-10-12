from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import AllergenSeverity, EvidenceLevel


class AvailabilityUpdate(BaseModel):
    available: bool


class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=500)
    sort_order: int = 0
    is_active: bool = True


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=500)
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: Optional[str]
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class HealthBenefitCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    icon: Optional[str] = Field(default=None, max_length=255)
    category: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = True


class HealthBenefitUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    icon: Optional[str] = Field(default=None, max_length=255)
    category: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = None


class HealthBenefitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: Optional[str]
    icon: Optional[str]
    category: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AllergenCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    severity: AllergenSeverity = AllergenSeverity.MEDIUM
    is_active: bool = True


class AllergenUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    severity: Optional[AllergenSeverity] = None
    is_active: Optional[bool] = None


class AllergenRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: Optional[str]
    severity: AllergenSeverity
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DietTagCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    is_active: bool = True


class DietTagUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    is_active: Optional[bool] = None


class DietTagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class IngredientCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    unit: str = Field(default="g", max_length=20)
    price_extra: Decimal = Field(default=Decimal("0"), ge=0)
    available: bool = True

    calories: Optional[Decimal] = Field(default=None, ge=0)
    protein: Optional[Decimal] = Field(default=None, ge=0)
    carbs: Optional[Decimal] = Field(default=None, ge=0)
    fat: Optional[Decimal] = Field(default=None, ge=0)
    fiber: Optional[Decimal] = Field(default=None, ge=0)
    sodium: Optional[Decimal] = Field(default=None, ge=0)

    origin: Optional[str] = Field(default=None, max_length=255)
    is_organic: bool = False
    health_notes: Optional[str] = Field(default=None, max_length=2000)

    benefit_ids: List[UUID] = []
    allergen_ids: List[UUID] = []
    diet_tag_ids: List[UUID] = []


class IngredientUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    unit: Optional[str] = Field(default=None, max_length=20)
    price_extra: Optional[Decimal] = Field(default=None, ge=0)
    available: Optional[bool] = None

    calories: Optional[Decimal] = Field(default=None, ge=0)
    protein: Optional[Decimal] = Field(default=None, ge=0)
    carbs: Optional[Decimal] = Field(default=None, ge=0)
    fat: Optional[Decimal] = Field(default=None, ge=0)
    fiber: Optional[Decimal] = Field(default=None, ge=0)
    sodium: Optional[Decimal] = Field(default=None, ge=0)

    origin: Optional[str] = Field(default=None, max_length=255)
    is_organic: Optional[bool] = None
    health_notes: Optional[str] = Field(default=None, max_length=2000)

    benefit_ids: Optional[List[UUID]] = None
    allergen_ids: Optional[List[UUID]] = None
    diet_tag_ids: Optional[List[UUID]] = None


class IngredientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: Optional[str]
    unit: str
    price_extra: Decimal
    available: bool

    calories: Optional[Decimal]
    protein: Optional[Decimal]
    carbs: Optional[Decimal]
    fat: Optional[Decimal]
    fiber: Optional[Decimal]
    sodium: Optional[Decimal]

    origin: Optional[str]
    is_organic: bool
    health_notes: Optional[str]

    benefits: List[HealthBenefitRead] = []
    allergens: List[AllergenRead] = []
    diet_tags: List[DietTagRead] = []

    created_at: datetime
    updated_at: datetime


class RecipeIngredientUpsert(BaseModel):
    ingredient_id: UUID
    quantity: Decimal = Field(default=Decimal("0"), ge=0)
    unit: str = Field(default="g", max_length=20)
    is_removable: bool = False
    is_addable: bool = False
    extra_price: Optional[Decimal] = Field(default=None, ge=0)
    sort_order: int = 0


class RecipeUpdate(BaseModel):
    items: List[RecipeIngredientUpsert]


class RecipeIngredientPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ingredient_id: UUID
    ingredient_name: Optional[str]
    quantity: Decimal
    unit: str
    is_removable: bool
    is_addable: bool
    extra_price: Decimal = Field(validation_alias="effective_extra_price")
    ingredient: IngredientRead


class DishCreate(BaseModel):
    category_id: UUID
    name: str = Field(min_length=2, max_length=255)
    short_description: Optional[str] = Field(default=None, max_length=500)
    long_description: Optional[str] = Field(default=None, max_length=2000)
    price_base: Decimal = Field(gt=0)
    cost_price: Optional[Decimal] = Field(default=None, ge=0)
    image_url: Optional[str] = Field(default=None, max_length=500)
    preparation_time_minutes: int = Field(default=0, ge=0)
    available: bool = True
    is_featured: bool = False
    calories_estimate: Optional[Decimal] = Field(default=None, ge=0)
    diet_tag_ids: List[UUID] = []


class DishUpdate(BaseModel):
    category_id: Optional[UUID] = None
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    short_description: Optional[str] = Field(default=None, max_length=500)
    long_description: Optional[str] = Field(default=None, max_length=2000)
    price_base: Optional[Decimal] = Field(default=None, gt=0)
    cost_price: Optional[Decimal] = Field(default=None, ge=0)
    image_url: Optional[str] = Field(default=None, max_length=500)
    preparation_time_minutes: Optional[int] = Field(default=None, ge=0)
    available: Optional[bool] = None
    is_featured: Optional[bool] = None
    calories_estimate: Optional[Decimal] = Field(default=None, ge=0)
    diet_tag_ids: Optional[List[UUID]] = None


class DishRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category_id: UUID
    category_name: Optional[str]
    name: str
    short_description: Optional[str]
    long_description: Optional[str]
    price_base: Decimal
    cost_price: Optional[Decimal]
    image_url: Optional[str]
    preparation_time_minutes: int
    available: bool
    is_featured: bool
    calories_estimate: Optional[Decimal]

    recipe: List[RecipeIngredientPublic] = []
    diet_tags: List[DietTagRead] = []

    created_at: datetime
    updated_at: datetime


class DishPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category_id: UUID
    category_name: Optional[str]
    name: str
    short_description: Optional[str]
    long_description: Optional[str]
    price_base: Decimal
    image_url: Optional[str]
    preparation_time_minutes: int
    available: bool
    is_featured: bool
    calories_estimate: Optional[Decimal]

    diet_tags: List[DietTagRead] = []
    ingredients: List[RecipeIngredientPublic] = []
    allergens: List[AllergenRead] = []
    benefits: List[HealthBenefitRead] = []


class CartaCategoryPublic(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    dishes: List[DishPublic]
