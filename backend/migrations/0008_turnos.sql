DO $$
BEGIN
    CREATE TYPE shift_status AS ENUM (
        'PROGRAMADO',
        'CONFIRMADO',
        'EN_TURNO',
        'EN_DESCANSO',
        'FINALIZADO',
        'AUSENTE',
        'CANCELADO'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE shift_event_type AS ENUM (
        'CLOCK_IN',
        'CLOCK_OUT',
        'BREAK_START',
        'BREAK_END',
        'STATUS_CHANGED'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    branch_id UUID NULL REFERENCES branches(id) ON DELETE SET NULL,
    employee_code VARCHAR(50) NOT NULL UNIQUE,
    document_number VARCHAR(50) NULL UNIQUE,
    position VARCHAR(255) NULL,
    hourly_wage NUMERIC(12,2) NULL CHECK (hourly_wage >= 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_employees_branch_id
ON employees(branch_id);

CREATE TABLE IF NOT EXISTS shift_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_id UUID NULL REFERENCES branches(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    weekdays JSONB NOT NULL DEFAULT '[]',
    notes VARCHAR(2000) NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_shift_templates_branch_id
ON shift_templates(branch_id);

CREATE TABLE IF NOT EXISTS shifts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    branch_id UUID NULL REFERENCES branches(id) ON DELETE SET NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PROGRAMADO',
    scheduled_start TIMESTAMPTZ NOT NULL,
    scheduled_end TIMESTAMPTZ NOT NULL,
    actual_start TIMESTAMPTZ NULL,
    actual_end TIMESTAMPTZ NULL,
    notes VARCHAR(2000) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_shifts_employee_scheduled_start UNIQUE (employee_id, scheduled_start),
    CONSTRAINT ck_shifts_schedule CHECK (scheduled_end > scheduled_start)
);

CREATE INDEX IF NOT EXISTS ix_shifts_employee_id
ON shifts(employee_id);

CREATE INDEX IF NOT EXISTS ix_shifts_branch_id
ON shifts(branch_id);

CREATE INDEX IF NOT EXISTS ix_shifts_status
ON shifts(status);

CREATE INDEX IF NOT EXISTS ix_shifts_scheduled_start
ON shifts(scheduled_start);

CREATE TABLE IF NOT EXISTS shift_breaks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shift_id UUID NOT NULL REFERENCES shifts(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at TIMESTAMPTZ NULL,
    notes VARCHAR(1000) NULL,
    CONSTRAINT ck_shift_breaks_time CHECK (ended_at IS NULL OR ended_at >= started_at)
);

CREATE INDEX IF NOT EXISTS ix_shift_breaks_shift_id
ON shift_breaks(shift_id);

CREATE TABLE IF NOT EXISTS clock_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shift_id UUID NOT NULL REFERENCES shifts(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    ip_address VARCHAR(45) NULL,
    device VARCHAR(255) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_clock_events_shift_id
ON clock_events(shift_id);

CREATE INDEX IF NOT EXISTS ix_clock_events_employee_id
ON clock_events(employee_id);

CREATE INDEX IF NOT EXISTS ix_clock_events_event_type
ON clock_events(event_type);

CREATE TABLE IF NOT EXISTS shift_assignments (
    shift_id UUID NOT NULL REFERENCES shifts(id) ON DELETE CASCADE,
    table_id UUID NOT NULL REFERENCES tables(id) ON DELETE CASCADE,
    PRIMARY KEY (shift_id, table_id)
);

CREATE INDEX IF NOT EXISTS ix_shift_assignments_table_id
ON shift_assignments(table_id);
