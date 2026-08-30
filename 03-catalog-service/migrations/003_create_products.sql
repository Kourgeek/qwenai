-- Migration 003: Create products table

-- UP
CREATE TABLE IF NOT EXISTS products (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name             VARCHAR(500) NOT NULL,
    slug             VARCHAR(500) NOT NULL UNIQUE,
    description      TEXT,
    category_id      UUID REFERENCES categories(id) ON DELETE SET NULL,
    brand_id         UUID REFERENCES brands(id) ON DELETE SET NULL,
    price            FLOAT NOT NULL,
    compare_at_price FLOAT,
    sku              VARCHAR(100) UNIQUE,
    stock_quantity   INTEGER NOT NULL DEFAULT 0,
    image_urls       JSONB,
    tag_ids          JSONB,
    metadata         JSONB,
    is_active        BOOLEAN NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_products_category_id ON products(category_id);
CREATE INDEX idx_products_brand_id ON products(brand_id);
CREATE INDEX idx_products_is_active ON products(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_products_sku ON products(sku) WHERE sku IS NOT NULL;

-- Down
DROP TABLE IF EXISTS products;
