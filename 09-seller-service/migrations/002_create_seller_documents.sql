-- Migration 002: Create seller_documents table

-- UP
CREATE TABLE IF NOT EXISTS seller_documents (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    seller_id   UUID NOT NULL REFERENCES sellers(id) ON DELETE CASCADE,
    type        VARCHAR(100) NOT NULL,
    file_url    VARCHAR(1024) NOT NULL,
    status      VARCHAR(50) NOT NULL DEFAULT 'pending',
    verified_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_seller_documents_seller_id ON seller_documents(seller_id);
CREATE INDEX idx_seller_documents_status ON seller_documents(status);

-- Down
DROP TABLE IF EXISTS seller_documents;
