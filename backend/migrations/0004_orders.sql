DO $$
BEGIN
    CREATE TYPE order_type AS ENUM ('MESA', 'DOMICILIO');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE order_status AS ENUM ('ABIERTA', 'CERRADA', 'PAGADA', 'ENCUESTADA', 'CANCELADA');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE order_item_status AS ENUM ('RECIBIDO', 'EN_PREPARACION', 'LISTO', 'ENTREGADO', 'CANCELADO');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE modification_action AS ENUM ('QUITAR', 'AGREGAR');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE order_channel AS ENUM ('QR', 'STAFF');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    display_code VARCHAR(20) NULL,

    branch_id UUID NULL REFERENCES branches(id) ON DELETE SET NULL,
    table_id UUID NULL REFERENCES tables(id) ON DELETE SET NULL,

    order_type order_type NOT NULL DEFAULT 'MESA',
    status order_status NOT NULL DEFAULT 'ABIERTA',
    channel order_channel NOT NULL DEFAULT 'QR',

    customer_name VARCHAR(255) NULL,
    customer_phone VARCHAR(50) NULL,
    customer_address VARCHAR(500) NULL,

    notes VARCHAR(2000) NULL,

    subtotal NUMERIC(12,2) NOT NULL DEFAULT 0,
    tax_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    tip_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    delivery_fee NUMERIC(12,2) NOT NULL DEFAULT 0,
    discount_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    total NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_paid NUMERIC(12,2) NOT NULL DEFAULT 0,

    opened_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at TIMESTAMPTZ NULL,
    paid_at TIMESTAMPTZ NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_orders_open_table
ON orders(table_id)
WHERE status = 'ABIERTA';

CREATE INDEX IF NOT EXISTS ix_orders_branch_id
ON orders(branch_id);

CREATE INDEX IF NOT EXISTS ix_orders_table_id
ON orders(table_id);

CREATE INDEX IF NOT EXISTS ix_orders_status
ON orders(status);

CREATE INDEX IF NOT EXISTS ix_orders_order_type
ON orders(order_type);

CREATE TABLE IF NOT EXISTS order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    dish_id UUID NOT NULL REFERENCES dishes(id) ON DELETE RESTRICT,

    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
    subtotal NUMERIC(12,2) NOT NULL CHECK (subtotal >= 0),

    status order_item_status NOT NULL DEFAULT 'RECIBIDO',
    observations VARCHAR(1000) NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    prepared_at TIMESTAMPTZ NULL,
    ready_at TIMESTAMPTZ NULL,
    delivered_at TIMESTAMPTZ NULL,
    cancelled_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_order_items_order_id
ON order_items(order_id);

CREATE INDEX IF NOT EXISTS ix_order_items_dish_id
ON order_items(dish_id);

CREATE INDEX IF NOT EXISTS ix_order_items_status
ON order_items(status);

CREATE TABLE IF NOT EXISTS item_modifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_item_id UUID NOT NULL REFERENCES order_items(id) ON DELETE CASCADE,
    ingredient_id UUID NOT NULL REFERENCES ingredients(id) ON DELETE RESTRICT,

    ingredient_name VARCHAR(255) NOT NULL,
    action modification_action NOT NULL,
    extra_cost NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (extra_cost >= 0),

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_item_modifications_order_item_id
ON item_modifications(order_item_id);

CREATE INDEX IF NOT EXISTS ix_item_modifications_ingredient_id
ON item_modifications(ingredient_id);

CREATE TABLE IF NOT EXISTS order_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    order_item_id UUID NULL REFERENCES order_items(id) ON DELETE SET NULL,
    actor_user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,

    actor_role VARCHAR(50) NULL,
    action VARCHAR(255) NOT NULL,
    detail JSONB NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_order_events_order_id
ON order_events(order_id);

CREATE INDEX IF NOT EXISTS ix_order_events_order_item_id
ON order_events(order_item_id);

CREATE INDEX IF NOT EXISTS ix_order_events_actor_user_id
ON order_events(actor_user_id);

CREATE INDEX IF NOT EXISTS ix_order_events_action
ON order_events(action);
