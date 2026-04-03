-- ============================================
-- 站点客流预测系统表结构
-- 功能：基于班次密度预测各站点分时客流指数
-- ============================================

-- 站点客流预测表
CREATE TABLE IF NOT EXISTS stop_flow_predictions (
    id SERIAL PRIMARY KEY,                           -- 主键
    stop_id VARCHAR(50) NOT NULL,                    -- 站点ID
    region VARCHAR(20) NOT NULL,                     -- 地区
    day_type VARCHAR(10) NOT NULL,                   -- weekday/weekend
    hour_of_day SMALLINT NOT NULL,                   -- 0-23
    scheduled_trips INTEGER DEFAULT 0,               -- 计划班次数
    predicted_flow_index DECIMAL(8,2),               -- 相对客流指数（100=该站平均水平）
    computed_at TIMESTAMP DEFAULT NOW(),             -- 计算时间
    UNIQUE(stop_id, region, day_type, hour_of_day)
);
CREATE INDEX IF NOT EXISTS idx_flow_region ON stop_flow_predictions(region);
CREATE INDEX IF NOT EXISTS idx_flow_stop ON stop_flow_predictions(stop_id, region);
