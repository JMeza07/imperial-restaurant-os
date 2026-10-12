DO $$
BEGIN
    CREATE TYPE stock_movement_direction AS ENUM ('IN', 'OUT');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE stock_movement_type AS ENUM (
        'INICIAL',
        'COMPRA',
        'VENTA',
        'DEVOLUCION_VENTA',
        'AJUSTE_ENTRADA',
        'AJUSTE_SALIDA',
        'DESPERDICIO'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE purchase_order_status AS ENUM (
        'BORRADOR',
        'RECIBIDA',
        'ANULADA'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    contact_name VARCHAR(255) NULL,
    phone VARCHAR(50) NULL,
    email VARCHAR(255) NULL,
    address VARCHAR(500) NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS stock_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_id UUID NULL REFERENCES branches(id) ON DELETE SET NULL,
    ingredient_id UUID NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    quantity NUMERIC(14,3) NOT NULL DEFAULT 0,
    min_quantity NUMERIC(14,3) NOT NULL DEFAULT 0,
    last_unit_cost NUMERIC(12,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_stock_items_branch_ingredient UNIQUE (branch_id, ingredient_id)
);

CREATE INDEX IF NOT EXISTS ix_stock_items_branch_id
ON stock_items(branch_id);

CREATE INDEX IF NOT EXISTS ix_stock_items_ingredient_id
ON stock_items(ingredient_id);

CREATE TABLE IF NOT EXISTS purchase_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_id UUID NULL REFERENCES branches(id) ON DELETE SET NULL,
    supplier_id UUID NOT NULL REFERENCES suppliers(id) ON DELETE RESTRICT,
    status purchase_order_status NOT NULL DEFAULT 'BORRADOR',
    order_date TIMESTAMPTZ NOT NULL DEFAULT now(),
    received_at TIMESTAMPTZ NULL,
    total NUMERIC(12,2) NOT NULL DEFAULT 0,
    notes VARCHAR(2000) NULL,
    created_by_user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_purchase_orders_branch_id
ON purchase_orders(branch_id);

CREATE INDEX IF NOT EXISTS ix_purchase_orders_supplier_id
ON purchase_orders(supplier_id);

CREATE INDEX IF NOT EXISTS ix_purchase_orders_status
ON purchase_orders(status);

CREATE TABLE IF NOT EXISTS purchase_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_order_id UUID NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    ingredient_id UUID NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    quantity NUMERIC(14,3) NOT NULL CHECK (quantity > 0),
    unit_cost NUMERIC(12,2) NOT NULL CHECK (unit_cost >= 0),
    received_quantity NUMERIC(14,3) NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS ix_purchase_items_purchase_order_id
ON purchase_items(purchase_order_id);

CREATE INDEX IF NOT EXISTS ix_purchase_items_ingredient_id
ON purchase_items(ingredient_id);

CREATE TABLE IF NOT EXISTS stock_movements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_id UUID NULL REFERENCES branches(id) ON DELETE SET NULL,
    stock_item_id UUID NOT NULL REFERENCES stock_items(id) ON DELETE CASCADE,
    ingredient_id UUID NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    movement_type stock_movement_type NOT NULL,
    direction stock_movement_direction NOT NULL,
    quantity NUMERIC(14,3) NOT NULL CHECK (quantity > 0),
    stock_after NUMERIC(14,3) NOT NULL,
    unit_cost NUMERIC(12,2) NULL,
    order_item_id UUID NULL REFERENCES order_items(id) ON DELETE SET NULL,
    purchase_order_id UUID NULL REFERENCES purchase_orders(id) ON DELETE SET NULL,
    created_by_user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,
    note VARCHAR(1000) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_stock_movements_branch_id
ON stock_movements(branch_id);

CREATE INDEX IF NOT EXISTS ix_stock_movements_stock_item_id
ON stock_movements(stock_item_id);

CREATE INDEX IF NOT EXISTS ix_stock_movements_ingredient_id
ON stock_movements(ingredient_id);

CREATE INDEX IF NOT EXISTS ix_stock_movements_movement_type
ON stock_movements(movement_type);

CREATE INDEX IF NOT EXISTS ix_stock_movements_order_item_id
ON stock_movements(order_item_id);

CREATE INDEX IF NOT EXISTS ix_stock_movements_purchase_order_id
ON stock_movements(purchase_order_id);

CREATE TABLE IF NOT EXISTS waste_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_id UUID NULL REFERENCES branches(id) ON DELETE SET NULL,
    ingredient_id UUID NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    quantity NUMERIC(14,3) NOT NULL CHECK (quantity > 0),
    reason VARCHAR(1000) NULL,
    created_by_user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_waste_events_branch_id
ON waste_events(branch_id);

CREATE INDEX IF NOT EXISTS ix_waste_events_ingredient_id
ON waste_events(ingredient_id);
