-- Migration 002: Create addresses table

-- UP
CREATE TABLE IF NOT EXISTS addresses (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type         VARCHAR(50) NOT NULL,
    street       VARCHAR(500) NOT NULL,
    city         VARCHAR(200) NOT NULL,
    state        VARCHAR(200),
    postal_code  VARCHAR(20) NOT NULL,
    country      VARCHAR(100) NOT NULL,
    is_default   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_addresses_user_id ON addresses(user_id);

-- Down
DROP TABLE IF EXISTS addresses;
