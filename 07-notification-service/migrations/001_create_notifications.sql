-- Migration 001: Create notifications table

-- UP
CREATE TABLE IF NOT EXISTS notifications (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL,
    type        VARCHAR(100) NOT NULL,
    channel     VARCHAR(50) NOT NULL,
    title       VARCHAR(500) NOT NULL,
    body        TEXT NOT NULL,
    data        JSONB,
    status      VARCHAR(50) NOT NULL DEFAULT 'pending',
    read_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_type ON notifications(type);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_read_at ON notifications(read_at) WHERE read_at IS NOT NULL;

-- Down
DROP TABLE IF EXISTS notifications;
