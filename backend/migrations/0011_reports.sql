CREATE INDEX IF NOT EXISTS ix_orders_paid_at
ON orders(paid_at);

CREATE INDEX IF NOT EXISTS ix_orders_status_paid_at
ON orders(status, paid_at);

CREATE INDEX IF NOT EXISTS ix_order_items_created_at
ON order_items(created_at);

CREATE INDEX IF NOT EXISTS ix_payments_created_at
ON payments(created_at);

CREATE INDEX IF NOT EXISTS ix_payments_approved_at
ON payments(approved_at);

CREATE INDEX IF NOT EXISTS ix_surveys_created_at
ON surveys(created_at);

CREATE INDEX IF NOT EXISTS ix_stock_movements_created_at
ON stock_movements(created_at);

CREATE INDEX IF NOT EXISTS ix_waste_events_created_at
ON waste_events(created_at);

CREATE INDEX IF NOT EXISTS ix_deliveries_delivered_at
ON deliveries(delivered_at);

CREATE INDEX IF NOT EXISTS ix_commission_events_created_at
ON commission_events(created_at);

CREATE INDEX IF NOT EXISTS ix_commission_payouts_created_at
ON commission_payouts(created_at);
