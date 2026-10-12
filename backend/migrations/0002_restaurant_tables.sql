CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
BEGIN
    CREATE TYPE table_status AS ENUM (
        'LIBRE',
        'OCUPADA',
        'RESERVADA',
        'BLOQUEADA'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS restaurants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255) NULL,
    nit VARCHAR(50) NULL,
    address VARCHAR(255) NULL,
    phone VARCHAR(50) NULL,
    email VARCHAR(255) NULL,
    logo_url VARCHAR(500) NULL,
    primary_color VARCHAR(20) NULL,
    secondary_color VARCHAR(20) NULL,
    default_tax_rate NUMERIC(5,2) NOT NULL DEFAULT 0.08,
    default_tip_rate NUMERIC(5,2) NOT NULL DEFAULT 0.10,
    currency VARCHAR(3) NOT NULL DEFAULT 'COP',
    timezone VARCHAR(100) NOT NULL DEFAULT 'America/Bogota',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS branches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    address VARCHAR(255) NULL,
    phone VARCHAR(50) NULL,
    latitude NUMERIC(9,6) NULL,
    longitude NUMERIC(9,6) NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_branches_restaurant_name UNIQUE (restaurant_id, name)
);

CREATE INDEX IF NOT EXISTS ix_branches_restaurant_id
ON branches(restaurant_id);

CREATE TABLE IF NOT EXISTS zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_id UUID NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description VARCHAR(500) NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_zones_branch_name UNIQUE (branch_id, name)
);

CREATE INDEX IF NOT EXISTS ix_zones_branch_id
ON zones(branch_id);

CREATE TABLE IF NOT EXISTS tables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_id UUID NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
    zone_id UUID NULL REFERENCES zones(id) ON DELETE SET NULL,
    number INTEGER NOT NULL CHECK (number > 0),
    capacity INTEGER NOT NULL DEFAULT 4 CHECK (capacity > 0),
    status table_status NOT NULL DEFAULT 'LIBRE',
    qr_code UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_tables_branch_number UNIQUE (branch_id, number)
);

CREATE INDEX IF NOT EXISTS ix_tables_branch_id
ON tables(branch_id);

CREATE INDEX IF NOT EXISTS ix_tables_zone_id
ON tables(zone_id);

CREATE INDEX IF NOT EXISTS ix_tables_qr_code
ON tables(qr_code);

CREATE INDEX IF NOT EXISTS ix_tables_status
ON tables(status);
