-- Migration 001: Create payments table

-- UP
CREATE TABLE IF NOT EXISTS payments (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id              UUID NOT NULL,
    amount                DECIMAL(15, 2) NOT NULL,
    currency              VARCHAR(3) NOT NULL DEFAULT 'USD',
    status                VARCHAR(50) NOT NULL DEFAULT 'pending',
    payment_method        VARCHAR(50),
    provider              VARCHAR(100),
    provider_payment_id   VARCHAR(500),
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_payments_order_id ON payments(order_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_provider_payment_id ON payments(provider_payment_id) WHERE provider_payment_id IS NOT NULL;

-- Down
DROP TABLE IF EXISTS payments;
