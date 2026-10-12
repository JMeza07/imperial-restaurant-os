ALTER TABLE order_items
ADD COLUMN IF NOT EXISTS prepared_by_user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE order_items
ADD COLUMN IF NOT EXISTS ready_by_user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE order_items
ADD COLUMN IF NOT EXISTS delivered_by_user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE order_items
ADD COLUMN IF NOT EXISTS cancelled_by_user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS ix_order_items_prepared_by_user_id
ON order_items(prepared_by_user_id);

CREATE INDEX IF NOT EXISTS ix_order_items_ready_by_user_id
ON order_items(ready_by_user_id);

CREATE INDEX IF NOT EXISTS ix_order_items_delivered_by_user_id
ON order_items(delivered_by_user_id);

CREATE INDEX IF NOT EXISTS ix_order_items_cancelled_by_user_id
ON order_items(cancelled_by_user_id);
