-- Migration 001: Create saved_carts table

-- UP
CREATE TABLE IF NOT EXISTS saved_carts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL,
    items       JSONB NOT NULL,
    saved_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_saved_carts_user_id ON saved_carts(user_id);
CREATE INDEX idx_saved_carts_updated_at ON saved_carts(updated_at);

-- Down
DROP TABLE IF EXISTS saved_carts;
