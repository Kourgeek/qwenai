-- Migration 003: Create refunds table

-- UP
CREATE TABLE IF NOT EXISTS refunds (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id  UUID NOT NULL,
    amount      DECIMAL(15, 2) NOT NULL,
    reason      TEXT,
    status      VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_refunds_payment_id ON refunds(payment_id);
CREATE INDEX idx_refunds_status ON refunds(status);

-- Down
DROP TABLE IF EXISTS refunds;
