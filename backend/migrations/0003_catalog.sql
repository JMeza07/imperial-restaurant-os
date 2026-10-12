CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
BEGIN
    CREATE TYPE allergen_severity AS ENUM ('LOW', 'MEDIUM', 'HIGH');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE evidence_level AS ENUM ('INFO', 'TRADITIONAL', 'NUTRITIONAL', 'CLINICAL');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description VARCHAR(500) NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS health_benefits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description VARCHAR(1000) NULL,
    icon VARCHAR(255) NULL,
    category VARCHAR(255) NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS allergens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description VARCHAR(1000) NULL,
    severity allergen_severity NOT NULL DEFAULT 'MEDIUM',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS diet_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description VARCHAR(1000) NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ingredients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description VARCHAR(1000) NULL,
    unit VARCHAR(20) NOT NULL DEFAULT 'g',
    price_extra NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (price_extra >= 0),
    available BOOLEAN NOT NULL DEFAULT TRUE,
    calories NUMERIC(10,2) NULL,
    protein NUMERIC(10,2) NULL,
    carbs NUMERIC(10,2) NULL,
    fat NUMERIC(10,2) NULL,
    fiber NUMERIC(10,2) NULL,
    sodium NUMERIC(10,2) NULL,
    origin VARCHAR(255) NULL,
    is_organic BOOLEAN NOT NULL DEFAULT FALSE,
    health_notes VARCHAR(2000) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ingredient_benefits (
    ingredient_id UUID NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    health_benefit_id UUID NOT NULL REFERENCES health_benefits(id) ON DELETE CASCADE,
    description VARCHAR(1000) NULL,
    evidence_level evidence_level NOT NULL DEFAULT 'INFO',
    PRIMARY KEY (ingredient_id, health_benefit_id)
);

CREATE TABLE IF NOT EXISTS ingredient_allergens (
    ingredient_id UUID NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    allergen_id UUID NOT NULL REFERENCES allergens(id) ON DELETE CASCADE,
    note VARCHAR(1000) NULL,
    PRIMARY KEY (ingredient_id, allergen_id)
);

CREATE TABLE IF NOT EXISTS ingredient_diet_tags (
    ingredient_id UUID NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    diet_tag_id UUID NOT NULL REFERENCES diet_tags(id) ON DELETE CASCADE,
    PRIMARY KEY (ingredient_id, diet_tag_id)
);

CREATE TABLE IF NOT EXISTS dishes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    name VARCHAR(255) NOT NULL,
    short_description VARCHAR(500) NULL,
    long_description VARCHAR(2000) NULL,
    price_base NUMERIC(12,2) NOT NULL CHECK (price_base > 0),
    cost_price NUMERIC(12,2) NULL,
    image_url VARCHAR(500) NULL,
    preparation_time_minutes INTEGER NOT NULL DEFAULT 0,
    available BOOLEAN NOT NULL DEFAULT TRUE,
    is_featured BOOLEAN NOT NULL DEFAULT FALSE,
    calories_estimate NUMERIC(10,2) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_dishes_category_name UNIQUE (category_id, name)
);

CREATE INDEX IF NOT EXISTS ix_dishes_category_id
ON dishes(category_id);

CREATE TABLE IF NOT EXISTS recipe_ingredients (
    dish_id UUID NOT NULL REFERENCES dishes(id) ON DELETE CASCADE,
    ingredient_id UUID NOT NULL REFERENCES ingredients(id) ON DELETE RESTRICT,
    quantity NUMERIC(10,2) NOT NULL DEFAULT 0,
    unit VARCHAR(20) NOT NULL DEFAULT 'g',
    is_removable BOOLEAN NOT NULL DEFAULT FALSE,
    is_addable BOOLEAN NOT NULL DEFAULT FALSE,
    extra_price NUMERIC(12,2) NULL CHECK (extra_price >= 0),
    sort_order INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (dish_id, ingredient_id)
);

CREATE INDEX IF NOT EXISTS ix_recipe_ingredients_dish_id
ON recipe_ingredients(dish_id);

CREATE INDEX IF NOT EXISTS ix_recipe_ingredients_ingredient_id
ON recipe_ingredients(ingredient_id);

CREATE TABLE IF NOT EXISTS dish_diet_tags (
    dish_id UUID NOT NULL REFERENCES dishes(id) ON DELETE CASCADE,
    diet_tag_id UUID NOT NULL REFERENCES diet_tags(id) ON DELETE CASCADE,
    PRIMARY KEY (dish_id, diet_tag_id)
);
