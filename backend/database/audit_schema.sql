-- 审计日志表（记录管理员和用户的关键操作，便于审计追溯）
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,                    -- 操作用户ID，未登录时为 NULL
    username VARCHAR(50),               -- 冗余存储用户名，方便查询展示
    action VARCHAR(50) NOT NULL,        -- 操作类型：login, login_failed, register, logout, create_user, delete_user, toggle_user, reset_password, change_password, refresh_punctuality
    target VARCHAR(100),                -- 操作对象：如 "user:5", "punctuality:sf"
    detail JSONB DEFAULT '{}',          -- 操作详情 JSON
    ip_address VARCHAR(45),             -- 客户端 IP（支持 IPv6）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引：覆盖主要筛选维度
CREATE INDEX IF NOT EXISTS idx_audit_logs_time ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
