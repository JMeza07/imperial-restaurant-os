-- Índices para queries frecuentes
CREATE INDEX IF NOT EXISTS ix_dishes_available
ON dishes(available);

CREATE INDEX IF NOT EXISTS ix_dishes_category_available
ON dishes(category_id, available);

CREATE INDEX IF NOT EXISTS ix_ingredients_available
ON ingredients(available);

CREATE INDEX IF NOT EXISTS ix_orders_created_at
ON orders(created_at DESC);

CREATE INDEX IF NOT EXISTS ix_orders_table_status
ON orders(table_id, status);

CREATE INDEX IF NOT EXISTS ix_order_items_status_created
ON order_items(status, created_at);

CREATE INDEX IF NOT EXISTS ix_order_items_order_status
ON order_items(order_id, status);

CREATE INDEX IF NOT EXISTS ix_audit_logs_user_created
ON audit_logs(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_audit_logs_resource_id
ON audit_logs(resource_id);

-- Índices parciales para hot path
CREATE INDEX IF NOT EXISTS ix_orders_open
ON orders(status)
WHERE status = 'ABIERTA';

CREATE INDEX IF NOT EXISTS ix_order_items_pending
ON order_items(status, created_at)
WHERE status IN ('RECIBIDO', 'EN_PREPARACION');

CREATE INDEX IF NOT EXISTS ix_order_items_ready
ON order_items(status, ready_at)
WHERE status = 'LISTO';

-- Tabla para feature flags
CREATE TABLE IF NOT EXISTS feature_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    enabled BOOLEAN NOT NULL DEFAULT FALSE,
    description VARCHAR(500) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Tabla para API keys externas (futuras integraciones)
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,
    scopes JSONB NOT NULL DEFAULT '[]',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at TIMESTAMPTZ NULL,
    last_used_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_api_keys_user_id
ON api_keys(user_id);

CREATE INDEX IF NOT EXISTS ix_api_keys_active
ON api_keys(is_active);
