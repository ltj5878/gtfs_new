-- 用户订阅表（用户订阅关注的线路，设置准点率告警阈值）
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    route_id VARCHAR(100) NOT NULL,         -- 订阅的线路ID
    region VARCHAR(50) NOT NULL,            -- 线路所属地区
    threshold NUMERIC(5,2) NOT NULL DEFAULT 80.00,  -- 准点率阈值，低于此值触发通知
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, region, route_id)
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_route_region ON user_subscriptions(region, route_id);

-- 通知表（站内通知，包括准点率告警和系统公告）
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL DEFAULT 'alert',  -- 通知类型：alert(准点率告警), announcement(系统公告)
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL DEFAULT '',
    route_id VARCHAR(100),                  -- 关联线路ID（公告类型为 NULL）
    region VARCHAR(50),                     -- 关联地区（公告类型为 NULL）
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_user_created ON notifications(user_id, created_at DESC);
