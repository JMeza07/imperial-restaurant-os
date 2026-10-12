DO $$
BEGIN
    CREATE TYPE payment_method AS ENUM (
        'EFECTIVO',
        'TARJETA',
        'TRANSFERENCIA',
        'NEQUI',
        'DAVIPLATA',
        'OTRO'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE payment_status AS ENUM (
        'PENDIENTE',
        'APROBADO',
        'RECHAZADO',
        'REEMBOLSADO'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE cash_session_status AS ENUM ('ABIERTA', 'CERRADA');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS cash_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    branch_id UUID NULL REFERENCES branches(id) ON DELETE SET NULL,
    opened_by_user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,
    closed_by_user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,

    status cash_session_status NOT NULL DEFAULT 'ABIERTA',

    opening_amount NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (opening_amount >= 0),
    closing_amount NUMERIC(12,2) NULL CHECK (closing_amount >= 0),
    expected_amount NUMERIC(12,2) NULL CHECK (expected_amount >= 0),

    notes VARCHAR(2000) NULL,

    opened_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at TIMESTAMPTZ NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_cash_sessions_open_branch
ON cash_sessions(branch_id)
WHERE status = 'ABIERTA';

CREATE INDEX IF NOT EXISTS ix_cash_sessions_branch_id
ON cash_sessions(branch_id);

CREATE INDEX IF NOT EXISTS ix_cash_sessions_status
ON cash_sessions(status);

CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,

    payment_method payment_method NOT NULL,
    status payment_status NOT NULL DEFAULT 'APROBADO',

    amount NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    reference VARCHAR(255) NULL,
    note VARCHAR(1000) NULL,

    cash_session_id UUID NULL REFERENCES cash_sessions(id) ON DELETE SET NULL,
    registered_by_user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    approved_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_payments_order_id
ON payments(order_id);

CREATE INDEX IF NOT EXISTS ix_payments_cash_session_id
ON payments(cash_session_id);

CREATE INDEX IF NOT EXISTS ix_payments_registered_by_user_id
ON payments(registered_by_user_id);

CREATE INDEX IF NOT EXISTS ix_payments_status
ON payments(status);

CREATE INDEX IF NOT EXISTS ix_payments_payment_method
ON payments(payment_method);
