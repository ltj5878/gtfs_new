-- ============================================
-- 异常检测与告警系统表结构
-- 功能：记录实时异常检测告警
-- ============================================

-- 异常告警表
CREATE TABLE IF NOT EXISTS anomaly_alerts (
    id SERIAL PRIMARY KEY,                           -- 主键
    region VARCHAR(20) NOT NULL,                     -- 地区
    alert_type VARCHAR(50) NOT NULL,                 -- 告警类型：vehicle_stall/route_delay/stop_congestion/segment_slow
    entity_type VARCHAR(20) NOT NULL,                -- 实体类型：route/stop/vehicle
    entity_id VARCHAR(100) NOT NULL,                 -- 实体ID
    entity_name VARCHAR(200),                        -- 实体名称（冗余方便展示）
    severity VARCHAR(10) NOT NULL DEFAULT 'medium',  -- 严重程度：low/medium/high/critical
    title VARCHAR(200) NOT NULL,                     -- 告警标题
    alert_data JSONB,                                -- 告警详情（延误分钟数等）
    triggered_at TIMESTAMP NOT NULL DEFAULT NOW(),   -- 触发时间
    resolved_at TIMESTAMP,                           -- 解决时间（NULL=未解决）
    notified BOOLEAN DEFAULT FALSE                   -- 是否已推送通知
);
CREATE INDEX IF NOT EXISTS idx_alerts_region ON anomaly_alerts(region);
CREATE INDEX IF NOT EXISTS idx_alerts_active ON anomaly_alerts(region, resolved_at) WHERE resolved_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_alerts_time ON anomaly_alerts(triggered_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON anomaly_alerts(alert_type);
