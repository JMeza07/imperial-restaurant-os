ALTER TABLE orders
ADD COLUMN IF NOT EXISTS waiter_id UUID NULL REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS ix_orders_waiter_id
ON orders(waiter_id);

DO $$
BEGIN
    CREATE TYPE commission_rule_type AS ENUM (
        'PERCENT_NET_SALES',
        'FIXED_PER_ORDER',
        'PERCENT_ITEM_SALES',
        'FIXED_PER_ITEM',
        'FIXED_PER_DELIVERY',
        'SURVEY_BONUS_FIXED'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE commission_period_status AS ENUM (
        'ABIERTA',
        'CALCULADA',
        'APROBADA',
        'PAGADA',
        'ANULADA'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE commission_event_status AS ENUM (
        'CALCULADA',
        'APROBADA',
        'ANULADA'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE commission_payout_status AS ENUM (
        'PENDIENTE',
        'PAGADO',
        'ANULADO'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS commission_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    rule_type commission_rule_type NOT NULL,
    value NUMERIC(12,2) NOT NULL CHECK (value >= 0),
    cap_per_order NUMERIC(12,2) NULL CHECK (cap_per_order >= 0),
    cap_per_period NUMERIC(12,2) NULL CHECK (cap_per_period >= 0),
    conditions JSONB NOT NULL DEFAULT '{}',
    starts_at DATE NULL,
    ends_at DATE NULL,
    priority INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS commission_periods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_id UUID NULL REFERENCES branches(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status commission_period_status NOT NULL DEFAULT 'ABIERTA',
    calculated_at TIMESTAMPTZ NULL,
    approved_at TIMESTAMPTZ NULL,
    paid_at TIMESTAMPTZ NULL,
    notes VARCHAR(2000) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_commission_periods_dates CHECK (end_date >= start_date)
);

CREATE INDEX IF NOT EXISTS ix_commission_periods_branch_id
ON commission_periods(branch_id);

CREATE INDEX IF NOT EXISTS ix_commission_periods_status
ON commission_periods(status);

CREATE TABLE IF NOT EXISTS commission_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    period_id UUID NOT NULL REFERENCES commission_periods(id) ON DELETE CASCADE,
    rule_id UUID NOT NULL REFERENCES commission_rules(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    order_id UUID NULL REFERENCES orders(id) ON DELETE SET NULL,
    order_item_id UUID NULL REFERENCES order_items(id) ON DELETE SET NULL,
    base_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    amount NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (amount >= 0),
    status commission_event_status NOT NULL DEFAULT 'CALCULADA',
    dedup_key VARCHAR(500) NOT NULL UNIQUE,
    detail JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_commission_events_period_id
ON commission_events(period_id);

CREATE INDEX IF NOT EXISTS ix_commission_events_rule_id
ON commission_events(rule_id);

CREATE INDEX IF NOT EXISTS ix_commission_events_employee_id
ON commission_events(employee_id);

CREATE INDEX IF NOT EXISTS ix_commission_events_order_id
ON commission_events(order_id);

CREATE TABLE IF NOT EXISTS commission_payouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    period_id UUID NOT NULL REFERENCES commission_periods(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    amount NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
    status commission_payout_status NOT NULL DEFAULT 'PENDIENTE',
    payment_method VARCHAR(50) NULL,
    reference VARCHAR(255) NULL,
    paid_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_commission_payouts_period_employee UNIQUE (period_id, employee_id)
);

CREATE INDEX IF NOT EXISTS ix_commission_payouts_period_id
ON commission_payouts(period_id);

CREATE INDEX IF NOT EXISTS ix_commission_payouts_employee_id
ON commission_payouts(employee_id);

CREATE TABLE IF NOT EXISTS surveys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL UNIQUE REFERENCES orders(id) ON DELETE CASCADE,
    food_score INTEGER NOT NULL CHECK (food_score >= 1 AND food_score <= 5),
    service_score INTEGER NOT NULL CHECK (service_score >= 1 AND service_score <= 5),
    general_score INTEGER NOT NULL CHECK (general_score >= 1 AND general_score <= 5),
    comment VARCHAR(2000) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_surveys_order_id
ON surveys(order_id);
