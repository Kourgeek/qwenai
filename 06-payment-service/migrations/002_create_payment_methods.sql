-- Migration 002: Create payment_methods table

-- UP
CREATE TABLE IF NOT EXISTS payment_methods (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL,
    type        VARCHAR(50) NOT NULL,
    last_four   VARCHAR(4),
    expiry_month INTEGER,
    expiry_year  INTEGER,
    is_default  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_payment_methods_user_id ON payment_methods(user_id);

-- Down
DROP TABLE IF EXISTS payment_methods;
