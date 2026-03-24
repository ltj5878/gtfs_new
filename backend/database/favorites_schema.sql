-- 用户收藏表
CREATE TABLE IF NOT EXISTS user_favorites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    region TEXT NOT NULL,
    item_type TEXT NOT NULL,   -- 'route' 或 'stop'
    item_id TEXT NOT NULL,     -- route_id 或 stop_id
    item_name TEXT,            -- 冗余存储名称，减少连表查询
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, region, item_type, item_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (region) REFERENCES regions(region_id)
);

CREATE INDEX IF NOT EXISTS idx_user_favorites_user ON user_favorites(user_id);
