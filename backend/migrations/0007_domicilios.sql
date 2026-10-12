ALTER TYPE order_channel ADD VALUE IF NOT EXISTS 'WEB';

DO $$
BEGIN
    CREATE TYPE delivery_status AS ENUM (
        'PENDIENTE',
        'ASIGNADO',
        'EN_CAMINO',
        'ENTREGADO',
        'CANCELADO'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS delivery_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    branch_id UUID NULL REFERENCES branches(id) ON DELETE SET NULL,

    name VARCHAR(255) NOT NULL,
    description VARCHAR(1000) NULL,

    delivery_fee NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (delivery_fee >= 0),
    max_distance_km NUMERIC(6,2) NOT NULL DEFAULT 5.00 CHECK (max_distance_km >= 0),

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_delivery_zones_branch_name UNIQUE (branch_id, name)
);

CREATE INDEX IF NOT EXISTS ix_delivery_zones_branch_id
ON delivery_zones(branch_id);

CREATE TABLE IF NOT EXISTS deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    order_id UUID NOT NULL UNIQUE REFERENCES orders(id) ON DELETE CASCADE,
    delivery_zone_id UUID NULL REFERENCES delivery_zones(id) ON DELETE SET NULL,

    customer_name VARCHAR(255) NOT NULL,
    customer_phone VARCHAR(50) NOT NULL,
    customer_address VARCHAR(500) NOT NULL,

    delivery_fee NUMERIC(12,2) NOT NULL CHECK (delivery_fee >= 0),

    status delivery_status NOT NULL DEFAULT 'PENDIENTE',

    assigned_domiciliario_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,

    assigned_at TIMESTAMPTZ NULL,
    enroute_at TIMESTAMPTZ NULL,
    delivered_at TIMESTAMPTZ NULL,
    cancelled_at TIMESTAMPTZ NULL,

    notes VARCHAR(2000) NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_deliveries_order_id
ON deliveries(order_id);

CREATE INDEX IF NOT EXISTS ix_deliveries_delivery_zone_id
ON deliveries(delivery_zone_id);

CREATE INDEX IF NOT EXISTS ix_deliveries_status
ON deliveries(status);

CREATE INDEX IF NOT EXISTS ix_deliveries_assigned_domiciliario_id
ON deliveries(assigned_domiciliario_id);
