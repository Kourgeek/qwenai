-- ============================================================
-- HyperScale Marketplace — Database Initialization
-- ============================================================

-- Create individual databases for each service
-- Note: PostgreSQL creates the main DB (marketplace) automatically
-- We create service-specific databases here

\c postgres

-- Auth database
SELECT 'CREATE DATABASE auth_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'auth_db')\gexec

-- User database
SELECT 'CREATE DATABASE user_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'user_db')\gexec

-- Catalog database
SELECT 'CREATE DATABASE catalog_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'catalog_db')\gexec

-- Cart database
SELECT 'CREATE DATABASE cart_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'cart_db')\gexec

-- Order database
SELECT 'CREATE DATABASE order_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'order_db')\gexec

-- Payment database
SELECT 'CREATE DATABASE payment_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'payment_db')\gexec

-- Notification database
SELECT 'CREATE DATABASE notification_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'notification_db')\gexec

-- Search database
SELECT 'CREATE DATABASE search_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'search_db')\gexec

-- Seller database
SELECT 'CREATE DATABASE seller_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'seller_db')\gexec

-- Admin database
SELECT 'CREATE DATABASE admin_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'admin_db')\gexec

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE auth_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE user_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE catalog_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE cart_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE order_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE payment_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE notification_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE search_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE seller_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE admin_db TO postgres;
