-- Migration 001: Create sellers table

-- UP
CREATE TABLE IF NOT EXISTS sellers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL,
    business_name   VARCHAR(300) NOT NULL,
    tax_id          VARCHAR(100),
    status          VARCHAR(50) NOT NULL DEFAULT 'pending',
    verified_at     TIMESTAMPTZ,
    commission_rate DECIMAL(5, 4) NOT NULL DEFAULT 0.1000,
    bank_details    JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_sellers_user_id ON sellers(user_id);
CREATE INDEX idx_sellers_status ON sellers(status);

-- Down
DROP TABLE IF EXISTS sellers;
