-- ============================================
-- 出行碳排放计算系统表结构
-- 功能：记录用户绿色出行与碳排放对比
-- ============================================

-- 线路距离缓存表
CREATE TABLE IF NOT EXISTS route_distances (
    route_id VARCHAR(50) NOT NULL,                   -- 线路ID
    region VARCHAR(20) NOT NULL,                     -- 地区
    direction_id INTEGER NOT NULL DEFAULT 0,         -- 方向
    distance_km DECIMAL(8,3),                        -- 距离（公里）
    calculated_at TIMESTAMP DEFAULT NOW(),           -- 计算时间
    PRIMARY KEY (route_id, region, direction_id)
);

-- 用户碳排放记录表
CREATE TABLE IF NOT EXISTS user_carbon_records (
    id SERIAL PRIMARY KEY,                           -- 主键
    user_id INTEGER,                                 -- 用户ID
    route_id VARCHAR(50),                            -- 线路ID
    region VARCHAR(20),                              -- 地区
    trip_date DATE DEFAULT CURRENT_DATE,             -- 出行日期
    distance_km DECIMAL(8,3),                        -- 行程距离
    transit_emission DECIMAL(8,4),                   -- 公交排放 kg CO2
    car_emission DECIMAL(8,4),                       -- 等效私家车排放
    carbon_saved DECIMAL(8,4),                       -- 节省 kg CO2
    created_at TIMESTAMP DEFAULT NOW()               -- 记录时间
);
CREATE INDEX IF NOT EXISTS idx_carbon_user ON user_carbon_records(user_id);
CREATE INDEX IF NOT EXISTS idx_carbon_date ON user_carbon_records(trip_date);
