-- Migration: Add seller_id to products table
-- Description: Links products to sellers for the seller dashboard

-- Add seller_id column
ALTER TABLE products ADD COLUMN IF NOT EXISTS seller_id UUID REFERENCES sellers(id) ON DELETE SET NULL;

-- Add index for faster queries
CREATE INDEX IF NOT EXISTS idx_products_seller_id ON products(seller_id);

-- Add comment
COMMENT ON COLUMN products.seller_id IS 'Reference to the seller who owns this product';
