-- Migration 001: Create user_profiles table

-- UP
CREATE TABLE IF NOT EXISTS user_profiles (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    address      TEXT,
    phone        VARCHAR(50),
    avatar_url   VARCHAR(1024),
    preferences  JSONB,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_user_profiles_user_id ON user_profiles(user_id);

-- Down
DROP TABLE IF EXISTS user_profiles;
